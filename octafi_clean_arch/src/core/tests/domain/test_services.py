"""Testes dos Domain Services do Core"""

from datetime import datetime

import pytest

from src.core.domain.exceptions import ValidationError
from src.core.domain.services import PhoneValidator, TokenGenerator
from src.core.domain.value_objects import PhoneNumber, SMSToken


class TestTokenGenerator:
    """Testes do TokenGenerator"""

    def test_generate_token(self):
        """Deve gerar token de 6 dígitos"""
        token = TokenGenerator.generate()

        assert isinstance(token, SMSToken)
        assert len(token.value) == 6
        assert token.value.isdigit()

    def test_generate_unique_tokens(self):
        """Deve gerar tokens diferentes (probabilisticamente)"""
        tokens = [TokenGenerator.generate().value for _ in range(10)]

        # Com 10 tokens de 6 dígitos, é muito improvável ter duplicatas
        # Mas aceitar até 1 duplicata para evitar falso negativo
        unique_count = len(set(tokens))
        assert unique_count >= 9

    def test_calculate_expiration(self):
        """Deve calcular data de expiração corretamente"""
        now = datetime.now()
        expiration = TokenGenerator.calculate_expiration(minutes=10)

        # Deve estar aproximadamente 10 minutos no futuro
        delta = expiration - now
        assert 9 <= delta.total_seconds() / 60 <= 11

    def test_calculate_expiration_custom_minutes(self):
        """Deve aceitar minutos customizados"""
        now = datetime.now()
        expiration = TokenGenerator.calculate_expiration(minutes=30)

        delta = expiration - now
        assert 29 <= delta.total_seconds() / 60 <= 31


class TestPhoneValidator:
    """Testes do PhoneValidator"""

    def test_validate_valid_ddd(self):
        """Deve validar DDD válido sem erro"""
        phone = PhoneNumber("11987654321")

        # Não deve lançar exceção
        PhoneValidator.validate_ddd(phone)

    def test_validate_invalid_ddd(self):
        """Deve rejeitar DDD inválido"""
        # DDD 00 não existe
        phone = PhoneNumber("00987654321")

        with pytest.raises(ValidationError, match="Invalid DDD"):
            PhoneValidator.validate_ddd(phone)

    def test_validate_sp_ddds(self):
        """Deve aceitar todos DDDs de São Paulo"""
        sp_ddds = ["11", "12", "13", "14", "15", "16", "17", "18", "19"]

        for ddd in sp_ddds:
            phone = PhoneNumber(f"{ddd}987654321")
            PhoneValidator.validate_ddd(phone)  # Não deve lançar exceção

    def test_is_blacklisted(self):
        """Deve identificar telefone em blacklist"""
        phone = PhoneNumber("11987654321")
        blacklist = ["11987654321", "21987654321"]

        assert PhoneValidator.is_blacklisted(phone, blacklist)

    def test_is_not_blacklisted(self):
        """Deve identificar telefone não blacklisted"""
        phone = PhoneNumber("11987654321")
        blacklist = ["21987654321"]

        assert not PhoneValidator.is_blacklisted(phone, blacklist)

    def test_normalize_for_provider(self):
        """Deve normalizar telefone para provider"""
        phone = PhoneNumber("11987654321")

        normalized = PhoneValidator.normalize_for_provider(phone)
        assert normalized == "+5511987654321"

    def test_normalize_for_provider_custom_country_code(self):
        """Deve aceitar código de país customizado"""
        phone = PhoneNumber("11987654321")

        normalized = PhoneValidator.normalize_for_provider(phone, country_code="1")
        assert normalized == "+111987654321"
