"""Port para integração com API Raro (dados de clientes)"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from src.core.domain.value_objects import CompanyId, PhoneNumber


@dataclass
class CustomerData:
    """Dados do cliente da API Raro"""

    phone: PhoneNumber
    name: Optional[str] = None
    email: Optional[str] = None
    document: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True


class CustomerDataProvider(ABC):
    """Port para provedores de dados de clientes (API Raro, etc)"""

    @abstractmethod
    def get_customer_by_phone(
        self, company_id: CompanyId, phone: PhoneNumber
    ) -> Optional[CustomerData]:
        """
        Busca dados do cliente por telefone na API externa.

        Args:
            company_id: ID da empresa
            phone: Telefone do cliente

        Returns:
            CustomerData ou None se não encontrado
        """
        pass

    @abstractmethod
    def validate_customer_status(
        self, company_id: CompanyId, phone: PhoneNumber
    ) -> bool:
        """Verifica se cliente está ativo/liberado"""
        pass
