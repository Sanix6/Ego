from django import forms
from .models import DeliveryZone

class DeliveryZoneAdminForm(forms.ModelForm):
    class Meta:
        model = DeliveryZone
        fields = "__all__"
        widgets = {
            "polygon": forms.HiddenInput(),
        }