"""Domain Entities - Objetos com identidade e lógica de negócio"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

from .value_objects import CompanyId, PhoneNumber, CPF, MACAddress, SMSToken


class SMSProvider(Enum):
    """Provedores de SMS suportados"""
    SINCH = "sinch"
    ZENVIA = "zenvia"
    SMSMARKET = "smsmarket"


class SMSStatus(Enum):
    """Status de entrega de SMS"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class User:
    """Entidade de usuário guest (WiFi)"""
    company_id: CompanyId
    phone: PhoneNumber
    id: Optional[int] = None
    name: Optional[str] = None
    cpf: Optional[CPF] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.name and len(self.name) > 256:
            raise ValueError("Name cannot exceed 256 characters")


@dataclass
class SMSTokenEntity:
    """Entidade de token SMS para verificação"""
    company_id: CompanyId
    phone: PhoneNumber
    token: SMSToken
    id: Optional[int] = None
    name: Optional[str] = None
    cpf: Optional[CPF] = None
    resend_count: int = 0
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Verifica se token expirou"""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    def can_resend(self, max_resends: int = 3) -> bool:
        """Verifica se pode reenviar token"""
        return self.resend_count < max_resends
    
    def increment_resend(self) -> None:
        """Incrementa contador de reenvios"""
        self.resend_count += 1


@dataclass
class Connection:
    """Entidade de conexão de rede (histórico)"""
    company_id: CompanyId
    user_phone: PhoneNumber
    mac_address: MACAddress
    controller_name: str
    id: Optional[int] = None
    ip_address: Optional[str] = None
    connected_at: Optional[datetime] = None
    disconnected_at: Optional[datetime] = None
    
    def is_active(self) -> bool:
        """Verifica se conexão está ativa"""
        return self.disconnected_at is None
    
    def duration_minutes(self) -> Optional[int]:
        """Duração da conexão em minutos"""
        if not self.connected_at or not self.disconnected_at:
            return None
        
        delta = self.disconnected_at - self.connected_at
        return int(delta.total_seconds() / 60)


@dataclass
class SMSDelivery:
    """Entidade de envio de SMS (rastreamento)"""
    company_id: CompanyId
    phone: PhoneNumber
    # message: str
    provider: SMSProvider
    id: Optional[int] = None
    status: SMSStatus = SMSStatus.PENDING
    provider_message_id: Optional[str] = None
    correlation_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def mark_as_sent(self, provider_message_id: str) -> None:
        """Marca SMS como enviado"""
        self.status = SMSStatus.SENT
        self.provider_message_id = provider_message_id
        self.sent_at = datetime.now()
    
    def mark_as_delivered(self) -> None:
        """Marca SMS como entregue"""
        self.status = SMSStatus.DELIVERED
        self.delivered_at = datetime.now()
    
    def mark_as_failed(self, error: str) -> None:
        """Marca SMS como falho"""
        self.status = SMSStatus.FAILED
        self.error_message = error


@dataclass
class Historico:
    """Entidade de histórico de ações (audit log)"""
    company_id: CompanyId
    action: str
    user_phone: Optional[PhoneNumber] = None
    id: Optional[int] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: Optional[datetime] = None
