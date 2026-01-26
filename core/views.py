from datetime import date

import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render

from campanhas.models import Campanha
from core.forms import CpfForm, LoginForm, PasscodeForm, TelefoneForm
from core.models import TokenSMS, Usuario
from core.services.libera_guest import libera_guest
from core.services.send_messages import send_sms
from core.utils import (
    add_mask,
    checa_token_sms,
    get_nome_cpf_cliente,
    get_template,
    verifica_limite_conexoes,
)
from empresas.models import Empresa
from equipamentos.models import Equipamento
from octafi import settings
from parametros.models import Parametro
from utils.logger import configure_logger

logger = configure_logger()


def hotsite(request):
    return render(request, "core/hotsite.html")


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():

            recaptcha_response = request.POST.get("g-recaptcha-response")

            data = {
                "secret": settings.RECAPTCHA_SECRET_KEY,
                "response": recaptcha_response,
            }

            response = requests.post(
                "https://www.google.com/recaptcha/api/siteverify", data=data
            )

            result_captcha = response.json()

            username = request.POST["username"]
            password = request.POST["password"]

            user = authenticate(username=username, password=password)

            if user and result_captcha.get("success"):  # Login funcionou
                login(request, user)
                return redirect("dashboard")

            messages.error(request, "Usuário ou senha incorreto.")

    else:
        form = LoginForm()

    context = {"form": form, "site_key": settings.RECAPTCHA_SITE_KEY}

    return render(
        request,
        "core/login.html",
        context,
    )


def logout_view(request):
    logout(request)
    return redirect("/")


def landingpage_guest_pre(request, site_id):
    mac_ap = request.GET.get("ap")
    user_mac = request.GET.get("id")

    equipamento = Equipamento.objects.get(mac=mac_ap)

    campanha_ativa = (
        Campanha.objects.filter(empresas=equipamento.empresas.id)
        .filter(inicio_campanha__lte=date.today())
        .filter(final_campanha__gte=date.today())
        .order_by("inicio_campanha")
        .values()
        .first()
    )

    try:
        campanha_id = campanha_ativa.get("id")
    except AttributeError:
        campanha_id = None

    if campanha_ativa:

        if campanha_ativa.get("pre_login_mobile") or campanha_ativa.get(
            "pre_login_desktop"
        ):

            ua_string = str(request.META["HTTP_USER_AGENT"])

            tempo = 0

            if "Mobile" in ua_string:
                imagem_pre = campanha_ativa.get("pre_login_mobile")
                if imagem_pre:
                    tempo = campanha_ativa.get("tempo_pre_login_mobile")
            else:
                imagem_pre = campanha_ativa.get("pre_login_desktop")
                if imagem_pre:
                    tempo = campanha_ativa.get("tempo_pre_login_desktop")

            return render(
                request,
                "core/landingpage_guest_pre.html",
                {
                    "mac": user_mac,
                    "site_id": site_id,
                    "campanha_id": campanha_id,
                    "empresa": equipamento.empresas.id,
                    "imagem": imagem_pre,
                    "tempo": tempo,
                },
            )

    return render(
        request,
        "core/landingpage_guest_pre.html",
        {
            "mac": user_mac,
            "site_id": site_id,
            "campanha_id": campanha_id,
            "empresa": equipamento.empresas.id,
        },
    )


def landingpage_guest(request, mac, site_id, campanha_id, empresa):

    parametros = Parametro.objects.filter(empresas=empresa)

    empresa = Empresa.objects.get(id=empresa)

    envia_sms = empresa.envia_sms

    integracao_raro = empresa.integracao_raro

    template_name = get_template(integracao_raro)

    try:
        campanha = Campanha.objects.get(id=campanha_id)
    except (ObjectDoesNotExist, ValueError):
        campanha = None

    limite_conexoes = parametros.get().limite_conexoes
    limite_conexoes_excedido = False

    if limite_conexoes > 0:
        limite_conexoes_excedido = verifica_limite_conexoes(
            mac, empresa, limite_conexoes
        )

    if request.method == "POST":

        usuario = None

        if envia_sms:

            form = (
                CpfForm(request.POST) if integracao_raro else TelefoneForm(request.POST)
            )

            if form.is_valid():

                cpf_cliente = None
                nome_cliente = None

                telefone = form.cleaned_data.get("telefone")

                logger.info(f"Telefone informado: {add_mask(telefone)}")

                try:
                    # Verifica se o usuário já está no banco de dados
                    usuario = Usuario.objects.filter(telefone=telefone).filter(
                        empresas=empresa
                    )
                except ObjectDoesNotExist:
                    usuario = None

                # Usuário não existe no sistema
                if not usuario:

                    if integracao_raro:
                        cpf_informado = form.cleaned_data.get("cpf_usuario")

                        logger.info(f"CPF informado: {add_mask(cpf_informado)}")

                        nome_cliente, cpf_cliente = get_nome_cpf_cliente(
                            cpf_informado, empresa.id
                        )

                    # Verifica se o token_sms existe no banco ou cria um novo
                    token_sms = checa_token_sms(
                        telefone, nome_cliente, cpf_cliente, empresa
                    )

                    mensagem = (
                        "Seja bem-vindo ao Octafi! Codigo para acesso: {}".format(
                            token_sms
                        )
                    )

                    finalidade = "Codigo Acesso - "

                    sms_enviado = send_sms(
                        telefone, mensagem, token_sms, empresa, finalidade
                    )

                    if sms_enviado:
                        return render(
                            request,
                            "core/landingpage_passcode.html",
                            {
                                "site_id": site_id,
                                "telefone": telefone,
                                "campanha_id": campanha_id,
                                "mac": mac,
                                "empresa": empresa.id,
                            },
                        )
                    else:
                        messages.error(
                            request,
                            "Não foi possível enviar SMS. Por favor, tente novamente mais tarde.",
                        )

                        return render(
                            request,
                            template_name,
                            {"form": form, "envia_sms": envia_sms},
                        )

                # Usuário existe no sistema
                else:
                    if integracao_raro:

                        cpf_informado = form.cleaned_data.get("cpf_usuario")

                        logger.info(f"CPF informado: {add_mask(cpf_informado)}")

                        nome_cliente, cpf_cliente = get_nome_cpf_cliente(
                            cpf_informado, empresa.id
                        )

                        if usuario.get().cpf_usuario != cpf_cliente:
                            usuario.update(cpf_usuario=cpf_cliente)

                        if usuario.get().nome_usuario != nome_cliente:
                            usuario.update(nome_usuario=nome_cliente)

                    usuario = usuario.get()
            else:
                return render(
                    request,
                    template_name,
                    {"form": form, "envia_sms": envia_sms},
                )

        pagina = libera_guest(mac, site_id, campanha, empresa, usuario)
        return redirect("landingpage_guest_pos", pagina=pagina, empresa=empresa.id)

    if limite_conexoes_excedido:
        messages.error(request, "Sua quantidade de conexões diárias expirou.")

    return render(
        request,
        template_name,
        {"envia_sms": envia_sms},
    )


