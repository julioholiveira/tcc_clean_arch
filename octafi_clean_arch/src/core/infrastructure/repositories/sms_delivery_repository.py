"""Implementação Django ORM do SMSDeliveryRepository."""

from datetime import datetime
from typing import List, Optional

from core.models import SMSEnviado

from src.core.domain.entities import SMSDelivery, SMSStatus
from src.core.domain.repositories import SMSDeliveryRepository
from src.core.domain.value_objects import CompanyId, PhoneNumber


class DjangoSMSDeliveryRepository(SMSDeliveryRepository):
    """Adaptador ORM Django para SMSEnviado (rastreamento de envios)."""

    @staticmethod
    def _bool_to_status(sent: bool, delivered: bool) -> SMSStatus:
        """Converte os dois BooleanFields legados para o enum SMSStatus."""
        if delivered:
            return SMSStatus.DELIVERED
        if sent:
            return SMSStatus.SENT
        return SMSStatus.PENDING

    @staticmethod
    def _status_to_bools(status: SMSStatus) -> tuple:
        """Converte SMSStatus para (sent_status, delivered_status) booleanos legados."""
        if status == SMSStatus.DELIVERED:
            return (True, True)
        if status == SMSStatus.SENT:
            return (True, False)
        return (False, False)

    @staticmethod
    def _to_domain(orm: SMSEnviado) -> SMSDelivery:
        return SMSDelivery(
            id=orm.pk,
            company_id=CompanyId(orm.empresas_id),
            phone=PhoneNumber(orm.telefone),
            # message=orm.message or "",
            provider=orm.operadora or "",
            correlation_id=orm.correlation_id,
            status=DjangoSMSDeliveryRepository._bool_to_status(bool(orm.sent_status), bool(orm.delivered_status)),
        )

    def save(self, delivery: SMSDelivery) -> SMSDelivery:
        if delivery.id:
            sent, delivered = self._status_to_bools(delivery.status)
            SMSEnviado.objects.filter(pk=delivery.id).update(
                sent_status=sent,
                delivered_status=delivered,
                operadora=delivery.provider,
            )
            orm = SMSEnviado.objects.get(pk=delivery.id)
        else:
            orm = SMSEnviado.objects.create(
                empresas_id=delivery.company_id.value,
                telefone=delivery.phone.value,
                # message=delivery.message,
                operadora=delivery.provider,
                correlation_id=delivery.correlation_id,
                sent_status=self._status_to_bools(delivery.status)[0],
                delivered_status=self._status_to_bools(delivery.status)[1],
            )
        return self._to_domain(orm)

    def find_by_provider_id(self, provider_message_id: str) -> Optional[SMSDelivery]:
        try:
            return self._to_domain(SMSEnviado.objects.get(correlation_id=provider_message_id))
        except SMSEnviado.DoesNotExist:
            return None

    def find_by_correlation_id(self, correlation_id: str) -> Optional[SMSDelivery]:
        return self.find_by_provider_id(correlation_id)

    def update_status(
        self,
        correlation_id: str,
        status: SMSStatus,
        carrier: Optional[str] = None,
    ) -> bool:
        """
        Resolve P9: atualização de status sem hardcode para Sinch.
        Chamado por UpdateSMSStatusUseCase com qualquer provider.
        """
        sent, delivered = self._status_to_bools(status)
        kwargs: dict = {"sent_status": sent, "delivered_status": delivered}
        if carrier:
            kwargs["operadora"] = carrier
        updated = SMSEnviado.objects.filter(correlation_id=correlation_id).update(**kwargs)
        return updated > 0

    def get_status(self, company_id: CompanyId, correlation_id: str) -> Optional[SMSStatus]:
        """
        Resolve P3: lógica de get_sms_status sai do model para o repository.
        Recebe company_id em vez do objeto request (resolve ISP P11).
        """
        try:
            orm = SMSEnviado.objects.get(
                correlation_id=correlation_id,
                empresas_id=company_id.value,
            )
            return self._bool_to_status(bool(orm.sent_status), bool(orm.delivered_status))
        except SMSEnviado.DoesNotExist:
            return None

    def count_filtered(
        self,
        company_id: CompanyId,
        phone: Optional[PhoneNumber] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> int:
        qs = SMSEnviado.objects.filter(empresas_id=company_id.value)
        if phone:
            qs = qs.filter(telefone=phone.value)
        if date_from:
            qs = qs.filter(created_at__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__lte=date_to)
        return qs.count()

    def list_filtered(
        self,
        company_id: CompanyId,
        phone: Optional[PhoneNumber] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SMSDelivery]:
        qs = SMSEnviado.objects.filter(empresas_id=company_id.value)
        if phone:
            qs = qs.filter(telefone=phone.value)
        if date_from:
            qs = qs.filter(created_at__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__lte=date_to)
        qs = qs.order_by("-created_at")[offset : offset + limit]
        return [self._to_domain(s) for s in qs]

    def get_delivery_stats(
        self,
        company_id: CompanyId,
        from_date: datetime,
        to_date: datetime,
    ) -> dict:
        from django.db.models import Count

        qs = SMSEnviado.objects.filter(
            empresas_id=company_id.value,
            created_at__gte=from_date,
            created_at__lte=to_date,
        )
        total = qs.count()
        by_status = qs.values("sent_status").annotate(count=Count("id"))
        return {
            "total": total,
            "by_status": {row["sent_status"]: row["count"] for row in by_status},
        }
