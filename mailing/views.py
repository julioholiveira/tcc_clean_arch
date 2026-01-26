# -*- encoding: utf-8 -*-

from datetime import datetime
from unicodedata import normalize

import random
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse


from core.models import Usuario, Historico
from core.services.send_messages import send_sms
from mailing.forms import MailingForm, HistoricoFiltroForm
from mailing.models import Mailing, ResultadoMailing


@permission_required("mailing.lista_mailings", raise_exception=True)
@login_required(login_url="login")
def lista_mailings(request):
    administrador = False
    if request.user.is_superuser:
        administrador = True
        mailings = Mailing.objects.all().order_by("data_mailing", "nome_mailing")
    else:
        mailings = Mailing.objects.filter(
            empresas=request.user.customuser.empresas
        ).order_by("data_mailing", "nome_mailing")
    return render(
        request,
        "mailing/lista_mailings.html",
        {"mailings": mailings, "adminstrador": administrador},
    )


@permission_required("mailing.adiciona_mailing", raise_exception=True)
@login_required(login_url="login")
def cadastro_mailing(request):
    if request.method == "POST":
        form = MailingForm(request.POST, request.FILES)
        if form.is_valid():
            mailing = form.save(commit=False)
            mailing.empresas = request.user.customuser.empresas
            mailing.save()
            return HttpResponseRedirect(reverse("mailing:lista_mailings"))
    else:
        form = MailingForm()
    return render(request, "mailing/cadastro_mailing.html", {"form": form})


@permission_required("mailing.edita_mailing", raise_exception=True)
@login_required(login_url="login")
def edita_mailing(request, pk):
    mailing_id = get_object_or_404(Mailing, pk=pk)
    if request.method == "POST":
        form = MailingForm(request.POST, request.FILES, instance=mailing_id)
        if form.is_valid():
            mailing = form.save(commit=False)
            if request.user.is_superuser:
                mailing_id = get_object_or_404(Mailing, pk=pk)
                mailing.empresas = mailing_id.empresas
            else:
                mailing.empresas = request.user.customuser.empresas
            mailing.save()
            return HttpResponseRedirect(reverse("mailing:lista_mailings"))
    else:
        form = MailingForm(instance=mailing_id)
    return render(request, "mailing/edita_mailing.html", {"form": form})


@permission_required("mailing.remove_mailing", raise_exception=True)
@login_required(login_url="login")
def remove_mailing(request, pk):
    form = get_object_or_404(Mailing, pk=pk)
    if request.method == "POST":
        form.delete()
        return HttpResponseRedirect(reverse("mailing:lista_mailings"))
    return render(request, "mailing/remove_mailing.html", {"form": form})


@permission_required("mailing.filtrar_destinatarios", raise_exception=True)
@login_required(login_url="login")
def filtrar_destinatarios(request, mailing_id):
    mailing_choice = mailing_id

    form = HistoricoFiltroForm()

    return render(
        request,
        "mailing/filtra_destinatarios.html",
        {"form": form, "mailing_choice": mailing_choice},
    )


@permission_required("mailing.selecionar_destinatarios", raise_exception=True)
@login_required(login_url="login")
def selecionar_destinatarios(request, mailing_id):
    form = HistoricoFiltroForm(request.POST or None)

    if request.method == "POST":

        if form.is_valid():

            if form.cleaned_data["data_inicial"] and form.cleaned_data["data_final"]:

                data_inicial = datetime.combine(
                    form.cleaned_data["data_inicial"], datetime.min.time()
                )
                data_final = datetime.combine(
                    form.cleaned_data["data_final"], datetime.max.time()
                )

                telefones = (
                    Historico.objects.filter(data_conexao__gte=data_inicial)
                    .filter(data_conexao__lte=data_final)
                    .filter(empresas=request.user.customuser.empresas)
                    .values("usuarios__telefone", "usuarios")
                    .distinct("usuarios")
                    .order_by("-usuarios")
                )
            else:
                telefones = (
                    Historico.objects.filter(empresas=request.user.customuser.empresas)
                    .values("usuarios__telefone", "usuarios")
                    .distinct("usuarios")
                    .order_by("-usuarios")
                )

            quantidade_telefones = len(telefones)

            return render(
                request,
                "mailing/selecionar_destinatarios.html",
                {
                    "telefones": telefones,
                    "quantidade_telefones": quantidade_telefones,
                    "mailing_id": mailing_id,
                },
            )

    form = HistoricoFiltroForm()
    return render(
        request,
        "mailing/filtra_destinatarios.html",
        {"form": form, "mailing_id": mailing_id},
    )


@permission_required("mailing.enviar_mailing", raise_exception=True)
@login_required(login_url="login")
def enviar_mailing(request, mailing_id):
    mailing = Mailing.objects.get(id=mailing_id)

    if request.method == "POST":

        destinatarios = request.POST.getlist("destinatarios")

        texto_mensagem = (
            normalize("NFKD", mailing.texto_mensagem)
            .encode("ASCII", "ignore")
            .decode("ASCII")
        )

        resultado_envio = []

        for destinatario in destinatarios:
            token_sms = "".join(random.choice("0123456789") for i in range(6))

            telefone_destinatario = Usuario.objects.get(id=destinatario).telefone

            empresas = request.user.customuser.empresas

            finalidade = mailing.nome_mailing + " "

            send_sms(telefone_destinatario, texto_mensagem, token_sms, empresas, finalidade)

            resultado_mailing = ResultadoMailing()
            resultado_mailing.usuarios = Usuario.objects.get(id=destinatario)
            resultado_mailing.mailings = mailing
            resultado_mailing.codigo_sms = token_sms
            resultado_mailing.empresas = request.user.customuser.empresas
            resultado_mailing.save()

            resultado_envio.append(resultado_mailing)

        return render(
            request,
            "mailing/processamento_mailing.html",
            {"resultado_envio": resultado_envio},
        )

    else:
        destinatarios = request.GET.getlist("destinatarios")
        list_destinatarios = []
        for destinatario in destinatarios:
            usuario = Usuario.objects.get(id=destinatario)
            list_destinatarios.append({"id": usuario.id, "telefone": usuario.telefone})

        return render(
            request,
            "mailing/enviar_mailing.html",
            {"destinatarios": list_destinatarios, "mailing": mailing},
        )
