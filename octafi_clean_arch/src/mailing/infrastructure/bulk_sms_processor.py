"""
Implementação de BulkSMSProcessor usando SMSProviderFactory.
Resolve P7 (OCP) e P9 (nenhum provider hardcoded).
"""

import logging
import time
from datetime import datetime
from typing import Callable, List, Optional

from src.core.infrastructure.sms.factory import SMSProviderFactory
from src.mailing.application.ports.bulk_sms_processor import BulkSMSProcessor, BulkSMSProgress
from src.mailing.domain.entities import MailMessage

logger = logging.getLogger(__name__)


class DjangoBulkSMSProcessor(BulkSMSProcessor):
    """
    Processa envio em lote de SMS utilizando SMSProviderFactory.
    Resolve P9 (OCP): provider é injetado via empresa, sem Sinch hardcoded.
    """

    def __init__(self, empresa):
        self.empresa = empresa
        self._gateway = SMSProviderFactory.create(empresa)

    def process_bulk_send(
        self,
        messages: List[MailMessage],
        batch_size: int = 100,
        delay_between_batches_seconds: int = 1,
        progress_callback: Optional[Callable[[BulkSMSProgress], None]] = None,
    ) -> BulkSMSProgress:
        """Envia mensagens em lotes, em ordem."""

        total = len(messages)
        sent = 0
        failed = 0
        started_at = datetime.now()

        for batch_idx in range(0, total, batch_size):
            batch = messages[batch_idx : batch_idx + batch_size]

            for msg in batch:
                try:
                    phone = msg.recipient.phone
                    result = self._gateway.send(
                        destination=phone,
                        message=msg.content,
                        correlation_id=str(msg.id or ""),
                    )
                    if result.success:
                        msg.mark_as_sent(result.provider_message_id or "")
                        sent += 1
                    else:
                        msg.mark_as_failed(result.error_message or "Provider error")
                        failed += 1
                except Exception as exc:
                    logger.error("Erro ao enviar SMS msg=%s: %s", msg.id, exc)
                    msg.mark_as_failed(str(exc))
                    failed += 1

            progress = BulkSMSProgress(
                total=total,
                sent=sent,
                failed=failed,
                current_batch=batch_idx // batch_size + 1,
                started_at=started_at,
            )

            if progress_callback:
                progress_callback(progress)

            if delay_between_batches_seconds > 0 and batch_idx + batch_size < total:
                time.sleep(delay_between_batches_seconds)

        return BulkSMSProgress(
            total=total,
            sent=sent,
            failed=failed,
            current_batch=(total + batch_size - 1) // batch_size,
            started_at=started_at,
            estimated_completion=datetime.now(),
        )

    def cancel_bulk_send(self, campaign_id: int) -> bool:
        """Cancelamento síncrono não é suportado — envio já ocorreu no processo."""
        return False

    def get_progress(self, campaign_id: int) -> None:
        """Progresso em tempo real não disponível no processador síncrono."""
        return None
