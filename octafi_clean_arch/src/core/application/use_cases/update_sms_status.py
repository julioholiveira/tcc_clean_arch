"""
Use Case: Atualização de status dos SMS enviados.
Resolve P9 — sem hardcode para Sinch; delega para SMSGateway port.
"""

import structlog

from src.core.application.ports.sms_gateway import SMSGateway
from src.core.domain.repositories import SMSDeliveryRepository

logger = structlog.get_logger(__name__)


class UpdateSMSStatusUseCase:
    """
    Atualiza o status dos SMS enviados para uma empresa.
    Resolve P9 (OCP): não hardcoded para Sinch.
    O provider correto é injetado via SMSGateway port pela Factory.
    """

    def __init__(
        self,
        sms_gateway: SMSGateway,
        delivery_repository: SMSDeliveryRepository,
    ) -> None:
        self.sms_gateway = sms_gateway
        self.delivery_repository = delivery_repository

    def execute(self, empresa_id: int) -> int:
        """
        Busca atualizações de status junto ao provider e persiste.

        Args:
            empresa_id: ID da empresa cujos SMS serão verificados.

        Returns:
            Número de registros atualizados.
        """
        # Apenas Sinch suporta consulta em lote; outros providers retornam []
        if not hasattr(self.sms_gateway, "get_bulk_status_updates"):
            logger.debug(
                "provider_bulk_status_not_supported",
                provider=self.sms_gateway.provider_name,
            )
            return 0

        updates = self.sms_gateway.get_bulk_status_updates()  # type: ignore[union-attr]
        updated_count = 0

        for item in updates:
            correlation_id = item.get("correlation_id")
            status = item.get("status")
            carrier = item.get("carrier")

            if not correlation_id or not status:
                continue

            success = self.delivery_repository.update_status(
                correlation_id=correlation_id,
                status=status,
                carrier=carrier,
            )
            if success:
                updated_count += 1
                logger.debug(
                    "sms_status_record_updated",
                    correlation_id=correlation_id,
                    status=status.value,
                    provider=self.sms_gateway.provider_name,
                )

        logger.info(
            "update_sms_status_complete",
            empresa_id=empresa_id,
            provider=self.sms_gateway.provider_name,
            updated=updated_count,
            total_from_provider=len(updates),
        )
        return updated_count
