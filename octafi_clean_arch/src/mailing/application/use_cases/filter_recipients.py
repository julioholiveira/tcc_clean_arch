import logging
from datetime import datetime

from src.mailing.domain.repositories import RecipientRepository
from src.mailing.application.dto.campaign import (
    FilterRecipientsRequest,
    FilterRecipientsResponse,
)

logger = logging.getLogger(__name__)


class FilterRecipientsUseCase:
    """Filtra destinatarios com suporte a paginacao."""

    def __init__(self, recipient_repository: RecipientRepository):
        self.recipient_repository = recipient_repository

    def execute(self, request: FilterRecipientsRequest) -> FilterRecipientsResponse:
        """Filtra destinatarios com paginacao."""
        try:
            date_from = request.date_from or datetime(2020, 1, 1)
            date_to = request.date_to or datetime.now()

            total_count = self.recipient_repository.count_filtered(
                company_id=request.company_id,
                campaign_id=request.campaign_id,
                date_from=date_from,
                date_to=date_to,
            )

            recipients = self.recipient_repository.list_filtered(
                company_id=request.company_id,
                campaign_id=request.campaign_id,
                date_from=date_from,
                date_to=date_to,
                limit=request.limit,
                offset=request.offset,
            )

            has_more = (request.offset + len(recipients)) < total_count

            logger.info(
                f"Filtro de destinatarios: {total_count} total, {len(recipients)} retornados",
                extra={"company_id": request.company_id, "offset": request.offset},
            )

            return FilterRecipientsResponse(
                total=total_count,
                recipients=recipients,
                has_more=has_more,
                offset=request.offset,
            )

        except Exception as e:
            logger.error(f"Erro ao filtrar destinatarios: {str(e)}", exc_info=True)
            return FilterRecipientsResponse(
                total=0,
                recipients=[],
                has_more=False,
                offset=request.offset,
            )
