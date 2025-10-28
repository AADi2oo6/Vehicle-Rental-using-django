# rental/signals.py
from django.db.models.signals import post_save, pre_save, pre_delete, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.db import IntegrityError
from django.contrib.auth.models import User
from .models import Customer, CustomerActivityLog

# Signal 1: ON INSERT - Auto-create Customer profile for new User
@receiver(post_save, sender=User)
def create_customer_profile(sender, instance, created, **kwargs):
    if created:
        # This signal now acts as a failsafe. If a User is created without a
        # Customer profile (e.g., via createsuperuser), this will create one.
        # The main registration logic in register_view now handles primary creation.
        if not Customer.objects.filter(user=instance).exists():
            Customer.objects.create(
                user=instance,
                email=instance.email,
                first_name=instance.first_name.strip() if instance.first_name else instance.username,
                last_name=instance.last_name.strip() if instance.last_name else ".", # Provide a default if last_name is empty
            )