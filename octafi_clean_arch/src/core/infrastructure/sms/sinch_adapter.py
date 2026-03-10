"""Adapter Sinch — implementa SMSGateway (resolve DIP P12, ISP P10, OCP P7)."""

import httpx
import structlog

from src.core.application.ports.sms_gateway import SMSGateway, SMSResult
from src.core.domain.entities import SMSStatus
from src.core.domain.value_objects import PhoneNumber

logger = structlog.get_logger(__name__)


class SinchAdapter(SMSGateway):
    """
    Adapter para o provedor Sinch (Wavy).
    Assinatura uniforme send() resolve ISP P10 — credenciais injetadas no __init__,
    não na assinatura do método.
    """

    SEND_ENDPOINT = "https://api-messaging.wavy.global/v1/send-sms"
    STATUS_ENDPOINT = "https://api-messaging.wavy.global/v1/sms/status/list"

    def __init__(self, sms_user: str, sms_password: str) -> None:
        self._sms_user = sms_user
        self._sms_password = sms_password

    def _get_auth_headers(self) -> dict:
        return {
            "username": self._sms_user,
            "authenticationToken": self._sms_password,
            "content-type": "application/json",
        }

    def send(
        self,
        destination: PhoneNumber,
        message: str,
        correlation_id: str,
    ) -> SMSResult:
        """Envia SMS via Sinch com assinatura padronizada."""
        e164 = "55" + destination.value
        payload = {
            "correlationId": correlation_id,
            "destination": e164,
            "messageText": message,
            "flashSMS": False,
        }
        log = logger.bind(
            provider=self.provider_name,
            correlation_id=correlation_id,
            destination=destination.masked(),
        )
        try:
            response = httpx.post(
                self.SEND_ENDPOINT,
                headers=self._get_auth_headers(),
                json=payload,
                timeout=10.0,
            )
            response.raise_for_status()
            log.info("sms_sent_success", status_code=response.status_code)
            return SMSResult.success(message_id=correlation_id)
        except httpx.TimeoutException:
            log.error("sms_send_timeout")
            return SMSResult.failure(error="Sinch request timed out")
        except httpx.HTTPStatusError as exc:
            log.error("sms_send_http_error", status_code=exc.response.status_code)
            return SMSResult.failure(error=f"Sinch HTTP {exc.response.status_code}")
        except Exception as exc:
            log.error("sms_send_unexpected_error", error=str(exc))
            return SMSResult.failure(error=str(exc))

    def get_delivery_status(self, provider_message_id: str) -> SMSStatus:
        """Consulta status de uma mensagem específica via Sinch."""
        try:
            response = httpx.get(
                self.STATUS_ENDPOINT,
                headers=self._get_auth_headers(),
                timeout=10.0,
            )
            response.raise_for_status()
            for entry in response.json().get("smsStatuses", []):
                if entry.get("correlationId") == provider_message_id:
                    return _map_sinch_status(entry.get("status", "").upper())
        except Exception as exc:
            logger.error(
                "sinch_status_query_error",
                error=str(exc),
                message_id=provider_message_id,
            )
        return SMSStatus.PENDING

    def get_bulk_status_updates(self) -> list[dict]:
        """
        Retorna atualizações de status em lote.
        Usado pela Celery task UpdateSMSStatusUseCase.
        """
        try:
            response = httpx.get(
                self.STATUS_ENDPOINT,
                headers=self._get_auth_headers(),
                timeout=10.0,
            )
            response.raise_for_status()
            return [
                {
                    "correlation_id": s.get("correlationId"),
                    "status": _map_sinch_status(s.get("status", "").upper()),
                    "carrier": s.get("operatorName"),
                }
                for s in response.json().get("smsStatuses", [])
                if s.get("correlationId")
            ]
        except Exception as exc:
            logger.error("sinch_bulk_status_error", error=str(exc))
            return []

    @property
    def provider_name(self) -> str:
        return "sinch"


def _map_sinch_status(raw: str) -> SMSStatus:
    return {
        "DELIVERED": SMSStatus.DELIVERED,
        "SENT": SMSStatus.SENT,
        "FAILED": SMSStatus.FAILED,
        "EXPIRED": SMSStatus.EXPIRED,
        "UNDELIVERABLE": SMSStatus.FAILED,
    }.get(raw, SMSStatus.PENDING)
