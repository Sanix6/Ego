from django.db import models
from apps.users.models import User



class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=100)

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    type_payment = models.CharField(max_length=25, null=True, blank=True)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    external_id = models.CharField(max_length=255, unique=True)
    payment_link = models.URLField(max_length=1000, blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("success", "Success"),
            ("failed", "Failed"),
        ],
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        verbose_name = "Namba One"
        verbose_name_plural = "Namba One"