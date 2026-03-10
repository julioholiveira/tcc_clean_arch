"""Use Case: Atualização de Campanha"""

import logging

from src.mailing.application.dto.campaign import (
    UpdateCampaignRequest,
    UpdateCampaignResponse,
)
from src.mailing.domain.exceptions import CampaignStateError
from src.mailing.domain.repositories import CampaignRepository

logger = logging.getLogger(__name__)


class UpdateCampaignUseCase:
    """Atualiza campanha existente"""

    def __init__(self, campaign_repository: CampaignRepository):
        self.campaign_repository = campaign_repository

    def execute(self, request: UpdateCampaignRequest) -> UpdateCampaignResponse:
        """
        Atualiza campanha.

        Fluxo:
        1. Busca campanha
        2. Valida estado
        3. Atualiza campos
        4. Persiste
        """

        try:
            campaign = self.campaign_repository.find_by_id(request.campaign_id)

            if not campaign:
                return UpdateCampaignResponse(
                    success=False,
                    message="Campanha não encontrada",
                    error_code="CAMPAIGN_NOT_FOUND",
                )

            # Valida estado (não pode atualizar campanhas em andamento ou concluídas)
            if campaign.status.value in ["in_progress", "completed"]:
                raise CampaignStateError(
                    "Não é possível atualizar campanhas em andamento ou concluídas"
                )

            # Atualiza campos
            if request.name:
                campaign.name = request.name

            if request.template_id:
                campaign.template_id = request.template_id

            if request.scheduled_for:
                campaign.scheduled_for = request.scheduled_for

            # Persiste
            self.campaign_repository.save(campaign)

            logger.info(f"Campanha {request.campaign_id} atualizada")

            return UpdateCampaignResponse(
                success=True, message="Campanha atualizada com sucesso"
            )

        except CampaignStateError as e:
            logger.warning(f"Erro de estado: {str(e)}")
            return UpdateCampaignResponse(
                success=False, message=str(e), error_code="INVALID_STATE"
            )

        except Exception as e:
            logger.error(f"Erro ao atualizar campanha: {str(e)}", exc_info=True)
            return UpdateCampaignResponse(
                success=False,
                message="Erro interno ao atualizar campanha",
                error_code="INTERNAL_ERROR",
            )
