"""Testes das Entities do Core Domain"""

from datetime import datetime, timedelta

import pytest

from src.core.domain.entities import (
    Connection,
    SMSDelivery,
    SMSProvider,
    SMSStatus,
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


class TestUser:
    """Testes da entity User"""

    def test_create_user(self):
        """Deve criar usuário"""
        company = CompanyId(1)
        phone = PhoneNumber("11987654321")
        user = User(company_id=company, phone=phone, name="João Silva")

        assert user.company_id == company
        assert user.phone == phone
        assert user.name == "João Silva"

    def test_user_with_cpf(self):
        """Deve criar usuário com CPF"""
        company = CompanyId(1)
        phone = PhoneNumber("11987654321")
        cpf = CPF("12345678909")
        user = User(company_id=company, phone=phone, cpf=cpf)

        assert user.cpf == cpf

    def test_user_name_too_long(self):
        """Deve rejeitar nome muito longo"""
        company = CompanyId(1)
        phone = PhoneNumber("11987654321")

        with pytest.raises(ValueError, match="cannot exceed 256 characters"):
            User(company_id=company, phone=phone, name="a" * 257)


class TestSMSTokenEntity:
    """Testes da entity SMSTokenEntity"""

    def test_create_sms_token(self):
        """Deve criar token SMS"""
        company = CompanyId(1)
        phone = PhoneNumber("11987654321")
        token = SMSToken("123456")

        sms_token = SMSTokenEntity(company_id=company, phone=phone, token=token)

        assert sms_token.token == token
        assert sms_token.resend_count == 0

    def test_token_not_expired(self):
        """Token não deve estar expirado"""
        company = CompanyId(1)
        phone = PhoneNumber("11987654321")
        token = SMSToken("123456")

        sms_token = SMSTokenEntity(
            company_id=company,
            phone=phone,
            token=token,
            expires_at=datetime.now() + timedelta(minutes=10),
        )

        assert not sms_token.is_expired()

    def test_token_expired(self):
        """Token deve estar expirado"""
        company = CompanyId(1)
        phone = PhoneNumber("11987654321")
        token = SMSToken("123456")

        sms_token = SMSTokenEntity(
            company_id=company,
            phone=phone,
            token=token,
            expires_at=datetime.now() - timedelta(minutes=1),
        )

        assert sms_token.is_expired()

    def test_can_resend(self):
        """Deve permitir reenvio quando abaixo do limite"""
        company = CompanyId(1)
        phone = PhoneNumber("11987654321")
        token = SMSToken("123456")

        sms_token = SMSTokenEntity(
            company_id=company, phone=phone, token=token, resend_count=2
        )

        assert sms_token.can_resend(max_resends=3)

    def test_cannot_resend(self):
        """Não deve permitir reenvio quando atingiu o limite"""
        company = CompanyId(1)
        phone = PhoneNumber("11987654321")
        token = SMSToken("123456")

        sms_token = SMSTokenEntity(
            company_id=company, phone=phone, token=token, resend_count=3
        )

        assert not sms_token.can_resend(max_resends=3)

    def test_increment_resend(self):
        """Deve incrementar contador de reenvios"""
        company = CompanyId(1)
        phone = PhoneNumber("11987654321")
        token = SMSToken("123456")

        sms_token = SMSTokenEntity(company_id=company, phone=phone, token=token)

        assert sms_token.resend_count == 0
        sms_token.increment_resend()
        assert sms_token.resend_count == 1


class TestConnection:
    """Testes da entity Connection"""

    def test_create_connection(self):
        """Deve criar conexão"""
        company = CompanyId(1)
        phone = PhoneNumber("11987654321")
        mac = MACAddress("AA:BB:CC:DD:EE:FF")

        connection = Connection(
            company_id=company,
            user_phone=phone,
            mac_address=mac,
            controller_name="Main Controller",
        )

        assert connection.controller_name == "Main Controller"

    def test_active_connection(self):
        """Conexão sem disconnected_at deve estar ativa"""
        company = CompanyId(1)
        phone = PhoneNumber("11987654321")
        mac = MACAddress("AA:BB:CC:DD:EE:FF")

        connection = Connection(
            company_id=company,
            user_phone=phone,
            mac_address=mac,
            controller_name="Main",
            connected_at=datetime.now(),
        )

        assert connection.is_active()

    def test_inactive_connection(self):
        """Conexão com disconnected_at não deve estar ativa"""
        company = CompanyId(1)
        phone = PhoneNumber("11987654321")
        mac = MACAddress("AA:BB:CC:DD:EE:FF")

        connection = Connection(
            company_id=company,
            user_phone=phone,
            mac_address=mac,
            controller_name="Main",
            connected_at=datetime.now(),
            disconnected_at=datetime.now(),
        )

        assert not connection.is_active()

    def test_duration_minutes(self):
        """Deve calcular duração em minutos"""
        company = CompanyId(1)
        phone = PhoneNumber("11987654321")
        mac = MACAddress("AA:BB:CC:DD:EE:FF")

        now = datetime.now()
        connection = Connection(
            company_id=company,
            user_phone=phone,
            mac_address=mac,
            controller_name="Main",
            connected_at=now,
            disconnected_at=now + timedelta(minutes=30),
        )

        assert connection.duration_minutes() == 30


class TestSMSDelivery:
    """Testes da entity SMSDelivery"""

    def test_create_sms_delivery(self):
        """Deve criar entrega de SMS"""
        company = CompanyId(1)
        phone = PhoneNumber("11987654321")

        delivery = SMSDelivery(
            company_id=company,
            phone=phone,
            message="Test message",
            provider=SMSProvider.SINCH,
        )

        assert delivery.status == SMSStatus.PENDING

    def test_mark_as_sent(self):
        """Deve marcar SMS como enviado"""
        company = CompanyId(1)
        phone = PhoneNumber("11987654321")

        delivery = SMSDelivery(
            company_id=company, phone=phone, message="Test", provider=SMSProvider.SINCH
        )

        delivery.mark_as_sent("provider-msg-id-123")

        assert delivery.status == SMSStatus.SENT
        assert delivery.provider_message_id == "provider-msg-id-123"
        assert delivery.sent_at is not None

    def test_mark_as_delivered(self):
        """Deve marcar SMS como entregue"""
        company = CompanyId(1)
        phone = PhoneNumber("11987654321")

        delivery = SMSDelivery(
            company_id=company, phone=phone, message="Test", provider=SMSProvider.SINCH
        )

        delivery.mark_as_delivered()

        assert delivery.status == SMSStatus.DELIVERED
        assert delivery.delivered_at is not None

    def test_mark_as_failed(self):
        """Deve marcar SMS como falho"""
        company = CompanyId(1)
        phone = PhoneNumber("11987654321")

        delivery = SMSDelivery(
            company_id=company, phone=phone, message="Test", provider=SMSProvider.SINCH
        )

        delivery.mark_as_failed("Network error")

        assert delivery.status == SMSStatus.FAILED
        assert delivery.error_message == "Network error"
