"""Use Case: Criacao de Campanha"""

import logging

from src.mailing.application.dto.campaign import (
    CreateCampaignRequest,
    CreateCampaignResponse,
)
from src.mailing.domain.entities import Campaign, CampaignStatus
from src.mailing.domain.exceptions import TemplateNotFoundError
from src.mailing.domain.repositories import CampaignRepository, MailTemplateRepository

logger = logging.getLogger(__name__)


class CreateCampaignUseCase:
    """Cria nova campanha de mailing"""

    def __init__(self, campaign_repository: CampaignRepository, template_repository: MailTemplateRepository):
        self.campaign_repository = campaign_repository
        self.template_repository = template_repository

    def execute(self, request: CreateCampaignRequest) -> CreateCampaignResponse:
        """Cria campanha."""
        try:
            if not request.name or not request.name.strip():
                return CreateCampaignResponse(
                    success=False,
                    message="Nome da campanha e obrigatorio",
                    error_code="VALIDATION_ERROR",
                )

            template = self.template_repository.find_by_id(request.template_id)
            if not template:
                raise TemplateNotFoundError(f"Template {request.template_id} nao encontrado")

            initial_status = CampaignStatus.SCHEDULED if request.scheduled_for else CampaignStatus.DRAFT

            campaign = Campaign(
                company_id=request.company_id,
                name=request.name,
                template=template,
                status=initial_status,
                scheduled_at=request.scheduled_for,
            )

            campaign = self.campaign_repository.save(campaign)

            logger.info(f"Campanha criada: {campaign.id}", extra={"company_id": request.company_id.value})

            return CreateCampaignResponse(
                success=True,
                campaign_id=campaign.id,
                message="Campanha criada com sucesso",
            )

        except TemplateNotFoundError as e:
            logger.warning(f"Template nao encontrado: {str(e)}")
            return CreateCampaignResponse(success=False, message=str(e), error_code="TEMPLATE_NOT_FOUND")

        except Exception as e:
            logger.error(f"Erro ao criar campanha: {str(e)}", exc_info=True)
            return CreateCampaignResponse(
                success=False, message="Erro interno ao criar campanha", error_code="INTERNAL_ERROR"
            )
