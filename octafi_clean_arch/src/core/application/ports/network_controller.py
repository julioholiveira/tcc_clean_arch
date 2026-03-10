"""Port para controle de rede WiFi (UniFi, etc)"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from src.core.domain.value_objects import MACAddress, PhoneNumber


@dataclass
class NetworkAuthorizationResult:
    """Resultado de autorização de acesso à rede"""

    success: bool
    session_id: Optional[str] = None
    duration_minutes: int = 60
    error_message: Optional[str] = None


class NetworkController(ABC):
    """Port para controle de acesso à rede"""

    @abstractmethod
    def authorize_guest(
        self,
        mac_address: MACAddress,
        user_phone: PhoneNumber,
        duration_minutes: int = 60,
        bandwidth_limit_kbps: Optional[int] = None,
    ) -> NetworkAuthorizationResult:
        """
        Autoriza acesso de guest à rede WiFi.

        Args:
            mac_address: Endereço MAC do dispositivo
            user_phone: Telefone do usuário (para rastreamento)
            duration_minutes: Duração do acesso
            bandwidth_limit_kbps: Limite de banda (opcional)

        Returns:
            NetworkAuthorizationResult
        """
        pass

    @abstractmethod
    def revoke_access(self, mac_address: MACAddress) -> bool:
        """Revoga acesso de um dispositivo"""
        pass

    @abstractmethod
    def get_active_connections_count(self, user_phone: PhoneNumber) -> int:
        """Conta conexões ativas de um usuário"""
        pass
