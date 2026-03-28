from django.urls import path
from .views import DeliveryReviewView, TaxiReviewView

urlpatterns = [
    path("deliveries/<int:delivery_id>/review/", DeliveryReviewView.as_view(), name="delivery-review"),
    path("rides/<int:ride_id>/review/", TaxiReviewView.as_view(), name="ride-review"),
]