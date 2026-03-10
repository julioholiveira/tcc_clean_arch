"""Testes do VerifySMSTokenUseCase"""

from datetime import datetime, timedelta

import pytest

from src.core.application.dto.guest_auth import VerifySMSTokenRequest
from src.core.application.ports.network_controller import NetworkAuthorizationResult
from src.core.application.use_cases.verify_sms_token import VerifySMSTokenUseCase


class TestVerifySMSTokenUseCase:
    """Testa o use case de verificação de token SMS"""

    @pytest.fixture
    def use_case(self, mock_token_repository, mock_network_controller):
        """Cria use case com mocks"""
        return VerifySMSTokenUseCase(
            token_repository=mock_token_repository,
            network_controller=mock_network_controller,
        )

    @pytest.fixture
    def valid_request(self, company_id, phone_number, mac_address):
        """Request válido de verificação"""
        return VerifySMSTokenRequest(
            company_id=company_id,
            phone=phone_number,
            token_value="123456",
            mac_address=mac_address,
            correlation_id="test-123",
        )

    def test_verify_token_success(
        self,
        use_case,
        valid_request,
        sample_token_entity,
        mock_token_repository,
        mock_network_controller,
    ):
        """Deve verificar token e autorizar rede com sucesso"""
        # Arrange
        mock_token_repository.find_valid_token.return_value = sample_token_entity

        # Act
        response = use_case.execute(valid_request)

        # Assert
        assert response.success is True
        assert response.network_authorized is True
        assert response.session_id == "session-123"
        assert "autorizado" in response.message.lower()

        # Verifica que rede foi autorizada
        mock_network_controller.authorize_guest.assert_called_once()
        call_args = mock_network_controller.authorize_guest.call_args
        assert call_args.kwargs["mac_address"] == valid_request.mac_address
        assert call_args.kwargs["user_phone"] == valid_request.phone

    def test_verify_token_invalid_token(
        self, use_case, valid_request, mock_token_repository
    ):
        """Deve rejeitar token inválido"""
        # Arrange
        mock_token_repository.find_valid_token.return_value = None

        # Act
        response = use_case.execute(valid_request)

        # Assert
        assert response.success is False
        assert response.network_authorized is False
        assert response.error_code == "INVALID_TOKEN"
        assert "inválido" in response.message.lower()

    def test_verify_token_expired(
        self, use_case, valid_request, sample_token_entity, mock_token_repository
    ):
        """Deve rejeitar token expirado"""
        # Arrange
        sample_token_entity.expires_at = datetime.now() - timedelta(minutes=1)
        mock_token_repository.find_valid_token.return_value = sample_token_entity

        # Act
        response = use_case.execute(valid_request)

        # Assert
        assert response.success is False
        assert response.error_code == "TOKEN_EXPIRED"
        assert "expirado" in response.message.lower()

    def test_verify_token_network_authorization_failed(
        self,
        use_case,
        valid_request,
        sample_token_entity,
        mock_token_repository,
        mock_network_controller,
    ):
        """Deve tratar falha na autorização de rede"""
        # Arrange
        mock_token_repository.find_valid_token.return_value = sample_token_entity
        mock_network_controller.authorize_guest.return_value = (
            NetworkAuthorizationResult(
                success=False, error_message="Network controller error"
            )
        )

        # Act
        response = use_case.execute(valid_request)

        # Assert
        assert response.success is False
        assert response.network_authorized is False
        assert response.error_code == "NETWORK_AUTH_FAILED"
