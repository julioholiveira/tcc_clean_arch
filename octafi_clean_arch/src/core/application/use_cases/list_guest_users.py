"""Use Case: Listagem de Usuários Guest - resolve P3"""

import logging

from src.core.domain.repositories import UserRepository
from src.core.domain.value_objects import CompanyId

logger = logging.getLogger(__name__)


class ListGuestUsersUseCase:
    """
    Lista usuários guest de uma empresa.
    Extrai lógica de get_guest_users do model (P3).
    """

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def execute(self, company_id: CompanyId, limit: int = 100, offset: int = 0):
        """
        Lista usuários com paginação.

        Args:
            company_id: ID da empresa (não `request`)
            limit: Limite de resultados
            offset: Offset para paginação

        Returns:
            Lista de usuários
        """
        try:
            users = self.user_repository.list_by_company(
                company_id=company_id, limit=limit, offset=offset
            )

            logger.info(
                f"Listados {len(users)} usuários",
                extra={"company_id": company_id.value},
            )

            return users

        except Exception as e:
            logger.error(f"Erro ao listar usuários: {str(e)}", exc_info=True)
            return []
