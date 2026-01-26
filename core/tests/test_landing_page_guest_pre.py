from django.test import TestCase, tag

from empresas.models import Empresa
from equipamentos.models import Equipamento
from modelos_equipamentos.models import ModeloEquipamento
from operadora_sms.models import OperadoraSMS
from parametros.models import Parametro


# @tag("no_test")
class LandingpageGuestPreTestCase(TestCase):

    def setUp(self):

        self.operadora = OperadoraSMS.objects.create(
            name="Sinch",
            slug_name="sinch",
        )

        self.empresas = Empresa.objects.create(
            id=1,
            site_id="default",
            operadora_sms=self.operadora,
            usuario_operadora="admin",
            senha_operadora="admin",
            envia_sms=True,
        )

        self.parametros = Parametro.objects.create(
            guest_timeout=10, empresas=self.empresas
        )

        self.modelo_equipamento = ModeloEquipamento.objects.create(
            nome="Teste", marca="Unifi"
        )

        self.equipamento = Equipamento.objects.create(
            nome="Teste",
            mac="d0:21:f9:b7:7e:7d",
            localizacao="Teste",
            modelo=self.modelo_equipamento,
            empresas=self.empresas,
        )

        self.url = "/guest/s/default/?ap=d0:21:f9:b7:7e:7d&id=36:fa:23:7b:cf:ae&t=1737497811&url=http://captive.apple.com%2Fhotspot-detect.html&ssid=home"

    def test_get_landingpage_pre_campanha_none(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
