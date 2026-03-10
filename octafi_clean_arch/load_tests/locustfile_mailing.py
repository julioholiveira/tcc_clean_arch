"""
Load tests para módulo Mailing - Baseline
Simula seleção de destinatários e envio de campanhas
"""

import random
from datetime import date, timedelta

from locust import HttpUser, between, task


class MailingUser(HttpUser):
    """Simula usuário do sistema de mailing"""

    wait_time = between(2, 5)

    def on_start(self):
        """Login antes dos testes"""
        self.campaign_id = random.randint(1, 10)
        self.client.post(
            "/login/",
            data={"username": "admin", "password": "admin123"},
            name="/login/",
            catch_response=True,
        )

    @task(3)
    def list_campaigns(self):
        """Lista campanhas de mailing"""
        with self.client.get(
            "/mailing/lista_mailings/",
            name="/mailing/lista_mailings/",
            catch_response=True,
        ) as response:
            if response.status_code in [200]:  # 302 = redirect to login
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(5)
    def select_recipients(self):
        """Seleciona destinatários para campanha"""
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        with self.client.get(
            f"/mailing/selecionar_destinatarios/{self.campaign_id}",
            params={
                "data_inicial": start_date.strftime("%Y-%m-%d"),
                "data_final": end_date.strftime("%Y-%m-%d"),
            },
            name="/mailing/selecionar_destinatarios/[id]",
            catch_response=True,
        ) as response:
            if response.status_code in [200]:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(1)
    def send_campaign(self):
        """Simula envio de campanha (GET, não POST real)"""
        with self.client.get(
            f"/mailing/enviar_mailing/{self.campaign_id}",
            name="/mailing/enviar_mailing/[id]",
            catch_response=True,
        ) as response:
            if response.status_code in [200]:  # 405 = method not allowed
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
