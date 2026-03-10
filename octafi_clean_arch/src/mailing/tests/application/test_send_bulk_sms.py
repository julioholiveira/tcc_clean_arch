"""Testes do SendBulkSMSUseCase"""
from datetime import datetime
from unittest.mock import Mock

import pytest

from src.mailing.application.dto.campaign import SendBulkSMSRequest
from src.mailing.application.ports.bulk_sms_processor import BulkSMSProgress
from src.mailing.application.use_cases.send_bulk_sms import SendBulkSMSUseCase
from src.mailing.domain.entities import CampaignStatus


class TestSendBulkSMSUseCase:
    @pytest.fixture
    def use_case(self, mock_campaign_repository, mock_message_repository, mock_bulk_sms_processor):
        return SendBulkSMSUseCase(
            campaign_repository=mock_campaign_repository,
            message_repository=mock_message_repository,
            bulk_processor=mock_bulk_sms_processor,
        )

    @pytest.fixture
    def valid_request(self, company_id):
        return SendBulkSMSRequest(company_id=company_id, campaign_id=1, correlation_id="test-123")

    def test_send_bulk_sms_success(self, use_case, valid_request, sample_campaign,
            mock_campaign_repository, mock_message_repository, mock_bulk_sms_processor):
        mock_campaign_repository.find_by_id.return_value = sample_campaign
        mock_message_repository.list_by_campaign.return_value = [Mock(), Mock(), Mock()]
        response = use_case.execute(valid_request)
        assert response.success is True
        assert response.total_recipients == 3
        assert response.sent_count == 3
        assert response.failed_count == 0
        mock_bulk_sms_processor.process_bulk_send.assert_called_once()

    def test_send_bulk_sms_campaign_not_found(self, use_case, valid_request, mock_campaign_repository):
        mock_campaign_repository.find_by_id.return_value = None
        response = use_case.execute(valid_request)
        assert response.success is False
        assert response.error_message is not None

    def test_send_bulk_sms_no_recipients(self, use_case, valid_request, sample_campaign,
            mock_campaign_repository, mock_message_repository):
        mock_campaign_repository.find_by_id.return_value = sample_campaign
        mock_message_repository.list_by_campaign.return_value = []
        response = use_case.execute(valid_request)
        assert response.success is True
        assert response.total_recipients == 0
        assert response.completed_at is not None

    def test_send_bulk_sms_with_failures(self, use_case, valid_request, sample_campaign,
            mock_campaign_repository, mock_message_repository, mock_bulk_sms_processor):
        mock_campaign_repository.find_by_id.return_value = sample_campaign
        mock_message_repository.list_by_campaign.return_value = [Mock(), Mock(), Mock()]
        # Override the side_effect set in conftest to force a specific result
        mock_bulk_sms_processor.process_bulk_send.side_effect = None
        mock_bulk_sms_processor.process_bulk_send.return_value = BulkSMSProgress(
            total=3, sent=2, failed=1, current_batch=1, started_at=datetime.now()
        )
        response = use_case.execute(valid_request)
        assert response.success is True
        assert response.sent_count == 2
        assert response.failed_count == 1

    def test_send_bulk_sms_updates_campaign_status(self, use_case, valid_request, sample_campaign,
            mock_campaign_repository, mock_message_repository):
        mock_campaign_repository.find_by_id.return_value = sample_campaign
        mock_message_repository.list_by_campaign.return_value = [Mock(), Mock()]
        use_case.execute(valid_request)
        saved_campaign = mock_campaign_repository.save.call_args_list[-1][0][0]
        assert saved_campaign.status == CampaignStatus.COMPLETED

    def test_send_bulk_sms_cannot_start(self, use_case, valid_request, sample_campaign, mock_campaign_repository):
        sample_campaign.status = CampaignStatus.COMPLETED
        mock_campaign_repository.find_by_id.return_value = sample_campaign
        response = use_case.execute(valid_request)
        assert response.success is False
