import os
import random
from datetime import date

from core.models import Historico, TokenSMS
from octafi import settings
from raro.raro import Raro
from utils.logger import configure_logger

logger = configure_logger()


def add_mask(element: str, start: int = 4):
    if not element:
        return
    return element[-start:].rjust(len(element), "*")


def handle_uploaded_file(f, index):
    directory = settings.MEDIA_ROOT + "/" + str(index) + "/"
    if not dir_exists(directory):
        os.makedirs(directory)

    with open(directory + f.name, "wb+") as destination:
        for chunk in f.chunks():
            destination.write(chunk)


def dir_exists(directory):
    if os.path.exists(directory):
        return os.listdir(directory)
    else:
        return False


def verifica_limite_conexoes(mac, empresa, limite_conexoes):
    numero_conexoes = (
        Historico.objects.filter(data_conexao__date=date.today())
        .filter(mac__exact=mac)
        .filter(empresas=empresa)
        .count()
    )
    return numero_conexoes >= limite_conexoes


def checa_token_sms(telefone, nome_cliente, cpf_cliente, empresa):
    token_sms = "".join(random.choice("0123456789") for i in range(6))

    token, created = TokenSMS.objects.get_or_create(
        telefone=telefone,
        empresas=empresa,
        defaults={
            "token": token_sms,
            "nome_usuario": nome_cliente,
            "cpf_usuario": cpf_cliente,
        },
    )

    if not created:
        TokenSMS.objects.filter(id=token.id).update(reenvios=token.reenvios + 1)
        token_sms = token.token

    return token_sms


def get_template(integracao_raro):
    return "core/landingpage_raro.html" if integracao_raro else "core/landingpage.html"


def get_provider(empresa):
    return empresa.operadora_sms.slug_name.lower()


def get_nome_cpf_cliente(cpf_informado, empresa):

    raro = Raro(cpf_informado, empresa)
    nome_cliente, cpf_cliente = raro.consulta_cliente()

    if cpf_cliente is None:
        cpf_cliente = cpf_informado

    logger.info(
        f"Raro API: Nome: {add_mask(nome_cliente, 10)}, CPF: {add_mask(cpf_cliente)}"
    )

    return (nome_cliente, cpf_cliente)
