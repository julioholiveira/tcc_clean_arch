"""Testes das dataclasses dos ports do Core"""

from datetime import datetime

from src.core.application.ports.customer_data_provider import CustomerData
from src.core.application.ports.network_controller import NetworkAuthorizationResult
from src.core.application.ports.sms_gateway import SMSResult
from src.core.domain.entities import SMSStatus
from src.core.domain.value_objects import PhoneNumber


class TestSMSResult:
    def test_success_factory(self):
        result = SMSResult.success("msg-123")

        assert result.status == SMSStatus.SENT
        assert result.provider_message_id == "msg-123"
        assert isinstance(result.sent_at, datetime)
        assert result.error_message is None

    def test_failure_factory(self):
        result = SMSResult.failure("provider timeout")

        assert result.status == SMSStatus.FAILED
        assert result.error_message == "provider timeout"
        assert result.provider_message_id is None
        assert result.sent_at is None

    def test_direct_instantiation_defaults(self):
        result = SMSResult(status=SMSStatus.PENDING)

        assert result.status == SMSStatus.PENDING
        assert result.provider_message_id is None
        assert result.sent_at is None
        assert result.error_message is None


class TestNetworkAuthorizationResult:
    def test_success_with_session(self):
        result = NetworkAuthorizationResult(success=True, session_id="sess-1", duration_minutes=30)

        assert result.success is True
        assert result.session_id == "sess-1"
        assert result.duration_minutes == 30
        assert result.error_message is None

    def test_defaults(self):
        result = NetworkAuthorizationResult(success=False)

        assert result.success is False
        assert result.session_id is None
        assert result.duration_minutes == 60
        assert result.error_message is None

    def test_failure_with_error(self):
        result = NetworkAuthorizationResult(success=False, error_message="controller offline")

        assert result.success is False
        assert result.error_message == "controller offline"


class TestCustomerData:
    def test_minimal_instantiation_defaults(self):
        phone = PhoneNumber("11987654321")
        customer = CustomerData(phone=phone)

        assert customer.phone == phone
        assert customer.name is None
        assert customer.email is None
        assert customer.document is None
        assert customer.address is None
        assert customer.is_active is True

    def test_full_instantiation(self):
        phone = PhoneNumber("11987654321")
        customer = CustomerData(
            phone=phone,
            name="João",
            email="joao@example.com",
            document="12345678901",
            address="Rua A, 100",
            is_active=False,
        )

        assert customer.name == "João"
        assert customer.email == "joao@example.com"
        assert customer.document == "12345678901"
        assert customer.address == "Rua A, 100"
        assert customer.is_active is False
