"""Adapter SMSMarket — implementa SMSGateway com assinatura uniforme."""

import base64
from urllib.parse import urlencode

import httpx
import structlog

from src.core.application.ports.sms_gateway import SMSGateway, SMSResult
from src.core.domain.entities import SMSStatus
from src.core.domain.value_objects import PhoneNumber

logger = structlog.get_logger(__name__)

_SEND_ENDPOINT = "https://api.smsmarket.com.br/webservice-rest/send-single"


class SMSMarketAdapter(SMSGateway):
    """
    Adapter para o provedor SMSMarket.
    correlation_id mapeado para campaign_id do provider.
    Resolve ISP P10: assinatura uniforme; credenciais injetadas no __init__.
    """

    def __init__(self, username: str, password: str) -> None:
        auth_bytes = f"{username}:{password}".encode("utf-8")
        b64 = base64.b64encode(auth_bytes).decode("utf-8")
        self._headers = {
            "Authorization": f"Basic {b64}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def send(
        self,
        destination: PhoneNumber,
        message: str,
        correlation_id: str,
    ) -> SMSResult:
        """Envia SMS via SMSMarket com assinatura padronizada."""
        data = urlencode(
            {
                "number": destination.value,
                "content": message,
                "campaign_id": correlation_id,
                "type": 0,
                "schedule": "",
            }
        )
        log = logger.bind(
            provider=self.provider_name,
            correlation_id=correlation_id,
            destination=destination.masked(),
        )
        try:
            response = httpx.post(
                _SEND_ENDPOINT,
                headers=self._headers,
                content=data,
                timeout=10.0,
            )
            response.raise_for_status()
            body = response.json()
            if body.get("responseCode") == "000":
                log.info("sms_sent_success")
                return SMSResult.success(message_id=correlation_id)
            error_msg = body.get("responseMessage", "Unknown SMSMarket error")
            log.error("sms_send_business_error", error=error_msg)
            return SMSResult.failure(error=error_msg)
        except httpx.TimeoutException:
            log.error("sms_send_timeout")
            return SMSResult.failure(error="SMSMarket request timed out")
        except httpx.HTTPStatusError as exc:
            log.error("sms_send_http_error", status_code=exc.response.status_code)
            return SMSResult.failure(error=f"SMSMarket HTTP {exc.response.status_code}")
        except Exception as exc:
            log.error("sms_send_unexpected_error", error=str(exc))
            return SMSResult.failure(error=str(exc))

    def get_delivery_status(self, provider_message_id: str) -> SMSStatus:
        # SMSMarket não possui endpoint de status individual
        logger.warning(
            "smsmarket_status_not_supported",
            message_id=provider_message_id,
        )
        return SMSStatus.PENDING

    @property
    def provider_name(self) -> str:
        return "smsmarket"
