"""Serializers para autenticação de guest - Camada de Apresentação"""

import re

from rest_framework import serializers


def _validate_mobile_phone(value: str) -> str:
    """Garante que o telefone informado pelo usuário é um celular moderno (3º dígito = 9)."""
    cleaned = re.sub(r"\D", "", value)
    if len(cleaned) == 11 and cleaned[2] != "9":
        raise serializers.ValidationError(f"Mobile number must start with 9 after DDD: {cleaned}")
    return value


class AuthenticateGuestInputSerializer(serializers.Serializer):
    """Valida entrada do fluxo de autenticação de guest."""

    mac_address = serializers.CharField(max_length=17, help_text="MAC do dispositivo, ex: AA:BB:CC:DD:EE:FF")
    phone = serializers.CharField(max_length=20, help_text="Telefone no formato E.164")
    site_id = serializers.CharField(max_length=100)

    def validate_phone(self, value):
        return _validate_mobile_phone(value)

    campaign_id = serializers.IntegerField(required=False, allow_null=True)
    name = serializers.CharField(max_length=200, required=False, allow_null=True, allow_blank=True)
    cpf = serializers.CharField(max_length=14, required=False, allow_null=True, allow_blank=True)
    correlation_id = serializers.CharField(max_length=100, required=False, allow_null=True)


class AuthenticateGuestOutputSerializer(serializers.Serializer):
    """Saída do fluxo de autenticação de guest."""

    success = serializers.BooleanField()
    token_sent = serializers.BooleanField()
    message = serializers.CharField()
    requires_verification = serializers.BooleanField()
    user_id = serializers.IntegerField(allow_null=True, required=False)
    error_code = serializers.CharField(allow_null=True, required=False)


class VerifyPasscodeInputSerializer(serializers.Serializer):
    """Valida entrada para verificação de passcode SMS."""

    phone = serializers.CharField(max_length=20)
    token = serializers.CharField(max_length=10)

    def validate_phone(self, value):
        return _validate_mobile_phone(value)

    mac_address = serializers.CharField(max_length=17)
    correlation_id = serializers.CharField(max_length=100, required=False, allow_null=True)


class VerifyPasscodeOutputSerializer(serializers.Serializer):
    """Saída da verificação de passcode."""

    success = serializers.BooleanField()
    message = serializers.CharField()
    network_authorized = serializers.BooleanField()
    session_id = serializers.CharField(allow_null=True, required=False)
    error_code = serializers.CharField(allow_null=True, required=False)


class AuthorizeNetworkInputSerializer(serializers.Serializer):
    """Valida entrada para autorização de rede."""

    mac_address = serializers.CharField(max_length=17)
    phone = serializers.CharField(max_length=20)
    duration_minutes = serializers.IntegerField(default=60, min_value=1, max_value=1440)

    def validate_phone(self, value):
        return _validate_mobile_phone(value)

    bandwidth_limit_kbps = serializers.IntegerField(required=False, allow_null=True, min_value=0)


class AuthorizeNetworkOutputSerializer(serializers.Serializer):
    """Saída da autorização de rede."""

    success = serializers.BooleanField()
    message = serializers.CharField()
    session_id = serializers.CharField(allow_null=True, required=False)
    duration_minutes = serializers.IntegerField()
    error_code = serializers.CharField(allow_null=True, required=False)


class GuestUserItemSerializer(serializers.Serializer):
    """Serializer para item de usuário guest com sanitização de PII."""

    id = serializers.IntegerField()
    # Phone mascarado - resolve PII
    phone = serializers.SerializerMethodField()
    name = serializers.CharField(allow_null=True)
    mac_address = serializers.CharField()
    first_seen = serializers.DateTimeField(allow_null=True)
    last_seen = serializers.DateTimeField(allow_null=True)

    def get_phone(self, obj) -> str:
        """Mascara os primeiros dígitos do telefone."""
        phone = getattr(obj, "phone", None) or ""
        if hasattr(phone, "masked"):
            return phone.masked()
        phone_str = str(phone)
        if len(phone_str) > 4:
            return f"{'*' * (len(phone_str) - 4)}{phone_str[-4:]}"
        return phone_str


class GuestUserListOutputSerializer(serializers.Serializer):
    """Saída paginada da lista de usuários guest."""

    total = serializers.IntegerField()
    users = GuestUserItemSerializer(many=True)
    has_more = serializers.BooleanField()
