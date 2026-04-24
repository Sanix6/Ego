from django.urls import path
from .views import *

urlpatterns = [
    path("prices/", TaxiPricesPreviewView.as_view(), name="taxi-prices-preview"),
    path("orders", TaxiRideCreateView.as_view(), name="taxi-order-create"),
    path("taxi-offers/<int:offer_id>/accept/", AcceptTaxiOfferView.as_view(), name="taxi-offer-accept"),
    path("taxi-offers/<int:offer_id>/reject/", RejectTaxiOfferView.as_view(), name="taxi-offer-reject"),
    path("taxi/rides/<int:ride_id>/tracking/", TaxiTrackingView.as_view(), name="taxi-tracking"),
    path("trips/<int:taxi_id>/arrive/", TaxiArriveView.as_view(), name="taxi-arrive"),
    path("trips/<int:taxi_id>/start/", TaxiStartTripView.as_view(), name="taxi-start"),
    path("trips/<int:taxi_id>/complete/", TaxiCompleteView.as_view(), name="taxi-complete"),
    path("driver/rides/history/", DriverRideHistoryView.as_view(), name="driver-ride-history"),
    path("taxi/<int:taxi_id>/cancel/", TaxiCancelByClientView.as_view(), name="taxi-cancel-by-client"),
]