"""
Repositório Django para campanhas de mailing.
Mapeia Mailing (legacy ORM) → Campaign (domain entity).
"""

import logging
from datetime import datetime
from typing import List, Optional

from src.core.domain.value_objects import CompanyId
from src.mailing.domain.entities import Campaign, CampaignStatus, MailTemplate
from src.mailing.domain.repositories import CampaignRepository

logger = logging.getLogger(__name__)


class DjangoCampaignRepository(CampaignRepository):
    """
    Adapter para persistência de campanhas usando o modelo Mailing do Django.
    Resolve P12 (DIP): use cases não dependem do ORM diretamente.
    """

    def save(self, campaign: Campaign) -> Campaign:
        """Salva ou atualiza campanha."""
        from mailing.models import Mailing  # import ORM delayed (DIP)

        template_id = campaign.template.id if campaign.template else None

        if campaign.id:
            obj, _ = Mailing.objects.update_or_create(
                pk=campaign.id,
                defaults={
                    "nome_mailing": campaign.name,
                    "empresas_id": campaign.company_id.value,
                },
            )
        else:
            obj = Mailing.objects.create(
                nome_mailing=campaign.name,
                empresas_id=campaign.company_id.value,
            )

        campaign.id = obj.pk
        return campaign

    def find_by_id(self, campaign_id: int) -> Optional[Campaign]:
        """Busca campanha por ID."""
        from mailing.models import Mailing

        try:
            obj = Mailing.objects.get(pk=campaign_id)
        except Mailing.DoesNotExist:
            return None

        return self._to_domain(obj)

    def list_scheduled(self, before: datetime) -> List[Campaign]:
        """Lista campanhas agendadas antes de uma data."""

        # Campo scheduled_at não existe no legacy model — retorna vazio até migração
        return []

    def list_by_company(self, company_id: CompanyId, limit: int = 50, offset: int = 0) -> List[Campaign]:
        """Lista campanhas da empresa com paginação."""
        from mailing.models import Mailing

        qs = Mailing.objects.filter(empresas_id=company_id.value).order_by("-id")
        objs = qs[offset : offset + limit]
        return [self._to_domain(obj) for obj in objs]

    @staticmethod
    def _to_domain(obj) -> Campaign:
        """Converte modelo ORM para entidade de domínio."""
        template = MailTemplate(
            id=None,
            company_id=CompanyId(obj.empresas_id or 0),
            name=obj.nome_mailing,
            content=obj.texto_mensagem or "",
        )
        return Campaign(
            id=obj.pk,
            company_id=CompanyId(obj.empresas_id or 0),
            name=obj.nome_mailing,
            template=template,
            status=CampaignStatus.DRAFT,
        )
