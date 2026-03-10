"""
Fábricas de injeção de dependência para a camada de apresentação.
Resolve P12 (DIP): views não conhecem implementações concretas.
"""

from src.core.application.use_cases.authenticate_guest import AuthenticateGuestUseCase
from src.core.application.use_cases.authorize_network_access import AuthorizeNetworkAccessUseCase
from src.core.application.use_cases.get_sms_status import GetSMSStatusUseCase
from src.core.application.use_cases.list_guest_users import ListGuestUsersUseCase
from src.core.application.use_cases.send_verification_sms import SendVerificationSMSUseCase
from src.core.application.use_cases.verify_sms_token import VerifySMSTokenUseCase
from src.core.infrastructure.external_apis.raro_adapter import RaroAdapter
from src.core.infrastructure.network.unifi_adapter import UniFiAdapter
from src.core.infrastructure.repositories.sms_delivery_repository import DjangoSMSDeliveryRepository
from src.core.infrastructure.repositories.sms_token_repository import DjangoSMSTokenRepository
from src.core.infrastructure.repositories.user_repository import (
    DjangoConnectionRepository,
    DjangoUserRepository,
)
from src.core.infrastructure.sms.factory import SMSProviderFactory


def build_authenticate_guest_use_case(empresa) -> AuthenticateGuestUseCase:
    """Constrói o use case de autenticação com todas as dependências injetadas."""
    sms_gateway = SMSProviderFactory.create(empresa)
    customer_provider = RaroAdapter(empresa) if getattr(empresa, "usa_raro", False) else None
    return AuthenticateGuestUseCase(
        user_repository=DjangoUserRepository(),
        token_repository=DjangoSMSTokenRepository(),
        connection_repository=DjangoConnectionRepository(),
        sms_gateway=sms_gateway,
        customer_data_provider=customer_provider,
    )


def build_verify_sms_token_use_case(empresa) -> VerifySMSTokenUseCase:
    """Constrói o use case de verificação de token."""
    return VerifySMSTokenUseCase(
        token_repository=DjangoSMSTokenRepository(),
        network_controller=UniFiAdapter(empresa),
    )


def build_authorize_network_use_case(empresa) -> AuthorizeNetworkAccessUseCase:
    """Constrói o use case de autorização de rede."""
    network_controller = UniFiAdapter(empresa)
    return AuthorizeNetworkAccessUseCase(
        network_controller=network_controller,
        connection_repository=DjangoConnectionRepository(),
    )


def build_send_sms_use_case(empresa) -> SendVerificationSMSUseCase:
    """Constrói o use case de envio de SMS individual."""
    sms_gateway = SMSProviderFactory.create(empresa)
    return SendVerificationSMSUseCase(
        sms_gateway=sms_gateway,
        delivery_repository=DjangoSMSDeliveryRepository(),
    )


def build_get_sms_status_use_case(empresa) -> GetSMSStatusUseCase:
    """Constrói o use case de consulta de status SMS."""
    return GetSMSStatusUseCase(
        delivery_repository=DjangoSMSDeliveryRepository(),
    )


def build_list_guest_users_use_case() -> ListGuestUsersUseCase:
    """Constrói o use case de listagem de usuários guest."""
    return ListGuestUsersUseCase(
        user_repository=DjangoUserRepository(),
    )
