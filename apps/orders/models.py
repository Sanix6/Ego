from django.db import models
from assets.helpers.choices import ORDER_TYPES, ORDER_STATUSES

class Order(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='orders')
    order_type = models.CharField("Тип заказа", max_length=50, choices=ORDER_TYPES)
    address = models.CharField("Адрес", max_length=255)
    assembler = models.CharField("Сборщик", max_length=255)
    courier_name = models.CharField("Имя курьера", max_length=255)
    order_status = models.CharField("Статус заказа", max_length=50, choices=ORDER_STATUSES, default="created")
    time_left = models.IntegerField("Осталось времени",default=0)
    delivered_to = models.CharField("Доставить до", max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.phone}"
    
    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"