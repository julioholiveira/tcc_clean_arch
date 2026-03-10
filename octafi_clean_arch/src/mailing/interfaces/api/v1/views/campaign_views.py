"""
Views para campanhas de mailing.
Resolve P1 (SRP): cada view tem uma responsabilidade.
"""

import structlog
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from src.core.domain.value_objects import CompanyId
from src.mailing.application.dto.campaign import (
    CreateCampaignRequest,
    ScheduleCampaignRequest,
    SendBulkSMSRequest,
    UpdateCampaignRequest,
)
from src.mailing.interfaces.api.v1.dependencies import (
    build_create_campaign_use_case,
    build_schedule_campaign_use_case,
    build_send_bulk_sms_use_case,
    build_update_campaign_use_case,
)
from src.mailing.interfaces.api.v1.serializers.campaign_serializers import (
    CampaignOutputSerializer,
    CreateCampaignInputSerializer,
    ScheduleCampaignInputSerializer,
    ScheduleCampaignOutputSerializer,
    SendCampaignInputSerializer,
    SendCampaignOutputSerializer,
    UpdateCampaignInputSerializer,
)

logger = structlog.get_logger(__name__)


def _resolve_empresa(request):
    """Resolve empresa a partir do header X-Empresa-ID."""
    from empresas.models import Empresa

    empresa_id = request.headers.get("X-Empresa-ID")
    if not empresa_id:
        raise ValueError("Header X-Empresa-ID é obrigatório")
    try:
        return Empresa.objects.get(pk=int(empresa_id))
    except Exception:
        raise ValueError(f"Empresa {empresa_id} não encontrada")


class CampaignListCreateView(APIView):
    """
    GET  /api/v1/mailing/campaigns/  — lista campanhas da empresa
    POST /api/v1/mailing/campaigns/  — cria nova campanha
    """

    def get(self, request):
        try:
            empresa = _resolve_empresa(request)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        from src.mailing.infrastructure.repositories.campaign_repository import DjangoCampaignRepository

        repo = DjangoCampaignRepository()
        try:
            limit = int(request.query_params.get("limit", 50))
            offset = int(request.query_params.get("offset", 0))
        except (ValueError, TypeError):
            return Response({"detail": "limit/offset inválidos"}, status=status.HTTP_400_BAD_REQUEST)

        campaigns = repo.list_by_company(CompanyId(empresa.id), limit=limit, offset=offset)
        data = [
            {"id": c.id, "name": c.name, "status": c.status.value}
            for c in campaigns
        ]
        return Response({"total": len(data), "campaigns": data, "limit": limit, "offset": offset})

    def post(self, request):
        try:
            empresa = _resolve_empresa(request)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CreateCampaignInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        data = serializer.validated_data
        create_request = CreateCampaignRequest(
            company_id=CompanyId(empresa.id),
            name=data["name"],
            template_id=data["template_id"],
            scheduled_for=data.get("scheduled_for"),
        )

        use_case = build_create_campaign_use_case()
        result = use_case.execute(create_request)

        logger.info("campaign_create", empresa_id=empresa.id, success=result.success)
        http_status = status.HTTP_201_CREATED if result.success else status.HTTP_400_BAD_REQUEST
        return Response(CampaignOutputSerializer(result).data, status=http_status)


class CampaignDetailView(APIView):
    """
    PATCH /api/v1/mailing/campaigns/<campaign_id>/  — atualiza campanha
    """

    def patch(self, request, campaign_id: int):
        try:
            _resolve_empresa(request)  # validates empresa header
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UpdateCampaignInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        data = serializer.validated_data
        update_request = UpdateCampaignRequest(
            campaign_id=campaign_id,
            name=data.get("name"),
            template_id=data.get("template_id"),
            scheduled_for=data.get("scheduled_for"),
        )

        use_case = build_update_campaign_use_case()
        result = use_case.execute(update_request)

        logger.info("campaign_update", campaign_id=campaign_id, success=result.success)
        http_status = status.HTTP_200_OK if result.success else status.HTTP_400_BAD_REQUEST
        return Response(CampaignOutputSerializer(result).data, status=http_status)


class CampaignSendView(APIView):
    """
    POST /api/v1/mailing/campaigns/<campaign_id>/send/
    Inicia envio da campanha.
    """

    def post(self, request, campaign_id: int):
        try:
            empresa = _resolve_empresa(request)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = SendCampaignInputSerializer(data=request.data or {})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        data = serializer.validated_data
        send_request = SendBulkSMSRequest(
            company_id=CompanyId(empresa.id),
            campaign_id=campaign_id,
            batch_size=data.get("batch_size", 100),
            delay_between_batches_seconds=data.get("delay_between_batches_seconds", 1),
            correlation_id=data.get("correlation_id"),
        )

        use_case = build_send_bulk_sms_use_case(empresa)
        result = use_case.execute(send_request)

        logger.info(
            "campaign_send",
            empresa_id=empresa.id,
            campaign_id=campaign_id,
            sent=result.sent_count,
            failed=result.failed_count,
        )

        http_status = status.HTTP_202_ACCEPTED if result.success else status.HTTP_400_BAD_REQUEST
        return Response(SendCampaignOutputSerializer(result).data, status=http_status)


class CampaignScheduleView(APIView):
    """
    POST /api/v1/mailing/campaigns/<campaign_id>/schedule/
    Agenda envio de uma campanha.
    """

    def post(self, request, campaign_id: int):
        try:
            _resolve_empresa(request)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ScheduleCampaignInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        data = serializer.validated_data
        schedule_request = ScheduleCampaignRequest(
            campaign_id=campaign_id,
            scheduled_for=data["scheduled_for"],
        )

        use_case = build_schedule_campaign_use_case()
        result = use_case.execute(schedule_request)

        logger.info("campaign_schedule", campaign_id=campaign_id, success=result.success)
        http_status = status.HTTP_200_OK if result.success else status.HTTP_400_BAD_REQUEST
        return Response(ScheduleCampaignOutputSerializer(result).data, status=http_status)
