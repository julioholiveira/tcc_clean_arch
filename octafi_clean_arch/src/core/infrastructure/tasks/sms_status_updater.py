"""
Celery tasks refatoradas — delegam para use cases puros.
Resolve P9: sem hardcode para Sinch; provider resolvido via SMSProviderFactory.
Substitui diretamente core/tasks.py do legado em octafi_clean_arch/.
"""

import structlog
from celery import shared_task

from src.core.application.use_cases.update_sms_status import UpdateSMSStatusUseCase
from src.core.domain.exceptions import UnsupportedProviderError
from src.core.infrastructure.repositories.sms_delivery_repository import (
    DjangoSMSDeliveryRepository,
)
from src.core.infrastructure.sms.factory import SMSProviderFactory

logger = structlog.get_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def update_sms_status_task(self) -> None:  # type: ignore[misc]
    """
    Atualiza status dos SMS enviados para todas as empresas ativas.
    Substitui atualiza_sms_status de core/tasks.py do legado.

    Diferenças em relação ao legado:
    - Não hardcoded para Sinch (resolve P9/OCP)
    - Delega para UpdateSMSStatusUseCase (resolve DIP)
    - Retry automático via Celery em caso de falha
    - Logs estruturados com structlog
    """
    from empresas.models import Empresa

    delivery_repo = DjangoSMSDeliveryRepository()
    empresas = Empresa.objects.filter(envia_sms=True).select_related("operadora_sms")

    for empresa in empresas:
        log = logger.bind(empresa_id=empresa.pk)
        try:
            gateway = SMSProviderFactory.create(empresa)
            use_case = UpdateSMSStatusUseCase(
                sms_gateway=gateway,
                delivery_repository=delivery_repo,
            )
            updated_count = use_case.execute(empresa_id=empresa.pk)
            log.info("sms_status_updated", count=updated_count)
        except UnsupportedProviderError as exc:
            log.warning("sms_provider_not_supported", error=str(exc))
        except Exception as exc:
            log.error("sms_status_update_failed", error=str(exc))
            try:
                raise self.retry(exc=exc)
            except self.MaxRetriesExceededError:
                log.error("sms_status_max_retries_exceeded", empresa_id=empresa.pk)


@shared_task
def cleanup_expired_tokens_task() -> None:
    """
    Remove tokens com reenvios >= 3.
    Substitui limpa_tokens_reenviados de core/tasks.py do legado.
    """
    from datetime import datetime

    from src.core.infrastructure.repositories.sms_token_repository import (
        DjangoSMSTokenRepository,
    )

    deleted = DjangoSMSTokenRepository().delete_expired(before=datetime.now())
    logger.info("expired_tokens_cleaned", count=deleted)
