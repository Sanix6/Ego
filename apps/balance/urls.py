from django.urls import path
from .views import *

urlpatterns = [
    path("wallet/dashboard/", WalletDashboardView.as_view(), name="wallet-dashboard"),
    path("withdraw", WithdrawalRequestCreateAPIView.as_view()),
    path("wallet/history/", WalletHistoryView.as_view())
]