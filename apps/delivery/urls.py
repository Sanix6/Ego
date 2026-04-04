from django.urls import path
from .views import *

urlpatterns = [
    path("orders", DeliveryCreateView.as_view(), name="delivery-create"),
    path("prices/", DeliveryPricesPreviewView.as_view(), name="delivery-prices-preview"),
    path("slots", SlotListView.as_view(), name="slot-list"),
    path("courier-slots/<int:slot_id>/book/", CourierSlotBookView.as_view(), name="courier-slot-book"),
    path("courier/slots/<int:slot_id>/cancel/", CourierSlotCancelView.as_view(), name="courier-slot-cancel"),
    path("courier-slots/own/", MyCourierSlotsView.as_view(), name="my-courier-slots"),
    path("offers/<int:offer_id>/accept/", AcceptOfferView.as_view()),
    path("offers/<int:offer_id>/reject/", RejectOfferView.as_view()),
    path("deliveries/<int:delivery_id>/tracking/", DeliveryTrackingView.as_view(), name="delivery-tracking"),
    path("deliveries/<int:delivery_id>/arrive/", DeliveryArriveView.as_view(), name="delivery-arrive"),
    path("deliveries/<int:delivery_id>/pickup/", DeliveryPickupView.as_view(), name="delivery-pickup"),
    path("deliveries/<int:delivery_id>/arrive-b/",DeliveryArrivePointBView.as_view(), name="delivery-arrive-b",),
    path("deliveries/<int:delivery_id>/complete/", DeliveryCompleteView.as_view(), name="delivery-complete"),
    path("deliveries/<int:delivery_id>/cancel/client/",DeliveryCancelByClientView.as_view(),name="delivery-cancel-by-client",),
    path("courier/orders/history/", CourierOrderHistoryView.as_view(), name="courier-order-history"),

]