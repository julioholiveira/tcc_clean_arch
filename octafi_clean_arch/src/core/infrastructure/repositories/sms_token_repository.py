"""Implementação Django ORM do SMSTokenRepository."""

from datetime import datetime
from typing import Optional

from core.models import TokenSMS
from src.core.domain.entities import SMSTokenEntity
from src.core.domain.repositories import SMSTokenRepository
from src.core.domain.value_objects import CompanyId, PhoneNumber, SMSToken


class DjangoSMSTokenRepository(SMSTokenRepository):
    """Adaptador ORM Django para a entidade SMSTokenEntity."""

    @staticmethod
    def _to_domain(orm: TokenSMS) -> SMSTokenEntity:
        return SMSTokenEntity(
            id=orm.pk,
            company_id=CompanyId(orm.empresas_id),
            phone=PhoneNumber(orm.telefone),
            token=SMSToken(orm.token),
            name=orm.nome_usuario,
            cpf=orm.cpf_usuario,
            resend_count=orm.reenvios or 0,
        )

    def save(self, token: SMSTokenEntity) -> SMSTokenEntity:
        """Salva ou atualiza token, incrementando reenvios se já existir."""
        orm, created = TokenSMS.objects.get_or_create(
            telefone=token.phone.value,
            empresas_id=token.company_id.value,
            defaults={
                "token": token.token.value,
                "nome_usuario": token.name,
                "cpf_usuario": token.cpf,
                "reenvios": 0,
            },
        )
        if not created:
            TokenSMS.objects.filter(pk=orm.pk).update(reenvios=orm.reenvios + 1)
            orm.refresh_from_db()
        return self._to_domain(orm)

    def find_valid_token(
        self,
        company_id: CompanyId,
        phone: PhoneNumber,
        token_value: str,
    ) -> Optional[SMSTokenEntity]:
        try:
            return self._to_domain(
                TokenSMS.objects.get(
                    telefone=phone.value,
                    empresas_id=company_id.value,
                    token=token_value,
                )
            )
        except TokenSMS.DoesNotExist:
            return None

    def delete_expired(self, before: datetime) -> int:
        """
        Remove tokens com reenvios >= 3.
        Equivalente ao limpa_tokens_reenviados do legado (core/tasks.py).
        """
        count, _ = TokenSMS.objects.filter(reenvios__gte=3).delete()
        return count
