import sys
import uuid

from core.decorators import checa_limite_reenvios
from core.models import SMSEnviado
from empresas.models import Empresa
from operadora_sms.models import OperadoraSMS
from providers.sinch import Sinch
from providers.sms_market import SMSMarket
from providers.zenvia import Zenvia


def process_sinch(username, password, destinatario, mensagem, correlation_id):
    enviado = Sinch(username, password).send_message(
        destinatario, mensagem, correlation_id
    )
    return enviado


def process_zenvia(destinatario, mensagem, correlation_id):
    enviado = Zenvia().send_message(destinatario, mensagem, correlation_id)
    return enviado


def process_sms_market(destinatario, mensagem, correlation_id):
    enviado = SMSMarket().send_message(destinatario, mensagem, correlation_id)
    return enviado


@checa_limite_reenvios
def send_sms(destinatario, mensagem, token_sms, empresa, finalidade):

    company = Empresa.objects.get(id=empresa.id)
    correlation_id = None
    sms_sent = None

    if company.operadora_sms:
        correlation_id = str(uuid.uuid4())
        username = company.usuario_operadora
        password = company.senha_operadora

        provider_method_name = f"process_{company.operadora_sms.slug_name.lower()}"
        provider_method = getattr(sys.modules[__name__], provider_method_name, None)

        if provider_method:
            sms_sent = provider_method(
                username, password, destinatario, mensagem, correlation_id
            )
    else:
        provider_name = OperadoraSMS.objects.filter(default=True)
        if not provider_name:
            provider_name = OperadoraSMS.objects.first()
        provider_method_name = f"process_{provider_name.get().slug_name.lower()}"
        provider_method = getattr(sys.modules[__name__], provider_method_name, None)
        correlation_id = str(uuid.uuid4())

        if provider_method:
            sms_sent = provider_method(
                destinatario,
                mensagem,
                correlation_id,
            )

    if sms_sent:
        sms_enviado = SMSEnviado()
        sms_enviado.telefone = destinatario
        sms_enviado.token_sms = token_sms
        sms_enviado.empresas = company
        sms_enviado.sms_propose = finalidade + token_sms
        sms_enviado.correlation_id = correlation_id
        sms_enviado.save()

        return True

    return False
