"""Strategy Pattern para seleção de formulários - resolve P8 (OCP)"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class FormField:
    """Representação de campo de formulário"""

    def __init__(
        self,
        name: str,
        field_type: str,
        required: bool = True,
        label: str = "",
        validation: str = "",
    ):
        self.name = name
        self.field_type = field_type
        self.required = required
        self.label = label or name.capitalize()
        self.validation = validation


class FormSelectionStrategy(ABC):
    """
    Strategy base para seleção de campos de formulário.
    Elimina `if integracao_raro` em validação de campos.
    """

    @abstractmethod
    def get_required_fields(self) -> List[FormField]:
        """Retorna campos obrigatórios do formulário"""
        pass

    @abstractmethod
    def get_optional_fields(self) -> List[FormField]:
        """Retorna campos opcionais"""
        pass

    @abstractmethod
    def validate_submission(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Valida submissão do formulário.

        Returns:
            (is_valid, error_messages)
        """
        pass


class StandardFormStrategy(FormSelectionStrategy):
    """Strategy padrão - campos básicos"""

    def get_required_fields(self) -> List[FormField]:
        return [
            FormField(
                "phone",
                "tel",
                required=True,
                label="Telefone",
                validation="^[0-9]{11}$",
            ),
        ]

    def get_optional_fields(self) -> List[FormField]:
        return [
            FormField("name", "text", required=False, label="Nome"),
            FormField("email", "email", required=False, label="Email"),
        ]

    def validate_submission(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        errors = []

        if not data.get("phone"):
            errors.append("Telefone é obrigatório")

        return (len(errors) == 0, errors)


class RaroIntegratedFormStrategy(FormSelectionStrategy):
    """Strategy com integração Raro - CPF obrigatório"""

    def get_required_fields(self) -> List[FormField]:
        return [
            FormField(
                "phone",
                "tel",
                required=True,
                label="Telefone",
                validation="^[0-9]{11}$",
            ),
            FormField(
                "cpf", "text", required=True, label="CPF", validation="^[0-9]{11}$"
            ),
        ]

    def get_optional_fields(self) -> List[FormField]:
        return [
            FormField("email", "email", required=False, label="Email"),
        ]

    def validate_submission(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        errors = []

        if not data.get("phone"):
            errors.append("Telefone é obrigatório")

        if not data.get("cpf"):
            errors.append("CPF é obrigatório para validação com Raro")

        return (len(errors) == 0, errors)


def create_form_strategy(has_raro_integration: bool) -> FormSelectionStrategy:
    """Factory para criar strategy de formulário"""
    if has_raro_integration:
        return RaroIntegratedFormStrategy()
    return StandardFormStrategy()
