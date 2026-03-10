"""
Adapter para API Raro — implementa CustomerDataProvider.
Resolve DIP P12: use cases dependem do port, não da classe Raro legada.
Adiciona caching (5 min) e retry (3x) ausentes no legado.
"""

from typing import Optional

import httpx
import structlog
from django.core.cache import cache

from src.core.application.ports.customer_data_provider import (
    CustomerData,
    CustomerDataProvider,
)
from src.core.domain.value_objects import CompanyId, PhoneNumber

logger = structlog.get_logger(__name__)

_CACHE_TTL_SECONDS = 300  # 5 minutos — evita chamadas repetidas no hot path
_MAX_RETRIES = 3


class RaroAdapter(CustomerDataProvider):
    """
    Adapter para integração com a API Raro.
    Caching por telefone+empresa evita chamadas repetidas (hot path do landingpage_guest).
    Retry automático em TimeoutException com até 3 tentativas.
    """

    def __init__(self, base_url: str, api_key: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    def _build_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _cache_key(self, company_id: CompanyId, phone: PhoneNumber) -> str:
        return f"raro:customer:{company_id.value}:{phone.value}"

    def get_customer_by_phone(
        self,
        company_id: CompanyId,
        phone: PhoneNumber,
    ) -> Optional[CustomerData]:
        """Busca cliente na API Raro com cache de 5 minutos e retry automático."""
        cache_key = self._cache_key(company_id, phone)
        cached = cache.get(cache_key)
        if cached is not None:
            logger.debug("raro_cache_hit", phone=phone.masked())
            return cached

        log = logger.bind(company_id=company_id.value, phone=phone.masked())

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                response = httpx.get(
                    f"{self._base_url}/customers",
                    headers=self._build_headers(),
                    params={"phone": phone.value, "company_id": company_id.value},
                    timeout=8.0,
                )
                if response.status_code == 404:
                    log.info("raro_customer_not_found")
                    return None
                response.raise_for_status()
                data = response.json()
                customer = CustomerData(
                    phone=phone,
                    name=data.get("name"),
                    email=data.get("email"),
                    document=data.get("cpf"),
                    address=data.get("address"),
                    is_active=data.get("active", True),
                )
                cache.set(cache_key, customer, _CACHE_TTL_SECONDS)
                log.info("raro_customer_fetched", attempt=attempt)
                return customer
            except httpx.TimeoutException:
                log.warning("raro_timeout", attempt=attempt)
            except httpx.HTTPStatusError as exc:
                log.error(
                    "raro_http_error",
                    status_code=exc.response.status_code,
                    attempt=attempt,
                )
                break  # Erros HTTP não são retriable
            except Exception as exc:
                log.error("raro_unexpected_error", error=str(exc), attempt=attempt)
                break

        return None

    def validate_customer_status(
        self,
        company_id: CompanyId,
        phone: PhoneNumber,
    ) -> bool:
        """Verifica se cliente está ativo na base da Raro."""
        customer = self.get_customer_by_phone(company_id, phone)
        return customer is not None and customer.is_active
