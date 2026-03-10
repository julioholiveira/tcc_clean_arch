"""
Load tests para módulo Core — API v1 (arquitetura limpa)

Endpoints testados:
  POST /api/v1/guest/authenticate/     — inicia fluxo, envia token SMS
  POST /api/v1/guest/verify-passcode/  — verifica token recebido
  POST /api/v1/guest/authorize/        — autoriza acesso à rede
  GET  /api/v1/sms/status/             — consulta status de entregas SMS

Todos os requests incluem o header obrigatório X-Empresa-ID.
Configurável via variável de ambiente LOCUST_EMPRESA_ID (padrão: 1).

Paridade com locustfile_core.py (baseline):
  - Mesmo número de usuários, spawn-rate e duração
  - Mesmos helpers de geração de MAC e telefone
  - Mesmos pesos de task
"""

import os
import random

from locust import HttpUser, between, task

# Empresa padrão para testes — sobrescrever com LOCUST_EMPRESA_ID=<id>
EMPRESA_ID = os.getenv("LOCUST_EMPRESA_ID", "1")

# Site de referência para testes
SITE_ID = os.getenv("LOCUST_SITE_ID", "default")


def _generate_mac() -> str:
    """Gera endereço MAC aleatório no formato AA:BB:CC:DD:EE:FF."""
    return ":".join(f"{random.randint(0, 255):02X}" for _ in range(6))


def _generate_phone_e164() -> str:
    """
    Gera telefone brasileiro no formato E.164 (+55DDXXXXXXXXX).
    DDDs utilizados: 11, 15, 21, 47, 51 — mesmos do baseline.
    """
    ddd = random.choice(["11", "15", "21", "47", "51"])
    # Primeiro dígito do número = 9 (celular)
    number = "9" + "".join(str(random.randint(0, 9)) for _ in range(8))
    return f"+55{ddd}{number}"


def _generate_token() -> str:
    """Gera token SMS de 6 dígitos para testes de verificação."""
    return "".join(str(random.randint(0, 9)) for _ in range(6))


class GuestAuthV1User(HttpUser):
    """
    Simula usuário guest se autenticando via API v1.

    Pesos equivalentes ao baseline GuestAuthUser:
      authenticate    — weight 5
      verify_passcode — weight 3
      authorize       — weight 2
      (sem task GET pré-login pois a v1 não expõe landing page HTML)
    """

    wait_time = between(1, 3)

    def on_start(self) -> None:
        self.mac_address = _generate_mac()
        self.phone = _generate_phone_e164()
        self._common_headers = {
            "X-Empresa-ID": EMPRESA_ID,
            "Content-Type": "application/json",
        }

    @task(5)
    def authenticate(self) -> None:
        """
        POST /api/v1/guest/authenticate/
        Inicia o fluxo: valida dados e dispara envio de token SMS.
        """
        payload = {
            "mac_address": self.mac_address,
            "phone": self.phone,
            "site_id": SITE_ID,
        }
        with self.client.post(
            "/api/v1/guest/authenticate/",
            json=payload,
            headers=self._common_headers,
            name="POST /api/v1/guest/authenticate/",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 400, 422):
                # 400 = dados inválidos (esperado com dados sintéticos)
                # 422 = falha de validação de serializer
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(3)
    def verify_passcode(self) -> None:
        """
        POST /api/v1/guest/verify-passcode/
        Verifica token SMS. Com token aleatório esperamos 200 (falha de negócio) ou 400.
        """
        payload = {
            "phone": self.phone,
            "token": _generate_token(),
            "mac_address": self.mac_address,
        }
        with self.client.post(
            "/api/v1/guest/verify-passcode/",
            json=payload,
            headers=self._common_headers,
            name="POST /api/v1/guest/verify-passcode/",
            catch_response=True,
        ) as response:
            # 200 success=False (token inválido) ou 400 são respostas válidas aqui
            if response.status_code in (200, 400, 422):
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(2)
    def authorize_network(self) -> None:
        """
        POST /api/v1/guest/authorize/
        Autoriza acesso à rede para o dispositivo identificado por MAC + phone.
        """
        payload = {
            "mac_address": self.mac_address,
            "phone": self.phone,
            "duration_minutes": 60,
        }
        with self.client.post(
            "/api/v1/guest/authorize/",
            json=payload,
            headers=self._common_headers,
            name="POST /api/v1/guest/authorize/",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 400, 422):
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class SMSStatusV1User(HttpUser):
    """
    Simula consultas de status de SMS via API v1.
    Equivalente ao SMSStatusUser do baseline.
    """

    wait_time = between(2, 5)

    def on_start(self) -> None:
        self._common_headers = {"X-Empresa-ID": EMPRESA_ID}

    @task
    def get_sms_status(self) -> None:
        """
        GET /api/v1/sms/status/
        Consulta histórico de entregas SMS. Aceita query params opcionais:
        phone, delivery_id, date_from, date_to, limit, offset.
        """
        with self.client.get(
            "/api/v1/sms/status/",
            headers=self._common_headers,
            name="GET /api/v1/sms/status/",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 400, 401, 403, 404):
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
