"""Interfaces de repositórios (Ports) - contratos para persistência"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from .entities import User, SMSTokenEntity, Connection, SMSDelivery, Historico
from .value_objects import CompanyId, PhoneNumber


class UserRepository(ABC):
    """Contrato para persistência de usuários"""
    
    @abstractmethod
    def save(self, user: User) -> User:
        """Salva ou atualiza usuário"""
        pass
    
    @abstractmethod
    def find_by_id(self, user_id: int) -> Optional[User]:
        """Busca usuário por ID"""
        pass
    
    @abstractmethod
    def find_by_phone(self, company_id: CompanyId, phone: PhoneNumber) -> Optional[User]:
        """Busca usuário por telefone e empresa"""
        pass
    
    @abstractmethod
    def list_by_company(
        self, 
        company_id: CompanyId, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[User]:
        """Lista usuários de uma empresa com paginação"""
        pass


class SMSTokenRepository(ABC):
    """Contrato para persistência de tokens SMS"""
    
    @abstractmethod
    def save(self, token: SMSTokenEntity) -> SMSTokenEntity:
        """Salva ou atualiza token"""
        pass
    
    @abstractmethod
    def find_valid_token(
        self, 
        company_id: CompanyId, 
        phone: PhoneNumber, 
        token_value: str
    ) -> Optional[SMSTokenEntity]:
        """Busca token válido (não expirado)"""
        pass
    
    @abstractmethod
    def delete_expired(self, before: datetime) -> int:
        """Remove tokens expirados"""
        pass


class ConnectionRepository(ABC):
    """Contrato para persistência de conexões"""
    
    @abstractmethod
    def save(self, connection: Connection) -> Connection:
        """Salva conexão"""
        pass
    
    @abstractmethod
    def count_active_connections(
        self, 
        company_id: CompanyId, 
        user_phone: PhoneNumber
    ) -> int:
        """Conta conexões ativas de um usuário"""
        pass
    
    @abstractmethod
    def list_by_user(
        self, 
        company_id: CompanyId, 
        user_phone: PhoneNumber, 
        limit: int = 50
    ) -> List[Connection]:
        """Lista histórico de conexões de usuário"""
        pass


class SMSDeliveryRepository(ABC):
    """Contrato para persistência de entregas SMS"""
    
    @abstractmethod
    def save(self, delivery: SMSDelivery) -> SMSDelivery:
        """Salva entrega"""
        pass
    
    @abstractmethod
    def find_by_provider_id(self, provider_message_id: str) -> Optional[SMSDelivery]:
        """Busca por ID do provider"""
        pass
    
    @abstractmethod
    def get_delivery_stats(
        self, 
        company_id: CompanyId, 
        from_date: datetime, 
        to_date: datetime
    ) -> dict:
        """Estatísticas de entrega por período"""
        pass


class HistoricoRepository(ABC):
    """Contrato para persistência de histórico"""
    
    @abstractmethod
    def save(self, historico: Historico) -> Historico:
        """Salva registro de histórico"""
        pass
