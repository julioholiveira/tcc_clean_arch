"""Testes do AuthenticateGuestUseCase"""

import pytest

from src.core.application.dto.guest_auth import AuthenticateGuestRequest
from src.core.application.ports.customer_data_provider import CustomerData
from src.core.application.ports.sms_gateway import SMSResult
from src.core.application.use_cases.authenticate_guest import AuthenticateGuestUseCase
from src.core.domain.entities import User


class TestAuthenticateGuestUseCase:
    """Testa o use case de autenticação de guest"""

    @pytest.fixture
    def use_case(
        self,
        mock_user_repository,
        mock_token_repository,
        mock_connection_repository,
        mock_sms_gateway,
    ):
        """Cria use case com mocks"""
        return AuthenticateGuestUseCase(
            user_repository=mock_user_repository,
            token_repository=mock_token_repository,
            connection_repository=mock_connection_repository,
            sms_gateway=mock_sms_gateway,
            customer_data_provider=None,
            max_connections_per_user=3,
        )

    @pytest.fixture
    def valid_request(self, company_id, phone_number, mac_address):
        """Request válido de autenticação"""
        return AuthenticateGuestRequest(
            company_id=company_id,
            mac_address=mac_address,
            phone=phone_number,
            site_id="site-1",
            name="João Silva",
            correlation_id="test-123",
        )

    def test_authenticate_guest_success_new_user(
        self,
        use_case,
        valid_request,
        mock_user_repository,
        mock_token_repository,
        mock_sms_gateway,
    ):
        """Deve autenticar guest novo usuário com sucesso"""
        # Arrange
        mock_user_repository.find_by_phone.return_value = None
        new_user = User(
            id=1,
            company_id=valid_request.company_id,
            phone=valid_request.phone,
            name=valid_request.name,
        )
        mock_user_repository.save.return_value = new_user

        # Act
        response = use_case.execute(valid_request)

        # Assert
        assert response.success is True
        assert response.token_sent is True
        assert response.requires_verification is True
        assert response.user_id == 1
        assert "enviado" in response.message.lower()

        # Verifica que usuário foi criado
        mock_user_repository.save.assert_called_once()

        # Verifica que token foi salvo
        mock_token_repository.save.assert_called_once()

        # Verifica que SMS foi enviado
        mock_sms_gateway.send.assert_called_once()
        call_args = mock_sms_gateway.send.call_args
        assert call_args.kwargs["destination"] == valid_request.phone
        assert "código" in call_args.kwargs["message"].lower()

    def test_authenticate_guest_existing_user(
        self, use_case, valid_request, sample_user, mock_user_repository
    ):
        """Deve autenticar usuário existente"""
        # Arrange
        mock_user_repository.find_by_phone.return_value = sample_user

        # Act
        response = use_case.execute(valid_request)

        # Assert
        assert response.success is True
        assert response.user_id == sample_user.id

        # Não deve criar novo usuário
        mock_user_repository.save.assert_not_called()

    def test_authenticate_guest_connection_limit_exceeded(
        self, use_case, valid_request, mock_connection_repository
    ):
        """Deve rejeitar quando limite de conexões for excedido"""
        # Arrange
        mock_connection_repository.count_active_connections.return_value = 5

        # Act
        response = use_case.execute(valid_request)

        # Assert
        assert response.success is False
        assert response.token_sent is False
        assert response.error_code == "CONNECTION_LIMIT_EXCEEDED"
        assert "conexões" in response.message.lower()

    def test_authenticate_guest_sms_send_failure(
        self, use_case, valid_request, mock_sms_gateway, mock_user_repository
    ):
        """Deve tratar falha no envio de SMS"""
        # Arrange
        mock_user_repository.find_by_phone.return_value = None
        mock_user_repository.save.return_value = User(
            id=1, company_id=valid_request.company_id, phone=valid_request.phone
        )
        mock_sms_gateway.send.return_value = SMSResult.failure("Provider error")

        # Act
        response = use_case.execute(valid_request)

        # Assert
        assert response.success is False
        assert response.token_sent is False
        assert response.error_code == "SMS_SEND_FAILED"

    def test_authenticate_guest_invalid_site_id(self, use_case, valid_request):
        """Deve rejeitar site_id vazio"""
        # Arrange
        valid_request.site_id = ""

        # Act
        response = use_case.execute(valid_request)

        # Assert
        assert response.success is False
        assert response.error_code == "VALIDATION_ERROR"
        assert "site_id" in response.message.lower()

    def test_authenticate_guest_with_raro_integration_inactive_customer(
        self,
        mock_user_repository,
        mock_token_repository,
        mock_connection_repository,
        mock_sms_gateway,
        mock_customer_data_provider,
        valid_request,
    ):
        """Deve rejeitar cliente inativo no Raro"""
        # Arrange
        inactive_customer = CustomerData(
            phone=valid_request.phone, name="João Silva", is_active=False
        )
        mock_customer_data_provider.get_customer_by_phone.return_value = (
            inactive_customer
        )

        use_case = AuthenticateGuestUseCase(
            user_repository=mock_user_repository,
            token_repository=mock_token_repository,
            connection_repository=mock_connection_repository,
            sms_gateway=mock_sms_gateway,
            customer_data_provider=mock_customer_data_provider,
        )

        # Act
        response = use_case.execute(valid_request)

        # Assert
        assert response.success is False
        assert response.error_code == "CUSTOMER_INACTIVE"
        assert "inativo" in response.message.lower()

    def test_authenticate_guest_with_raro_integration_active_customer(
        self,
        mock_user_repository,
        mock_token_repository,
        mock_connection_repository,
        mock_sms_gateway,
        mock_customer_data_provider,
        valid_request,
    ):
        """Deve usar dados do Raro para cliente ativo"""
        # Arrange
        active_customer = CustomerData(
            phone=valid_request.phone, name="João Silva da API Raro", is_active=True
        )
        mock_customer_data_provider.get_customer_by_phone.return_value = active_customer
        mock_user_repository.find_by_phone.return_value = None
        mock_user_repository.save.return_value = User(
            id=1,
            company_id=valid_request.company_id,
            phone=valid_request.phone,
            name=active_customer.name,
        )

        use_case = AuthenticateGuestUseCase(
            user_repository=mock_user_repository,
            token_repository=mock_token_repository,
            connection_repository=mock_connection_repository,
            sms_gateway=mock_sms_gateway,
            customer_data_provider=mock_customer_data_provider,
        )

        # Act
        response = use_case.execute(valid_request)

        # Assert
        assert response.success is True

        # Verifica que nome do Raro foi usado
        saved_user = mock_user_repository.save.call_args[0][0]
        assert saved_user.name == "João Silva da API Raro"
