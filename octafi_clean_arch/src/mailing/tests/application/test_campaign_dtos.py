"""Testes dos DTOs de Campaign"""
from datetime import datetime, timedelta
from src.core.domain.value_objects import CompanyId
from src.mailing.application.dto.campaign import (
    CreateCampaignRequest, CreateCampaignResponse,
    FilterRecipientsRequest, FilterRecipientsResponse,
    ScheduleCampaignRequest, SendBulkSMSRequest, SendBulkSMSResponse,
    UpdateCampaignRequest, UpdateCampaignResponse,
)


class TestCreateCampaignRequest:
    def test_create_request_valid(self):
        req = CreateCampaignRequest(company_id=CompanyId(1), name="Campanha Teste", template_id=1)
        assert req.name == "Campanha Teste"
        assert req.template_id == 1

    def test_create_request_optional_defaults(self):
        req = CreateCampaignRequest(company_id=CompanyId(1), name="Campanha Teste", template_id=1)
        assert req.scheduled_for is None


class TestCreateCampaignResponse:
    def test_success_response(self):
        resp = CreateCampaignResponse(success=True, campaign_id=1, message="OK")
        assert resp.success is True
        assert resp.error_code is None

    def test_error_response(self):
        resp = CreateCampaignResponse(success=False, message="Erro", error_code="TEMPLATE_NOT_FOUND")
        assert resp.campaign_id is None


class TestUpdateCampaignRequest:
    def test_partial_fields(self):
        req = UpdateCampaignRequest(campaign_id=1, name="Novo Nome")
        assert req.name == "Novo Nome"
        assert req.template_id is None

    def test_all_optional(self):
        req = UpdateCampaignRequest(campaign_id=1)
        assert req.name is None


class TestScheduleCampaignRequest:
    def test_with_future_date(self):
        future = datetime.now() + timedelta(hours=2)
        req = ScheduleCampaignRequest(campaign_id=1, scheduled_for=future)
        assert req.scheduled_for == future


class TestSendBulkSMSRequest:
    def test_defaults(self):
        req = SendBulkSMSRequest(company_id=CompanyId(1), campaign_id=1)
        assert req.batch_size == 100
        assert req.delay_between_batches_seconds == 1
        assert req.correlation_id is None


class TestSendBulkSMSResponse:
    def test_success_response(self):
        started = datetime.now()
        resp = SendBulkSMSResponse(success=True, campaign_id=1, total_recipients=100,
                                   sent_count=95, failed_count=5, started_at=started)
        assert resp.total_recipients == 100
        assert resp.sent_count + resp.failed_count == 100
        assert resp.error_message is None


class TestFilterRecipientsRequest:
    def test_defaults(self):
        req = FilterRecipientsRequest(company_id=CompanyId(1))
        assert req.limit == 100
        assert req.offset == 0
        assert req.campaign_id is None

    def test_with_pagination(self):
        req = FilterRecipientsRequest(company_id=CompanyId(1), campaign_id=1, limit=10, offset=20)
        assert req.limit == 10
        assert req.offset == 20


class TestFilterRecipientsResponse:
    def test_response(self):
        resp = FilterRecipientsResponse(total=2, recipients=[{"phone": "11"}], has_more=False, offset=0)
        assert resp.total == 2
        assert resp.has_more is False
        assert resp.offset == 0
