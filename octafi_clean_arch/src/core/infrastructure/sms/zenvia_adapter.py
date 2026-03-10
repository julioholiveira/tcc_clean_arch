"""Adapter Zenvia — implementa SMSGateway com assinatura uniforme."""

import httpx
import structlog

from src.core.application.ports.sms_gateway import SMSGateway, SMSResult
from src.core.domain.entities import SMSStatus
from src.core.domain.value_objects import PhoneNumber

logger = structlog.get_logger(__name__)

_SEND_ENDPOINT = "https://api.zenvia.com/v2/channels/sms/messages"
_STATUS_ENDPOINT = "https://api.zenvia.com/v2/channels/sms/messages/{id}"


class ZenviaAdapter(SMSGateway):
    """
    Adapter para o provedor Zenvia.
    Recebe credenciais no __init__ (injetadas pela Factory), não na assinatura
    do método send() — resolve ISP P10.
    """

    def __init__(self, api_token: str, sender: str) -> None:
        self._api_token = api_token
        self._sender = sender

    def _get_headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "X-API-TOKEN": self._api_token,
        }

    def send(
        self,
        destination: PhoneNumber,
        message: str,
        correlation_id: str,
    ) -> SMSResult:
        """Envia SMS via Zenvia com assinatura padronizada."""
        e164 = "55" + destination.value
        data = {
            "externalId": correlation_id,
            "from": self._sender,
            "to": e164,
            "contents": [{"type": "text", "text": message}],
        }
        log = logger.bind(
            provider=self.provider_name,
            correlation_id=correlation_id,
            destination=destination.masked(),
        )
        try:
            response = httpx.post(
                _SEND_ENDPOINT,
                headers=self._get_headers(),
                json=data,
                timeout=10.0,
            )
            response.raise_for_status()
            message_id = response.json().get("id", correlation_id)
            log.info("sms_sent_success", zenvia_id=message_id)
            return SMSResult.success(message_id=message_id)
        except httpx.TimeoutException:
            log.error("sms_send_timeout")
            return SMSResult.failure(error="Zenvia request timed out")
        except httpx.HTTPStatusError as exc:
            log.error("sms_send_http_error", status_code=exc.response.status_code)
            return SMSResult.failure(error=f"Zenvia HTTP {exc.response.status_code}")
        except Exception as exc:
            log.error("sms_send_unexpected_error", error=str(exc))
            return SMSResult.failure(error=str(exc))

    def get_delivery_status(self, provider_message_id: str) -> SMSStatus:
        try:
            url = _STATUS_ENDPOINT.format(id=provider_message_id)
            response = httpx.get(url, headers=self._get_headers(), timeout=10.0)
            response.raise_for_status()
            return _map_zenvia_status(response.json().get("status", "").upper())
        except Exception as exc:
            logger.error(
                "zenvia_status_query_error",
                error=str(exc),
                message_id=provider_message_id,
            )
            return SMSStatus.PENDING

    @property
    def provider_name(self) -> str:
        return "zenvia"


def _map_zenvia_status(raw: str) -> SMSStatus:
    return {
        "DELIVERED": SMSStatus.DELIVERED,
        "SENT": SMSStatus.SENT,
        "FAILED": SMSStatus.FAILED,
        "REJECTED": SMSStatus.FAILED,
        "NOT_DELIVERED": SMSStatus.FAILED,
    }.get(raw, SMSStatus.PENDING)
