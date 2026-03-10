"""Testes do SendVerificationSMSUseCase"""

import pytest

from src.core.application.dto.sms import SendSMSRequest
from src.core.application.use_cases.send_verification_sms import SendVerificationSMSUseCase


class TestSendVerificationSMSUseCase:
    @pytest.fixture
    def use_case(self, mock_sms_gateway, mock_delivery_repository):
        return SendVerificationSMSUseCase(
            sms_gateway=mock_sms_gateway, delivery_repository=mock_delivery_repository
        )

    @pytest.fixture
    def valid_request(self, company_id, phone_number):
        return SendSMSRequest(
            company_id=company_id,
            phone=phone_number,
            message="Seu codigo de verificacao e: 123456",
            correlation_id="test-123",
        )

    def test_send_sms_success(self, use_case, valid_request, mock_sms_gateway, mock_delivery_repository):
        response = use_case.execute(valid_request)

        assert response.success is True
        assert response.provider_message_id == "msg-123"
        assert response.provider_name == "mock-provider"

        mock_sms_gateway.send.assert_called_once_with(
            destination=valid_request.phone,
            message=valid_request.message,
            correlation_id=valid_request.correlation_id,
        )
        mock_delivery_repository.save.assert_called_once()
        saved_delivery = mock_delivery_repository.save.call_args[0][0]
        assert saved_delivery.company_id == valid_request.company_id

    def test_send_sms_gateway_failure(self, use_case, valid_request, mock_sms_gateway):
        from src.core.application.ports.sms_gateway import SMSResult
        mock_sms_gateway.send.return_value = SMSResult.failure("Provider timeout")
        response = use_case.execute(valid_request)
        assert response.success is False

    def test_send_sms_empty_message(self, use_case, valid_request):
        valid_request.message = ""
        response = use_case.execute(valid_request)
        # Use case sends anyway; gateway handles empty message
        # Just verify it returns a response without crashing
        assert hasattr(response, "success")
