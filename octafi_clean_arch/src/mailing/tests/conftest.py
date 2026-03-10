"""Configuração de fixtures para testes do Mailing"""

import pytest

from src.core.domain.value_objects import CompanyId, PhoneNumber
from src.mailing.domain.entities import (
    Campaign,
    MailMessage,
    MailTemplate,
    Recipient,
)


@pytest.fixture
def company_id():
    """Fixture de CompanyId padrão"""
    return CompanyId(1)


@pytest.fixture
def phone_number():
    """Fixture de PhoneNumber padrão"""
    return PhoneNumber("11987654321")


@pytest.fixture
def mail_template(company_id):
    """Fixture de MailTemplate padrão"""
    return MailTemplate(
        company_id=company_id,
        name="Test Template",
        content="Olá {name}, seu código é {code}!",
    )


@pytest.fixture
def recipient(phone_number):
    """Fixture de Recipient padrão"""
    return Recipient(phone=phone_number, name="João Silva")


@pytest.fixture
def campaign(company_id, mail_template):
    """Fixture de Campaign padrão"""
    return Campaign(
        company_id=company_id,
        name="Test Campaign",
        template=mail_template,
        total_recipients=100,
    )


@pytest.fixture
def mail_message(recipient):
    """Fixture de MailMessage padrão"""
    return MailMessage(
        campaign_id=1, recipient=recipient, content="Test message content"
    )
