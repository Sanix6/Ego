from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_profiles(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == "courier":
            CourierProfile.objects.create(user=instance)

        if instance.user_type == "driver":
            DriverProfile.objects.create(user=instance)