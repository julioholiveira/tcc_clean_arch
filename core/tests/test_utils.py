from django.core.exceptions import ValidationError
from django.test import TestCase

from core.forms import validate_phone
from core.utils import add_mask, get_provider
from empresas.models import Empresa
from operadora_sms.models import OperadoraSMS


class UtilsTestCase(TestCase):
    def setUp(self):

        self.operadora = OperadoraSMS.objects.create(
            name="Sinch",
            slug_name="sinch",
        )

        self.empresa = Empresa.objects.create(
            razao_social="Teste",
            site_id="default",
            operadora_sms=self.operadora,
            usuario_operadora="admin",
            senha_operadora="admin",
        )

    def test_get_provider(self):
        result = get_provider(self.empresa)
        self.assertEqual(result, "sinch")

    def test_validate_phone(self):
        telefone_teste = "01599791520"

        with self.assertRaises(ValidationError):
            validate_phone(telefone_teste)

    def test_add_mask(self):
        element = "111.111.111-12"

        result = add_mask(element, 3)

        self.assertEqual(result, "***********-12")

    def test_add_mask_without_start_parameter(self):
        element = "JOAO SOUZA DA SILVA"

        result = add_mask(element)

        self.assertEqual(result, "***************ILVA")

    def test_add_mask_element_is_none(self):
        element = None

        result = add_mask(element)

        self.assertIsNone(result)
