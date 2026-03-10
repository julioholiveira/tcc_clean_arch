"""Testes do FilterRecipientsUseCase"""
import pytest
from src.mailing.application.dto.campaign import FilterRecipientsRequest
from src.mailing.application.use_cases.filter_recipients import FilterRecipientsUseCase


class TestFilterRecipientsUseCase:
    @pytest.fixture
    def use_case(self, mock_recipient_repository):
        return FilterRecipientsUseCase(recipient_repository=mock_recipient_repository)

    @pytest.fixture
    def valid_request(self, company_id):
        return FilterRecipientsRequest(company_id=company_id, campaign_id=1, limit=10, offset=0)

    def test_filter_recipients_success(self, use_case, valid_request, sample_recipients, mock_recipient_repository):
        mock_recipient_repository.count_filtered.return_value = 3
        mock_recipient_repository.list_filtered.return_value = sample_recipients
        response = use_case.execute(valid_request)
        assert response.total == 3
        assert len(response.recipients) == 3
        assert response.has_more is False
        assert response.offset == 0
        mock_recipient_repository.list_filtered.assert_called_once()

    def test_filter_recipients_empty(self, use_case, valid_request, mock_recipient_repository):
        mock_recipient_repository.count_filtered.return_value = 0
        mock_recipient_repository.list_filtered.return_value = []
        response = use_case.execute(valid_request)
        assert response.total == 0
        assert len(response.recipients) == 0
        assert response.has_more is False

    def test_filter_recipients_has_more(self, use_case, company_id, mock_recipient_repository, sample_recipients):
        request = FilterRecipientsRequest(company_id=company_id, campaign_id=1, limit=2, offset=0)
        mock_recipient_repository.count_filtered.return_value = 10
        mock_recipient_repository.list_filtered.return_value = sample_recipients[:2]
        response = use_case.execute(request)
        assert response.total == 10
        assert response.has_more is True

    def test_filter_recipients_with_offset(self, use_case, company_id, mock_recipient_repository):
        request = FilterRecipientsRequest(company_id=company_id, campaign_id=1, limit=10, offset=20)
        mock_recipient_repository.count_filtered.return_value = 0
        mock_recipient_repository.list_filtered.return_value = []
        use_case.execute(request)
        call_kwargs = mock_recipient_repository.list_filtered.call_args.kwargs
        assert call_kwargs["offset"] == 20
        assert call_kwargs["limit"] == 10
