"""Strategy Pattern para seleção de templates - resolve P8 (OCP)"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class TemplateSelectionStrategy(ABC):
    """
    Strategy base para seleção de templates.
    Elimina `if integracao_raro` hardcoded.
    """

    @abstractmethod
    def get_landing_template(self, site_id: str) -> str:
        """Retorna path do template de landing page"""
        pass

    @abstractmethod
    def get_success_template(self, site_id: str) -> str:
        """Retorna path do template de sucesso"""
        pass

    @abstractmethod
    def get_template_context(
        self, site_id: str, user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Retorna contexto para renderização do template"""
        pass


class StandardTemplateStrategy(TemplateSelectionStrategy):
    """Strategy padrão - sem integração Raro"""

    def get_landing_template(self, site_id: str) -> str:
        return f"core/landing_guest_{site_id}.html"

    def get_success_template(self, site_id: str) -> str:
        return f"core/success_guest_{site_id}.html"

    def get_template_context(
        self, site_id: str, user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "site_id": site_id,
            "user": user_data,
            "show_name_field": True,
            "show_cpf_field": False,
        }


class RaroIntegratedTemplateStrategy(TemplateSelectionStrategy):
    """Strategy com integração Raro - templates diferentes"""

    def get_landing_template(self, site_id: str) -> str:
        return f"core/raro_landing_guest_{site_id}.html"

    def get_success_template(self, site_id: str) -> str:
        return f"core/raro_success_guest_{site_id}.html"

    def get_template_context(
        self, site_id: str, user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "site_id": site_id,
            "user": user_data,
            "show_name_field": False,  # Raro preenche automaticamente
            "show_cpf_field": True,
            "raro_integrated": True,
        }


def create_template_strategy(has_raro_integration: bool) -> TemplateSelectionStrategy:
    """
    Factory Method para criar strategy de template.
    Configuração vem do banco de dados, não de flags hardcoded.
    """
    if has_raro_integration:
        return RaroIntegratedTemplateStrategy()
    return StandardTemplateStrategy()
