"""Ports (interfaces) para adapters externos"""

from .customer_data_provider import CustomerData, CustomerDataProvider
from .network_controller import NetworkAuthorizationResult, NetworkController
from .sms_gateway import SMSGateway, SMSResult

__all__ = [
    "SMSGateway",
    "SMSResult",
    "NetworkController",
    "NetworkAuthorizationResult",
    "CustomerDataProvider",
    "CustomerData",
]
