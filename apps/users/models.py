from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import CustomUserManager
from random import randint
from assets.helpers.choices import *
from apps.main.models import DarkStore


class User(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField("Телефон", max_length=15, unique=True)
    email = models.EmailField("Email", blank=True)
    user_type = models.CharField("Тип пользователя", choices=USER_TYPERS, default="client", max_length=20, blank=True)
    first_name = models.CharField("Имя", max_length=30, blank=True)
    last_name = models.CharField("Фамилия", max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    home_address = models.CharField(max_length=255, blank=True, null=True)
    work_address = models.CharField(max_length=255, blank=True, null=True)
    verification_code = models.CharField(
        "Код подтверждения", max_length=4, blank=True, null=True
    )
    rating_avg = models.DecimalField("Средний рейтинг", max_digits=3, decimal_places=2, default=0)
    rating_count = models.PositiveIntegerField("Количество отзывов", default=0)
    orders_count = models.PositiveIntegerField("Количество заказов", default=0)

    objects = CustomUserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    def generate_code(self):
        self.verification_code = str(randint(1000, 9999))
        self.save(update_fields=["verification_code"])
        return self.verification_code

    def __str__(self):
        return f'{self.phone} {self.get_user_type_display()} - {self.first_name} {self.last_name}'
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class Client(User):
    class Meta:
        proxy = True
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"


class Operator(User):
    class Meta:
        proxy = True
        verbose_name = "Оператор"
        verbose_name_plural = "Операторы"


class Admin(User):
    class Meta:
        proxy = True
        verbose_name = "Администратор"
        verbose_name_plural = "Администраторы"


class CourierProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="courier_profile",
        limit_choices_to={"user_type": "courier"}
    )
    darkstore = models.ForeignKey(
        DarkStore,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="couriers",
        verbose_name="Даркстор"
    )

    transport_type = models.CharField(
        max_length=20,
        choices=TRANSPORT_TYPES
    )

    selfie = models.ImageField(upload_to="couriers/selfie/", blank=True, null=True)
    passport_front = models.ImageField(upload_to="couriers/passport/front/", blank=True, null=True)
    passport_back = models.ImageField(upload_to="couriers/passport/back/", blank=True, null=True)
    driver_license_front = models.ImageField(
        "Права лицевая сторона",
        upload_to='couriers/license/front/',
        blank=True,
        null=True
    )

    driver_license_back = models.ImageField(
        "Права обратная сторона",
        upload_to='couriers/license/back/',
        blank=True,
        null=True
    )

    car_brand = models.CharField(max_length=100, blank=True)
    car_model = models.CharField(max_length=100, blank=True)
    car_color = models.CharField(max_length=50, blank=True)
    car_number = models.CharField(max_length=20, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Курьер"
        verbose_name_plural = "Курьеры"


class DriverProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='driver_profile'
    )

    selfie = models.ImageField(
        "Селфи",
        upload_to='drivers/selfie/',
        blank=True,
        null=True
    )

    passport_front = models.ImageField(
        "Паспорт лицевая сторона",
        upload_to='drivers/passport/front/',
        blank=True,
        null=True
    )

    passport_back = models.ImageField(
        "Паспорт обратная сторона",
        upload_to='drivers/passport/back/',
        blank=True,
        null=True
    )
    passport_number = models.CharField("Номер паспорта", max_length=20, blank=True)


    seria_and_number = models.CharField("Серия и номер водительского права", max_length=50, blank=True)
    date_of_issue = models.DateField("Дата выдачи водительского права", blank=True, null=True)
    issuing_authority = models.CharField("Орган, выдавший водительское право", max_length=255, blank=True)
    driver_license_front = models.ImageField(
        "Права лицевая сторона",
        upload_to='drivers/license/front/',
        blank=True,
        null=True
    )

    driver_license_back = models.ImageField(
        "Права обратная сторона",
        upload_to='drivers/license/back/',
        blank=True,
        null=True
    )
 
    car_brand = models.CharField("Марка машины", max_length=100, blank=True)
    car_model = models.CharField("Модель машины", max_length=100, blank=True)
    car_color = models.CharField("Цвет машины", max_length=50, blank=True)
    car_number = models.CharField("Номер машины", max_length=20, blank=True)
    car_type = models.CharField("Тип машины", max_length=50, blank=True)

    car_photo = models.ImageField(
        "Фото машины",
        upload_to='drivers/car/',
        blank=True,
        null=True
    )

    status = models.CharField(
        "Статус проверки",
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Водитель {self.user.phone}"

    class Meta:
        verbose_name = "Таксист"
        verbose_name_plural = "Таксисты"


class WorkerStatus(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="worker_status")
    is_online = models.BooleanField(default=False)
    is_busy = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.phone} | online={self.is_online} | busy={self.is_busy}"

    class Meta:
        verbose_name = "Cтатусы водителей/курьеров"
        verbose_name_plural  = "Cтатусы водителей/курьеров"


class WorkerLocation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="worker_location")
    lat = models.FloatField()
    lon = models.FloatField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.phone} ({self.lat}, {self.lon})"

    class Meta:
        verbose_name = "Местоположение водителей/курьеров"
        verbose_name_plural  = "Местоположение водителей/курьеров"
        



class CourierDispatch(User):
    class Meta:
        proxy = True
        verbose_name = "Диспетчерская курьеров"
        verbose_name_plural = "Диспетчерская курьеров"


class DriverDispatch(User):
    class Meta:
        proxy = True
        verbose_name = "Диспетчерская таксистов"
        verbose_name_plural = "Диспетчерская таксистов"