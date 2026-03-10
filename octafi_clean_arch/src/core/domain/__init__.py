"""Domain layer - regras de negócio puras, sem dependências de framework"""

from .entities import (
    User,
    SMSTokenEntity,
    Connection,
    SMSDelivery,
    Historico,
    SMSProvider,
    SMSStatus,
)
from .value_objects import (
    CompanyId,
    PhoneNumber,
    CPF,
    MACAddress,
    SMSToken,
)
from .exceptions import (
    DomainException,
    ValidationError,
    BusinessRuleViolation,
    TokenExpiredError,
    MaxResendExceededError,
    ConnectionLimitExceededError,
    UserNotFoundError,
    SMSDeliveryError,
    NetworkAccessDeniedError,
)
from .repositories import (
    UserRepository,
    SMSTokenRepository,
    ConnectionRepository,
    SMSDeliveryRepository,
    HistoricoRepository,
)
from .services import TokenGenerator, PhoneValidator

__all__ = [
    # Entities
    'User',
    'SMSTokenEntity',
    'Connection',
    'SMSDelivery',
    'Historico',
    'SMSProvider',
    'SMSStatus',
    # Value Objects
    'CompanyId',
    'PhoneNumber',
    'CPF',
    'MACAddress',
    'SMSToken',
    # Exceptions
    'DomainException',
    'ValidationError',
    'BusinessRuleViolation',
    'TokenExpiredError',
    'MaxResendExceededError',
    'ConnectionLimitExceededError',
    'UserNotFoundError',
    'SMSDeliveryError',
    'NetworkAccessDeniedError',
    # Repositories
    'UserRepository',
    'SMSTokenRepository',
    'ConnectionRepository',
    'SMSDeliveryRepository',
    'HistoricoRepository',
    # Services
    'TokenGenerator',
    'PhoneValidator',
]
