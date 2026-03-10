"""Port para envio de SMS - contrato padronizado (resolve P10, P12)"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.core.domain.entities import SMSStatus
from src.core.domain.value_objects import PhoneNumber


@dataclass
class SMSResult:
    """Resultado padronizado de envio de SMS (resolve LSP)"""

    status: SMSStatus
    provider_message_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None

    @classmethod
    def success(cls, message_id: str) -> "SMSResult":
        """Cria resultado de sucesso"""
        return cls(
            status=SMSStatus.SENT,
            provider_message_id=message_id,
            sent_at=datetime.now(),
        )

    @classmethod
    def failure(cls, error: str) -> "SMSResult":
        """Cria resultado de falha"""
        return cls(status=SMSStatus.FAILED, error_message=error)


class SMSGateway(ABC):
    """
    Port para envio de SMS - assinatura uniforme para todos os providers.
    Resolve P10 (ISP), P12 (DIP) e P7 (OCP).
    """

    @abstractmethod
    def send(
        self, destination: PhoneNumber, message: str, correlation_id: str
    ) -> SMSResult:
        """
        Envia SMS com assinatura padronizada.

        Args:
            destination: Telefone do destinatário
            message: Conteúdo da mensagem
            correlation_id: ID para rastreamento distributed tracing

        Returns:
            SMSResult padronizado
        """
        pass

    @abstractmethod
    def get_delivery_status(self, provider_message_id: str) -> SMSStatus:
        """Consulta status de entrega de uma mensagem"""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Nome do provider (sinch, zenvia, smsmarket)"""
        pass
