"""Testes do port BulkSMSProcessor e da dataclass BulkSMSProgress"""

from datetime import datetime, timedelta
from typing import Callable, List, Optional

from src.mailing.application.ports.bulk_sms_processor import (
    BulkSMSProcessor,
    BulkSMSProgress,
)
from src.mailing.domain.entities import MailMessage


class FakeBulkSMSProcessor(BulkSMSProcessor):
    """Implementação concreta de BulkSMSProcessor para exercitar o contrato"""

    def __init__(self):
        self._progress: dict[int, BulkSMSProgress] = {}
        self._cancelled: set[int] = set()

    def process_bulk_send(
        self,
        messages: List[MailMessage],
        batch_size: int = 100,
        delay_between_batches_seconds: int = 1,
        progress_callback: Optional[Callable[[BulkSMSProgress], None]] = None,
    ) -> BulkSMSProgress:
        n = len(messages)
        progress = BulkSMSProgress(total=n, sent=n, failed=0, current_batch=1, started_at=datetime.now())
        if progress_callback:
            progress_callback(progress)
        return progress

    def cancel_bulk_send(self, campaign_id: int) -> bool:
        if campaign_id in self._progress:
            self._cancelled.add(campaign_id)
            return True
        return False

    def get_progress(self, campaign_id: int) -> Optional[BulkSMSProgress]:
        return self._progress.get(campaign_id)


class TestBulkSMSProgress:
    def test_minimal_instantiation_defaults(self):
        now = datetime.now()
        progress = BulkSMSProgress(total=10, sent=4, failed=1, current_batch=2, started_at=now)

        assert progress.total == 10
        assert progress.sent == 4
        assert progress.failed == 1
        assert progress.current_batch == 2
        assert progress.started_at == now
        assert progress.estimated_completion is None

    def test_with_estimated_completion(self):
        now = datetime.now()
        eta = now + timedelta(minutes=5)
        progress = BulkSMSProgress(
            total=10,
            sent=4,
            failed=1,
            current_batch=2,
            started_at=now,
            estimated_completion=eta,
        )

        assert progress.estimated_completion == eta


class TestBulkSMSProcessorContract:
    def test_process_bulk_send_returns_progress(self):
        processor = FakeBulkSMSProcessor()

        progress = processor.process_bulk_send(messages=[], batch_size=50)

        assert isinstance(progress, BulkSMSProgress)
        assert progress.total == 0

    def test_process_bulk_send_invokes_callback(self):
        processor = FakeBulkSMSProcessor()
        received = []

        processor.process_bulk_send(messages=[], progress_callback=lambda p: received.append(p))

        assert len(received) == 1
        assert isinstance(received[0], BulkSMSProgress)

    def test_get_progress_returns_none_when_unknown(self):
        processor = FakeBulkSMSProcessor()

        assert processor.get_progress(999) is None

    def test_get_progress_returns_stored_progress(self):
        processor = FakeBulkSMSProcessor()
        progress = BulkSMSProgress(total=5, sent=5, failed=0, current_batch=1, started_at=datetime.now())
        processor._progress[1] = progress

        assert processor.get_progress(1) is progress

    def test_cancel_bulk_send_unknown_campaign(self):
        processor = FakeBulkSMSProcessor()

        assert processor.cancel_bulk_send(123) is False

    def test_cancel_bulk_send_existing_campaign(self):
        processor = FakeBulkSMSProcessor()
        processor._progress[1] = BulkSMSProgress(total=5, sent=0, failed=0, current_batch=1, started_at=datetime.now())

        assert processor.cancel_bulk_send(1) is True
