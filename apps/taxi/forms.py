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