from datetime import datetime

from unifi_client.unifi_client import UnifiClient

from controllers.models import Controller
from core.models import Historico
from parametros.models import Parametro


def libera_guest(mac, site_id, campanha_id, empresa, usuario=None):

    redir = "/welcome_page/"

    controller = Controller.objects.get(empresas=empresa)

    if controller is not None:
        unifi_config = {
            "host": controller.ip,
            "port": controller.port,
            "username": controller.username,
            "password": controller.password,
            "site_id": site_id,
            "udm_pro": controller.udm_pro,
        }
    else:
        raise Exception("Nenhum controller cadastrado")

    ip_visitante = "0.0.0.0"

    parametros = Parametro.objects.filter(empresas=empresa).values()

    for parametro in parametros:

        guest_timeout = parametro["guest_timeout"]
        pagina_inicial = parametro["welcome_page"]
        down_bandwidth = parametro["velocidade_down"]
        up_bandwidth = parametro["velocidade_up"]

    unifi = UnifiClient(unifi_config)

    unifi.authorize_guest(mac, guest_timeout, up_bandwidth, down_bandwidth, bytes=None)

    for cliente in unifi.list_sta():
        if "ip" in cliente:
            if cliente["mac"] == mac:
                ip_visitante = cliente["ip"]

    historico = Historico()
    historico.usuarios = usuario
    historico.campanhas = campanha_id
    historico.data_conexao = datetime.now()
    historico.mac = mac
    if ip_visitante:
        historico.ip = ip_visitante
    historico.empresas = empresa
    historico.save()

    unifi.logout()

    if pagina_inicial:
        pagina = pagina_inicial
    else:
        pagina = redir

    return pagina
