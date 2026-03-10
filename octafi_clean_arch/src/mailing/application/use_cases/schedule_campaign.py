"""Use Case: Agendamento de Campanha"""

import logging
from datetime import datetime, timezone

from src.mailing.application.dto.campaign import (
    ScheduleCampaignRequest,
    ScheduleCampaignResponse,
)
from src.mailing.domain.entities import CampaignStatus
from src.mailing.domain.exceptions import CampaignStateError
from src.mailing.domain.repositories import CampaignRepository

logger = logging.getLogger(__name__)


class ScheduleCampaignUseCase:
    """Agenda campanha para envio futuro"""

    def __init__(self, campaign_repository: CampaignRepository):
        self.campaign_repository = campaign_repository

    def execute(self, request: ScheduleCampaignRequest) -> ScheduleCampaignResponse:
        """Agenda campanha."""
        try:
            campaign = self.campaign_repository.find_by_id(request.campaign_id)

            if not campaign:
                return ScheduleCampaignResponse(
                    success=False, message="Campanha nao encontrada", error_code="CAMPAIGN_NOT_FOUND"
                )

            if campaign.status != CampaignStatus.DRAFT:
                raise CampaignStateError(
                    f"Apenas campanhas em rascunho podem ser agendadas. Status atual: {campaign.status.value}"
                )

            if request.scheduled_for <= datetime.now(tz=request.scheduled_for.tzinfo):
                return ScheduleCampaignResponse(
                    success=False,
                    message="Data de agendamento deve ser futura",
                    error_code="INVALID_SCHEDULE_DATE",
                )

            campaign.scheduled_at = request.scheduled_for
            campaign.status = CampaignStatus.SCHEDULED
            self.campaign_repository.save(campaign)

            logger.info(f"Campanha {request.campaign_id} agendada para {request.scheduled_for}")

            return ScheduleCampaignResponse(
                success=True,
                message="Campanha agendada com sucesso",
                scheduled_for=request.scheduled_for,
            )

        except CampaignStateError as e:
            logger.warning(f"Erro de estado: {str(e)}")
            return ScheduleCampaignResponse(success=False, message=str(e), error_code="INVALID_STATE")

        except Exception as e:
            logger.error(f"Erro ao agendar campanha: {str(e)}", exc_info=True)
            return ScheduleCampaignResponse(
                success=False, message="Erro interno ao agendar campanha", error_code="INTERNAL_ERROR"
            )
