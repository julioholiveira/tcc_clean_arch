import uuid
from unittest.mock import patch

from django.test import TestCase

from core.models import SMSEnviado, TokenSMS
from core.tasks import atualiza_sms_status, limpa_tokens_reenviados
from empresas.models import Empresa
from operadora_sms.models import OperadoraSMS
from parametros.models import Parametro


# @tag("no_test")
class TaskStatusTestCase(TestCase):
    """Testa as tasks do Celery."""

    def setUp(self):
        """Cria os objetos necessários para os testes."""

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

        self.parametros = Parametro.objects.create(
            guest_timeout=10, empresas=self.empresa
        )

        tokens = [
            TokenSMS(
                telefone="15997915209",
                empresas=self.empresa,
                token="999999",
                reenvios=4,
            ),
            TokenSMS(
                telefone="15991587851",
                empresas=self.empresa,
                token="999999",
                reenvios=4,
            ),
        ]

        TokenSMS.objects.bulk_create(tokens)

    def send_sms_for_testing(self):
        finalidade = "Teste"
        destinatario = "15997915209"
        token_sms = "999999"
        mensagem = "Teste de mensagem"
        correlation_id = str(uuid.uuid4())

        SMSEnviado.objects.create(
            telefone=destinatario,
            empresas=self.empresa,
            token_sms=token_sms,
            sms_propose=finalidade + token_sms,
            correlation_id=correlation_id,
            operadora="sinch",
        )

        return True

    def test_limpa_tokens_reenviados(self):
        """Testa a task limpa_tokens_reenviados."""
        limpa_tokens_reenviados()
        self.assertFalse(TokenSMS.objects.filter(reenvios__gte=3).exists())

    @patch("providers.sinch.Sinch.update_sms_status")
    def test_atualiza_status_sms(self, update_sms_status_mock):
        """Testa a task atualiza_sms_status."""
        correlation_id_1 = str(uuid.uuid4())
        correlation_id_2 = str(uuid.uuid4())

        sms_enviados = [
            SMSEnviado(
                telefone="15900001111",
                empresas=self.empresa,
                token_sms="999999",
                sms_propose="Teste 999999",
                correlation_id=correlation_id_1,
            ),
            SMSEnviado(
                telefone="15900002222",
                empresas=self.empresa,
                token_sms="111111",
                sms_propose="Teste 111111",
                correlation_id=correlation_id_2,
            ),
        ]

        SMSEnviado.objects.bulk_create(sms_enviados)

        update_sms_status_mock.return_value = [
            {
                "correlation_id": correlation_id_1,
                "sent_status": True,
                "operadora": "TIM",
            },
            {
                "correlation_id": correlation_id_2,
                "sent_status": True,
                "operadora": "VIVO",
            },
        ]

        atualiza_sms_status()

        sms_enviado_1111 = SMSEnviado.objects.get(telefone="15900001111")
        sms_enviado_2222 = SMSEnviado.objects.get(telefone="15900002222")

        self.assertTrue(sms_enviado_1111.sent_status)
        self.assertTrue(sms_enviado_2222.sent_status)

    def test_atualiza_status_sms_não_envia_sms(self):
        """Testa a task atualiza_sms_status quando a empresa não envia SMS."""
        Empresa.objects.filter(id=self.empresa.id).update(envia_sms=False)

        result = atualiza_sms_status()

        self.assertIsNone(result)
