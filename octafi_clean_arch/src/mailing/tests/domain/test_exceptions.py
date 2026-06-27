"""Testes das exceções de domínio do Mailing"""

import pytest

from src.mailing.domain.exceptions import (
    BulkSendError,
    CampaignStateError,
    MailingDomainException,
    RecipientValidationError,
    TemplateNotFoundError,
    TemplateRenderError,
)

ALL_EXCEPTIONS = [
    MailingDomainException,
    TemplateNotFoundError,
    TemplateRenderError,
    CampaignStateError,
    RecipientValidationError,
    BulkSendError,
]

SUBCLASSES = [
    TemplateNotFoundError,
    TemplateRenderError,
    CampaignStateError,
    RecipientValidationError,
    BulkSendError,
]


class TestMailingExceptionHierarchy:
    """Verifica a hierarquia de herança das exceções de mailing"""

    def test_base_is_exception(self):
        assert issubclass(MailingDomainException, Exception)

    @pytest.mark.parametrize("exc_class", SUBCLASSES)
    def test_subclasses_of_base(self, exc_class):
        assert issubclass(exc_class, MailingDomainException)


class TestMailingExceptionInstantiation:
    """Verifica instanciação, mensagem e captura das exceções"""

    @pytest.mark.parametrize("exc_class", ALL_EXCEPTIONS)
    def test_instantiation_with_message(self, exc_class):
        exc = exc_class("mensagem de erro")
        assert str(exc) == "mensagem de erro"
        assert isinstance(exc, MailingDomainException)

    @pytest.mark.parametrize("exc_class", ALL_EXCEPTIONS)
    def test_can_be_raised_and_caught(self, exc_class):
        with pytest.raises(exc_class):
            raise exc_class("erro")

    @pytest.mark.parametrize("exc_class", SUBCLASSES)
    def test_caught_as_base(self, exc_class):
        with pytest.raises(MailingDomainException):
            raise exc_class("erro")
