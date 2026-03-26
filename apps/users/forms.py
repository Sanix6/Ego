from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.utils.timezone import now

from apps.users.models import (
    User,
    WorkerStatus,
    WorkerLocation,
    CourierProfile,
    DriverProfile,
    CourierDispatch,
    DriverDispatch,
)


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

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = "courier"

        if commit:
            user.save()

            worker_status, _ = WorkerStatus.objects.get_or_create(user=user)
            worker_status.is_online = self.cleaned_data.get("is_online", False)
            worker_status.is_busy = self.cleaned_data.get("is_busy", False)
            worker_status.save()

            lat = self.cleaned_data.get("lat")
            lon = self.cleaned_data.get("lon")

            if lat is not None and lon is not None:
                worker_location, _ = WorkerLocation.objects.get_or_create(
                    user=user,
                    defaults={"lat": lat, "lon": lon}
                )
                worker_location.lat = lat
                worker_location.lon = lon
                worker_location.save()

            courier_profile, _ = CourierProfile.objects.get_or_create(
                user=user,
                defaults={
                    "transport_type": self.cleaned_data.get("transport_type") or "bike",
                    "status": self.cleaned_data.get("courier_profile_status") or "pending",
                }
            )
            courier_profile.status = self.cleaned_data.get("courier_profile_status") or courier_profile.status
            courier_profile.transport_type = self.cleaned_data.get("transport_type") or courier_profile.transport_type
            courier_profile.darkstore = self.cleaned_data.get("darkstore")
            courier_profile.car_brand = self.cleaned_data.get("car_brand", "")
            courier_profile.car_model = self.cleaned_data.get("car_model", "")
            courier_profile.car_color = self.cleaned_data.get("car_color", "")
            courier_profile.car_number = self.cleaned_data.get("car_number", "")
            courier_profile.save()

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

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = "driver"

        if commit:
            user.save()

            worker_status, _ = WorkerStatus.objects.get_or_create(user=user)
            worker_status.is_online = self.cleaned_data.get("is_online", False)
            worker_status.is_busy = self.cleaned_data.get("is_busy", False)
            worker_status.save()

            lat = self.cleaned_data.get("lat")
            lon = self.cleaned_data.get("lon")

            if lat is not None and lon is not None:
                worker_location, _ = WorkerLocation.objects.get_or_create(
                    user=user,
                    defaults={"lat": lat, "lon": lon}
                )
                worker_location.lat = lat
                worker_location.lon = lon
                worker_location.save()

            driver_profile, _ = DriverProfile.objects.get_or_create(
                user=user,
                defaults={
                    "status": self.cleaned_data.get("driver_profile_status") or "pending",
                }
            )
            driver_profile.status = self.cleaned_data.get("driver_profile_status") or driver_profile.status
            driver_profile.car_brand = self.cleaned_data.get("car_brand", "")
            driver_profile.car_model = self.cleaned_data.get("car_model", "")
            driver_profile.car_color = self.cleaned_data.get("car_color", "")
            driver_profile.car_number = self.cleaned_data.get("car_number", "")
            driver_profile.car_type = self.cleaned_data.get("car_type", "")
            driver_profile.passport_number = self.cleaned_data.get("passport_number", "")
            driver_profile.seria_and_number = self.cleaned_data.get("seria_and_number", "")
            driver_profile.issuing_authority = self.cleaned_data.get("issuing_authority", "")
            driver_profile.save()

        return user

