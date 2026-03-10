"""
Repositório Django para templates de mailing.
O modelo legado não tem tabela separada de templates — usa texto_mensagem do Mailing.
"""

import logging
from typing import List, Optional

from src.core.domain.value_objects import CompanyId
from src.mailing.domain.entities import MailTemplate
from src.mailing.domain.repositories import MailTemplateRepository

logger = logging.getLogger(__name__)


class DjangoMailTemplateRepository(MailTemplateRepository):
    """
    Adapter de templates usando o campo texto_mensagem de Mailing.
    NOTE: modelo legacy não tem tabela de templates separada.
    Templates são embutidos na própria campanha (Mailing.texto_mensagem).
    """

    def save(self, template: MailTemplate) -> MailTemplate:
        """Salva template — reutiliza Mailing como container."""
        from mailing.models import Mailing

        if template.id:
            Mailing.objects.filter(pk=template.id).update(
                nome_mailing=template.name,
                texto_mensagem=template.content,
            )
        else:
            obj = Mailing.objects.create(
                nome_mailing=template.name,
                texto_mensagem=template.content,
                empresas_id=template.company_id.value,
            )
            template.id = obj.pk
        return template

    def find_by_id(self, template_id: int) -> Optional[MailTemplate]:
        """Busca template por ID (usa registro Mailing)."""
        from mailing.models import Mailing

        try:
            obj = Mailing.objects.get(pk=template_id)
        except Mailing.DoesNotExist:
            return None

        return MailTemplate(
            id=obj.pk,
            company_id=CompanyId(obj.empresas_id or 0),
            name=obj.nome_mailing,
            content=obj.texto_mensagem or "",
        )

    def list_by_company(self, company_id: CompanyId) -> List[MailTemplate]:
        """Lista templates da empresa."""
        from mailing.models import Mailing

        qs = Mailing.objects.filter(empresas_id=company_id.value).order_by("-id")
        return [
            MailTemplate(
                id=obj.pk,
                company_id=company_id,
                name=obj.nome_mailing,
                content=obj.texto_mensagem or "",
            )
            for obj in qs
        ]

    def delete(self, template_id: int) -> None:
        """Remove template."""
        from mailing.models import Mailing

        Mailing.objects.filter(pk=template_id).delete()
