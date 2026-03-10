"""
Load tests para módulo Mailing — API v1 (arquitetura limpa)

Endpoints testados:
  GET  /api/v1/mailing/campaigns/                      — lista campanhas
  POST /api/v1/mailing/campaigns/                      — cria campanha
  POST /api/v1/mailing/campaigns/<id>/send/            — dispara envio
  POST /api/v1/mailing/campaigns/<id>/schedule/        — agenda envio

Todos os requests incluem o header obrigatório X-Empresa-ID.
Configurável via variável de ambiente LOCUST_EMPRESA_ID (padrão: 1).

Paridade com locustfile_mailing.py (baseline):
  - Mesmo número de usuários, spawn-rate e duração
  - campaign_id seed: random.randint(1, 10) — igual ao baseline
  - Mesmos pesos de task
"""

import os
import random
from datetime import datetime, timedelta, timezone

from locust import HttpUser, between, task

# Empresa padrão para testes — sobrescrever com LOCUST_EMPRESA_ID=<id>
EMPRESA_ID = os.getenv("LOCUST_EMPRESA_ID", "1")


def _future_datetime(hours_ahead: int = 24) -> str:
    """Retorna ISO 8601 UTC para agendamento de campanhas."""
    dt = datetime.now(tz=timezone.utc) + timedelta(hours=hours_ahead)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _campaign_name() -> str:
    """Gera nome único de campanha para testes."""
    return f"Locust Test Campaign {random.randint(1000, 9999)}"


class MailingV1User(HttpUser):
    """
    Simula usuário do sistema de mailing via API v1.

    Pesos equivalentes ao baseline MailingUser:
      list_campaigns   — weight 3
      create_campaign  — weight 5  (substitui select_recipients do baseline)
      send_campaign    — weight 1
      schedule_campaign — weight 1 (novo endpoint v1 sem equivalente direto no baseline)
    """

    wait_time = between(2, 5)

    def on_start(self) -> None:
        self.campaign_id = random.randint(1, 10)
        self._common_headers = {
            "X-Empresa-ID": EMPRESA_ID,
            "Content-Type": "application/json",
        }

    @task(3)
    def list_campaigns(self) -> None:
        """
        GET /api/v1/mailing/campaigns/
        Lista campanhas da empresa com paginação opcional.
        Equivalente a /mailing/lista_mailings/ do baseline.
        """
        with self.client.get(
            "/api/v1/mailing/campaigns/",
            headers={"X-Empresa-ID": EMPRESA_ID},
            params={"limit": 50, "offset": 0},
            name="GET /api/v1/mailing/campaigns/",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 302, 400):
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(5)
    def create_campaign(self) -> None:
        """
        POST /api/v1/mailing/campaigns/
        Cria nova campanha. template_id=1 usado como referência sintética.
        Equivalente funcional a select_recipients do baseline (principal operação de escrita).
        """
        payload = {
            "name": _campaign_name(),
            "template_id": random.randint(1, 5),
        }
        with self.client.post(
            "/api/v1/mailing/campaigns/",
            json=payload,
            headers=self._common_headers,
            name="POST /api/v1/mailing/campaigns/",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 201, 202, 400, 422):
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def send_campaign(self) -> None:
        """
        POST /api/v1/mailing/campaigns/<id>/send/
        Dispara envio de campanha existente.
        Equivalente a /mailing/enviar_mailing/<id> do baseline.
        """
        payload = {
            "batch_size": 100,
            "delay_between_batches_seconds": 1,
        }
        with self.client.post(
            f"/api/v1/mailing/campaigns/{self.campaign_id}/send/",
            json=payload,
            headers=self._common_headers,
            name="POST /api/v1/mailing/campaigns/[id]/send/",
            catch_response=True,
        ) as response:
            # 400/404 são esperados com IDs sintéticos
            if response.status_code in (200, 202, 400, 404, 422):
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def schedule_campaign(self) -> None:
        """
        POST /api/v1/mailing/campaigns/<id>/schedule/
        Agenda campanha para envio futuro. Novo endpoint sem equivalente direto no baseline.
        """
        payload = {
            "scheduled_for": _future_datetime(hours_ahead=random.randint(1, 72)),
        }
        with self.client.post(
            f"/api/v1/mailing/campaigns/{self.campaign_id}/schedule/",
            json=payload,
            headers=self._common_headers,
            name="POST /api/v1/mailing/campaigns/[id]/schedule/",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 400, 404, 422):
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
