"""Domain Entities para Mailing - Campanhas, Templates e Mensagens"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from src.core.domain.entities import SMSStatus
from src.core.domain.value_objects import CompanyId, PhoneNumber


class CampaignStatus(Enum):
    """Status de campanha de mailing"""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class MailTemplate:
    """Entidade de template de mensagem"""

    company_id: CompanyId
    name: str
    content: Optional[str] = None
    id: Optional[int] = None
    variables: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if len(self.name) > 100:
            raise ValueError("Template name cannot exceed 100 characters")

    def render(self, context: Dict[str, str]) -> str:
        """Renderiza template com variáveis"""
        rendered = self.content
        for var, value in context.items():
            rendered = rendered.replace(f"{{{var}}}", str(value))
        return rendered


@dataclass
class Recipient:
    """Entidade de destinatário de campanha"""

    phone: PhoneNumber
    name: Optional[str] = None
    custom_data: Dict[str, str] = field(default_factory=dict)

    def get_context(self) -> Dict[str, str]:
        """Retorna contexto para renderização de template"""
        return {
            "name": self.name or "Cliente",
            "phone": self.phone.formatted,
            **self.custom_data,
        }


@dataclass
class MailMessage:
    """Entidade de mensagem individual de campanha"""

    campaign_id: int
    recipient: Recipient
    content: str
    id: Optional[int] = None
    status: SMSStatus = SMSStatus.PENDING
    provider_message_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def mark_as_sent(self, provider_id: str) -> None:
        """Marca como enviada"""
        self.status = SMSStatus.SENT
        self.provider_message_id = provider_id
        self.sent_at = datetime.now()

    def mark_as_delivered(self) -> None:
        """Marca como entregue"""
        self.status = SMSStatus.DELIVERED
        self.delivered_at = datetime.now()

    def mark_as_failed(self, error: str) -> None:
        """Marca como falha"""
        self.status = SMSStatus.FAILED
        self.error_message = error


@dataclass
class Campaign:
    """Entidade de campanha de mailing"""

    company_id: CompanyId
    name: str
    template: MailTemplate
    id: Optional[int] = None
    status: CampaignStatus = CampaignStatus.DRAFT
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_recipients: int = 0
    sent_count: int = 0
    delivered_count: int = 0
    failed_count: int = 0

    def can_start(self) -> bool:
        """Verifica se campanha pode ser iniciada"""
        return self.status in [CampaignStatus.DRAFT, CampaignStatus.SCHEDULED]

    def start(self) -> None:
        """Inicia execução da campanha"""
        if not self.can_start():
            raise ValueError(f"Cannot start campaign with status {self.status}")

        self.status = CampaignStatus.IN_PROGRESS
        self.started_at = datetime.now()

    def complete(self) -> None:
        """Finaliza campanha"""
        self.status = CampaignStatus.COMPLETED
        self.completed_at = datetime.now()

    def increment_sent(self) -> None:
        """Incrementa contador de enviados"""
        self.sent_count += 1

    def increment_delivered(self) -> None:
        """Incrementa contador de entregues"""
        self.delivered_count += 1

    def increment_failed(self) -> None:
        """Incrementa contador de falhas"""
        self.failed_count += 1

    def progress_percentage(self) -> float:
        """Retorna percentual de progresso"""
        if self.total_recipients == 0:
            return 0.0
        return (self.sent_count / self.total_recipients) * 100
