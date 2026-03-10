"""Testes do ListGuestUsersUseCase"""

import pytest

from src.core.application.use_cases.list_guest_users import ListGuestUsersUseCase
from src.core.domain.entities import User


class TestListGuestUsersUseCase:
    @pytest.fixture
    def use_case(self, mock_user_repository):
        return ListGuestUsersUseCase(user_repository=mock_user_repository)

    @pytest.fixture
    def sample_users(self, company_id, phone_number):
        return [
            User(id=1, company_id=company_id, phone=phone_number, name="Joao"),
            User(id=2, company_id=company_id, phone=phone_number, name="Maria"),
            User(id=3, company_id=company_id, phone=phone_number, name="Pedro"),
        ]

    def test_list_users_success(self, use_case, company_id, sample_users, mock_user_repository):
        mock_user_repository.list_by_company.return_value = sample_users
        result = use_case.execute(company_id=company_id)
        assert len(result) == 3
        mock_user_repository.list_by_company.assert_called_once_with(
            company_id=company_id, limit=100, offset=0
        )

    def test_list_users_empty(self, use_case, company_id, mock_user_repository):
        mock_user_repository.list_by_company.return_value = []
        result = use_case.execute(company_id=company_id)
        assert result == []

    def test_list_users_with_limit_offset(self, use_case, company_id, mock_user_repository):
        mock_user_repository.list_by_company.return_value = []
        use_case.execute(company_id=company_id, limit=20, offset=40)
        call_args = mock_user_repository.list_by_company.call_args
        assert call_args.kwargs["limit"] == 20
        assert call_args.kwargs["offset"] == 40

    def test_list_users_repository_error(self, use_case, company_id, mock_user_repository):
        mock_user_repository.list_by_company.side_effect = Exception("DB error")
        result = use_case.execute(company_id=company_id)
        assert result == []
