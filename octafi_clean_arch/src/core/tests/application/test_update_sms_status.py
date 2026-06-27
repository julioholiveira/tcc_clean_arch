"""Testes do UpdateSMSStatusUseCase"""

from unittest.mock import Mock

import pytest

from src.core.application.ports.sms_gateway import SMSGateway
from src.core.application.use_cases.update_sms_status import UpdateSMSStatusUseCase
from src.core.domain.entities import SMSStatus


class TestUpdateSMSStatusUseCase:
    """Testa o use case de atualização de status de SMS"""

    @pytest.fixture
    def delivery_repository(self):
        repo = Mock()
        repo.update_status = Mock(return_value=True)
        return repo

    @pytest.fixture
    def gateway_with_bulk(self):
        """Gateway que suporta consulta em lote (ex.: Sinch)"""
        gateway = Mock()
        gateway.provider_name = "sinch"
        gateway.get_bulk_status_updates = Mock(return_value=[])
        return gateway

    @pytest.fixture
    def gateway_without_bulk(self):
        """Gateway sem suporte a consulta em lote (spec restringe atributos)"""
        gateway = Mock(spec=SMSGateway)
        gateway.provider_name = "zenvia"
        return gateway

    def test_provider_without_bulk_support_returns_zero(self, gateway_without_bulk, delivery_repository):
        use_case = UpdateSMSStatusUseCase(sms_gateway=gateway_without_bulk, delivery_repository=delivery_repository)

        result = use_case.execute(empresa_id=1)

        assert result == 0
        delivery_repository.update_status.assert_not_called()

    def test_no_updates_returns_zero(self, gateway_with_bulk, delivery_repository):
        gateway_with_bulk.get_bulk_status_updates.return_value = []

        use_case = UpdateSMSStatusUseCase(sms_gateway=gateway_with_bulk, delivery_repository=delivery_repository)

        result = use_case.execute(empresa_id=1)

        assert result == 0
        delivery_repository.update_status.assert_not_called()

    def test_updates_are_persisted(self, gateway_with_bulk, delivery_repository):
        gateway_with_bulk.get_bulk_status_updates.return_value = [
            {"correlation_id": "abc", "status": SMSStatus.DELIVERED, "carrier": "VIVO"},
            {"correlation_id": "def", "status": SMSStatus.SENT, "carrier": "TIM"},
        ]

        use_case = UpdateSMSStatusUseCase(sms_gateway=gateway_with_bulk, delivery_repository=delivery_repository)

        result = use_case.execute(empresa_id=10)

        assert result == 2
        assert delivery_repository.update_status.call_count == 2
        delivery_repository.update_status.assert_any_call(
            correlation_id="abc", status=SMSStatus.DELIVERED, carrier="VIVO"
        )

    def test_skips_items_without_correlation_id_or_status(self, gateway_with_bulk, delivery_repository):
        gateway_with_bulk.get_bulk_status_updates.return_value = [
            {"correlation_id": None, "status": SMSStatus.DELIVERED},
            {"correlation_id": "abc", "status": None},
            {"correlation_id": "ghi", "status": SMSStatus.DELIVERED, "carrier": None},
        ]

        use_case = UpdateSMSStatusUseCase(sms_gateway=gateway_with_bulk, delivery_repository=delivery_repository)

        result = use_case.execute(empresa_id=1)

        assert result == 1
        delivery_repository.update_status.assert_called_once_with(
            correlation_id="ghi", status=SMSStatus.DELIVERED, carrier=None
        )

    def test_update_status_returning_false_is_not_counted(self, gateway_with_bulk, delivery_repository):
        gateway_with_bulk.get_bulk_status_updates.return_value = [
            {"correlation_id": "abc", "status": SMSStatus.DELIVERED, "carrier": "VIVO"},
            {"correlation_id": "def", "status": SMSStatus.SENT, "carrier": "TIM"},
        ]
        delivery_repository.update_status.side_effect = [True, False]

        use_case = UpdateSMSStatusUseCase(sms_gateway=gateway_with_bulk, delivery_repository=delivery_repository)

        result = use_case.execute(empresa_id=1)

        assert result == 1
