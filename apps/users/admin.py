from django.contrib import admin
from django.contrib.auth.models import Group
from .models import User, Client, Courier, Driver, Operator, Admin

admin.site.unregister(Group)

class BaseUserAdmin(admin.ModelAdmin):
    list_display = (
        "phone",
        "first_name",
        "last_name",
        "user_type",
        "is_active",
        "is_staff",
        "date_joined",
    )
    list_filter = ("is_active", "is_staff")
    search_fields = ("phone", "first_name", "last_name")
    ordering = ("-date_joined",)

    readonly_fields = ("date_joined",)

    fieldsets = (
        ("Основное", {
            "fields": ("phone", "verification_code")
        }),
        ("Персональные данные", {
            "fields": ("first_name", "last_name", "email")
        }),
        ("Доступ", {
            "fields": ("user_type", "is_active", "is_staff", "is_superuser")
        }),
        ("Даты", {
            "fields": ("date_joined",)
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


@admin.register(Client)
class ClientAdmin(BaseUserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(user_type="client")

    def save_model(self, request, obj, form, change):
        obj.user_type = "client"
        obj.is_staff = False
        super().save_model(request, obj, form, change)


@admin.register(Courier)
class CourierAdmin(BaseUserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(user_type="courier")

    def save_model(self, request, obj, form, change):
        obj.user_type = "courier"
        obj.is_staff = False
        super().save_model(request, obj, form, change)


@admin.register(Driver)
class DriverAdmin(BaseUserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(user_type="driver")

    def save_model(self, request, obj, form, change):
        obj.user_type = "driver"
        obj.is_staff = False
        super().save_model(request, obj, form, change)


@admin.register(Operator)
class OperatorAdmin(BaseUserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(user_type="operator")

    def save_model(self, request, obj, form, change):
        obj.user_type = "operator"
        obj.is_staff = True  
        super().save_model(request, obj, form, change)


@admin.register(Admin)
class AdminUserAdmin(BaseUserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(user_type="admin")

    def save_model(self, request, obj, form, change):
        obj.user_type = "admin"
        obj.is_staff = True
        obj.is_superuser = True
        super().save_model(request, obj, form, change)


