from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from .models import Customer

class ActiveCustomerBackend(ModelBackend):
    """
    Custom authentication backend to check if the associated Customer profile is active.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # First, use the default backend to authenticate the user
        user = super().authenticate(request, username=username, password=password, **kwargs)

        # If the user is authenticated, perform our custom check
        if user is not None:
            try:
                # If the user is a staff member, skip the customer check.
                if user.is_staff:
                    return user
                
                # For regular users, check if their customer profile is active.
                customer = Customer.objects.get(user=user)
                if not customer.is_active:
                    return None # Block login if customer is inactive
            except Customer.DoesNotExist:
                return None # Block login if no customer profile exists
        return user