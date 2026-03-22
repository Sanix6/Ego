from django.urls import path
from .views import GeocodeView, ReverseGeocodeView, AddressSuggestView

urlpatterns = [
    path("geocode/", GeocodeView.as_view(), name="geocode"),
    path("reverse/", ReverseGeocodeView.as_view(), name="reverse-geocode"),
    path("address/suggest/", AddressSuggestView.as_view(), name="address-suggest"),
]