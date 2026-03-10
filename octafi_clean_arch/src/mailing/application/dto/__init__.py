"""DTOs para Mailing Application Layer"""

from .campaign import (
    CreateCampaignRequest,
    CreateCampaignResponse,
    FilterRecipientsRequest,
    FilterRecipientsResponse,
    ScheduleCampaignRequest,
    ScheduleCampaignResponse,
    SendBulkSMSRequest,
    SendBulkSMSResponse,
    UpdateCampaignRequest,
    UpdateCampaignResponse,
)

__all__ = [
    "SendBulkSMSRequest",
    "SendBulkSMSResponse",
    "FilterRecipientsRequest",
    "FilterRecipientsResponse",
    "CreateCampaignRequest",
    "CreateCampaignResponse",
    "UpdateCampaignRequest",
    "UpdateCampaignResponse",
    "ScheduleCampaignRequest",
    "ScheduleCampaignResponse",
]
