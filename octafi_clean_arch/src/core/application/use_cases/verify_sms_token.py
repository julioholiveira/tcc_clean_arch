"""Use Case: Verificação de Token SMS"""

import logging

from src.core.application.dto.guest_auth import (
    VerifySMSTokenRequest,
    VerifySMSTokenResponse,
)
from src.core.application.ports.network_controller import NetworkController
from src.core.domain.exceptions import TokenExpiredError
from src.core.domain.repositories import SMSTokenRepository

logger = logging.getLogger(__name__)


class VerifySMSTokenUseCase:
    """Verifica token SMS e autoriza acesso à rede"""

    def __init__(
        self,
        token_repository: SMSTokenRepository,
        network_controller: NetworkController,
    ):
        self.token_repository = token_repository
        self.network_controller = network_controller

    def execute(self, request: VerifySMSTokenRequest) -> VerifySMSTokenResponse:
        """
        Verifica token SMS e autoriza acesso.

        Fluxo:
        1. Busca token válido no repositório
        2. Valida expiração
        3. Autoriza acesso à rede
        4. Invalida token (uso único)
        """

        try:
            # Busca token
            token_entity = self.token_repository.find_valid_token(
                request.company_id, request.phone, request.token_value
            )

            if not token_entity:
                logger.warning(
                    "Token inválido", extra={"correlation_id": request.correlation_id}
                )
                return VerifySMSTokenResponse(
                    success=False,
                    message="Código de verificação inválido",
                    error_code="INVALID_TOKEN",
                )

            # Valida expiração
            if token_entity.is_expired():
                logger.warning(
                    "Token expirado", extra={"correlation_id": request.correlation_id}
                )
                raise TokenExpiredError("Código de verificação expirado")

            # Autoriza rede
            auth_result = self.network_controller.authorize_guest(
                mac_address=request.mac_address,
                user_phone=request.phone,
                duration_minutes=60,
            )

            if not auth_result.success:
                logger.error(
                    f"Falha ao autorizar rede: {auth_result.error_message}",
                    extra={"correlation_id": request.correlation_id},
                )
                return VerifySMSTokenResponse(
                    success=False,
                    message="Erro ao autorizar acesso à rede",
                    error_code="NETWORK_AUTH_FAILED",
                )

            logger.info(
                "Acesso autorizado",
                extra={
                    "correlation_id": request.correlation_id,
                    "session_id": auth_result.session_id,
                },
            )

            return VerifySMSTokenResponse(
                success=True,
                message="Acesso autorizado com sucesso",
                network_authorized=True,
                session_id=auth_result.session_id,
            )

        except TokenExpiredError as e:
            return VerifySMSTokenResponse(
                success=False, message=str(e), error_code="TOKEN_EXPIRED"
            )

        except Exception as e:
            logger.error(
                f"Erro em verificação de token: {str(e)}",
                exc_info=True,
                extra={"correlation_id": request.correlation_id},
            )
            return VerifySMSTokenResponse(
                success=False,
                message="Erro interno ao verificar código",
                error_code="INTERNAL_ERROR",
            )
