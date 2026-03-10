"""DTOs para autenticação de guests - resolve P11 (ISP)"""

from dataclasses import dataclass
from typing import Optional

from src.core.domain.value_objects import CPF, CompanyId, MACAddress, PhoneNumber


@dataclass
class AuthenticateGuestRequest:
    """
    DTO de entrada para autenticação de guest.
    Substitui dependência de `request` (resolve P11).
    """

    company_id: CompanyId
    mac_address: MACAddress
    phone: PhoneNumber
    site_id: str
    campaign_id: Optional[int] = None
    name: Optional[str] = None
    cpf: Optional[CPF] = None
    correlation_id: Optional[str] = None


@dataclass
class AuthenticateGuestResponse:
    """DTO de saída para autenticação"""

    success: bool
    token_sent: bool
    message: str
    requires_verification: bool = True
    user_id: Optional[int] = None
    error_code: Optional[str] = None


@dataclass
class VerifySMSTokenRequest:
    """DTO para verificação de token SMS"""

    company_id: CompanyId
    phone: PhoneNumber
    token_value: str
    mac_address: MACAddress
    correlation_id: Optional[str] = None


@dataclass
class VerifySMSTokenResponse:
    """DTO de saída para verificação"""

    success: bool
    message: str
    network_authorized: bool = False
    session_id: Optional[str] = None
    error_code: Optional[str] = None


@dataclass
class AuthorizeNetworkAccessRequest:
    """DTO para autorização de rede"""

    company_id: CompanyId
    mac_address: MACAddress
    phone: PhoneNumber
    duration_minutes: int = 60
    bandwidth_limit_kbps: Optional[int] = None


@dataclass
class AuthorizeNetworkAccessResponse:
    """DTO de saída para autorização"""

    success: bool
    message: str
    session_id: Optional[str] = None
    duration_minutes: int = 60
    error_code: Optional[str] = None
