"""Strategies - Strategy Pattern para eliminar condicionais hardcoded"""

from .form_selection import (
    FormField,
    FormSelectionStrategy,
    RaroIntegratedFormStrategy,
    StandardFormStrategy,
    create_form_strategy,
)
from .template_selection import (
    RaroIntegratedTemplateStrategy,
    StandardTemplateStrategy,
    TemplateSelectionStrategy,
    create_template_strategy,
)

__all__ = [
    "TemplateSelectionStrategy",
    "StandardTemplateStrategy",
    "RaroIntegratedTemplateStrategy",
    "create_template_strategy",
    "FormSelectionStrategy",
    "FormField",
    "StandardFormStrategy",
    "RaroIntegratedFormStrategy",
    "create_form_strategy",
]
