import json
import uuid
from unittest.mock import patch

from django.test import TestCase

from core.models import SMSEnviado, TokenSMS
from core.services.send_messages import send_sms
from empresas.models import Empresa
from operadora_sms.models import OperadoraSMS


class SendSmsCompanyHasProviderTestCase(TestCase):
    def setUp(self):
        self.operadora = OperadoraSMS.objects.create(
            name="Sinch",
            slug_name="sinch",
        )
        self.empresa = Empresa.objects.create(
            razao_social="Teste",
            operadora_sms=self.operadora,
            usuario_operadora="admin",
            senha_operadora="admin",
        )

        self.token_sms = TokenSMS.objects.create(
            telefone="15900001111", empresas=self.empresa, token="abcdef"
        )

    @patch("providers.sinch.Sinch.send_message")
    def test_send_sms_successful(self, send_message_mock):
        finalidade = "Teste"
        destinatario = "15900001111"
        token_sms = "123456"
        mensagem = "Teste de mensagem"

        send_message_mock.return_value = True

        result = send_sms(destinatario, mensagem, token_sms, self.empresa, finalidade)
        sms_enviado = SMSEnviado.objects.filter(token_sms=token_sms)

        self.assertTrue(sms_enviado.exists())
        self.assertTrue(result)

    @patch("providers.sinch.Sinch.send_message")
    def test_send_sms_limite_reenvios_atingido(self, send_message_mock):
        TokenSMS.objects.filter(id=self.token_sms.id).update(reenvios=4)
        finalidade = "Teste"
        destinatario = "15900001111"
        token_sms = "abcdef"
        mensagem = "Teste de mensagem"

        send_message_mock.return_value = False

        result = send_sms(destinatario, mensagem, token_sms, self.empresa, finalidade)
        sms_enviado = SMSEnviado.objects.filter(token_sms=token_sms)

        self.assertFalse(sms_enviado.exists())
        self.assertFalse(result)


class SendSmsUsingDefaultProviderTestCase(TestCase):

    def setUp(self):

        self.operadora = OperadoraSMS.objects.create(
            name="SMS Market",
            slug_name="sms_market",
            username="admin",
            password="admin",
            default=True,
        )

        self.empresa = Empresa.objects.create(
            razao_social="Teste",
        )

        self.token_sms = TokenSMS.objects.create(
            telefone="15900001111", empresas=self.empresa, token="123456"
        )

    @patch("providers.sms_market.SMSMarket.send_message")
    def test_send_sms_successful(self, send_message_mock):
        finalidade = "Teste"
        destinatario = "15900001111"
        token_sms = "432156"
        mensagem = "Teste de mensagem"

        send_message_mock.return_value = True

        result = send_sms(destinatario, mensagem, token_sms, self.empresa, finalidade)
        sms_enviado = SMSEnviado.objects.filter(token_sms=token_sms)

        self.assertTrue(sms_enviado.exists())
        self.assertTrue(result)

    @patch("providers.sms_market.SMSMarket.send_message")
    def test_send_sms_limite_reenvios_atingido(self, send_message_mock):
        TokenSMS.objects.filter(id=self.token_sms.id).update(reenvios=4)
        finalidade = "Teste"
        destinatario = "15900001111"
        token_sms = "123456"
        mensagem = "Teste de mensagem"

        send_message_mock.return_value = False

        result = send_sms(destinatario, mensagem, token_sms, self.empresa, finalidade)
        sms_enviado = SMSEnviado.objects.filter(token_sms=token_sms)

        self.assertFalse(sms_enviado.exists())

        self.assertFalse(result)
