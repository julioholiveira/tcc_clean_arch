"""DTOs para campanhas de mailing"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.domain.value_objects import CompanyId


@dataclass
class SendBulkSMSRequest:
    """DTO para envio de campanha"""

    company_id: CompanyId
    campaign_id: int
    batch_size: int = 100
    delay_between_batches_seconds: int = 1
    correlation_id: Optional[str] = None


@dataclass
class SendBulkSMSResponse:
    """DTO de resposta de envio bulk"""

    success: bool
    campaign_id: int
    total_recipients: int
    sent_count: int
    failed_count: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class FilterRecipientsRequest:
    """DTO para filtro de destinatários"""

    company_id: CompanyId
    campaign_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


@dataclass
class FilterRecipientsResponse:
    """DTO de resposta de filtro"""

    total: int
    recipients: List[Dict[str, Any]]
    has_more: bool
    offset: int


@dataclass
class CreateCampaignRequest:
    """DTO para criação de campanha"""

    company_id: CompanyId
    name: str
    template_id: int
    scheduled_for: Optional[datetime] = None


@dataclass
class CreateCampaignResponse:
    """DTO de resposta de criação"""

    success: bool
    message: str
    campaign_id: Optional[int] = None
    error_code: Optional[str] = None


@dataclass
class UpdateCampaignRequest:
    """DTO para atualização de campanha"""

    campaign_id: int
    name: Optional[str] = None
    template_id: Optional[int] = None
    scheduled_for: Optional[datetime] = None


@dataclass
class UpdateCampaignResponse:
    """DTO de resposta de atualização"""

    success: bool
    message: str
    error_code: Optional[str] = None


@dataclass
class ScheduleCampaignRequest:
    """DTO para agendamento de campanha"""

    campaign_id: int
    scheduled_for: datetime


@dataclass
class ScheduleCampaignResponse:
    """DTO de resposta de agendamento"""

    success: bool
    message: str
    scheduled_for: Optional[datetime] = None
    error_code: Optional[str] = None
