from django.urls import path
from .views import CreateDeliveryPaymentAPIView, CreateTaxiPaymentAPIView
urlpatterns = [
    path("deliveries/<int:delivery_id>/pay/",CreateDeliveryPaymentAPIView.as_view(),name="delivery-create-payment"),
    path("taxi/rides/<int:ride_id>/pay/", CreateTaxiPaymentAPIView.as_view(),name="taxi-create-payment")
]