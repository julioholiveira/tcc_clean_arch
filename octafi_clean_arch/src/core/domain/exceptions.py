"""Exceções de domínio do Core - violações de regras de negócio"""


class DomainException(Exception):
    """Base para exceções de domínio"""

    pass


class ValidationError(DomainException):
    """Erro de validação de entidade ou value object"""

    pass


class BusinessRuleViolation(DomainException):
    """Violação de regra de negócio"""

    pass


class TokenExpiredError(BusinessRuleViolation):
    """Token SMS expirado"""

    pass


class MaxResendExceededError(BusinessRuleViolation):
    """Limite de reenvios de token excedido"""

    pass


class ConnectionLimitExceededError(BusinessRuleViolation):
    """Limite de conexões simultâneas excedido"""

    pass


class UserNotFoundError(DomainException):
    """Usuário não encontrado"""

    pass


class SMSDeliveryError(DomainException):
    """Erro no envio de SMS"""

    pass


class NetworkAccessDeniedError(BusinessRuleViolation):
    """Acesso à rede negado"""

    pass


class UnsupportedProviderError(DomainException):
    """Raised when an SMS provider slug is not registered in SMSProviderFactory."""

    pass
