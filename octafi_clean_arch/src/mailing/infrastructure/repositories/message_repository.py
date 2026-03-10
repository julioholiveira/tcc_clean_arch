"""
Repositório Django para mensagens de mailing.
Mapeia ResultadoMailing (legacy ORM) → MailMessage (domain entity).
"""

import logging
from typing import List, Optional

from src.mailing.domain.entities import MailMessage, Recipient
from src.mailing.domain.repositories import MailMessageRepository

logger = logging.getLogger(__name__)


class DjangoMailMessageRepository(MailMessageRepository):
    """
    Adapter para mensagens de mailing usando ResultadoMailing.
    Resolve P12 (DIP): use cases operam pela interface de repositório.
    """

    def save(self, message: MailMessage) -> MailMessage:
        """Salva mensagem individual."""
        from mailing.models import ResultadoMailing

        phone_str = (
            message.recipient.phone.value if hasattr(message.recipient.phone, "value") else str(message.recipient.phone)
        )

        obj = ResultadoMailing.objects.create(
            mailings_id=message.campaign_id,
            usuarios_id=None,  # pode ser NULL em implementações futuras
            codigo_sms=message.provider_message_id or "",
            status_sms=message.status.value if hasattr(message.status, "value") else str(message.status),
        )
        message.id = obj.pk
        return message

    def save_batch(self, messages: List[MailMessage]) -> List[MailMessage]:
        """Salva lote de mensagens via bulk_create."""
        from mailing.models import ResultadoMailing

        objs = [
            ResultadoMailing(
                mailings_id=m.campaign_id,
                usuarios_id=None,
                codigo_sms=m.provider_message_id or "",
                status_sms=m.status.value if hasattr(m.status, "value") else str(m.status),
            )
            for m in messages
        ]
        created = ResultadoMailing.objects.bulk_create(objs)
        for i, msg in enumerate(messages):
            msg.id = created[i].pk
        return messages

    def update_status(
        self,
        message_id: int,
        status: str,
        provider_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Atualiza status de mensagem."""
        from mailing.models import ResultadoMailing

        updates = {"status_sms": status}
        if provider_id:
            updates["codigo_sms"] = provider_id
        ResultadoMailing.objects.filter(pk=message_id).update(**updates)

    def list_by_campaign(self, campaign_id: int, limit: int = 100, offset: int = 0) -> List[MailMessage]:
        """Lista mensagens de uma campanha."""
        from mailing.models import ResultadoMailing
        from src.core.domain.entities import SMSStatus
        from src.core.domain.value_objects import PhoneNumber

        qs = ResultadoMailing.objects.filter(mailings_id=campaign_id).select_related("usuarios")
        objs = qs[offset : offset + limit]

        result = []
        for obj in objs:
            try:
                phone = PhoneNumber(obj.usuarios.telefone) if obj.usuarios else PhoneNumber("0000000000")
                recipient = Recipient(phone=phone, name=getattr(obj.usuarios, "nome", None))
                msg = MailMessage(
                    id=obj.pk,
                    campaign_id=campaign_id,
                    recipient=recipient,
                    content="",
                    status=SMSStatus(obj.status_sms) if obj.status_sms else SMSStatus.PENDING,
                    provider_message_id=obj.codigo_sms,
                    sent_at=obj.data_envio,
                    delivered_at=obj.data_recebimento,
                )
                result.append(msg)
            except Exception as exc:
                logger.warning("Erro ao mapear mensagem %s: %s", obj.pk, exc)
        return result
