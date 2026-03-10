"""
Fábricas de injeção de dependência para a camada de apresentação do mailing.
Resolve P12 (DIP): views não conhecem implementações concretas.
"""

from src.mailing.application.use_cases.create_campaign import CreateCampaignUseCase
from src.mailing.application.use_cases.filter_recipients import FilterRecipientsUseCase
from src.mailing.application.use_cases.schedule_campaign import ScheduleCampaignUseCase
from src.mailing.application.use_cases.send_bulk_sms import SendBulkSMSUseCase
from src.mailing.application.use_cases.update_campaign import UpdateCampaignUseCase
from src.mailing.infrastructure.bulk_sms_processor import DjangoBulkSMSProcessor
from src.mailing.infrastructure.repositories.campaign_repository import DjangoCampaignRepository
from src.mailing.infrastructure.repositories.message_repository import DjangoMailMessageRepository
from src.mailing.infrastructure.repositories.recipient_repository import DjangoRecipientRepository
from src.mailing.infrastructure.repositories.template_repository import DjangoMailTemplateRepository


def build_create_campaign_use_case() -> CreateCampaignUseCase:
    """Constrói o use case de criação de campanha."""
    return CreateCampaignUseCase(
        campaign_repository=DjangoCampaignRepository(),
        template_repository=DjangoMailTemplateRepository(),
    )


def build_update_campaign_use_case() -> UpdateCampaignUseCase:
    """Constrói o use case de atualização de campanha."""
    return UpdateCampaignUseCase(
        campaign_repository=DjangoCampaignRepository(),
    )


def build_schedule_campaign_use_case() -> ScheduleCampaignUseCase:
    """Constrói o use case de agendamento de campanha."""
    return ScheduleCampaignUseCase(
        campaign_repository=DjangoCampaignRepository(),
    )


def build_send_bulk_sms_use_case(empresa) -> SendBulkSMSUseCase:
    """Constrói o use case de envio em massa de SMS."""
    return SendBulkSMSUseCase(
        campaign_repository=DjangoCampaignRepository(),
        message_repository=DjangoMailMessageRepository(),
        bulk_processor=DjangoBulkSMSProcessor(empresa),
    )


def build_filter_recipients_use_case() -> FilterRecipientsUseCase:
    """Constrói o use case de filtro de destinatários."""
    return FilterRecipientsUseCase(
        recipient_repository=DjangoRecipientRepository(),
    )
