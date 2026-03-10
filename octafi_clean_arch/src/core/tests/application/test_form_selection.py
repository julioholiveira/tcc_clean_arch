"""Testes das Strategies de seleção de formulários"""

import pytest

from src.core.application.strategies.form_selection import (
    FormField,
    RaroIntegratedFormStrategy,
    StandardFormStrategy,
    create_form_strategy,
)


class TestFormField:
    """Testa FormField"""

    def test_create_field(self):
        """Deve criar campo com valores padrão"""
        field = FormField("phone", "tel", required=True, label="Telefone")

        assert field.name == "phone"
        assert field.field_type == "tel"
        assert field.required is True
        assert field.label == "Telefone"

    def test_create_field_auto_label(self):
        """Deve gerar label automaticamente"""
        field = FormField("email", "email")
        assert field.label == "Email"


class TestStandardFormStrategy:
    """Testa strategy padrão de formulários"""

    @pytest.fixture
    def strategy(self):
        """Cria strategy padrão"""
        return StandardFormStrategy()

    def test_get_required_fields(self, strategy):
        """Deve retornar apenas telefone como obrigatório"""
        fields = strategy.get_required_fields()

        assert len(fields) == 1
        assert fields[0].name == "phone"
        assert fields[0].required is True

    def test_get_optional_fields(self, strategy):
        """Deve retornar nome e email como opcionais"""
        fields = strategy.get_optional_fields()

        assert len(fields) == 2
        field_names = [f.name for f in fields]
        assert "name" in field_names
        assert "email" in field_names

    def test_validate_submission_valid(self, strategy):
        """Deve validar submissão com telefone"""
        data = {"phone": "11987654321"}
        is_valid, errors = strategy.validate_submission(data)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_submission_missing_phone(self, strategy):
        """Deve rejeitar sem telefone"""
        data = {"name": "João"}
        is_valid, errors = strategy.validate_submission(data)

        assert is_valid is False
        assert len(errors) > 0
        assert any("telefone" in e.lower() for e in errors)


class TestRaroIntegratedFormStrategy:
    """Testa strategy com integração Raro"""

    @pytest.fixture
    def strategy(self):
        """Cria strategy Raro"""
        return RaroIntegratedFormStrategy()

    def test_get_required_fields(self, strategy):
        """Deve exigir telefone e CPF"""
        fields = strategy.get_required_fields()

        assert len(fields) == 2
        field_names = [f.name for f in fields]
        assert "phone" in field_names
        assert "cpf" in field_names

    def test_validate_submission_valid(self, strategy):
        """Deve validar submissão com telefone e CPF"""
        data = {"phone": "11987654321", "cpf": "12345678909"}
        is_valid, errors = strategy.validate_submission(data)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_submission_missing_cpf(self, strategy):
        """Deve rejeitar sem CPF"""
        data = {"phone": "11987654321"}
        is_valid, errors = strategy.validate_submission(data)

        assert is_valid is False
        assert any("cpf" in e.lower() for e in errors)


class TestFormStrategyFactory:
    """Testa factory de strategies"""

    def test_create_strategy_without_raro(self):
        """Deve criar strategy padrão"""
        strategy = create_form_strategy(has_raro_integration=False)
        assert isinstance(strategy, StandardFormStrategy)

    def test_create_strategy_with_raro(self):
        """Deve criar strategy Raro"""
        strategy = create_form_strategy(has_raro_integration=True)
        assert isinstance(strategy, RaroIntegratedFormStrategy)
