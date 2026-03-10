"""Testes dos DTOs de SMS"""

from datetime import datetime

from src.core.application.dto.sms import (
    SendSMSRequest,
    SendSMSResponse,
    SMSStatusItem,
    SMSStatusRequest,
    SMSStatusResponse,
)
from src.core.domain.entities import SMSStatus
from src.core.domain.value_objects import CompanyId, PhoneNumber


class TestSendSMSRequest:
    def test_create_request_valid(self):
        request = SendSMSRequest(
            company_id=CompanyId(1),
            phone=PhoneNumber("11987654321"),
            message="Teste de mensagem",
            correlation_id="test-123",
        )
        assert request.company_id.value == 1
        assert str(request.phone) == "11987654321"
        assert request.message == "Teste de mensagem"

    def test_create_request_with_provider(self):
        request = SendSMSRequest(
            company_id=CompanyId(1),
            phone=PhoneNumber("11987654321"),
            message="Teste",
            provider_slug="sinch",
        )
        assert request.provider_slug == "sinch"

    def test_create_request_without_optional_fields(self):
        request = SendSMSRequest(
            company_id=CompanyId(1),
            phone=PhoneNumber("11987654321"),
            message="Teste",
        )
        assert request.provider_slug is None
        assert request.correlation_id is None


class TestSendSMSResponse:
    def test_create_success_response(self):
        response = SendSMSResponse(
            success=True,
            provider_name="sinch",
            provider_message_id="msg-123",
        )
        assert response.success is True
        assert response.provider_message_id == "msg-123"
        assert response.provider_name == "sinch"
        assert response.error_message is None

    def test_create_error_response(self):
        response = SendSMSResponse(
            success=False,
            provider_name="sinch",
            error_message="Provider timeout",
        )
        assert response.success is False
        assert response.provider_message_id is None
        assert response.error_message == "Provider timeout"


class TestSMSStatusRequest:
    def test_create_request_defaults(self):
        request = SMSStatusRequest(company_id=CompanyId(1))
        assert request.phone is None
        assert request.delivery_id is None
        assert request.limit == 100
        assert request.offset == 0

    def test_create_request_with_filters(self):
        request = SMSStatusRequest(
            company_id=CompanyId(1),
            phone=PhoneNumber("11987654321"),
            delivery_id=42,
            limit=10,
            offset=20,
        )
        assert str(request.phone) == "11987654321"
        assert request.delivery_id == 42
        assert request.limit == 10
        assert request.offset == 20


class TestSMSStatusResponse:
    def test_create_response_empty(self):
        response = SMSStatusResponse(total=0, items=[], has_more=False)
        assert response.total == 0
        assert response.items == []
        assert response.has_more is False

    def test_create_response_with_items(self):
        sent_at = datetime.now()
        items = [
            SMSStatusItem(
                delivery_id=1,
                phone="11987654321",
                message="Teste",
                status=SMSStatus.DELIVERED,
                provider="sinch",
                sent_at=sent_at,
                delivered_at=sent_at,
                error_message=None,
            )
        ]
        response = SMSStatusResponse(total=1, items=items, has_more=False)
        assert response.total == 1
        assert len(response.items) == 1
        assert response.items[0].status == SMSStatus.DELIVERED

    def test_has_more_flag(self):
        response = SMSStatusResponse(total=100, items=[], has_more=True)
        assert response.has_more is True
