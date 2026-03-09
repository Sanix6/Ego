from django import forms
from django.core.exceptions import ValidationError
from .models import Delivery
from django import forms
from .models import CourierSlot



class CourierSlotAdminForm(forms.ModelForm):
    class Meta:
        model = CourierSlot
        fields = "__all__"
        widgets = {
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for f in ("start_at", "end_at"):
            val = getattr(self.instance, f, None)
            if val:
                self.fields[f].initial = val.strftime("%Y-%m-%dT%H:%M")


class DeliveryAdminForm(forms.ModelForm):
    class Meta:
        model = Delivery
        fields = "__all__"
        widgets = {
            "pickup_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "delivered_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "deadline_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for f in ("pickup_at", "delivered_at"):
            val = getattr(self.instance, f, None)
            if val:
                self.fields[f].initial = val.strftime("%Y-%m-%dT%H:%M")

    def clean_courier(self):
        courier = self.cleaned_data.get("courier")
        if courier and getattr(courier, "user_type", None) != "courier":
            raise ValidationError("Назначить можно только пользователя с ролью courier.")
        return courier
    