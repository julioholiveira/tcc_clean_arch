"""Serializers para operações de SMS - Camada de Apresentação"""

import re

from rest_framework import serializers


def _validate_mobile_phone(value: str) -> str:
    """Garante que o telefone informado pelo usuário é um celular moderno (3º dígito = 9)."""
    cleaned = re.sub(r"\D", "", value)
    if len(cleaned) == 11 and cleaned[2] != "9":
        raise serializers.ValidationError(f"Mobile number must start with 9 after DDD: {cleaned}")
    return value


class SendSMSInputSerializer(serializers.Serializer):
    """Valida entrada para envio de SMS."""

    phone = serializers.CharField(max_length=20, help_text="Telefone no formato E.164")
    message = serializers.CharField(max_length=160)

    def validate_phone(self, value):
        return _validate_mobile_phone(value)

    provider_slug = serializers.ChoiceField(
        choices=["sinch", "zenvia", "sms_market"],
        required=False,
        allow_null=True,
        help_text="Provedor; None = padrão da empresa",
    )
    correlation_id = serializers.CharField(max_length=100, required=False, allow_null=True)


class SendSMSOutputSerializer(serializers.Serializer):
    """Saída do envio de SMS."""

    success = serializers.BooleanField()
    provider_name = serializers.CharField()
    provider_message_id = serializers.CharField(allow_null=True, required=False)
    sent_at = serializers.DateTimeField(allow_null=True, required=False)
    error_message = serializers.CharField(allow_null=True, required=False)


class SMSStatusItemSerializer(serializers.Serializer):
    """Item de status com sanitização de PII."""

    delivery_id = serializers.IntegerField()
    # Telefone mascarado
    phone = serializers.SerializerMethodField()
    message = serializers.CharField()
    status = serializers.CharField(source="status.value")
    provider = serializers.CharField()
    sent_at = serializers.DateTimeField(allow_null=True)
    delivered_at = serializers.DateTimeField(allow_null=True)
    error_message = serializers.CharField(allow_null=True)

    def get_phone(self, obj) -> str:
        """Mascara os primeiros dígitos do telefone para sanitização de PII."""
        phone_str = str(getattr(obj, "phone", "") or "")
        if len(phone_str) > 4:
            return f"{'*' * (len(phone_str) - 4)}{phone_str[-4:]}"
        return phone_str


class SMSStatusQuerySerializer(serializers.Serializer):
    """Parâmetros de query para filtro de status SMS."""

    phone = serializers.CharField(max_length=20, required=False, allow_null=True)
    delivery_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_phone(self, value):
        if value is None:
            return value
        return _validate_mobile_phone(value)

    date_from = serializers.DateTimeField(required=False, allow_null=True)
    date_to = serializers.DateTimeField(required=False, allow_null=True)
    limit = serializers.IntegerField(default=100, min_value=1, max_value=500)
    offset = serializers.IntegerField(default=0, min_value=0)


class SMSStatusOutputSerializer(serializers.Serializer):
    """Saída paginada de status SMS."""

    total = serializers.IntegerField()
    items = SMSStatusItemSerializer(many=True)
    has_more = serializers.BooleanField()
