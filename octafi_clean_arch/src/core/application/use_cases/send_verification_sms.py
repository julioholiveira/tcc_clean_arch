"""Use Case: Envio de SMS de Verificação (genérico)"""

import logging

from src.core.application.dto.sms import SendSMSRequest, SendSMSResponse
from src.core.application.ports.sms_gateway import SMSGateway
from src.core.domain.entities import SMSDelivery
from src.core.domain.repositories import SMSDeliveryRepository

logger = logging.getLogger(__name__)


class SendVerificationSMSUseCase:
    """Envia SMS genérico (verificação, notificação, etc)"""

    def __init__(
        self, sms_gateway: SMSGateway, delivery_repository: SMSDeliveryRepository
    ):
        self.sms_gateway = sms_gateway
        self.delivery_repository = delivery_repository

    def execute(self, request: SendSMSRequest) -> SendSMSResponse:
        """
        Envia SMS e registra entrega.

        Fluxo:
        1. Envia SMS via gateway
        2. Persiste registro de entrega
        3. Retorna resultado
        """

        try:
            # Envia SMS
            result = self.sms_gateway.send(
                destination=request.phone,
                message=request.message,
                correlation_id=request.correlation_id or "send-sms",
            )

            # Persiste entrega
            delivery = SMSDelivery(
                company_id=request.company_id,
                phone=request.phone,
                message=request.message,
                provider=self.sms_gateway.provider_name,
                status=result.status,
                provider_message_id=result.provider_message_id,
                sent_at=result.sent_at,
                error_message=result.error_message,
            )
            self.delivery_repository.save(delivery)

            logger.info(
                f"SMS enviado via {self.sms_gateway.provider_name}",
                extra={
                    "correlation_id": request.correlation_id,
                    "delivery_id": delivery.id,
                },
            )

            return SendSMSResponse(
                success=result.status.value in ["sent", "pending"],
                provider_message_id=result.provider_message_id,
                provider_name=self.sms_gateway.provider_name,
                sent_at=result.sent_at,
                error_message=result.error_message,
            )

        except Exception as e:
            logger.error(
                f"Erro ao enviar SMS: {str(e)}",
                exc_info=True,
                extra={"correlation_id": request.correlation_id},
            )
            return SendSMSResponse(
                success=False,
                provider_name=self.sms_gateway.provider_name,
                error_message=str(e),
            )
