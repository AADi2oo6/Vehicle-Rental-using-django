from .models import Customer

def customer_context(request):
    customer = None
    if request.user.is_authenticated:
        try:
            # Assuming Customer is linked to Django's User model via a OneToOneField
            customer = Customer.objects.get(user=request.user)
        except Customer.DoesNotExist:
            pass
    return {'customer': customer}