"""Fixtures compartilhadas para testes de Application Layer de Mailing"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from src.core.domain.value_objects import CompanyId, PhoneNumber
from src.mailing.application.ports.bulk_sms_processor import (
    BulkSMSProcessor,
    BulkSMSProgress,
)
from src.mailing.domain.entities import (
    Campaign,
    CampaignStatus,
    MailTemplate,
    Recipient,
)


@pytest.fixture
def company_id():
    return CompanyId(1)


@pytest.fixture
def sample_template(company_id):
    return MailTemplate(
        id=1,
        company_id=company_id,
        name="Template Teste",
        content="Ola {name}, sua mensagem: {message}",
    )


@pytest.fixture
def sample_recipients():
    return [
        Recipient(phone=PhoneNumber("11987654321"), name="Joao Silva", custom_data={"message": "Teste 1"}),
        Recipient(phone=PhoneNumber("11987654322"), name="Maria Silva", custom_data={"message": "Teste 2"}),
        Recipient(phone=PhoneNumber("11987654323"), name="Pedro Silva", custom_data={"message": "Teste 3"}),
    ]


@pytest.fixture
def sample_campaign(company_id, sample_template):
    return Campaign(
        id=1,
        company_id=company_id,
        name="Campanha Teste",
        template=sample_template,
        status=CampaignStatus.DRAFT,
    )


@pytest.fixture
def mock_campaign_repository():
    repo = Mock()
    repo.save = Mock()
    repo.find_by_id = Mock()
    repo.list_by_company = Mock()
    repo.count_by_company = Mock()
    return repo


@pytest.fixture
def mock_message_repository():
    repo = Mock()
    repo.save = Mock()
    repo.save_batch = Mock()
    repo.find_by_id = Mock()
    repo.list_by_campaign = Mock()
    repo.count_by_campaign = Mock()
    return repo


@pytest.fixture
def mock_template_repository():
    repo = Mock()
    repo.save = Mock()
    repo.find_by_id = Mock()
    repo.list_by_company = Mock()
    return repo


@pytest.fixture
def mock_recipient_repository():
    repo = Mock()
    repo.save = Mock()
    repo.list_filtered = Mock()
    repo.count_filtered = Mock()
    return repo


@pytest.fixture
def mock_bulk_sms_processor():
    processor = Mock(spec=BulkSMSProcessor)

    def process_bulk_send_side(messages, batch_size=100, delay_between_batches_seconds=1, progress_callback=None):
        n = len(messages)
        return BulkSMSProgress(
            total=n, sent=n, failed=0, current_batch=1, started_at=datetime.now()
        )

    processor.process_bulk_send.side_effect = process_bulk_send_side
    return processor
