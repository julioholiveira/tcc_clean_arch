"""
View para listagem de destinatários com paginação e sanitização de PII.
"""

import structlog
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from src.core.domain.value_objects import CompanyId
from src.mailing.application.dto.campaign import FilterRecipientsRequest
from src.mailing.interfaces.api.v1.dependencies import build_filter_recipients_use_case
from src.mailing.interfaces.api.v1.serializers.campaign_serializers import (
    RecipientListOutputSerializer,
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


class RecipientListView(APIView):
    """
    GET /api/v1/mailing/recipients/
    Lista destinatários com filtros opcionais e paginação.
    PII: telefones são mascarados no repositório.
    """

    def get(self, request):
        try:
            empresa = _resolve_empresa(request)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            limit = int(request.query_params.get("limit", 100))
            offset = int(request.query_params.get("offset", 0))
            campaign_id_raw = request.query_params.get("campaign_id")
            campaign_id = int(campaign_id_raw) if campaign_id_raw else None
        except (ValueError, TypeError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        limit = max(1, min(limit, 500))
        offset = max(0, offset)

        # date filters (optional)
        from datetime import datetime

        date_from = None
        date_to = None
        try:
            if request.query_params.get("date_from"):
                date_from = datetime.fromisoformat(request.query_params["date_from"])
            if request.query_params.get("date_to"):
                date_to = datetime.fromisoformat(request.query_params["date_to"])
        except ValueError:
            return Response({"detail": "Formato de data inválido (ISO 8601)"}, status=status.HTTP_400_BAD_REQUEST)

        filter_request = FilterRecipientsRequest(
            company_id=CompanyId(empresa.id),
            campaign_id=campaign_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset,
        )

        use_case = build_filter_recipients_use_case()
        result = use_case.execute(filter_request)

        logger.info(
            "recipient_list",
            empresa_id=empresa.id,
            total=result.total,
            offset=offset,
        )

        return Response(RecipientListOutputSerializer(result).data, status=status.HTTP_200_OK)
