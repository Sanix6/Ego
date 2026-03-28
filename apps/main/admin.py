from django.contrib import admin
from django_celery_beat.models import (
    PeriodicTask,
    IntervalSchedule,
    CrontabSchedule,
    SolarSchedule,
    ClockedSchedule
)
from .models import Tariff, DarkStore, DeliveryTariff



admin.site.unregister(PeriodicTask)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(SolarSchedule)
admin.site.unregister(ClockedSchedule)

@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ("city", "car_class", "base_fare", "per_km_rate", "per_min_rate", "is_active")
    list_filter = ("city", "car_class", "is_active")
    search_fields = ("city",)
    

@admin.register(DeliveryTariff)
class DeliveryTariffAdmin(admin.ModelAdmin):
    list_display = ("type_delivery", "base_fare", "per_km_rate", "per_min_rate", "is_active")
    list_filter = ("type_delivery", "is_active")
    

@admin.register(DarkStore)
class DarkStoreAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "lat", "lon", "created_at")
    search_fields = ("name", "address")


