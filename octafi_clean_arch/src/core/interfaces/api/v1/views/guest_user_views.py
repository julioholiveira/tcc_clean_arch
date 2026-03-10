"""
View para listagem de usuários guest com paginação.
Resolve P3 (SRP) e sanitização de PII.
"""

import structlog
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from src.core.domain.value_objects import CompanyId
from src.core.interfaces.api.v1.dependencies import build_list_guest_users_use_case
from src.core.interfaces.api.v1.serializers.guest_serializers import (
    GuestUserListOutputSerializer,
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


class GuestUserListView(APIView):
    """
    GET /api/v1/guest/users/
    Lista usuários guest da empresa com paginação.
    Telefone é sanitizado (PII): apenas últimos 4 dígitos visíveis.
    """

    def get(self, request):
        try:
            empresa = _resolve_empresa(request)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            limit = int(request.query_params.get("limit", 50))
            offset = int(request.query_params.get("offset", 0))
        except (ValueError, TypeError):
            return Response(
                {"detail": "limit e offset devem ser inteiros"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        limit = max(1, min(limit, 500))
        offset = max(0, offset)

        use_case = build_list_guest_users_use_case()
        # execute() aceita args diretos — sem DTO de request
        users = use_case.execute(
            company_id=CompanyId(empresa.id),
            limit=limit,
            offset=offset,
        )
        result = {"total": len(users), "users": users, "has_more": len(users) == limit}

        logger.info(
            "guest_user_list",
            empresa_id=empresa.id,
            total=result.total,
            limit=limit,
            offset=offset,
        )

        return Response(GuestUserListOutputSerializer(result).data, status=status.HTTP_200_OK)
