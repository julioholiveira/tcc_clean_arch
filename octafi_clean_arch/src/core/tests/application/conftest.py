"""Fixtures compartilhadas para testes de Application Layer"""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from src.core.application.ports.customer_data_provider import CustomerDataProvider
from src.core.application.ports.network_controller import (
    NetworkAuthorizationResult,
    NetworkController,
)
from src.core.application.ports.sms_gateway import SMSGateway, SMSResult
from src.core.domain.entities import SMSStatus, SMSTokenEntity, User
from src.core.domain.value_objects import CompanyId, MACAddress, PhoneNumber, SMSToken


@pytest.fixture
def company_id():
    """Fixture de company ID"""
    return CompanyId(1)


@pytest.fixture
def phone_number():
    """Fixture de telefone"""
    return PhoneNumber("11987654321")


@pytest.fixture
def mac_address():
    """Fixture de MAC address"""
    return MACAddress("AA:BB:CC:DD:EE:FF")


@pytest.fixture
def sms_token():
    """Fixture de token SMS"""
    return SMSToken("123456")


@pytest.fixture
def sample_user(company_id, phone_number):
    """Fixture de usuário"""
    return User(id=1, company_id=company_id, phone=phone_number, name="João Silva")


@pytest.fixture
def sample_token_entity(company_id, phone_number, sms_token):
    """Fixture de token entity"""
    return SMSTokenEntity(
        id=1,
        company_id=company_id,
        phone=phone_number,
        token=sms_token,
        name="João Silva",
        expires_at=datetime.now() + timedelta(minutes=10),
    )


@pytest.fixture
def mock_user_repository():
    """Mock de UserRepository"""
    repo = Mock()
    repo.save = Mock()
    repo.find_by_phone = Mock()
    repo.find_by_id = Mock()
    repo.list_by_company = Mock()
    return repo


@pytest.fixture
def mock_token_repository():
    """Mock de SMSTokenRepository"""
    repo = Mock()
    repo.save = Mock()
    repo.find_valid_token = Mock()
    repo.delete_expired = Mock()
    return repo


@pytest.fixture
def mock_connection_repository():
    """Mock de ConnectionRepository"""
    repo = Mock()
    repo.save = Mock()
    repo.count_active_connections = Mock(return_value=0)
    return repo


@pytest.fixture
def mock_delivery_repository():
    """Mock de SMSDeliveryRepository"""
    repo = Mock()
    repo.save = Mock()
    repo.find_by_id = Mock()
    repo.list_filtered = Mock()
    repo.count_filtered = Mock()
    return repo


@pytest.fixture
def mock_sms_gateway():
    """Mock de SMSGateway"""
    gateway = Mock(spec=SMSGateway)
    gateway.send = Mock(return_value=SMSResult.success("msg-123"))
    gateway.get_delivery_status = Mock(return_value=SMSStatus.SENT)
    gateway.provider_name = "mock-provider"
    return gateway


@pytest.fixture
def mock_network_controller():
    """Mock de NetworkController"""
    controller = Mock(spec=NetworkController)
    controller.authorize_guest = Mock(
        return_value=NetworkAuthorizationResult(
            success=True, session_id="session-123", duration_minutes=60
        )
    )
    controller.revoke_access = Mock(return_value=True)
    controller.get_active_connections_count = Mock(return_value=0)
    return controller


@pytest.fixture
def mock_customer_data_provider():
    """Mock de CustomerDataProvider"""
    provider = Mock(spec=CustomerDataProvider)
    provider.get_customer_by_phone = Mock(return_value=None)
    provider.validate_customer_status = Mock(return_value=True)
    return provider
