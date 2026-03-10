"""
Use Case: Autenticação de Guest WiFi
Resolve P1 - Decomposição de landingpage_guest (9 responsabilidades)
"""

import logging
from typing import Any, Optional

from src.core.application.dto.guest_auth import (
    AuthenticateGuestRequest,
    AuthenticateGuestResponse,
)
from src.core.application.ports.customer_data_provider import CustomerDataProvider
from src.core.application.ports.sms_gateway import SMSGateway
from src.core.domain.entities import SMSTokenEntity, User
from src.core.domain.exceptions import (
    ConnectionLimitExceededError,
    ValidationError,
)
from src.core.domain.repositories import (
    ConnectionRepository,
    SMSTokenRepository,
    UserRepository,
)
from src.core.domain.services.phone_validator import PhoneValidator
from src.core.domain.services.token_generator import TokenGenerator

logger = logging.getLogger(__name__)


class AuthenticateGuestUseCase:
    """
    Orquestra as 9 responsabilidades de landingpage_guest:
    1. Validação HTTP/entrada
    2. Parâmetros empresa
    3. API Raro (se integrado)
    4. Tokens SMS
    5. Envio SMS
    6. Limite conexões
    7. CRUD usuários
    8. Templates (delegado para Strategy)
    9. Liberação WiFi (delegado para outro use case)
    """

    def __init__(
        self,
        user_repository: UserRepository,
        token_repository: SMSTokenRepository,
        connection_repository: ConnectionRepository,
        sms_gateway: SMSGateway,
        customer_data_provider: Optional[CustomerDataProvider] = None,
        max_connections_per_user: int = 3,
    ):
        self.user_repository = user_repository
        self.token_repository = token_repository
        self.connection_repository = connection_repository
        self.sms_gateway = sms_gateway
        self.customer_data_provider = customer_data_provider
        self.max_connections_per_user = max_connections_per_user

    def execute(self, request: AuthenticateGuestRequest) -> AuthenticateGuestResponse:
        """
        Executa autenticação de guest.

        Fluxo:
        1. Valida entrada
        2. Verifica dados do cliente (API Raro se configurado)
        3. Verifica limite de conexões
        4. Cria/atualiza usuário
        5. Gera e envia token SMS
        """

        try:
            # Responsabilidade 1: Validação HTTP/entrada
            self._validate_request(request)

            # Responsabilidade 2: Parâmetros empresa (já vem no DTO via company_id)
            company_id = request.company_id

            # Responsabilidade 3: API Raro (se integrado)
            customer_data = None
            if self.customer_data_provider:
                customer_data = self.customer_data_provider.get_customer_by_phone(
                    company_id, request.phone
                )
                if customer_data and not customer_data.is_active:
                    return AuthenticateGuestResponse(
                        success=False,
                        token_sent=False,
                        message="Cliente inativo no sistema",
                        error_code="CUSTOMER_INACTIVE",
                    )

            # Responsabilidade 6: Limite conexões
            active_connections = self.connection_repository.count_active_connections(
                company_id, request.phone
            )
            if active_connections >= self.max_connections_per_user:
                raise ConnectionLimitExceededError(
                    f"Máximo de {self.max_connections_per_user} conexões simultâneas"
                )

            # Responsabilidade 7: CRUD usuários
            user = self._get_or_create_user(request, customer_data)

            # Responsabilidade 4: Tokens SMS
            token = TokenGenerator.generate()
            expiration = TokenGenerator.calculate_expiration(minutes=10)

            token_entity = SMSTokenEntity(
                company_id=company_id,
                phone=request.phone,
                token=token,
                name=user.name,
                cpf=user.cpf,
                expires_at=expiration,
            )
            self.token_repository.save(token_entity)

            # Responsabilidade 5: Envio SMS
            message = (
                f"Seu código de acesso WiFi: {token.value}. Válido por 10 minutos."
            )
            sms_result = self.sms_gateway.send(
                destination=request.phone,
                message=message,
                correlation_id=request.correlation_id or "auth-guest",
            )

            if sms_result.status.value not in ["sent", "pending"]:
                logger.error(
                    f"Falha ao enviar SMS: {sms_result.error_message}",
                    extra={"correlation_id": request.correlation_id},
                )
                return AuthenticateGuestResponse(
                    success=False,
                    token_sent=False,
                    message="Erro ao enviar código de verificação",
                    error_code="SMS_SEND_FAILED",
                )

            logger.info(
                "Token SMS enviado com sucesso",
                extra={
                    "correlation_id": request.correlation_id,
                    "provider": self.sms_gateway.provider_name,
                },
            )

            return AuthenticateGuestResponse(
                success=True,
                token_sent=True,
                message="Código de verificação enviado por SMS",
                requires_verification=True,
                user_id=user.id,
            )

        except ValidationError as e:
            logger.warning(f"Erro de validação: {str(e)}")
            return AuthenticateGuestResponse(
                success=False,
                token_sent=False,
                message=str(e),
                error_code="VALIDATION_ERROR",
            )

        except ConnectionLimitExceededError as e:
            logger.warning(f"Limite de conexões excedido: {str(e)}")
            return AuthenticateGuestResponse(
                success=False,
                token_sent=False,
                message=str(e),
                error_code="CONNECTION_LIMIT_EXCEEDED",
            )

        except Exception as e:
            logger.error(
                f"Erro inesperado em autenticação: {str(e)}",
                exc_info=True,
                extra={"correlation_id": request.correlation_id},
            )
            return AuthenticateGuestResponse(
                success=False,
                token_sent=False,
                message="Erro interno ao processar solicitação",
                error_code="INTERNAL_ERROR",
            )

    def _validate_request(self, request: AuthenticateGuestRequest) -> None:
        """Valida entrada (responsabilidade 1)"""
        PhoneValidator.validate_ddd(request.phone)

        if not request.site_id:
            raise ValidationError("site_id é obrigatório")

    def _get_or_create_user(
        self, request: AuthenticateGuestRequest, customer_data: Optional[Any]
    ) -> User:
        """Cria ou atualiza usuário (responsabilidade 7)"""

        user = self.user_repository.find_by_phone(request.company_id, request.phone)

        if not user:
            # Prioriza dados da API Raro
            name = customer_data.name if customer_data else request.name

            user = User(
                company_id=request.company_id,
                phone=request.phone,
                name=name,
                cpf=request.cpf,
            )
            user = self.user_repository.save(user)

        return user
