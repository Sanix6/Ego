from django.urls import path
from .views import *

urlpatterns = [
    path("deliveries/<int:delivery_id>/review/", DeliveryReviewView.as_view(), name="delivery-review"),
    path("rides/<int:ride_id>/review/", TaxiReviewView.as_view(), name="ride-review"),
    path("courier/zones/", AvailableDeliveryZonesView.as_view(), name="courier-zones"),
    path("courier/zones/select/", AssignDeliveryZoneView.as_view(), name="courier-zone-select"),
    path("courier/zones/my/", MyDeliveryZoneView.as_view(), name="courier-my-zone")
]