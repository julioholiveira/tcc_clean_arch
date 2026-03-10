"""
Repositório Django para destinatários de mailing.
Usa ResultadoMailing + Usuario para filtros paginados.
Resolve P3 (SRP): lógica de filtro saiu do model.
"""

import logging
from datetime import datetime
from typing import Optional

from src.core.domain.value_objects import CompanyId
from src.mailing.domain.repositories import RecipientRepository

logger = logging.getLogger(__name__)


class DjangoRecipientRepository(RecipientRepository):
    """
    Adapter para destinatários usando ResultadoMailing.
    Resolve P3 (SRP) e P11 (ISP): sem dependência de `request`.
    """

    def _base_qs(
        self,
        company_id: CompanyId,
        campaign_id: Optional[int],
        date_from: Optional[datetime],
        date_to: Optional[datetime],
    ):
        from mailing.models import ResultadoMailing

        qs = ResultadoMailing.objects.filter(empresas_id=company_id.value)
        if campaign_id is not None:
            qs = qs.filter(mailings_id=campaign_id)
        if date_from:
            qs = qs.filter(data_envio__gte=date_from)
        if date_to:
            qs = qs.filter(data_envio__lte=date_to)
        return qs

    def list_filtered(
        self,
        company_id: CompanyId,
        campaign_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list:
        """Lista destinatários com filtros e paginação."""
        qs = self._base_qs(company_id, campaign_id, date_from, date_to)
        qs = qs.select_related("usuarios").order_by("-data_envio")
        rows = qs[offset : offset + limit]
        result = []
        for row in rows:
            phone = ""
            if row.usuarios:
                phone = getattr(row.usuarios, "telefone", "") or ""
            # Sanitização de PII: mascarar phone
            if len(phone) > 4:
                phone_display = f"{'*' * (len(phone) - 4)}{phone[-4:]}"
            else:
                phone_display = phone
            result.append(
                {
                    "id": row.pk,
                    "phone": phone_display,
                    "status": row.status_sms or "",
                    "sent_at": row.data_envio.isoformat() if row.data_envio else None,
                    "delivered_at": (row.data_recebimento.isoformat() if row.data_recebimento else None),
                    "campaign_id": row.mailings_id,
                }
            )
        return result

    def count_filtered(
        self,
        company_id: CompanyId,
        campaign_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> int:
        """Conta destinatários com filtros."""
        return self._base_qs(company_id, campaign_id, date_from, date_to).count()
