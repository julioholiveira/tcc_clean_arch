"""Interfaces de repositórios do Mailing"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from src.core.domain.value_objects import CompanyId

from .entities import Campaign, MailMessage, MailTemplate


class MailTemplateRepository(ABC):
    """Contrato para persistência de templates"""

    @abstractmethod
    def save(self, template: MailTemplate) -> MailTemplate:
        """Salva template"""
        pass

    @abstractmethod
    def find_by_id(self, template_id: int) -> Optional[MailTemplate]:
        """Busca template por ID"""
        pass

    @abstractmethod
    def list_by_company(self, company_id: CompanyId) -> List[MailTemplate]:
        """Lista templates da empresa"""
        pass

    @abstractmethod
    def delete(self, template_id: int) -> None:
        """Remove template"""
        pass


class CampaignRepository(ABC):
    """Contrato para persistência de campanhas"""

    @abstractmethod
    def save(self, campaign: Campaign) -> Campaign:
        """Salva campanha"""
        pass

    @abstractmethod
    def find_by_id(self, campaign_id: int) -> Optional[Campaign]:
        """Busca campanha por ID"""
        pass

    @abstractmethod
    def list_scheduled(self, before: datetime) -> List[Campaign]:
        """Lista campanhas agendadas para execução"""
        pass

    @abstractmethod
    def list_by_company(
        self, company_id: CompanyId, limit: int = 50, offset: int = 0
    ) -> List[Campaign]:
        """Lista campanhas da empresa com paginação"""
        pass


class MailMessageRepository(ABC):
    """Contrato para persistência de mensagens"""

    @abstractmethod
    def save(self, message: MailMessage) -> MailMessage:
        """Salva mensagem individual"""
        pass

    @abstractmethod
    def save_batch(self, messages: List[MailMessage]) -> List[MailMessage]:
        """Salva lote de mensagens"""
        pass

    @abstractmethod
    def update_status(
        self,
        message_id: int,
        status: str,
        provider_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Atualiza status de mensagem"""
        pass

    @abstractmethod
    def list_by_campaign(
        self, campaign_id: int, limit: int = 100, offset: int = 0
    ) -> List[MailMessage]:
        """Lista mensagens de uma campanha"""
        pass


class RecipientRepository(ABC):
    """Contrato para filtro e listagem de destinatários"""

    @abstractmethod
    def list_filtered(
        self,
        company_id: CompanyId,
        campaign_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list:
        """Lista destinatários com filtros e paginação"""
        pass

    @abstractmethod
    def count_filtered(
        self,
        company_id: CompanyId,
        campaign_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> int:
        """Conta destinatários com filtros"""
        pass
