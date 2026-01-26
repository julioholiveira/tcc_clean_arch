from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.timezone import make_aware

from .models_base import BaseEmpresa


def valida_celular(value):
    if value.isnumeric():
        if value[2] == "9":
            pass
        else:
            raise ValidationError("Número de celular inválido.")
    else:
        raise ValidationError("Obrigatório valor numérico.")


class Usuario(BaseEmpresa):
    telefone = models.CharField(max_length=11)
    nome_usuario = models.CharField(max_length=150, blank=True, null=True)
    cpf_usuario = models.CharField(max_length=14, blank=True, null=True)
    criacao = models.DateTimeField(null=False, blank=False, auto_now_add=True)
    empresas = models.ForeignKey("empresas.Empresa", on_delete=models.CASCADE)

    def __str__(self):
        return self.telefone

    class Meta:
        db_table = "usuarios"


class TokenSMS(BaseEmpresa):
    telefone = models.CharField(
        "Telefone Celular",
        max_length=11,
        validators=[valida_celular],
        null=False,
        blank=False,
    )
    token = models.CharField(max_length=6)
    nome_usuario = models.CharField(max_length=150, blank=True, null=True)
    cpf_usuario = models.CharField(max_length=14, blank=True, null=True)
    reenvios = models.IntegerField(null=True, blank=False, default=0)

    def __str__(self):
        return self.token

    class Meta:
        db_table = "tokens_sms"


class Historico(BaseEmpresa):
    usuarios = models.ForeignKey(
        "Usuario", on_delete=models.CASCADE, blank=True, null=True
    )
    campanhas = models.ForeignKey(
        "campanhas.Campanha", on_delete=models.CASCADE, blank=True, null=True
    )
    data_conexao = models.DateTimeField(null=False, blank=False)
    mac = models.CharField(max_length=17, null=False, blank=False)
    ip = models.GenericIPAddressField(
        null=True, blank=False, default="127.0.0.1", protocol="IPv4"
    )

    class Meta:
        db_table = "historicos"
        permissions = (("relatorio_historico", "Pode gerar o relatorio de historicos"),)

    def get_guest_users(self, request):
        if request.user.is_superuser:
            historico = Historico.objects.all()
        else:
            historico = Historico.objects.filter(
                empresas=request.user.customuser.empresas
            )
        guests_24 = historico.filter(
            data_conexao__gte=make_aware(datetime.now() - timedelta(days=1))
        ).count()
        guests_7 = historico.filter(
            data_conexao__gte=make_aware(datetime.now() - timedelta(days=7))
        ).count()
        guests_30 = historico.filter(
            data_conexao__gte=make_aware(datetime.now() - timedelta(days=30))
        ).count()

        return {
            "guests_online_24": guests_24,
            "guests_online_7": guests_7,
            "guests_online_30": guests_30,
        }


class SMSEnviado(BaseEmpresa):
    telefone = models.CharField(
        "Telefone Celular",
        max_length=11,
        validators=[valida_celular],
        null=False,
        blank=False,
    )
    correlation_id = models.CharField(max_length=256, blank=True, null=True)
    token_sms = models.CharField(max_length=25, blank=True, null=False)
    sms_propose = models.CharField(max_length=60, blank=True, null=True)
    sent_status = models.BooleanField(default=False)
    delivered_status = models.BooleanField(default=False)
    operadora = models.CharField(max_length=100, blank=True, null=True)
    data_criacao = models.DateTimeField(null=True, blank=True, auto_now_add=True)

    class Meta:
        db_table = "sms_enviados"
        permissions = (("relatorio_envio_sms", "Pode gerar relatorio de envio de SMS"),)

    def get_sms_status(self, request, dias):

        periodo = make_aware(datetime.now() - timedelta(days=dias))

        if request.user.is_superuser:
            sms_periodo = SMSEnviado.objects.filter(created_at__gte=periodo)

        else:
            sms_periodo = SMSEnviado.objects.filter(
                empresas=request.user.customuser.empresas
            ).filter(created_at__gte=periodo)

        sms = {
            "total_sms": sms_periodo.count(),
            "sms_enviados": sms_periodo.filter(sent_status=True).count(),
            "sms_nao_enviados": sms_periodo.filter(sent_status=False).count(),
            "sms_delivered": sms_periodo.filter(delivered_status=True).count(),
            "sms_not_delivered": sms_periodo.filter(delivered_status=False).count(),
        }

        return sms
