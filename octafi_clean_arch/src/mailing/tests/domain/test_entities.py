"""Testes das Entities do Mailing Domain"""

import pytest

from src.core.domain.entities import SMSStatus
from src.core.domain.value_objects import CompanyId, PhoneNumber
from src.mailing.domain.entities import (
    Campaign,
    CampaignStatus,
    MailMessage,
    MailTemplate,
    Recipient,
)


class TestMailTemplate:
    """Testes da entity MailTemplate"""

    def test_create_template(self):
        """Deve criar template"""
        company = CompanyId(1)
        template = MailTemplate(
            company_id=company, name="Welcome", content="Olá {name}!"
        )

        assert template.name == "Welcome"
        assert template.content == "Olá {name}!"

    def test_template_name_too_long(self):
        """Deve rejeitar nome muito longo"""
        company = CompanyId(1)

        with pytest.raises(ValueError, match="cannot exceed 100 characters"):
            MailTemplate(company_id=company, name="a" * 101, content="Test")

    def test_render_template(self):
        """Deve renderizar template com variáveis"""
        company = CompanyId(1)
        template = MailTemplate(
            company_id=company,
            name="Welcome",
            content="Olá {name}, seu código é {code}!",
        )

        rendered = template.render({"name": "João", "code": "123"})
        assert rendered == "Olá João, seu código é 123!"

    def test_render_template_missing_variable(self):
        """Renderização deve manter variável não fornecida"""
        company = CompanyId(1)
        template = MailTemplate(
            company_id=company, name="Welcome", content="Olá {name}!"
        )

        rendered = template.render({})
        assert rendered == "Olá {name}!"


class TestRecipient:
    """Testes da entity Recipient"""

    def test_create_recipient(self):
        """Deve criar destinatário"""
        phone = PhoneNumber("11987654321")
        recipient = Recipient(phone=phone, name="João Silva")

        assert recipient.phone == phone
        assert recipient.name == "João Silva"

    def test_get_context(self):
        """Deve gerar contexto para template"""
        phone = PhoneNumber("11987654321")
        recipient = Recipient(
            phone=phone, name="João Silva", custom_data={"cidade": "São Paulo"}
        )

        context = recipient.get_context()

        assert context["name"] == "João Silva"
        assert context["phone"] == "(11) 98765-4321"
        assert context["cidade"] == "São Paulo"

    def test_get_context_no_name(self):
        """Deve usar nome padrão quando não fornecido"""
        phone = PhoneNumber("11987654321")
        recipient = Recipient(phone=phone)

        context = recipient.get_context()
        assert context["name"] == "Cliente"


class TestMailMessage:
    """Testes da entity MailMessage"""

    def test_create_message(self):
        """Deve criar mensagem"""
        phone = PhoneNumber("11987654321")
        recipient = Recipient(phone=phone)

        message = MailMessage(
            campaign_id=1, recipient=recipient, content="Test message"
        )

        assert message.status == SMSStatus.PENDING

    def test_mark_as_sent(self):
        """Deve marcar como enviada"""
        phone = PhoneNumber("11987654321")
        recipient = Recipient(phone=phone)

        message = MailMessage(campaign_id=1, recipient=recipient, content="Test")

        message.mark_as_sent("provider-123")

        assert message.status == SMSStatus.SENT
        assert message.provider_message_id == "provider-123"
        assert message.sent_at is not None

    def test_mark_as_delivered(self):
        """Deve marcar como entregue"""
        phone = PhoneNumber("11987654321")
        recipient = Recipient(phone=phone)

        message = MailMessage(campaign_id=1, recipient=recipient, content="Test")

        message.mark_as_delivered()

        assert message.status == SMSStatus.DELIVERED
        assert message.delivered_at is not None

    def test_mark_as_failed(self):
        """Deve marcar como falha"""
        phone = PhoneNumber("11987654321")
        recipient = Recipient(phone=phone)

        message = MailMessage(campaign_id=1, recipient=recipient, content="Test")

        message.mark_as_failed("Network error")

        assert message.status == SMSStatus.FAILED
        assert message.error_message == "Network error"


