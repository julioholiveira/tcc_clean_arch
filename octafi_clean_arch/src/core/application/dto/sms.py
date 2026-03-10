"""DTOs para operações de SMS"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from src.core.domain.entities import SMSStatus
from src.core.domain.value_objects import CompanyId, PhoneNumber


@dataclass
class SendSMSRequest:
    """DTO para envio de SMS"""

    company_id: CompanyId
    phone: PhoneNumber
    message: str
    provider_slug: Optional[str] = None  # None = usar padrão da empresa
    correlation_id: Optional[str] = None


@dataclass
class SendSMSResponse:
    """DTO de resposta de envio"""

    success: bool
    provider_name: str
    provider_message_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class SMSStatusRequest:
    """DTO para consulta de status de SMS"""

    company_id: CompanyId
    phone: Optional[PhoneNumber] = None
    delivery_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


@dataclass
class SMSStatusItem:
    """Item de status de SMS"""

    delivery_id: int
    phone: str
    status: SMSStatus
    provider: str
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    error_message: Optional[str]
    message: Optional[str] = None


@dataclass
class SMSStatusResponse:
    """DTO de resposta de status"""

    total: int
    items: List[SMSStatusItem]
    has_more: bool
