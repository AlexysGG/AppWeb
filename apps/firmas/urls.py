from django.urls import path
from .views import WebhookFirmaView

urlpatterns = [
    path("webhook/", WebhookFirmaView.as_view(), name="webhook_firma"),
]
