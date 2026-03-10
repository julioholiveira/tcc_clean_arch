"""Testes das Strategies de seleção de templates"""

import pytest

from src.core.application.strategies.template_selection import (
    RaroIntegratedTemplateStrategy,
    StandardTemplateStrategy,
    create_template_strategy,
)


class TestStandardTemplateStrategy:
    """Testa strategy padrão de templates"""

    @pytest.fixture
    def strategy(self):
        """Cria strategy padrão"""
        return StandardTemplateStrategy()

    def test_get_landing_template(self, strategy):
        """Deve retornar template de landing correto"""
        template = strategy.get_landing_template("site-1")
        assert template == "core/landing_guest_site-1.html"

    def test_get_success_template(self, strategy):
        """Deve retornar template de sucesso correto"""
        template = strategy.get_success_template("site-1")
        assert template == "core/success_guest_site-1.html"

    def test_get_template_context(self, strategy):
        """Deve retornar contexto padrão"""
        user_data = {"name": "João", "phone": "11987654321"}
        context = strategy.get_template_context("site-1", user_data)

        assert context["site_id"] == "site-1"
        assert context["user"] == user_data
        assert context["show_name_field"] is True
        assert context["show_cpf_field"] is False
        assert "raro_integrated" not in context


class TestRaroIntegratedTemplateStrategy:
    """Testa strategy com integração Raro"""

    @pytest.fixture
    def strategy(self):
        """Cria strategy Raro"""
        return RaroIntegratedTemplateStrategy()

    def test_get_landing_template(self, strategy):
        """Deve retornar template Raro de landing"""
        template = strategy.get_landing_template("site-1")
        assert template == "core/raro_landing_guest_site-1.html"

    def test_get_success_template(self, strategy):
        """Deve retornar template Raro de sucesso"""
        template = strategy.get_success_template("site-1")
        assert template == "core/raro_success_guest_site-1.html"

    def test_get_template_context(self, strategy):
        """Deve retornar contexto com flag Raro"""
        user_data = {"name": "João", "phone": "11987654321"}
        context = strategy.get_template_context("site-1", user_data)

        assert context["site_id"] == "site-1"
        assert context["user"] == user_data
        assert context["show_name_field"] is False  # Raro preenche
        assert context["show_cpf_field"] is True
        assert context["raro_integrated"] is True


class TestTemplateStrategyFactory:
    """Testa factory de strategies"""

    def test_create_strategy_without_raro(self):
        """Deve criar strategy padrão"""
        strategy = create_template_strategy(has_raro_integration=False)
        assert isinstance(strategy, StandardTemplateStrategy)

    def test_create_strategy_with_raro(self):
        """Deve criar strategy Raro"""
        strategy = create_template_strategy(has_raro_integration=True)
        assert isinstance(strategy, RaroIntegratedTemplateStrategy)