def landingpage_passcode(request):

    if request.method == "POST":

        form = PasscodeForm(request.POST)

        site_id = request.POST["site_id"]
        telefone = request.POST["telefone"]
        empresa = request.POST["empresa"]
        campanha_id = request.POST["campanha_id"]
        mac = request.POST["mac"]

        empresa = Empresa.objects.get(id=empresa)

        integracao_raro = empresa.integracao_raro

        if form.is_valid():

            passcode = form.cleaned_data.get("passcode")

            try:
                campanha = Campanha.objects.get(id=campanha_id)
            except (ObjectDoesNotExist, ValueError):
                campanha = None

            token_sms = TokenSMS.objects.filter(telefone=telefone).filter(
                token=passcode
            )

            if not token_sms.exists():
                messages.error(request, "Código inválido.")
                return render(
                    request,
                    "core/landingpage_passcode.html",
                    {
                        "form": form,
                        "telefone": telefone,
                        "empresa": empresa.id,
                        "site_id": site_id,
                        "mac": mac,
                        "campanha_id": campanha_id,
                    },
                )
            if integracao_raro:
                usuario, created = Usuario.objects.update_or_create(
                    cpf_usuario=token_sms.get().cpf_usuario,
                    empresas=empresa,
                    defaults={"telefone": telefone},
                    create_defaults={
                        "telefone": telefone,
                        "cpf_usuario": token_sms.get().cpf_usuario,
                        "nome_usuario": token_sms.get().nome_usuario,
                        "empresas": empresa,
                    },
                )

            else:
                usuario = Usuario.objects.create(
                    telefone=telefone,
                    cpf_usuario=token_sms.get().cpf_usuario,
                    nome_usuario=token_sms.get().nome_usuario,
                    empresas=empresa,
                )

            # remove token
            token_sms.delete()

            pagina = libera_guest(mac, site_id, campanha, empresa, usuario)

            return redirect("landingpage_guest_pos", pagina=pagina, empresa=empresa.id)

        else:
            return render(
                request,
                "core/landingpage_passcode.html",
                {
                    "form": form,
                    "telefone": telefone,
                    "empresa": empresa.id,
                    "site_id": site_id,
                    "mac": mac,
                    "campanha_id": campanha_id,
                },
            )

    else:
        form = PasscodeForm()
        site_id = request.GET["site_id"]
        telefone = request.GET["telefone"]
        empresa = request.GET["empresa"]
        campanha_id = request.GET["campanha_id"]
        mac = request.GET["mac"]

        empresa = Empresa.objects.get(id=empresa)

        return render(
            request,
            "core/landingpage_passcode.html",
            {
                "form": form,
                "telefone": telefone,
                "empresa": empresa.id,
                "site_id": site_id,
                "mac": mac,
                "campanha_id": campanha_id,
            },
        )


def landingpage_guest_pos(request, pagina, empresa):
    empresa = Empresa.objects.get(id=empresa)

    campanha_ativa = (
        Campanha.objects.filter(empresas=empresa)
        .filter(inicio_campanha__lte=date.today())
        .filter(final_campanha__gte=date.today())
        .order_by("inicio_campanha")
        .values()
        .first()
    )

    if campanha_ativa:

        if campanha_ativa.get("pos_login_mobile") or campanha_ativa.get(
            "pos_login_desktop"
        ):

            ua_string = str(request.META["HTTP_USER_AGENT"])

            tempo = 0

            if "Mobile" in ua_string:
                imagem_pos = campanha_ativa.get("pos_login_mobile")
                if imagem_pos:
                    tempo = campanha_ativa.get("tempo_pos_login_mobile")
            else:
                imagem_pos = campanha_ativa.get("pos_login_desktop")
                if imagem_pos:
                    tempo = campanha_ativa.get("tempo_pos_login_desktop")

            return render(
                request,
                "core/landingpage_guest_pos.html",
                {"imagem": imagem_pos, "pagina": pagina, "tempo": tempo * 1000},
            )

    return redirect(pagina)


def welcome_page(request):
    return render(request, "core/welcome_page.html")
