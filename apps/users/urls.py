from django.urls import path
from .views import *

urlpatterns = [
    path("send-code/", SendCodeView.as_view(), name="send_code"),
    path("verify-code/", VerifyCodeView.as_view(), name="verify_code"),
    path('driver_register/', DriverRegisterView.as_view(), name='driver_register'),
    path('verify_code_driver/', VerifyCodeDriverView.as_view(), name='verify_code_driver'),
    path('resend_code_driver/', ResendCodeDriverView.as_view(), name='resend_code_driver'),
    path('scan_driver_documents/', ScanPersonalDriverView.as_view(), name='scan_personal_driver'),
    path('scan_drivers_license/', ScanDriversLicenseView.as_view(), name='scan_drivers_license'),
    path('scan_drivers_auto/', ScanDriversAutoView.as_view(), name='scan_drivers_auto'),
    path("addresses/home/", SaveHomeAddressView.as_view(), name="save-home-address"),
    path("addresses/work/", SaveWorkAddressView.as_view(), name="save-work-address"),
    path("personal/info/", PersonalInfoView.as_view(), name="personal-info"),
    path("workers/location/", WorkerLocationUpdateView.as_view(), name="worker-location-update"),
]
