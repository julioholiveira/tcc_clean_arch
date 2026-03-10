"""Configuração de fixtures para testes do Core"""

from datetime import datetime, timedelta

import pytest

from src.core.domain.entities import (
    Connection,
    SMSDelivery,
    SMSProvider,
    SMSTokenEntity,
    User,
)
from src.core.domain.value_objects import (
    CPF,
    CompanyId,
    MACAddress,
    PhoneNumber,
    SMSToken,
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
def cpf():
    """Fixture de CPF padrão"""
    return CPF("12345678909")


@pytest.fixture
def mac_address():
    """Fixture de MACAddress padrão"""
    return MACAddress("AA:BB:CC:DD:EE:FF")


@pytest.fixture
def sms_token():
    """Fixture de SMSToken padrão"""
    return SMSToken("123456")


@pytest.fixture
def user(company_id, phone_number):
    """Fixture de User padrão"""
    return User(company_id=company_id, phone=phone_number, name="Test User")


@pytest.fixture
def sms_token_entity(company_id, phone_number, sms_token):
    """Fixture de SMSTokenEntity padrão"""
    return SMSTokenEntity(
        company_id=company_id,
        phone=phone_number,
        token=sms_token,
        expires_at=datetime.now() + timedelta(minutes=10),
    )


@pytest.fixture
def connection(company_id, phone_number, mac_address):
    """Fixture de Connection padrão"""
    return Connection(
        company_id=company_id,
        user_phone=phone_number,
        mac_address=mac_address,
        controller_name="Test Controller",
        connected_at=datetime.now(),
    )


@pytest.fixture
def sms_delivery(company_id, phone_number):
    """Fixture de SMSDelivery padrão"""
    return SMSDelivery(
        company_id=company_id,
        phone=phone_number,
        message="Test message",
        provider=SMSProvider.SINCH,
    )