class TestCampaign:
    """Testes da entity Campaign"""

    def test_create_campaign(self):
        """Deve criar campanha"""
        company = CompanyId(1)
        template = MailTemplate(company_id=company, name="Test", content="Test content")

        campaign = Campaign(company_id=company, name="Campaign Test", template=template)

        assert campaign.status == CampaignStatus.DRAFT
        assert campaign.sent_count == 0

    def test_can_start_from_draft(self):
        """Deve permitir iniciar campanha rascunho"""
        company = CompanyId(1)
        template = MailTemplate(company_id=company, name="Test", content="Test")

        campaign = Campaign(company_id=company, name="Test", template=template)

        assert campaign.can_start()

    def test_can_start_from_scheduled(self):
        """Deve permitir iniciar campanha agendada"""
        company = CompanyId(1)
        template = MailTemplate(company_id=company, name="Test", content="Test")

        campaign = Campaign(
            company_id=company,
            name="Test",
            template=template,
            status=CampaignStatus.SCHEDULED,
        )

        assert campaign.can_start()

    def test_cannot_start_completed(self):
        """Não deve permitir iniciar campanha completada"""
        company = CompanyId(1)
        template = MailTemplate(company_id=company, name="Test", content="Test")

        campaign = Campaign(
            company_id=company,
            name="Test",
            template=template,
            status=CampaignStatus.COMPLETED,
        )

        assert not campaign.can_start()

    def test_start_campaign(self):
        """Deve iniciar campanha"""
        company = CompanyId(1)
        template = MailTemplate(company_id=company, name="Test", content="Test")

        campaign = Campaign(company_id=company, name="Test", template=template)

        campaign.start()

        assert campaign.status == CampaignStatus.IN_PROGRESS
        assert campaign.started_at is not None

    def test_start_campaign_invalid_status(self):
        """Deve rejeitar iniciar campanha em status inválido"""
        company = CompanyId(1)
        template = MailTemplate(company_id=company, name="Test", content="Test")

        campaign = Campaign(
            company_id=company,
            name="Test",
            template=template,
            status=CampaignStatus.COMPLETED,
        )

        with pytest.raises(ValueError, match="Cannot start campaign"):
            campaign.start()

    def test_complete_campaign(self):
        """Deve completar campanha"""
        company = CompanyId(1)
        template = MailTemplate(company_id=company, name="Test", content="Test")

        campaign = Campaign(
            company_id=company,
            name="Test",
            template=template,
            status=CampaignStatus.IN_PROGRESS,
        )

        campaign.complete()

        assert campaign.status == CampaignStatus.COMPLETED
        assert campaign.completed_at is not None

    def test_increment_counters(self):
        """Deve incrementar contadores"""
        company = CompanyId(1)
        template = MailTemplate(company_id=company, name="Test", content="Test")

        campaign = Campaign(company_id=company, name="Test", template=template)

        assert campaign.sent_count == 0
        campaign.increment_sent()
        assert campaign.sent_count == 1

        assert campaign.delivered_count == 0
        campaign.increment_delivered()
        assert campaign.delivered_count == 1

        assert campaign.failed_count == 0
        campaign.increment_failed()
        assert campaign.failed_count == 1

    def test_progress_percentage(self):
        """Deve calcular percentual de progresso"""
        company = CompanyId(1)
        template = MailTemplate(company_id=company, name="Test", content="Test")

        campaign = Campaign(
            company_id=company, name="Test", template=template, total_recipients=100
        )

        assert campaign.progress_percentage() == 0.0

        campaign.sent_count = 50
        assert campaign.progress_percentage() == 50.0

        campaign.sent_count = 100
        assert campaign.progress_percentage() == 100.0

    def test_progress_percentage_no_recipients(self):
        """Deve retornar 0% quando não há destinatários"""
        company = CompanyId(1)
        template = MailTemplate(company_id=company, name="Test", content="Test")

        campaign = Campaign(
            company_id=company, name="Test", template=template, total_recipients=0
        )

        assert campaign.progress_percentage() == 0.0
