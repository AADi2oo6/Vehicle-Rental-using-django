# rental/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from .models import Customer, CustomerActivityLog

# Signal 1: ON INSERT - Auto-create Customer profile for new User
@receiver(post_save, sender=User)
def create_customer_profile(sender, instance, created, **kwargs):
    if created:
        # Check if a Customer already exists for this user (e.g., if created via admin)
        if not Customer.objects.filter(user=instance).exists():
            Customer.objects.create(
                user=instance,
                email=instance.email,
                first_name=instance.first_name if instance.first_name else instance.username,
                last_name=instance.last_name,
                # Default values for new fields
                membership_tier='Bronze',
                is_subscribed_to_newsletter=True, # Default to subscribed
                is_active=True,
                is_verified=False, # Default to unverified
            )
            # Log registration activity
            CustomerActivityLog.objects.create(
                customer=Customer.objects.get(user=instance),
                activity_type='Registration',
                description=f'New customer profile created for {instance.email}'
            )

# Signal 2: ON INSERT - Send Welcome Email (after Customer is created)
@receiver(post_save, sender=Customer)
def send_welcome_email(sender, instance, created, **kwargs):
    if created:
        subject = 'Welcome to Velo-Rent!'
        message = f'Hi {instance.first_name},\n\nThank you for registering with Velo-Rent. We are excited to have you!\n\nYour referral code is: {instance.referral_code}\n\nStart exploring our fleet today!\n\nBest regards,\nThe Velo-Rent Team'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [instance.email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)

# Signal 7: ON UPDATE - Log Profile Update Activity
@receiver(pre_save, sender=Customer)
def log_profile_update(sender, instance, **kwargs):
    if instance.pk: # Only for existing instances (updates)
        try:
            old_instance = Customer.objects.get(pk=instance.pk)
            changed_fields = []
            for field in instance._meta.fields:
                if getattr(instance, field.name) != getattr(old_instance, field.name):
                    # Exclude fields that change automatically or are not user-editable
                    if field.name not in ['registration_date', 'credit_score', 'referral_code', 'user', 'is_active']:
                        changed_fields.append(f"{field.verbose_name} changed from '{getattr(old_instance, field.name)}' to '{getattr(instance, field.name)}'")
            
            if changed_fields:
                CustomerActivityLog.objects.create(
                    customer=instance,
                    activity_type='Profile Update',
                    description=f'Profile updated. Changes: {"; ".join(changed_fields)}'
                )
        except Customer.DoesNotExist:
            pass # New instance, handled by post_save for registration