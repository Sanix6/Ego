from django.urls import path
from .views import SendCodeView, VerifyCodeView

urlpatterns = [
    path("send-code/", SendCodeView.as_view(), name="send_code"),
    path("verify-code/", VerifyCodeView.as_view(), name="verify_code"),
]
