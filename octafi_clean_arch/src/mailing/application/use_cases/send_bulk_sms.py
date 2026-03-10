import logging
from datetime import datetime

from src.mailing.application.dto.campaign import (
    SendBulkSMSRequest,
    SendBulkSMSResponse,
)
from src.mailing.application.ports.bulk_sms_processor import BulkSMSProcessor
from src.mailing.domain.entities import CampaignStatus
from src.mailing.domain.exceptions import CampaignStateError

logger = logging.getLogger(__name__)


class SendBulkSMSUseCase:
    """Orquestra o envio em massa de SMS para uma campanha."""

    def __init__(self, campaign_repository, message_repository, bulk_processor: BulkSMSProcessor):
        self.campaign_repository = campaign_repository
        self.message_repository = message_repository
        self.bulk_processor = bulk_processor

    def execute(self, request: SendBulkSMSRequest) -> SendBulkSMSResponse:
        """Executa envio de campanha SMS."""
        started_at = datetime.now()

        try:
            campaign = self.campaign_repository.find_by_id(request.campaign_id)

            if not campaign:
                return SendBulkSMSResponse(
                    success=False,
                    campaign_id=request.campaign_id,
                    total_recipients=0,
                    sent_count=0,
                    failed_count=0,
                    started_at=started_at,
                    error_message="Campanha nao encontrada",
                )

            if not campaign.can_start():
                raise CampaignStateError(
                    f"Campanha nao pode ser iniciada. Status: {campaign.status.value}"
                )

            campaign.start()
            self.campaign_repository.save(campaign)

            messages = self.message_repository.list_by_campaign(request.campaign_id)

            if not messages:
                campaign.status = CampaignStatus.COMPLETED
                self.campaign_repository.save(campaign)
                return SendBulkSMSResponse(
                    success=True,
                    campaign_id=request.campaign_id,
                    total_recipients=0,
                    sent_count=0,
                    failed_count=0,
                    started_at=started_at,
                    completed_at=datetime.now(),
                )

            progress = self.bulk_processor.process_bulk_send(
                messages=messages,
                batch_size=request.batch_size,
                delay_between_batches_seconds=request.delay_between_batches_seconds,
            )

            campaign.sent_count = progress.sent
            campaign.failed_count = progress.failed
            campaign.total_recipients = progress.total
            campaign.complete()
            self.campaign_repository.save(campaign)

            completed_at = datetime.now()

            logger.info(
                f"Campanha {request.campaign_id} concluida",
                extra={
                    "correlation_id": request.correlation_id,
                    "total": progress.total,
                    "sent": progress.sent,
                    "failed": progress.failed,
                    "duration_seconds": (completed_at - started_at).total_seconds(),
                },
            )

            return SendBulkSMSResponse(
                success=True,
                campaign_id=request.campaign_id,
                total_recipients=progress.total,
                sent_count=progress.sent,
                failed_count=progress.failed,
                started_at=started_at,
                completed_at=completed_at,
            )

        except CampaignStateError as e:
            logger.warning(f"Erro de estado da campanha: {str(e)}")
            return SendBulkSMSResponse(
                success=False,
                campaign_id=request.campaign_id,
                total_recipients=0,
                sent_count=0,
                failed_count=0,
                started_at=started_at,
                error_message=str(e),
            )

        except Exception as e:
            logger.error(f"Erro ao processar campanha: {str(e)}", exc_info=True)
            try:
                campaign.status = CampaignStatus.FAILED
                self.campaign_repository.save(campaign)
            except Exception:
                pass
            return SendBulkSMSResponse(
                success=False,
                campaign_id=request.campaign_id,
                total_recipients=0,
                sent_count=0,
                failed_count=0,
                started_at=started_at,
                error_message="Erro interno ao processar campanha",
            )
