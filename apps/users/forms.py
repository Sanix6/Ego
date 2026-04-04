from django import forms
from django.db import transaction
from apps.balance.models import WorkerWallet


from apps.users.models import (
    WorkerStatus,
    WorkerLocation,
    CourierProfile,
    DriverProfile,
    CourierDispatch,
    DriverDispatch,
)


class CourierDispatchForm(forms.ModelForm):
    # ===== USER =====
    verification_code = forms.CharField(required=False, label="Код подтверждения")
    home_address = forms.CharField(required=False, label="Домашний адрес")
    work_address = forms.CharField(required=False, label="Рабочий адрес")
    rating_avg = forms.DecimalField(required=False, label="Средний рейтинг", max_digits=3, decimal_places=2)
    rating_count = forms.IntegerField(required=False, label="Количество отзывов", min_value=0)
    orders_count = forms.IntegerField(required=False, label="Количество заказов", min_value=0)

    # ===== STATUS =====
    is_online = forms.BooleanField(required=False, label="Онлайн")
    is_busy = forms.BooleanField(required=False, label="Занят")
    last_seen = forms.DateTimeField(required=False, label="Последняя активность", disabled=True)

    # ===== LOCATION =====
    lat = forms.FloatField(required=False, label="Широта")
    lon = forms.FloatField(required=False, label="Долгота")
    location_updated_at = forms.DateTimeField(required=False, label="Обновление гео", disabled=True)

    # ===== COURIER PROFILE =====
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
    delivery_zones = forms.ModelChoiceField(
        queryset=CourierProfile._meta.get_field("delivery_zones").remote_field.model.objects.all(),
        required=False,
        label="Разрешенные зоны доставки",
    )

    selfie = forms.ImageField(required=False, label="Селфи")
    passport_front = forms.ImageField(required=False, label="Паспорт лицевая сторона")
    passport_back = forms.ImageField(required=False, label="Паспорт обратная сторона")
    driver_license_front = forms.ImageField(required=False, label="Права лицевая сторона")
    driver_license_back = forms.ImageField(required=False, label="Права обратная сторона")

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
            "verification_code",
            "home_address",
            "work_address",
            "rating_avg",
            "rating_count",
            "orders_count",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user = self.instance
        status = getattr(user, "worker_status", None)
        location = getattr(user, "worker_location", None)
        profile = getattr(user, "courier_profile", None)

        # user
        self.fields["verification_code"].initial = user.verification_code
        self.fields["home_address"].initial = user.home_address
        self.fields["work_address"].initial = user.work_address
        self.fields["rating_avg"].initial = user.rating_avg
        self.fields["rating_count"].initial = user.rating_count
        self.fields["orders_count"].initial = user.orders_count

        # status
        if status:
            self.fields["is_online"].initial = status.is_online
            self.fields["is_busy"].initial = status.is_busy
            self.fields["last_seen"].initial = status.last_seen

        # location
        if location:
            self.fields["lat"].initial = location.lat
            self.fields["lon"].initial = location.lon
            self.fields["location_updated_at"].initial = location.updated_at

        # profile
        if profile:
            self.fields["courier_profile_status"].initial = profile.status
            self.fields["transport_type"].initial = profile.transport_type
            self.fields["darkstore"].initial = profile.darkstore
            self.fields["delivery_zones"].initial = profile.delivery_zones

            self.fields["selfie"].initial = profile.selfie
            self.fields["passport_front"].initial = profile.passport_front
            self.fields["passport_back"].initial = profile.passport_back
            self.fields["driver_license_front"].initial = profile.driver_license_front
            self.fields["driver_license_back"].initial = profile.driver_license_back

            self.fields["car_brand"].initial = profile.car_brand
            self.fields["car_model"].initial = profile.car_model
            self.fields["car_color"].initial = profile.car_color
            self.fields["car_number"].initial = profile.car_number

    def clean(self):
        cleaned_data = super().clean()

        lat = cleaned_data.get("lat")
        lon = cleaned_data.get("lon")

        if (lat is None) ^ (lon is None):
            raise forms.ValidationError("Для геолокации нужно указать и широту, и долготу.")

        transport_type = cleaned_data.get("transport_type")
        car_number = (cleaned_data.get("car_number") or "").strip()

        if transport_type == "car" and not car_number:
            self.add_error("car_number", "Для авто обязателен номер машины.")

        return cleaned_data

    def _update_file_field_if_changed(self, profile, field_name):
        if field_name in self.changed_data:
            setattr(profile, field_name, self.cleaned_data.get(field_name))

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = "courier"
        user.verification_code = self.cleaned_data.get("verification_code")
        user.home_address = self.cleaned_data.get("home_address")
        user.work_address = self.cleaned_data.get("work_address")
        user.rating_avg = self.cleaned_data.get("rating_avg") or 0
        user.rating_count = self.cleaned_data.get("rating_count") or 0
        user.orders_count = self.cleaned_data.get("orders_count") or 0

        if commit:
            user.save()

            WorkerWallet.objects.get_or_create(worker=user)
            worker_status, _ = WorkerStatus.objects.get_or_create(user=user)
            worker_status.is_online = self.cleaned_data.get("is_online", False)
            worker_status.is_busy = self.cleaned_data.get("is_busy", False)
            worker_status.save()

            lat = self.cleaned_data.get("lat")
            lon = self.cleaned_data.get("lon")
            if lat is not None and lon is not None:
                worker_location, _ = WorkerLocation.objects.get_or_create(user=user)
                worker_location.lat = lat
                worker_location.lon = lon
                worker_location.save()
            else:
                WorkerLocation.objects.filter(user=user).delete()

            profile, _ = CourierProfile.objects.get_or_create(user=user)
            profile.status = self.cleaned_data.get("courier_profile_status") or "pending"
            profile.transport_type = self.cleaned_data.get("transport_type") or ""
            profile.darkstore = self.cleaned_data.get("darkstore")
            profile.delivery_zones = self.cleaned_data.get("delivery_zones")
            profile.car_brand = self.cleaned_data.get("car_brand") or ""
            profile.car_model = self.cleaned_data.get("car_model") or ""
            profile.car_color = self.cleaned_data.get("car_color") or ""
            profile.car_number = self.cleaned_data.get("car_number") or ""

            self._update_file_field_if_changed(profile, "selfie")
            self._update_file_field_if_changed(profile, "passport_front")
            self._update_file_field_if_changed(profile, "passport_back")
            self._update_file_field_if_changed(profile, "driver_license_front")
            self._update_file_field_if_changed(profile, "driver_license_back")

            profile.save()

        return user


