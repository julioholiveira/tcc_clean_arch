"""
Views para autenticação de guest WiFi.
Resolve P1 (SRP): cada view tem uma única responsabilidade.
Resolve P11 (ISP): recebe empresa_id por header — sem dependência de request.
"""

import structlog
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from src.core.application.dto.guest_auth import (
    AuthenticateGuestRequest,
    AuthorizeNetworkAccessRequest,
    VerifySMSTokenRequest,
)
from src.core.domain.value_objects import CPF, CompanyId, MACAddress, PhoneNumber
from src.core.interfaces.api.v1.dependencies import (
    build_authenticate_guest_use_case,
    build_authorize_network_use_case,
    build_verify_sms_token_use_case,
)
from src.core.interfaces.api.v1.serializers.guest_serializers import (
    AuthenticateGuestInputSerializer,
    AuthenticateGuestOutputSerializer,
    AuthorizeNetworkInputSerializer,
    AuthorizeNetworkOutputSerializer,
    VerifyPasscodeInputSerializer,
    VerifyPasscodeOutputSerializer,
)

logger = structlog.get_logger(__name__)


def _resolve_empresa(request):
    """
    Resolve empresa a partir do header X-Empresa-ID.
    Lança ValueError se ausente ou inválido.
    """
    from empresas.models import Empresa  # Django ORM import — delayed to avoid circular deps

    empresa_id = request.headers.get("X-Empresa-ID")
    if not empresa_id:
        raise ValueError("Header X-Empresa-ID é obrigatório")
    try:
        return Empresa.objects.get(pk=int(empresa_id))
    except (Empresa.DoesNotExist, (ValueError, TypeError)):
        raise ValueError(f"Empresa {empresa_id} não encontrada")


class GuestAuthenticateView(APIView):
    """
    POST /api/v1/guest/authenticate/
    Inicia fluxo de autenticação: valida dados e envia token SMS.
    """

    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        try:
            empresa = _resolve_empresa(request)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AuthenticateGuestInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        data = serializer.validated_data

        try:
            auth_request = AuthenticateGuestRequest(
                company_id=CompanyId(empresa.id),
                mac_address=MACAddress(data["mac_address"]),
                phone=PhoneNumber(data["phone"]),
                site_id=data["site_id"],
                campaign_id=data.get("campaign_id"),
                name=data.get("name"),
                cpf=CPF(data["cpf"]) if data.get("cpf") else None,
                correlation_id=data.get("correlation_id"),
            )
        except (ValueError, TypeError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        use_case = build_authenticate_guest_use_case(empresa)
        result = use_case.execute(auth_request)

        logger.info(
            "guest_authenticate",
            empresa_id=empresa.id,
            success=result.success,
            # PII: nunca logar phone diretamente
        )

        http_status = status.HTTP_200_OK if result.success else status.HTTP_400_BAD_REQUEST
        return Response(AuthenticateGuestOutputSerializer(result).data, status=http_status)


class GuestVerifyPasscodeView(APIView):
    """
    POST /api/v1/guest/verify-passcode/
    Verifica o token SMS e libera rede se válido.
    """

    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        try:
            empresa = _resolve_empresa(request)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = VerifyPasscodeInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        data = serializer.validated_data

        try:
            verify_request = VerifySMSTokenRequest(
                company_id=CompanyId(empresa.id),
                phone=PhoneNumber(data["phone"]),
                token_value=data["token"],
                mac_address=MACAddress(data["mac_address"]),
                correlation_id=data.get("correlation_id"),
            )
        except (ValueError, TypeError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        use_case = build_verify_sms_token_use_case(empresa)
        result = use_case.execute(verify_request)

        logger.info(
            "guest_verify_passcode",
            empresa_id=empresa.id,
            success=result.success,
            network_authorized=result.network_authorized,
        )

        http_status = status.HTTP_200_OK if result.success else status.HTTP_400_BAD_REQUEST
        return Response(VerifyPasscodeOutputSerializer(result).data, status=http_status)


class GuestAuthorizeView(APIView):
    """
    POST /api/v1/guest/authorize/
    Autoriza acesso à rede para um dispositivo.
    """

    def post(self, request):
        try:
            empresa = _resolve_empresa(request)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AuthorizeNetworkInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        data = serializer.validated_data

        try:
            auth_request = AuthorizeNetworkAccessRequest(
                company_id=CompanyId(empresa.id),
                mac_address=MACAddress(data["mac_address"]),
                phone=PhoneNumber(data["phone"]),
                duration_minutes=data.get("duration_minutes", 60),
                bandwidth_limit_kbps=data.get("bandwidth_limit_kbps"),
            )
        except (ValueError, TypeError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        use_case = build_authorize_network_use_case(empresa)
        result = use_case.execute(auth_request)

        logger.info(
            "guest_authorize",
            empresa_id=empresa.id,
            success=result.success,
        )

        http_status = status.HTTP_200_OK if result.success else status.HTTP_400_BAD_REQUEST
        return Response(AuthorizeNetworkOutputSerializer(result).data, status=http_status)
