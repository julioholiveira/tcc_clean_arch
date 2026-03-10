"""
SMSProviderFactory — registro dinâmico sem getattr/sys.modules (resolve OCP P7).
Novos providers são adicionados apenas registrando-se no registry, sem modificar
código existente.
"""

from typing import Any, Callable, Dict

import structlog

from src.core.application.ports.sms_gateway import SMSGateway
from src.core.domain.exceptions import UnsupportedProviderError
from src.core.infrastructure.sms.sinch_adapter import SinchAdapter
from src.core.infrastructure.sms.sms_market_adapter import SMSMarketAdapter
from src.core.infrastructure.sms.zenvia_adapter import ZenviaAdapter

logger = structlog.get_logger(__name__)

# Registry: slug -> factory callable. Extensão sem modificação (OCP).
_PROVIDER_REGISTRY: Dict[str, Callable[..., SMSGateway]] = {}


def register_provider(slug: str, factory: Callable[..., SMSGateway]) -> None:
    """Registra novo provider sem modificar código existente (OCP)."""
    _PROVIDER_REGISTRY[slug] = factory
    logger.debug("sms_provider_registered", slug=slug)


def _sinch_factory(empresa: Any) -> SinchAdapter:
    return SinchAdapter(
        sms_user=empresa.usuario_operadora,
        sms_password=empresa.senha_operadora,
    )


def _zenvia_factory(empresa: Any) -> ZenviaAdapter:
    from octafi import settings
    from operadora_sms.models import OperadoraSMS

    sms_company = OperadoraSMS.objects.get(slug_name="zenvia")
    return ZenviaAdapter(api_token=sms_company.token, sender=settings.SENDER)


def _sms_market_factory(empresa: Any) -> SMSMarketAdapter:
    from operadora_sms.models import OperadoraSMS

    sms_company = OperadoraSMS.objects.get(slug_name="sms_market")
    return SMSMarketAdapter(username=sms_company.username, password=sms_company.password)


# Registro padrão dos 3 providers existentes
register_provider("sinch", _sinch_factory)
register_provider("zenvia", _zenvia_factory)
register_provider("sms_market", _sms_market_factory)


class SMSProviderFactory:
    """Factory de providers SMS. Instancia o adapter correto a partir do slug da empresa."""

    @staticmethod
    def create(empresa: Any) -> SMSGateway:
        """
        Cria o adapter de SMS para a empresa informada.

        Args:
            empresa: Instância do model Empresa com operadora_sms configurada.

        Returns:
            Implementação concreta de SMSGateway.

        Raises:
            UnsupportedProviderError: Se o slug do provider não estiver registrado.
        """
        slug = empresa.operadora_sms.slug_name.lower()
        factory_fn = _PROVIDER_REGISTRY.get(slug)
        if not factory_fn:
            raise UnsupportedProviderError(
                f"Provider '{slug}' not registered. Available: {list(_PROVIDER_REGISTRY.keys())}"
            )
        logger.debug("sms_provider_created", slug=slug, empresa_id=empresa.pk)
        return factory_fn(empresa)
