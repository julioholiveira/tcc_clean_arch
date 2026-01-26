from unittest.mock import patch

from django.test import Client, TestCase, tag

from core.models import TokenSMS
from empresas.models import Empresa
from operadora_sms.models import OperadoraSMS
from parametros.models import Parametro


# @tag("no_test")
class PasscodeTestCase(TestCase):

    def setUp(self):
        self.client = Client(
            HTTP_USER_AGENT="Mozilla/5.0 (iPhone; CPU iPhone OS 13_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
        )

        self.operadora = OperadoraSMS.objects.create(
            name="Sinch",
            slug_name="sinch",
        )

        self.empresa = Empresa.objects.create(
            id=1,
            razao_social="Teste",
            site_id="default",
            operadora_sms=self.operadora,
            usuario_operadora="admin",
            senha_operadora="admin",
        )

        self.parametros = Parametro.objects.create(
            guest_timeout=10, empresas=self.empresa
        )

        self.token_sms = TokenSMS.objects.create(
            telefone="15997915209", empresas=self.empresa, token="999999"
        )

    def test_get_passcode(self):
        response = self.client.get(
            "/landingpage_passcode/",
            {
                "site_id": "default",
                "telefone": "15997915209",
                "campanha_id": "None",
                "mac": "00:01:02:03:04:05",
                "empresa": 1,
            },
        )

        self.assertEqual(response.status_code, 200)

    @patch("core.views.libera_guest")
    def test_post_passcode_existe_token(self, mock_libera_guest):
        response = self.client.post(
            "/landingpage_passcode/",
            {
                "passcode": "999999",
                "site_id": "default",
                "telefone": "15997915209",
                "campanha_id": "None",
                "mac": "00:01:02:03:04:05",
                "empresa": self.empresa.id,
            },
        )

        mock_libera_guest.return_value = "/welcome/"

        token = TokenSMS.objects.filter(telefone="15997915209", empresas=self.empresa)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(token.exists())

    def test_post_passcode_incorrect_token(self):
        response = self.client.post(
            "/landingpage_passcode/",
            {
                "passcode": "123456",
                "site_id": "default",
                "telefone": "15997915209",
                "campanha_id": "None",
                "mac": "00:01:02:03:04:05",
                "empresa": 1,
            },
        )

        self.assertEqual(response.status_code, 200)
