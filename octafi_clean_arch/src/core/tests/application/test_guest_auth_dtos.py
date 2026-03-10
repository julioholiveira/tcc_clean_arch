"""Testes dos DTOs de Guest Authentication"""

from src.core.application.dto.guest_auth import (
    AuthenticateGuestRequest,
    AuthenticateGuestResponse,
    AuthorizeNetworkAccessRequest,
    AuthorizeNetworkAccessResponse,
    VerifySMSTokenRequest,
    VerifySMSTokenResponse,
)
from src.core.domain.value_objects import CompanyId, MACAddress, PhoneNumber


class TestAuthenticateGuestRequest:
    def test_create_request_valid(self):
        request = AuthenticateGuestRequest(
            company_id=CompanyId(1),
            mac_address=MACAddress("AA:BB:CC:DD:EE:FF"),
            phone=PhoneNumber("11987654321"),
            site_id="site-1",
            name="Joao Silva",
            correlation_id="test-123",
        )
        assert request.company_id.value == 1
        assert str(request.phone) == "11987654321"
        assert request.mac_address is not None
        assert request.site_id == "site-1"
        assert request.name == "Joao Silva"

    def test_create_request_optional_fields(self):
        request = AuthenticateGuestRequest(
            company_id=CompanyId(1),
            mac_address=MACAddress("AA:BB:CC:DD:EE:FF"),
            phone=PhoneNumber("11987654321"),
            site_id="site-1",
        )
        assert request.name is None
        assert request.cpf is None


class TestAuthenticateGuestResponse:
    def test_create_success_response(self):
        response = AuthenticateGuestResponse(
            success=True,
            token_sent=True,
            requires_verification=True,
            message="Token enviado com sucesso",
        )
        assert response.success is True
        assert response.token_sent is True
        assert response.error_code is None

    def test_create_error_response(self):
        response = AuthenticateGuestResponse(
            success=False,
            token_sent=False,
            requires_verification=False,
            message="Limite de conexoes excedido",
            error_code="CONNECTION_LIMIT_EXCEEDED",
        )
        assert response.success is False
        assert response.error_code == "CONNECTION_LIMIT_EXCEEDED"


class TestVerifySMSTokenRequest:
    def test_create_request_valid(self):
        request = VerifySMSTokenRequest(
            company_id=CompanyId(1),
            phone=PhoneNumber("11987654321"),
            token_value="123456",
            mac_address=MACAddress("AA:BB:CC:DD:EE:FF"),
            correlation_id="test-123",
        )
        assert request.token_value == "123456"
        assert str(request.phone) == "11987654321"


class TestVerifySMSTokenResponse:
    def test_create_success_response(self):
        response = VerifySMSTokenResponse(
            success=True,
            network_authorized=True,
            session_id="session-123",
            message="Acesso autorizado",
        )
        assert response.success is True
        assert response.network_authorized is True
        assert response.session_id == "session-123"


class TestAuthorizeNetworkAccessRequest:
    def test_create_request_with_default_duration(self):
        request = AuthorizeNetworkAccessRequest(
            company_id=CompanyId(1),
            mac_address=MACAddress("AA:BB:CC:DD:EE:FF"),
            phone=PhoneNumber("11987654321"),
        )
        assert request.duration_minutes == 60

    def test_create_request_with_custom_duration(self):
        request = AuthorizeNetworkAccessRequest(
            company_id=CompanyId(1),
            mac_address=MACAddress("AA:BB:CC:DD:EE:FF"),
            phone=PhoneNumber("11987654321"),
            duration_minutes=120,
        )
        assert request.duration_minutes == 120

    def test_create_request_with_bandwidth_limit(self):
        request = AuthorizeNetworkAccessRequest(
            company_id=CompanyId(1),
            mac_address=MACAddress("AA:BB:CC:DD:EE:FF"),
            phone=PhoneNumber("11987654321"),
            bandwidth_limit_kbps=1024,
        )
        assert request.bandwidth_limit_kbps == 1024


class TestAuthorizeNetworkAccessResponse:
    def test_create_success_response(self):
        response = AuthorizeNetworkAccessResponse(
            success=True,
            message="Acesso autorizado",
            session_id="session-123",
            duration_minutes=60,
        )
        assert response.success is True
        assert response.session_id == "session-123"
        assert response.error_code is None

    def test_create_error_response(self):
        response = AuthorizeNetworkAccessResponse(
            success=False,
            message="Erro ao autorizar",
            error_code="NETWORK_AUTH_FAILED",
        )
        assert response.success is False
        assert response.error_code == "NETWORK_AUTH_FAILED"
