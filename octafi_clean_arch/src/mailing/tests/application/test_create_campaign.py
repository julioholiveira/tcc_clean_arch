"""Testes do CreateCampaignUseCase"""
import pytest
from src.mailing.application.dto.campaign import CreateCampaignRequest
from src.mailing.application.use_cases.create_campaign import CreateCampaignUseCase
from src.mailing.domain.entities import CampaignStatus


class TestCreateCampaignUseCase:
    @pytest.fixture
    def use_case(self, mock_campaign_repository, mock_template_repository, sample_template):
        mock_template_repository.find_by_id.return_value = sample_template
        return CreateCampaignUseCase(
            campaign_repository=mock_campaign_repository,
            template_repository=mock_template_repository,
        )

    @pytest.fixture
    def valid_request(self, company_id, sample_template):
        return CreateCampaignRequest(company_id=company_id, name="Nova Campanha", template_id=sample_template.id)

    def test_create_campaign_success(self, use_case, valid_request, mock_campaign_repository, sample_campaign):
        mock_campaign_repository.save.return_value = sample_campaign
        response = use_case.execute(valid_request)
        assert response.success is True
        assert response.campaign_id == sample_campaign.id
        assert "criada" in response.message.lower()
        mock_campaign_repository.save.assert_called_once()
        saved = mock_campaign_repository.save.call_args[0][0]
        assert saved.name == valid_request.name
        assert saved.status == CampaignStatus.DRAFT

    def test_create_campaign_template_not_found(self, company_id, mock_campaign_repository, mock_template_repository):
        mock_template_repository.find_by_id.return_value = None
        use_case = CreateCampaignUseCase(campaign_repository=mock_campaign_repository, template_repository=mock_template_repository)
        request = CreateCampaignRequest(company_id=company_id, name="Campanha", template_id=999)
        response = use_case.execute(request)
        assert response.success is False
        assert response.error_code == "TEMPLATE_NOT_FOUND"

    def test_create_campaign_scheduled(self, use_case, company_id, sample_template, mock_campaign_repository, sample_campaign):
        from datetime import datetime, timedelta
        future_date = datetime.now() + timedelta(hours=2)
        mock_campaign_repository.save.return_value = sample_campaign
        request = CreateCampaignRequest(company_id=company_id, name="Campanha Agendada",
                                        template_id=sample_template.id, scheduled_for=future_date)
        use_case.execute(request)
        saved = mock_campaign_repository.save.call_args[0][0]
        assert saved.status == CampaignStatus.SCHEDULED

    def test_create_campaign_invalid_name(self, use_case, valid_request):
        valid_request.name = ""
        response = use_case.execute(valid_request)
        assert response.success is False
        assert response.error_code == "VALIDATION_ERROR"
