"""Testes do ScheduleCampaignUseCase"""
from datetime import datetime, timedelta

import pytest

from src.mailing.application.dto.campaign import ScheduleCampaignRequest
from src.mailing.application.use_cases.schedule_campaign import ScheduleCampaignUseCase
from src.mailing.domain.entities import CampaignStatus


class TestScheduleCampaignUseCase:
    @pytest.fixture
    def use_case(self, mock_campaign_repository):
        return ScheduleCampaignUseCase(campaign_repository=mock_campaign_repository)

    @pytest.fixture
    def future_date(self):
        return datetime.now() + timedelta(hours=2)

    @pytest.fixture
    def valid_request(self, future_date):
        return ScheduleCampaignRequest(campaign_id=1, scheduled_for=future_date)

    def test_schedule_campaign_success(self, use_case, valid_request, sample_campaign, mock_campaign_repository, future_date):
        mock_campaign_repository.find_by_id.return_value = sample_campaign
        response = use_case.execute(valid_request)
        assert response.success is True
        assert "agendada" in response.message.lower()
        mock_campaign_repository.save.assert_called_once()
        saved = mock_campaign_repository.save.call_args[0][0]
        assert saved.status == CampaignStatus.SCHEDULED
        assert saved.scheduled_at == future_date

    def test_schedule_campaign_past_date(self, use_case, sample_campaign, mock_campaign_repository):
        past_date = datetime.now() - timedelta(hours=1)
        request = ScheduleCampaignRequest(campaign_id=1, scheduled_for=past_date)
        mock_campaign_repository.find_by_id.return_value = sample_campaign
        response = use_case.execute(request)
        assert response.success is False
        assert response.error_code == "INVALID_SCHEDULE_DATE"
        assert "futura" in response.message.lower() or "passado" in response.message.lower()

    def test_schedule_campaign_not_draft(self, use_case, valid_request, sample_campaign, mock_campaign_repository):
        sample_campaign.status = CampaignStatus.IN_PROGRESS
        mock_campaign_repository.find_by_id.return_value = sample_campaign
        response = use_case.execute(valid_request)
        assert response.success is False
        assert response.error_code == "INVALID_STATE"

    def test_schedule_campaign_not_found(self, use_case, valid_request, mock_campaign_repository):
        mock_campaign_repository.find_by_id.return_value = None
        response = use_case.execute(valid_request)
        assert response.success is False
        assert response.error_code == "CAMPAIGN_NOT_FOUND"
