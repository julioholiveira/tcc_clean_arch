"""Adapter UniFi — implementa NetworkController port."""

from typing import Optional

import httpx
import structlog

from src.core.application.ports.network_controller import (
    NetworkAuthorizationResult,
    NetworkController,
)
from src.core.domain.value_objects import MACAddress, PhoneNumber

logger = structlog.get_logger(__name__)


class UniFiAdapter(NetworkController):
    """
    Adapter para controladores UniFi.
    Resolve DIP: use cases dependem de NetworkController, não desta classe concreta.
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        site: str = "default",
    ) -> None:
        self._host = host.rstrip("/")
        self._username = username
        self._password = password
        self._site = site
        self._session: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        if self._session is None:
            self._session = httpx.Client(
                base_url=self._host,
                verify=False,  # UniFi usa certificados self-signed
                timeout=15.0,
            )
            self._login()
        return self._session

    def _login(self) -> None:
        assert self._session is not None
        response = self._session.post(
            "/api/login",
            json={"username": self._username, "password": self._password},
        )
        if response.status_code != 200:
            raise RuntimeError(f"UniFi login failed: HTTP {response.status_code}")
        logger.debug("unifi_login_success", host=self._host, site=self._site)

    def authorize_guest(
        self,
        mac_address: MACAddress,
        user_phone: PhoneNumber,
        duration_minutes: int = 60,
        bandwidth_limit_kbps: Optional[int] = None,
    ) -> NetworkAuthorizationResult:
        """Autoriza MAC address no UniFi para duração especificada."""
        log = logger.bind(
            mac=mac_address.value,
            user=user_phone.masked(),
            site=self._site,
        )
        payload: dict = {
            "cmd": "authorize-guest",
            "mac": mac_address.value,
            "minutes": duration_minutes,
        }
        if bandwidth_limit_kbps:
            payload["down"] = bandwidth_limit_kbps
            payload["up"] = bandwidth_limit_kbps
        try:
            client = self._get_client()
            response = client.post(f"/api/s/{self._site}/cmd/stamgr", json=payload)
            response.raise_for_status()
            data = response.json()
            if data.get("meta", {}).get("rc") == "ok":
                log.info("unifi_guest_authorized")
                return NetworkAuthorizationResult(
                    success=True,
                    duration_minutes=duration_minutes,
                )
            error = data.get("meta", {}).get("msg", "Unknown UniFi error")
            log.error("unifi_authorize_failed", error=error)
            return NetworkAuthorizationResult(success=False, error_message=error)
        except httpx.HTTPStatusError as exc:
            log.error("unifi_http_error", status_code=exc.response.status_code)
            return NetworkAuthorizationResult(
                success=False,
                error_message=f"UniFi HTTP {exc.response.status_code}",
            )
        except Exception as exc:
            log.error("unifi_unexpected_error", error=str(exc))
            return NetworkAuthorizationResult(success=False, error_message=str(exc))

    def revoke_access(self, mac_address: MACAddress) -> bool:
        try:
            client = self._get_client()
            response = client.post(
                f"/api/s/{self._site}/cmd/stamgr",
                json={"cmd": "unauthorize-guest", "mac": mac_address.value},
            )
            response.raise_for_status()
            return response.json().get("meta", {}).get("rc") == "ok"
        except Exception as exc:
            logger.error("unifi_revoke_error", mac=mac_address.value, error=str(exc))
            return False

    def get_active_connections_count(self, user_phone: PhoneNumber) -> int:
        """
        Conta conexões ativas no site UniFi.
        NOTE: UniFi não filtra por telefone — use cases devem complementar
        com query no Historico se necessário para limite por usuário.
        """
        try:
            client = self._get_client()
            response = client.get(f"/api/s/{self._site}/stat/sta")
            response.raise_for_status()
            return len(response.json().get("data", []))
        except Exception as exc:
            logger.error("unifi_connections_count_error", error=str(exc))
            return 0
