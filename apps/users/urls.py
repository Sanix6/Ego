from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()
router.register("client/addresses", UserAddressViewSet, basename="addresses")

urlpatterns = [
    path("send-code/", SendCodeView.as_view(), name="send_code"),
    path("verify-code/", VerifyCodeView.as_view(), name="verify_code"),

    path("driver_register/", DriverRegisterView.as_view(), name="driver_register"),
    path("verify_code_driver/", VerifyCodeDriverView.as_view(), name="verify_code_driver"),
    path("resend_code_driver/", ResendCodeDriverView.as_view(), name="resend_code_driver"),

    path("scan_driver_documents/", ScanPersonalDriverView.as_view(), name="scan_personal_driver"),
    path("scan_drivers_license/", ScanDriversLicenseView.as_view(), name="scan_drivers_license"),
    path("scan_drivers_auto/", ScanDriversAutoView.as_view(), name="scan_drivers_auto"),

    path("personal/info/", PersonalInfoView.as_view(), name="personal-info"),
    path("profile-update/", UpdateProfileView.as_view(), name="profile-update"),

    path("workers/location/", WorkerLocationUpdateView.as_view(), name="worker-location-update"),
    path("workers/profile/", WorkerProfile.as_view(), name="profile-all"),

    path("client/orders/", MyOrdersView.as_view(), name="client-orders"),
    path("client/orders/<str:order_type>/<int:pk>/", MyOrderDetailView.as_view(), name="client-order-detail"),
    path("client/orders/<str:order_type>/<int:pk>/delete/", MyOrderDeleteView.as_view(), name="client-order-delete"),

    path("logout/profile", LogoutProfileView.as_view()),
    path("delete/profile", DeleteProfileView.as_view()),
    path("profile/logo/", LogoProfileView.as_view()),

    path("", include(router.urls)),
]