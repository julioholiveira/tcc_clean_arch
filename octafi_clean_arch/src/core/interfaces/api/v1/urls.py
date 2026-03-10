"""
URLs da API v1 — Core.
Padrão RESTful; resolve P11: empresa via header X-Empresa-ID (sem URLconf param).
"""

from django.urls import path

from octafi_clean_arch.src.core.interfaces.api.v1.views.guest_auth_views import (
    GuestAuthenticateView,
    GuestAuthorizeView,
    GuestVerifyPasscodeView,
)
from octafi_clean_arch.src.core.interfaces.api.v1.views.guest_user_views import GuestUserListView
from octafi_clean_arch.src.core.interfaces.api.v1.views.sms_views import SMSSendView, SMSStatusView

app_name = "core_v1"

urlpatterns = [
    # Guest auth flow
    path("guest/authenticate/", GuestAuthenticateView.as_view(), name="guest-authenticate"),
    path("guest/verify-passcode/", GuestVerifyPasscodeView.as_view(), name="guest-verify-passcode"),
    path("guest/authorize/", GuestAuthorizeView.as_view(), name="guest-authorize"),
    path("guest/users/", GuestUserListView.as_view(), name="guest-users"),
    # SMS
    path("sms/send/", SMSSendView.as_view(), name="sms-send"),
    path("sms/status/", SMSStatusView.as_view(), name="sms-status"),
]
