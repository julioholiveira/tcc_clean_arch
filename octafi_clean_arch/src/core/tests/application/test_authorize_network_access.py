"""Testes do AuthorizeNetworkAccessUseCase"""

import pytest

from src.core.application.dto.guest_auth import AuthorizeNetworkAccessRequest
from src.core.application.ports.network_controller import NetworkAuthorizationResult
from src.core.application.use_cases.authorize_network_access import AuthorizeNetworkAccessUseCase


class TestAuthorizeNetworkAccessUseCase:
    @pytest.fixture
    def use_case(self, mock_connection_repository, mock_network_controller):
        return AuthorizeNetworkAccessUseCase(
            network_controller=mock_network_controller,
            connection_repository=mock_connection_repository,
        )

    @pytest.fixture
    def valid_request(self, company_id, phone_number, mac_address):
        return AuthorizeNetworkAccessRequest(
            company_id=company_id,
            phone=phone_number,
            mac_address=mac_address,
            duration_minutes=60,
        )

    def test_authorize_success(self, use_case, valid_request, mock_connection_repository, mock_network_controller):
        response = use_case.execute(valid_request)

        assert response.success is True
        assert response.session_id == "session-123"
        assert response.duration_minutes == 60

        mock_network_controller.authorize_guest.assert_called_once()
        mock_connection_repository.save.assert_called_once()

    def test_authorize_network_controller_failure(
        self, use_case, valid_request, mock_connection_repository, mock_network_controller
    ):
        mock_network_controller.authorize_guest.return_value = NetworkAuthorizationResult(
            success=False, error_message="UniFi controller offline"
        )
        response = use_case.execute(valid_request)

        assert response.success is False
        assert response.error_code == "NETWORK_AUTH_FAILED"

    def test_authorize_custom_duration(self, use_case, valid_request, mock_network_controller):
        valid_request.duration_minutes = 120
        response = use_case.execute(valid_request)
        assert response.success is True
        call_args = mock_network_controller.authorize_guest.call_args
        assert call_args.kwargs["duration_minutes"] == 120

    def test_authorize_controller_exception(self, use_case, valid_request, mock_network_controller):
        mock_network_controller.authorize_guest.side_effect = Exception("Connection refused")
        response = use_case.execute(valid_request)
        assert response.success is False
        assert response.error_code == "INTERNAL_ERROR"
