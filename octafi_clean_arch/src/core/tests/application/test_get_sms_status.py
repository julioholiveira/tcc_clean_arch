"""Testes do GetSMSStatusUseCase"""

import pytest

from src.core.application.dto.sms import SMSStatusItem, SMSStatusRequest
from src.core.application.use_cases.get_sms_status import GetSMSStatusUseCase
from src.core.domain.entities import SMSStatus


class TestGetSMSStatusUseCase:
    @pytest.fixture
    def use_case(self, mock_delivery_repository):
        return GetSMSStatusUseCase(delivery_repository=mock_delivery_repository)

    @pytest.fixture
    def valid_request(self, company_id):
        return SMSStatusRequest(company_id=company_id, limit=10, offset=0)

    def test_get_status_success(self, use_case, valid_request, company_id, mock_delivery_repository):
        from datetime import datetime
        from unittest.mock import Mock

        delivery = Mock()
        delivery.id = 1
        delivery.phone.value = "11987654321"
        delivery.message = "Test message"
        delivery.status = SMSStatus.SENT
        delivery.provider = "sinch"
        delivery.sent_at = datetime.now()
        delivery.delivered_at = None
        delivery.error_message = None

        mock_delivery_repository.count_filtered.return_value = 1
        mock_delivery_repository.list_filtered.return_value = [delivery]

        response = use_case.execute(valid_request)

        assert response.total == 1
        assert len(response.items) == 1
        assert response.items[0].status == SMSStatus.SENT
        assert response.has_more is False

    def test_get_status_empty(self, use_case, valid_request, mock_delivery_repository):
        mock_delivery_repository.count_filtered.return_value = 0
        mock_delivery_repository.list_filtered.return_value = []

        response = use_case.execute(valid_request)

        assert response.total == 0
        assert response.items == []
        assert response.has_more is False

    def test_get_status_with_phone_filter(self, use_case, company_id, mock_delivery_repository, phone_number):
        request = SMSStatusRequest(company_id=company_id, phone=phone_number)
        mock_delivery_repository.count_filtered.return_value = 0
        mock_delivery_repository.list_filtered.return_value = []

        use_case.execute(request)

        call_kwargs = mock_delivery_repository.list_filtered.call_args.kwargs
        assert call_kwargs["phone"] == phone_number

    def test_get_status_has_more_flag(self, use_case, company_id, mock_delivery_repository):
        from unittest.mock import Mock
        from datetime import datetime

        request = SMSStatusRequest(company_id=company_id, limit=1, offset=0)

        delivery = Mock()
        delivery.id = 1
        delivery.phone.value = "11987654321"
        delivery.message = "Test"
        delivery.status = SMSStatus.SENT
        delivery.provider = "sinch"
        delivery.sent_at = datetime.now()
        delivery.delivered_at = None
        delivery.error_message = None

        mock_delivery_repository.count_filtered.return_value = 5
        mock_delivery_repository.list_filtered.return_value = [delivery]

        response = use_case.execute(request)

        assert response.total == 5
        assert response.has_more is True