class DriverDispatchForm(forms.ModelForm):
    # ===== USER =====
    verification_code = forms.CharField(required=False, label="Код подтверждения")
    home_address = forms.CharField(required=False, label="Домашний адрес")
    work_address = forms.CharField(required=False, label="Рабочий адрес")
    rating_avg = forms.DecimalField(required=False, label="Средний рейтинг", max_digits=3, decimal_places=2)
    rating_count = forms.IntegerField(required=False, label="Количество отзывов", min_value=0)
    orders_count = forms.IntegerField(required=False, label="Количество заказов", min_value=0)

    # ===== STATUS =====
    is_online = forms.BooleanField(required=False, label="Онлайн")
    is_busy = forms.BooleanField(required=False, label="Занят")
    last_seen = forms.DateTimeField(required=False, label="Последняя активность", disabled=True)

    # ===== LOCATION =====
    lat = forms.FloatField(required=False, label="Широта")
    lon = forms.FloatField(required=False, label="Долгота")
    location_updated_at = forms.DateTimeField(required=False, label="Обновление гео", disabled=True)

    # ===== DRIVER PROFILE =====
    driver_profile_status = forms.ChoiceField(
        required=False,
        label="Статус профиля таксиста",
        choices=DriverProfile._meta.get_field("status").choices,
    )

    selfie = forms.ImageField(required=False, label="Селфи")
    passport_front = forms.ImageField(required=False, label="Паспорт лицевая сторона")
    passport_back = forms.ImageField(required=False, label="Паспорт обратная сторона")
    passport_number = forms.CharField(required=False, label="Номер паспорта")

    seria_and_number = forms.CharField(required=False, label="Серия и номер водительского права")
    date_of_issue = forms.DateField(required=False, label="Дата выдачи водительского права", widget=forms.DateInput(attrs={"type": "date"}))
    issuing_authority = forms.CharField(required=False, label="Орган, выдавший водительское право")
    driver_license_front = forms.ImageField(required=False, label="Права лицевая сторона")
    driver_license_back = forms.ImageField(required=False, label="Права обратная сторона")

    car_brand = forms.CharField(required=False, label="Марка машины")
    car_model = forms.CharField(required=False, label="Модель машины")
    car_color = forms.CharField(required=False, label="Цвет машины")
    car_number = forms.CharField(required=False, label="Номер машины")
    car_type = forms.CharField(required=False, label="Тип машины")
    car_photo = forms.ImageField(required=False, label="Фото машины")

    class Meta:
        model = DriverDispatch
        fields = (
            "phone",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "verification_code",
            "home_address",
            "work_address",
            "rating_avg",
            "rating_count",
            "orders_count",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user = self.instance
        status = getattr(user, "worker_status", None)
        location = getattr(user, "worker_location", None)
        profile = getattr(user, "driver_profile", None)

        # user
        self.fields["verification_code"].initial = user.verification_code
        self.fields["home_address"].initial = user.home_address
        self.fields["work_address"].initial = user.work_address
        self.fields["rating_avg"].initial = user.rating_avg
        self.fields["rating_count"].initial = user.rating_count
        self.fields["orders_count"].initial = user.orders_count

        # status
        if status:
            self.fields["is_online"].initial = status.is_online
            self.fields["is_busy"].initial = status.is_busy
            self.fields["last_seen"].initial = status.last_seen

        # location
        if location:
            self.fields["lat"].initial = location.lat
            self.fields["lon"].initial = location.lon
            self.fields["location_updated_at"].initial = location.updated_at

        # profile
        if profile:
            self.fields["driver_profile_status"].initial = profile.status

            self.fields["selfie"].initial = profile.selfie
            self.fields["passport_front"].initial = profile.passport_front
            self.fields["passport_back"].initial = profile.passport_back
            self.fields["passport_number"].initial = profile.passport_number

            self.fields["seria_and_number"].initial = profile.seria_and_number
            self.fields["date_of_issue"].initial = profile.date_of_issue
            self.fields["issuing_authority"].initial = profile.issuing_authority
            self.fields["driver_license_front"].initial = profile.driver_license_front
            self.fields["driver_license_back"].initial = profile.driver_license_back

            self.fields["car_brand"].initial = profile.car_brand
            self.fields["car_model"].initial = profile.car_model
            self.fields["car_color"].initial = profile.car_color
            self.fields["car_number"].initial = profile.car_number
            self.fields["car_type"].initial = profile.car_type
            self.fields["car_photo"].initial = profile.car_photo

    def clean(self):
        cleaned_data = super().clean()

        lat = cleaned_data.get("lat")
        lon = cleaned_data.get("lon")

        if (lat is None) ^ (lon is None):
            raise forms.ValidationError("Для геолокации нужно указать и широту, и долготу.")

        return cleaned_data

    def _update_file_field_if_changed(self, profile, field_name):
        if field_name in self.changed_data:
            setattr(profile, field_name, self.cleaned_data.get(field_name))

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = "driver"
        user.verification_code = self.cleaned_data.get("verification_code")
        user.home_address = self.cleaned_data.get("home_address")
        user.work_address = self.cleaned_data.get("work_address")
        user.rating_avg = self.cleaned_data.get("rating_avg") or 0
        user.rating_count = self.cleaned_data.get("rating_count") or 0
        user.orders_count = self.cleaned_data.get("orders_count") or 0

        if commit:
            user.save()

            worker_status, _ = WorkerStatus.objects.get_or_create(user=user)
            worker_status.is_online = self.cleaned_data.get("is_online", False)
            worker_status.is_busy = self.cleaned_data.get("is_busy", False)
            worker_status.save()

            lat = self.cleaned_data.get("lat")
            lon = self.cleaned_data.get("lon")
            if lat is not None and lon is not None:
                worker_location, _ = WorkerLocation.objects.get_or_create(user=user)
                worker_location.lat = lat
                worker_location.lon = lon
                worker_location.save()
            else:
                WorkerLocation.objects.filter(user=user).delete()

            profile, _ = DriverProfile.objects.get_or_create(user=user)
            profile.status = self.cleaned_data.get("driver_profile_status") or "pending"

            profile.passport_number = self.cleaned_data.get("passport_number") or ""
            profile.seria_and_number = self.cleaned_data.get("seria_and_number") or ""
            profile.date_of_issue = self.cleaned_data.get("date_of_issue")
            profile.issuing_authority = self.cleaned_data.get("issuing_authority") or ""

            profile.car_brand = self.cleaned_data.get("car_brand") or ""
            profile.car_model = self.cleaned_data.get("car_model") or ""
            profile.car_color = self.cleaned_data.get("car_color") or ""
            profile.car_number = self.cleaned_data.get("car_number") or ""
            profile.car_type = self.cleaned_data.get("car_type") or ""

            self._update_file_field_if_changed(profile, "selfie")
            self._update_file_field_if_changed(profile, "passport_front")
            self._update_file_field_if_changed(profile, "passport_back")
            self._update_file_field_if_changed(profile, "driver_license_front")
            self._update_file_field_if_changed(profile, "driver_license_back")
            self._update_file_field_if_changed(profile, "car_photo")

            profile.save()

        return user