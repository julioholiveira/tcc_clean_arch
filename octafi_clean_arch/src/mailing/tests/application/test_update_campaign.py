"""Testes do UpdateCampaignUseCase"""
import pytest
from src.mailing.application.dto.campaign import UpdateCampaignRequest
from src.mailing.application.use_cases.update_campaign import UpdateCampaignUseCase
from src.mailing.domain.entities import CampaignStatus


class TestUpdateCampaignUseCase:
    @pytest.fixture
    def use_case(self, mock_campaign_repository):
        return UpdateCampaignUseCase(campaign_repository=mock_campaign_repository)

    @pytest.fixture
    def valid_request(self):
        return UpdateCampaignRequest(campaign_id=1, name="Campanha Atualizada")

    def test_update_campaign_success(self, use_case, valid_request, sample_campaign, mock_campaign_repository):
        mock_campaign_repository.find_by_id.return_value = sample_campaign
        response = use_case.execute(valid_request)
        assert response.success is True
        assert "atualizada" in response.message.lower()
        mock_campaign_repository.save.assert_called_once()
        updated = mock_campaign_repository.save.call_args[0][0]
        assert updated.name == "Campanha Atualizada"

    def test_update_campaign_not_found(self, use_case, valid_request, mock_campaign_repository):
        mock_campaign_repository.find_by_id.return_value = None
        response = use_case.execute(valid_request)
        assert response.success is False
        assert response.error_code == "CAMPAIGN_NOT_FOUND"

    def test_update_campaign_in_progress(self, use_case, valid_request, sample_campaign, mock_campaign_repository):
        sample_campaign.status = CampaignStatus.IN_PROGRESS
        mock_campaign_repository.find_by_id.return_value = sample_campaign
        response = use_case.execute(valid_request)
        assert response.success is False
        assert response.error_code == "INVALID_STATE"

    def test_update_campaign_completed(self, use_case, valid_request, sample_campaign, mock_campaign_repository):
        sample_campaign.status = CampaignStatus.COMPLETED
        mock_campaign_repository.find_by_id.return_value = sample_campaign
        response = use_case.execute(valid_request)
        assert response.success is False
        assert response.error_code == "INVALID_STATE"

    def test_update_campaign_partial_fields(self, use_case, sample_campaign, mock_campaign_repository):
        mock_campaign_repository.find_by_id.return_value = sample_campaign
        original_name = sample_campaign.name
        use_case.execute(UpdateCampaignRequest(campaign_id=1))
        updated = mock_campaign_repository.save.call_args[0][0]
        assert updated.name == original_name
