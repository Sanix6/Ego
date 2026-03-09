from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import CustomUserManager
from random import randint
from assets.helpers.choices import USER_TYPERS


class User(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField("Телефон", max_length=15, unique=True)
    email = models.EmailField("Email", blank=True)
    user_type = models.CharField("Тип пользователя", choices=USER_TYPERS, max_length=20, blank=True)
    first_name = models.CharField("Имя", max_length=30, blank=True)
    last_name = models.CharField("Фамилия", max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    verification_code = models.CharField(
        "Код подтверждения", max_length=4, blank=True, null=True
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    def generate_code(self):
        self.verification_code = str(randint(1000, 9999))
        self.save(update_fields=["verification_code"])
        return self.verification_code

    def __str__(self):
        return self.phone
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class Client(User):
    class Meta:
        proxy = True
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"


class Courier(User):
    class Meta:
        proxy = True
        verbose_name = "Курьер"
        verbose_name_plural = "Курьеры"


class Driver(User):
    class Meta:
        proxy = True
        verbose_name = "Водитель"
        verbose_name_plural = "Водители"


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
