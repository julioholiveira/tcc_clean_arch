"""Port para processamento de SMS em lote"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, List, Optional

from src.mailing.domain.entities import MailMessage


@dataclass
class BulkSMSProgress:
    """Progresso do processamento em lote"""

    total: int
    sent: int
    failed: int
    current_batch: int
    started_at: datetime
    estimated_completion: Optional[datetime] = None


class BulkSMSProcessor(ABC):
    """
    Port para processamento de SMS em lote.
    Permite diferentes estratégias (síncrono, assíncrono, batch, etc).
    """

    @abstractmethod
    def process_bulk_send(
        self,
        messages: List[MailMessage],
        batch_size: int = 100,
        delay_between_batches_seconds: int = 1,
        progress_callback: Optional[Callable[[BulkSMSProgress], None]] = None,
    ) -> BulkSMSProgress:
        """
        Processa envio em lote de mensagens.

        Args:
            messages: Lista de mensagens a enviar
            batch_size: Tamanho do batch
            delay_between_batches_seconds: Delay entre batches (rate limiting)
            progress_callback: Callback para atualização de progresso

        Returns:
            BulkSMSProgress final
        """
        pass

    @abstractmethod
    def cancel_bulk_send(self, campaign_id: int) -> bool:
        """Cancela envio em andamento"""
        pass

    @abstractmethod
    def get_progress(self, campaign_id: int) -> Optional[BulkSMSProgress]:
        """Consulta progresso de envio em andamento"""
        pass
