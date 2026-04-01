from django import forms

from apps.users.models import (
    WorkerStatus,
    WorkerLocation,
    CourierProfile,
    DriverProfile,
    CourierDispatch,
    DriverDispatch,
)
from apps.users.services import save_courier_dispatch, save_driver_dispatch


class CourierDispatchForm(forms.ModelForm):
    is_online = forms.BooleanField(required=False, label="Онлайн")
    is_busy = forms.BooleanField(required=False, label="Занят")
    last_seen = forms.DateTimeField(required=False, label="Последняя активность", disabled=True)

    lat = forms.FloatField(required=False, label="Широта")
    lon = forms.FloatField(required=False, label="Долгота")
    location_updated_at = forms.DateTimeField(required=False, label="Обновление гео", disabled=True)

    courier_profile_status = forms.ChoiceField(
        required=False,
        label="Статус профиля курьера",
        choices=CourierProfile._meta.get_field("status").choices,
    )
    transport_type = forms.ChoiceField(
        required=False,
        label="Транспорт",
        choices=CourierProfile._meta.get_field("transport_type").choices,
    )

    darkstore = forms.ModelChoiceField(
        queryset=CourierProfile._meta.get_field("darkstore").remote_field.model.objects.all(),
        required=False,
        label="Даркстор",
    )

    car_brand = forms.CharField(required=False, label="Марка")
    car_model = forms.CharField(required=False, label="Модель")
    car_color = forms.CharField(required=False, label="Цвет")
    car_number = forms.CharField(required=False, label="Номер")

    class Meta:
        model = CourierDispatch
        fields = (
            "phone",
            "email",
            "first_name",
            "last_name",
            "is_active",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user = self.instance

        status = getattr(user, "worker_status", None)
        location = getattr(user, "worker_location", None)
        profile = getattr(user, "courier_profile", None)

        if status:
            self.fields["is_online"].initial = status.is_online
            self.fields["is_busy"].initial = status.is_busy
            self.fields["last_seen"].initial = status.last_seen

        if location:
            self.fields["lat"].initial = location.lat
            self.fields["lon"].initial = location.lon
            self.fields["location_updated_at"].initial = location.updated_at

        if profile:
            self.fields["courier_profile_status"].initial = profile.status
            self.fields["transport_type"].initial = profile.transport_type
            self.fields["darkstore"].initial = profile.darkstore
            self.fields["car_brand"].initial = profile.car_brand
            self.fields["car_model"].initial = profile.car_model
            self.fields["car_color"].initial = profile.car_color
            self.fields["car_number"].initial = profile.car_number

    def clean(self):
        cleaned_data = super().clean()

        transport_type = cleaned_data.get("transport_type")
        car_brand = (cleaned_data.get("car_brand") or "").strip()
        car_model = (cleaned_data.get("car_model") or "").strip()
        car_color = (cleaned_data.get("car_color") or "").strip()
        car_number = (cleaned_data.get("car_number") or "").strip()

        lat = cleaned_data.get("lat")
        lon = cleaned_data.get("lon")

        if (lat is None) ^ (lon is None):
            raise forms.ValidationError("Для геолокации нужно указать и широту, и долготу.")

        if transport_type in ("car", ):
            if not car_number:
                self.add_error("car_number", "Для авто обязателен номер машины.")
        else:
            cleaned_data["car_brand"] = ""
            cleaned_data["car_model"] = ""
            cleaned_data["car_color"] = ""
            cleaned_data["car_number"] = ""

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = "courier"

        if commit:
            save_courier_dispatch(user, self.cleaned_data)

        return user


class DriverDispatchForm(forms.ModelForm):
    is_online = forms.BooleanField(required=False, label="Онлайн")
    is_busy = forms.BooleanField(required=False, label="Занят")
    last_seen = forms.DateTimeField(required=False, label="Последняя активность", disabled=True)

    lat = forms.FloatField(required=False, label="Широта")
    lon = forms.FloatField(required=False, label="Долгота")
    location_updated_at = forms.DateTimeField(required=False, label="Обновление гео", disabled=True)

    driver_profile_status = forms.ChoiceField(
        required=False,
        label="Статус профиля таксиста",
        choices=DriverProfile._meta.get_field("status").choices,
    )

    car_brand = forms.CharField(required=False, label="Марка")
    car_model = forms.CharField(required=False, label="Модель")
    car_color = forms.CharField(required=False, label="Цвет")
    car_number = forms.CharField(required=False, label="Номер")
    car_type = forms.CharField(required=False, label="Тип машины")
    passport_number = forms.CharField(required=False, label="Номер паспорта")
    seria_and_number = forms.CharField(required=False, label="Серия и номер прав")
    issuing_authority = forms.CharField(required=False, label="Кем выдано")

    class Meta:
        model = DriverDispatch
        fields = (
            "phone",
            "email",
            "first_name",
            "last_name",
            "is_active",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user = self.instance

        status = getattr(user, "worker_status", None)
        location = getattr(user, "worker_location", None)
        profile = getattr(user, "driver_profile", None)

        if status:
            self.fields["is_online"].initial = status.is_online
            self.fields["is_busy"].initial = status.is_busy
            self.fields["last_seen"].initial = status.last_seen

        if location:
            self.fields["lat"].initial = location.lat
            self.fields["lon"].initial = location.lon
            self.fields["location_updated_at"].initial = location.updated_at

        if profile:
            self.fields["driver_profile_status"].initial = profile.status
            self.fields["car_brand"].initial = profile.car_brand
            self.fields["car_model"].initial = profile.car_model
            self.fields["car_color"].initial = profile.car_color
            self.fields["car_number"].initial = profile.car_number
            self.fields["car_type"].initial = profile.car_type
            self.fields["passport_number"].initial = profile.passport_number
            self.fields["seria_and_number"].initial = profile.seria_and_number
            self.fields["issuing_authority"].initial = profile.issuing_authority

    def clean(self):
        cleaned_data = super().clean()

        lat = cleaned_data.get("lat")
        lon = cleaned_data.get("lon")

        if (lat is None) ^ (lon is None):
            raise forms.ValidationError("Для геолокации нужно указать и широту, и долготу.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = "driver"

        if commit:
            save_driver_dispatch(user, self.cleaned_data)

        return user