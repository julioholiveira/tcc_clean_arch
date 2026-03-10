"""Testes dos Value Objects do Core Domain"""

import pytest

from src.core.domain.value_objects import (
    CPF,
    CompanyId,
    MACAddress,
    PhoneNumber,
    SMSToken,
)


class TestPhoneNumber:
    """Testes do value object PhoneNumber"""

    def test_create_valid_phone(self):
        """Deve criar telefone válido"""
        phone = PhoneNumber("11987654321")
        assert phone.value == "11987654321"
        assert phone.ddd == "11"

    def test_formatted_phone(self):
        """Deve formatar telefone corretamente"""
        phone = PhoneNumber("11987654321")
        assert phone.formatted == "(11) 98765-4321"

    def test_phone_with_non_numeric_chars(self):
        """Deve remover caracteres não numéricos"""
        phone = PhoneNumber("(11) 98765-4321")
        assert phone.value == "11987654321"

    def test_invalid_phone_length(self):
        """Deve rejeitar telefone com tamanho inválido"""
        with pytest.raises(ValueError, match="must have 11 digits"):
            PhoneNumber("119876543")

    def test_legacy_phone_without_9(self):
        """Deve aceitar telefone legado que não começa com 9 (validação de celular é da API)"""
        phone = PhoneNumber("11887654321")
        assert phone.value == "11887654321"

    def test_phone_immutability(self):
        """Value object deve ser imutável"""
        phone = PhoneNumber("11987654321")
        with pytest.raises(AttributeError):
            phone.value = "21987654321"


class TestCPF:
    """Testes do value object CPF"""

    def test_create_valid_cpf(self):
        """Deve criar CPF válido"""
        cpf = CPF("12345678909")
        assert cpf.value == "12345678909"

    def test_formatted_cpf(self):
        """Deve formatar CPF corretamente"""
        cpf = CPF("12345678909")
        assert cpf.formatted == "123.456.789-09"

    def test_masked_cpf(self):
        """Deve mascarar CPF para logs"""
        cpf = CPF("12345678909")
        assert cpf.masked == "***.***.789-**"

    def test_cpf_with_formatting(self):
        """Deve remover formatação do CPF"""
        cpf = CPF("123.456.789-09")
        assert cpf.value == "12345678909"

    def test_invalid_cpf_length(self):
        """Deve rejeitar CPF com tamanho inválido"""
        with pytest.raises(ValueError, match="must have 11 digits"):
            CPF("123456789")

    def test_invalid_cpf_digits(self):
        """Deve rejeitar CPF com dígitos verificadores inválidos"""
        with pytest.raises(ValueError, match="Invalid CPF"):
            CPF("12345678900")

    def test_cpf_all_same_digits(self):
        """Deve rejeitar CPF com todos dígitos iguais"""
        with pytest.raises(ValueError, match="Invalid CPF"):
            CPF("11111111111")


class TestCompanyId:
    """Testes do value object CompanyId"""

    def test_create_valid_company_id(self):
        """Deve criar company ID válido"""
        company_id = CompanyId(1)
        assert company_id.value == 1

    def test_invalid_company_id_zero(self):
        """Deve rejeitar company ID zero"""
        with pytest.raises(ValueError, match="must be positive"):
            CompanyId(0)

    def test_invalid_company_id_negative(self):
        """Deve rejeitar company ID negativo"""
        with pytest.raises(ValueError, match="must be positive"):
            CompanyId(-1)


class TestMACAddress:
    """Testes do value object MACAddress"""

    def test_create_valid_mac(self):
        """Deve criar MAC address válido"""
        mac = MACAddress("AA:BB:CC:DD:EE:FF")
        assert mac.value == "AABBCCDDEEFF"

    def test_formatted_mac(self):
        """Deve formatar MAC address corretamente"""
        mac = MACAddress("AABBCCDDEEFF")
        assert mac.formatted == "AA:BB:CC:DD:EE:FF"

    def test_mac_with_hyphens(self):
        """Deve aceitar MAC com hífens"""
        mac = MACAddress("AA-BB-CC-DD-EE-FF")
        assert mac.value == "AABBCCDDEEFF"

    def test_mac_lowercase(self):
        """Deve normalizar para uppercase"""
        mac = MACAddress("aa:bb:cc:dd:ee:ff")
        assert mac.value == "AABBCCDDEEFF"

    def test_invalid_mac_format(self):
        """Deve rejeitar MAC address inválido"""
        with pytest.raises(ValueError, match="Invalid MAC address"):
            MACAddress("ZZZZZZZZZZZ")


class TestSMSToken:
    """Testes do value object SMSToken"""

    def test_create_valid_token(self):
        """Deve criar token válido"""
        token = SMSToken("123456")
        assert token.value == "123456"
        assert str(token) == "123456"

    def test_invalid_token_length(self):
        """Deve rejeitar token com tamanho inválido"""
        with pytest.raises(ValueError, match="must have exactly 6 digits"):
            SMSToken("12345")

    def test_invalid_token_non_numeric(self):
        """Deve rejeitar token não numérico"""
        with pytest.raises(ValueError, match="must contain only digits"):
            SMSToken("12345a")
