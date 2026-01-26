from unittest.mock import patch

from django.test import Client, TestCase

from core.models import TokenSMS, Usuario
from empresas.models import Empresa
from equipamentos.models import Equipamento
from modelos_equipamentos.models import ModeloEquipamento
from operadora_sms.models import OperadoraSMS
from parametros.models import Parametro


class LandingpageTelefoneTestCase(TestCase):

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
            envia_sms=True,
        )

        self.parametros = Parametro.objects.create(
            guest_timeout=10, empresas=self.empresa
        )

        self.modelo_equipamento = ModeloEquipamento.objects.create(
            nome="Teste", marca="Unifi"
        )

        self.equipamento = Equipamento.objects.create(
            nome="Teste",
            mac="f0:9f:c2:a3:96:08",
            localizacao="Teste",
            modelo=self.modelo_equipamento,
            empresas=self.empresa,
        )

        self.url = "/landingpage/mac=98:39:8e:70:21:23&site_id=default&campanha_id=None&empresa=1"

    def test_get_telefone(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_telefone_usuario_nao_existe_envio_sms(self):

        response = self.client.post(self.url, {"telefone": "15997915209", "empresa": 1})

        token = TokenSMS.objects.filter(telefone="15997915209", empresas=self.empresa)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(token.exists())

    @patch("core.views.libera_guest")
    def test_post_telefone_usuario_existe(self, mock_libera_guest):
        Usuario.objects.create(
            empresas=self.empresa,
            telefone="15997915209",
        )

        mock_libera_guest.return_value = "/welcome/"

        response = self.client.post(self.url, {"telefone": "15997915209"})

        self.assertEqual(response.content, b"")
        self.assertEqual(response.status_code, 302)

    @patch("core.views.libera_guest")
    def test_post_telefone_possui_token(self, mock_libera_guest):
        TokenSMS.objects.create(
            telefone="15997915209", empresas=self.empresa, token="999999"
        )
        mock_libera_guest.return_value = "/welcome/"
        response = self.client.post(self.url, {"telefone": "15997915209"})
        self.assertEqual(response.status_code, 200)


class LandingpageTestCase(TestCase):
    """Test ladingpage sem envio de sms"""

    def setUp(self):

        self.client = Client(
            HTTP_USER_AGENT="Mozilla/5.0 (iPhone; CPU iPhone OS 13_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
        )

        self.empresa = Empresa.objects.create(
            id=1,
            razao_social="Teste",
            site_id="default",
            envia_sms=False,
        )

        self.parametros = Parametro.objects.create(
            guest_timeout=10, empresas=self.empresa
        )

        self.modelo_equipamento = ModeloEquipamento.objects.create(
            nome="Teste", marca="Unifi"
        )

        self.equipamento = Equipamento.objects.create(
            nome="Teste",
            mac="f0:9f:c2:a3:96:08",
            localizacao="Teste",
            modelo=self.modelo_equipamento,
            empresas=self.empresa,
        )

        self.url = "/landingpage/mac=98:39:8e:70:21:23&site_id=default&campanha_id=None&empresa=1"

    @patch("core.views.libera_guest")
    def test_post_landinpage_não_envia_sms(self, mock_libera_guest):
        mock_libera_guest.return_value = "/welcome/"

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
