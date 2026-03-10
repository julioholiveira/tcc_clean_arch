"""Use Case: Consulta de Status de SMS - resolve P3"""

import logging

from src.core.application.dto.sms import (
    SMSStatusItem,
    SMSStatusRequest,
    SMSStatusResponse,
)
from src.core.domain.repositories import SMSDeliveryRepository

logger = logging.getLogger(__name__)


class GetSMSStatusUseCase:
    """
    Consulta status de SMS.
    Extrai lógica de get_sms_status do model (P3).
    """

    def __init__(self, delivery_repository: SMSDeliveryRepository):
        self.delivery_repository = delivery_repository

    def execute(self, request: SMSStatusRequest) -> SMSStatusResponse:
        """
        Consulta status de SMS com filtros.

        Args:
            request: DTO com filtros (não `request` HTTP)

        Returns:
            SMSStatusResponse com itens paginados
        """
        try:
            # Conta total
            total = self.delivery_repository.count_filtered(
                company_id=request.company_id,
                phone=request.phone,
                date_from=request.date_from,
                date_to=request.date_to,
            )

            # Busca itens
            deliveries = self.delivery_repository.list_filtered(
                company_id=request.company_id,
                phone=request.phone,
                date_from=request.date_from,
                date_to=request.date_to,
                limit=request.limit,
                offset=request.offset,
            )

            # Converte para DTOs
            items = [
                SMSStatusItem(
                    delivery_id=d.id,
                    phone=d.phone.value,
                    status=d.status,
                    provider=d.provider,
                    sent_at=d.sent_at,
                    delivered_at=d.delivered_at,
                    error_message=d.error_message,
                )
                for d in deliveries
            ]

            has_more = (request.offset + len(items)) < total

            logger.info(
                f"Consultados {len(items)} status de SMS",
                extra={"company_id": request.company_id.value, "total": total},
            )

            return SMSStatusResponse(total=total, items=items, has_more=has_more)

        except Exception as e:
            logger.error(f"Erro ao consultar status: {str(e)}", exc_info=True)
            return SMSStatusResponse(total=0, items=[], has_more=False)
