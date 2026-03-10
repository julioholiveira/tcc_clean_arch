"""
URLs da API v1 — Mailing.
"""

from django.urls import path

from src.mailing.interfaces.api.v1.views.campaign_views import (
    CampaignDetailView,
    CampaignListCreateView,
    CampaignScheduleView,
    CampaignSendView,
)
from src.mailing.interfaces.api.v1.views.recipient_views import RecipientListView

app_name = "mailing_v1"

urlpatterns = [
    path("campaigns/", CampaignListCreateView.as_view(), name="campaign-list-create"),
    path("campaigns/<int:campaign_id>/", CampaignDetailView.as_view(), name="campaign-detail"),
    path("campaigns/<int:campaign_id>/send/", CampaignSendView.as_view(), name="campaign-send"),
    path("campaigns/<int:campaign_id>/schedule/", CampaignScheduleView.as_view(), name="campaign-schedule"),
    path("recipients/", RecipientListView.as_view(), name="recipient-list"),
]
