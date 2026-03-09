from django.db import models

class Address(models.Model):
    address = models.CharField(max_length=255)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lng = models.DecimalField(max_digits=9, decimal_places=6)

    def __str__(self):
        return self.address
    
    class Meta:
        verbose_name = "Адрес"
        verbose_name_plural = "Адреса"

