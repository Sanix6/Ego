from django.contrib import admin
from django_celery_beat.models import (
    PeriodicTask,
    IntervalSchedule,
    CrontabSchedule,
    SolarSchedule,
    ClockedSchedule
)
from .models import Tariff

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
    


