"""Serializers para campanhas de mailing - Camada de Apresentação"""

from rest_framework import serializers


class CreateCampaignInputSerializer(serializers.Serializer):
    """Valida entrada para criação de campanha."""

    name = serializers.CharField(max_length=200)
    template_id = serializers.IntegerField()
    scheduled_for = serializers.DateTimeField(required=False, allow_null=True)


class UpdateCampaignInputSerializer(serializers.Serializer):
    """Valida entrada para atualização de campanha."""

    name = serializers.CharField(max_length=200, required=False)
    template_id = serializers.IntegerField(required=False)
    scheduled_for = serializers.DateTimeField(required=False, allow_null=True)


class CampaignOutputSerializer(serializers.Serializer):
    """Saída de criação/atualização de campanha."""

    success = serializers.BooleanField()
    message = serializers.CharField()
    campaign_id = serializers.IntegerField(allow_null=True, required=False)
    error_code = serializers.CharField(allow_null=True, required=False)


class ScheduleCampaignInputSerializer(serializers.Serializer):
    """Valida entrada para agendamento de campanha."""

    scheduled_for = serializers.DateTimeField()


class ScheduleCampaignOutputSerializer(serializers.Serializer):
    """Saída de agendamento."""

    success = serializers.BooleanField()
    message = serializers.CharField()
    scheduled_for = serializers.DateTimeField(allow_null=True, required=False)
    error_code = serializers.CharField(allow_null=True, required=False)


class SendCampaignInputSerializer(serializers.Serializer):
    """Valida entrada para envio de campanha."""

    batch_size = serializers.IntegerField(default=100, min_value=1, max_value=1000)
    delay_between_batches_seconds = serializers.IntegerField(default=1, min_value=0, max_value=60)
    correlation_id = serializers.CharField(max_length=100, required=False, allow_null=True)


class SendCampaignOutputSerializer(serializers.Serializer):
    """Saída de envio de campanha."""

    success = serializers.BooleanField()
    campaign_id = serializers.IntegerField()
    total_recipients = serializers.IntegerField()
    sent_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()
    started_at = serializers.DateTimeField()
    completed_at = serializers.DateTimeField(allow_null=True, required=False)
    error_message = serializers.CharField(allow_null=True, required=False)


class RecipientItemSerializer(serializers.Serializer):
    """Item de destinatário com sanitização de PII."""

    id = serializers.IntegerField(source="get", default=None, required=False)
    # PII: telefone mascarado
    phone = serializers.SerializerMethodField()
    status = serializers.CharField(required=False)
    sent_at = serializers.DateTimeField(required=False, allow_null=True)

    def to_representation(self, instance):
        """Suporta tanto dict quanto objetos."""
        if isinstance(instance, dict):
            rep = dict(instance)
            phone = rep.get("telefone") or rep.get("phone", "")
            phone_str = str(phone)
            if len(phone_str) > 4:
                rep["phone"] = f"{'*' * (len(phone_str) - 4)}{phone_str[-4:]}"
            else:
                rep["phone"] = phone_str
            return rep
        return super().to_representation(instance)

    def get_phone(self, obj) -> str:
        phone = getattr(obj, "phone", None) or getattr(obj, "telefone", "") or ""
        phone_str = str(phone)
        if len(phone_str) > 4:
            return f"{'*' * (len(phone_str) - 4)}{phone_str[-4:]}"
        return phone_str


class RecipientListOutputSerializer(serializers.Serializer):
    """Saída paginada de destinatários."""

    total = serializers.IntegerField()
    recipients = serializers.ListField(child=serializers.DictField())
    has_more = serializers.BooleanField()
    offset = serializers.IntegerField()
