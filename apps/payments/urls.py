from django.urls import path
from .views import *

urlpatterns = [
    path("create/", CreatePaymentView.as_view()),
    path("deposit/", DepositAPIView.as_view()),
    path("webhook/namba/", NambaWebhookView.as_view()),
]