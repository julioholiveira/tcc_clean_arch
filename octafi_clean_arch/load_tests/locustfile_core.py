"""
Load tests para módulo Core - Baseline
Simula cenários reais de autenticação guest e envio de SMS
"""

import random

from locust import HttpUser, between, task


class GuestAuthUser(HttpUser):
    """Simula usuário guest se autenticando na rede WiFi"""

    wait_time = between(1, 3)

    def on_start(self):
        """Setup inicial - dados de teste"""
        self.mac_address = self._generate_mac()
        self.phone = self._generate_phone()
        self.ap_mac = "78:8a:20:29:45:e7"  # MAC do access point
        self.phone = self._generate_phone()
        self.site_id = "default"
        self.empresa_id = 1
        self.empresa_envia_sms = False  # Força envio de SMS para teste
        self.empresa_integracao_sms = False  # Desativa integração real para teste local
        # Faz um GET inicial para popular o cookie de sessão e o csrftoken
        self._get_csrf_token()
        self.equipamento_id = 1
        self.modelo_id = 1
        self.equipamento_empresa_id = self.empresa_id
        self.equipamento_modelo_id = self.modelo_id
        self.equipamento_mac = self.ap_mac

    def _get_csrf_token(self) -> str:
        """Faz GET na landing page para garantir que o cookie csrftoken está presente."""
        url = f"/landingpage/mac={self.mac_address}&site_id={self.site_id}&campanha_id=None&empresa={self.empresa_id}"
        self.client.get(url, name="/landingpage/[csrf-refresh]", catch_response=True)
        return self.client.cookies.get("csrftoken", "")

    def _generate_mac(self):
        """Gera endereço MAC aleatório"""
        return ":".join([f"{random.randint(0, 255):02x}" for _ in range(6)])

    def _generate_phone(self):
        """Gera telefone brasileiro (11 dígitos)"""
        ddd = random.choice(["11", "15", "21", "47", "51"])
        number = "".join([str(random.randint(0, 9)) for _ in range(9)])
        return f"{ddd}{number}"

    @task(5)
    def landing_page_get(self):
        """GET na landing page"""
        with self.client.get(
            f"/landingpage/mac={self.mac_address}&site_id={self.site_id}&campanha_id=None&empresa={self.empresa_id}",
            name="/landingpage/[mac]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(3)
    def authenticate_with_phone(self):
        """POST de autenticação com telefone"""
        csrf_token = self._get_csrf_token()
        with self.client.post(
            f"/landingpage/mac={self.mac_address}&site_id={self.site_id}&campanha_id=None&empresa={self.empresa_id}",
            data={
                "telefone": self.phone,
                "empresa": self.empresa_id,
                "csrfmiddlewaretoken": csrf_token,
            },
            headers={"X-CSRFToken": csrf_token},
            name="/landingpage/[authenticate]",
            catch_response=True,
        ) as response:
            if response.status_code in [200, 302]:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(2)
    def verify_passcode(self):
        """POST de verificação de código SMS"""
        csrf_token = self._get_csrf_token()
        passcode = "".join([str(random.randint(0, 9)) for _ in range(6)])
        with self.client.post(
            "/landingpage_passcode/",
            data={
                "passcode": passcode,
                "telefone": self.phone,
                "mac": self.mac_address,
                "site_id": self.site_id,
                "campanha_id": "None",
                "empresa": self.empresa_id,
                "csrfmiddlewaretoken": csrf_token,
            },
            headers={"X-CSRFToken": csrf_token},
            name="/landingpage_passcode/",
            catch_response=True,
        ) as response:
            # Esperamos falha (código inválido) mas medimos performance
            if response.status_code in [200, 302, 400]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def landing_page_pre(self):
        """GET na página pré-login"""
        with self.client.get(
            f"/guest/s/{self.site_id}",
            params={"ap": self.ap_mac, "id": self.mac_address},
            name="/landingpage_guest_pre/[site]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")


# class SMSStatusUser(HttpUser):
#     """Simula requisições de status de SMS"""

#     wait_time = between(2, 5)

#     @task
#     def get_sms_status(self):
#         """GET de status de SMS (via API)"""
#         with self.client.get(
#             "/api/sms/status/",
#             headers={"X-Remote-Addr": "127.0.0.1"},
#             name="/api/sms/status/",
#             catch_response=True,
#         ) as response:
#             if response.status_code in [200, 401, 403, 404]:
#                 response.success()
#             else:
#                 response.failure(f"Status: {response.status_code}")
