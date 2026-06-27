"""Testes das exceções de domínio do Core"""

import pytest

from src.core.domain.exceptions import (
    BusinessRuleViolation,
    ConnectionLimitExceededError,
    DomainException,
    MaxResendExceededError,
    NetworkAccessDeniedError,
    SMSDeliveryError,
    TokenExpiredError,
    UnsupportedProviderError,
    UserNotFoundError,
    ValidationError,
)


class TestDomainExceptionHierarchy:
    """Verifica a hierarquia de herança das exceções de domínio"""

    def test_domain_exception_is_exception(self):
        assert issubclass(DomainException, Exception)

    @pytest.mark.parametrize(
        "exc_class",
        [ValidationError, BusinessRuleViolation, UserNotFoundError, SMSDeliveryError, UnsupportedProviderError],
    )
    def test_direct_subclasses_of_domain_exception(self, exc_class):
        assert issubclass(exc_class, DomainException)

    @pytest.mark.parametrize(
        "exc_class",
        [
            TokenExpiredError,
            MaxResendExceededError,
            ConnectionLimitExceededError,
            NetworkAccessDeniedError,
        ],
    )
    def test_business_rule_violation_subclasses(self, exc_class):
        assert issubclass(exc_class, BusinessRuleViolation)
        assert issubclass(exc_class, DomainException)


class TestDomainExceptionInstantiation:
    """Verifica instanciação e mensagem das exceções"""

    @pytest.mark.parametrize(
        "exc_class",
        [
            DomainException,
            ValidationError,
            BusinessRuleViolation,
            TokenExpiredError,
            MaxResendExceededError,
            ConnectionLimitExceededError,
            UserNotFoundError,
            SMSDeliveryError,
            NetworkAccessDeniedError,
            UnsupportedProviderError,
        ],
    )
    def test_instantiation_with_message(self, exc_class):
        exc = exc_class("mensagem de erro")
        assert str(exc) == "mensagem de erro"
        assert isinstance(exc, DomainException)

    @pytest.mark.parametrize(
        "exc_class",
        [
            DomainException,
            ValidationError,
            BusinessRuleViolation,
            TokenExpiredError,
            MaxResendExceededError,
            ConnectionLimitExceededError,
            UserNotFoundError,
            SMSDeliveryError,
            NetworkAccessDeniedError,
            UnsupportedProviderError,
        ],
    )
    def test_can_be_raised_and_caught(self, exc_class):
        with pytest.raises(exc_class):
            raise exc_class("erro")

    @pytest.mark.parametrize(
        "exc_class",
        [
            TokenExpiredError,
            MaxResendExceededError,
            ConnectionLimitExceededError,
            NetworkAccessDeniedError,
        ],
    )
    def test_business_rules_caught_as_base(self, exc_class):
        with pytest.raises(BusinessRuleViolation):
            raise exc_class("erro de regra de negócio")

    @pytest.mark.parametrize(
        "exc_class",
        [
            ValidationError,
            BusinessRuleViolation,
            TokenExpiredError,
            UserNotFoundError,
            SMSDeliveryError,
            UnsupportedProviderError,
        ],
    )
    def test_all_caught_as_domain_exception(self, exc_class):
        with pytest.raises(DomainException):
            raise exc_class("erro")
