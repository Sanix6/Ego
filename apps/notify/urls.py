from django.urls import path
from .views import PushDeviceRegisterView

urlpatterns = [
    path("register-device/", PushDeviceRegisterView.as_view()),
]