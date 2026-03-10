"""
Views para operações de SMS.
Resolve P9 (OCP): provider resolvido por factory — sem Sinch hardcoded.
"""

import structlog
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from src.core.application.dto.sms import SendSMSRequest, SMSStatusRequest
from src.core.domain.value_objects import CompanyId, PhoneNumber
from src.core.interfaces.api.v1.dependencies import (
    build_get_sms_status_use_case,
    build_send_sms_use_case,
)
from src.core.interfaces.api.v1.serializers.sms_serializers import (
    SendSMSInputSerializer,
    SendSMSOutputSerializer,
    SMSStatusOutputSerializer,
    SMSStatusQuerySerializer,
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


class SMSSendView(APIView):
    """
    POST /api/v1/sms/send/
    Envia SMS usando o provedor da empresa.
    Resolve P9: nenhuma menção a Sinch/Zenvia/SMSMarket.
    """

    def post(self, request):
        try:
            empresa = _resolve_empresa(request)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = SendSMSInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        data = serializer.validated_data

        try:
            sms_request = SendSMSRequest(
                company_id=CompanyId(empresa.id),
                phone=PhoneNumber(data["phone"]),
                message=data["message"],
                provider_slug=data.get("provider_slug"),
                correlation_id=data.get("correlation_id"),
            )
        except (ValueError, TypeError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        use_case = build_send_sms_use_case(empresa)
        result = use_case.execute(sms_request)

        logger.info(
            "sms_send",
            empresa_id=empresa.id,
            provider=result.provider_name,
            success=result.success,
        )

        http_status = status.HTTP_200_OK if result.success else status.HTTP_400_BAD_REQUEST
        return Response(SendSMSOutputSerializer(result).data, status=http_status)


class SMSStatusView(APIView):
    """
    GET /api/v1/sms/status/
    Consulta status de entregas de SMS com paginação.
    Resolve P3 (SRP): lógica de filtro em repositório.
    """

    def get(self, request):
        try:
            empresa = _resolve_empresa(request)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        query_serializer = SMSStatusQuerySerializer(data=request.query_params)
        if not query_serializer.is_valid():
            return Response(query_serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        data = query_serializer.validated_data

        try:
            phone = PhoneNumber(data["phone"]) if data.get("phone") else None
        except (ValueError, TypeError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        status_request = SMSStatusRequest(
            company_id=CompanyId(empresa.id),
            phone=phone,
            delivery_id=data.get("delivery_id"),
            date_from=data.get("date_from"),
            date_to=data.get("date_to"),
            limit=data["limit"],
            offset=data["offset"],
        )

        use_case = build_get_sms_status_use_case(empresa)
        result = use_case.execute(status_request)

        return Response(SMSStatusOutputSerializer(result).data, status=status.HTTP_200_OK)
