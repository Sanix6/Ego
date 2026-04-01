from django import forms
from django.core.exceptions import ValidationError
from .models import Delivery
from django import forms
from django.contrib.admin.widgets import AdminSplitDateTime
from .models import CourierSlot


class CourierSlotAdminForm(forms.ModelForm):
    start_at = forms.DateTimeField(
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"},
            format="%Y-%m-%dT%H:%M"
        ),
    )
    end_at = forms.DateTimeField(
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"},
            format="%Y-%m-%dT%H:%M"
        ),
    )

    class Meta:
        model = CourierSlot
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for f in ("start_at", "end_at"):
            val = getattr(self.instance, f, None)
            if val:
                self.initial[f] = val.strftime("%Y-%m-%dT%H:%M")

class DeliveryAdminForm(forms.ModelForm):
    class Meta:
        model = Delivery
        fields = "__all__"
        widgets = {
            "pickup_at": AdminSplitDateTime(),
            "delivered_at": AdminSplitDateTime(),
            "deadline_at": AdminSplitDateTime(),
        }

    def clean_courier(self):
        courier = self.cleaned_data.get("courier")
        if courier and getattr(courier, "user_type", None) != "courier":
            raise ValidationError("Назначить можно только пользователя с ролью courier.")
        return courier