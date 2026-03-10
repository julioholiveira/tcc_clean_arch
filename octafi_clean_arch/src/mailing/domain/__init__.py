"""Domain layer do Mailing - regras de negócio puras"""

from .entities import (
    Campaign,
    MailTemplate,
    MailMessage,
    Recipient,
    CampaignStatus,
)
from .exceptions import (
    MailingDomainException,
    TemplateNotFoundError,
    TemplateRenderError,
    CampaignStateError,
    RecipientValidationError,
    BulkSendError,
)
from .repositories import (
    MailTemplateRepository,
    CampaignRepository,
    MailMessageRepository,
)

__all__ = [
    # Entities
    'Campaign',
    'MailTemplate',
    'MailMessage',
    'Recipient',
    'CampaignStatus',
    # Exceptions
    'MailingDomainException',
    'TemplateNotFoundError',
    'TemplateRenderError',
    'CampaignStateError',
    'RecipientValidationError',
    'BulkSendError',
    # Repositories
    'MailTemplateRepository',
    'CampaignRepository',
    'MailMessageRepository',
]
