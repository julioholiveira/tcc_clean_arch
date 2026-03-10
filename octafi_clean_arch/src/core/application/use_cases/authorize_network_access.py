"""Use Case: Autorização de Acesso à Rede"""

import logging

from src.core.application.dto.guest_auth import (
    AuthorizeNetworkAccessRequest,
    AuthorizeNetworkAccessResponse,
)
from src.core.application.ports.network_controller import NetworkController
from src.core.domain.entities import Connection
from src.core.domain.repositories import ConnectionRepository

logger = logging.getLogger(__name__)


class AuthorizeNetworkAccessUseCase:
    """Autoriza acesso de guest à rede WiFi"""

    def __init__(
        self,
        network_controller: NetworkController,
        connection_repository: ConnectionRepository,
    ):
        self.network_controller = network_controller
        self.connection_repository = connection_repository

    def execute(
        self, request: AuthorizeNetworkAccessRequest
    ) -> AuthorizeNetworkAccessResponse:
        """
        Autoriza acesso à rede.

        Fluxo:
        1. Autoriza via network controller
        2. Registra conexão no repositório
        3. Retorna resposta
        """

        try:
            # Autoriza rede
            auth_result = self.network_controller.authorize_guest(
                mac_address=request.mac_address,
                user_phone=request.phone,
                duration_minutes=request.duration_minutes,
                bandwidth_limit_kbps=request.bandwidth_limit_kbps,
            )

            if not auth_result.success:
                logger.error(f"Falha ao autorizar rede: {auth_result.error_message}")
                return AuthorizeNetworkAccessResponse(
                    success=False,
                    message=auth_result.error_message or "Erro ao autorizar acesso",
                    error_code="NETWORK_AUTH_FAILED",
                )

            # Registra conexão
            connection = Connection(
                company_id=request.company_id,
                user_phone=request.phone,
                mac_address=request.mac_address,
                controller_name="unifi",  # TODO: parametrizar
            )
            self.connection_repository.save(connection)

            logger.info(
                "Acesso à rede autorizado",
                extra={
                    "session_id": auth_result.session_id,
                    "duration": request.duration_minutes,
                },
            )

            return AuthorizeNetworkAccessResponse(
                success=True,
                session_id=auth_result.session_id,
                duration_minutes=request.duration_minutes,
                message="Acesso autorizado com sucesso",
            )

        except Exception as e:
            logger.error(f"Erro ao autorizar acesso: {str(e)}", exc_info=True)
            return AuthorizeNetworkAccessResponse(
                success=False,
                message="Erro interno ao autorizar acesso",
                error_code="INTERNAL_ERROR",
            )
