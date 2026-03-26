from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError

from .models import TaxiRide


class TaxiRideAdminForm(forms.ModelForm):
    class Meta:
        model = TaxiRide
        fields = "__all__"

    def clean_driver(self):
        driver = self.cleaned_data.get("driver")
        if driver and getattr(driver, "user_type", None) != "driver":
            raise ValidationError("Назначить можно только пользователя с ролью driver.")
        return driver

    def clean_client(self):
        client = self.cleaned_data.get("client")
        if client and getattr(client, "user_type", None) != "client":
            raise ValidationError("Клиент должен иметь роль client.")
        return client


@admin.register(TaxiRide)
class TaxiRideAdmin(admin.ModelAdmin):
    form = TaxiRideAdminForm

    list_display = (
        "id",
        "status",
        "car_class",
        "client",
        "driver",
        "point_a",
        "point_b",
        "price",
        "payment_method",
        "payment_status",
        "requested_at",
        "updated_at",
    )
    list_filter = (
        "status",
        "car_class",
        "payment_method",
        "payment_status",
        "requested_at",
    )
    search_fields = (
        "id",
        "client__phone",
        "client__first_name",
        "client__last_name",
        "driver__phone",
        "driver__first_name",
        "driver__last_name",
        "point_a__address",
        "point_b__address",
    )
    ordering = ("-requested_at",)

    readonly_fields = ("requested_at", "updated_at")

    fieldsets = (
        ("Основное", {
            "fields": ("status", "car_class", "passengers")
        }),
        ("Участники", {
            "fields": ("client", "driver")
        }),
        ("Маршрут", {
            "fields": ("point_a", "point_b", "pickup_lat", "pickup_lon", "dropoff_lat", "dropoff_lon")
        }),
        ("Расчет", {
            "fields": ("distance_km", "duration_min", "price")
        }),
        ("Оплата", {
            "fields": ("payment_method", "payment_status")
        }),
        ("Комментарий", {
            "fields": ("client_comment",)
        }),
        ("Тайминги", {
            "fields": (
                "assigned_at",
                "accepted_at",
                "arrived_at",
                "started_at",
                "completed_at",
                "canceled_at",
            )
        }),
        ("Служебное", {
            "fields": ("requested_at", "updated_at")
        }),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "client":
            qs = kwargs.get("queryset", db_field.remote_field.model.objects.all())
            kwargs["queryset"] = qs.filter(user_type="client", is_active=True)

        if db_field.name == "driver":
            qs = kwargs.get("queryset", db_field.remote_field.model.objects.all())
            kwargs["queryset"] = qs.filter(user_type="driver", is_active=True)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)
