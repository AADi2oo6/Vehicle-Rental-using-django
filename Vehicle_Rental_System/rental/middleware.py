from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from .models import Customer

class CheckAccountActiveMiddleware:
    """
    Middleware to ensure that a customer with an active session has an active account.
    If the customer profile is inactive, their session is cleared.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'customer_id' in request.session:
            # Avoid a redirect loop on pages we're redirecting to
            if request.path in [reverse('home'), reverse('logout')]:
                return self.get_response(request)

            try:
                customer = Customer.objects.get(id=request.session['customer_id'])
                
                # If the customer is found but is NOT active, log them out.
                if not customer.is_active:
                    del request.session['customer_id']
                    messages.error(request, 'Your account has been deactivated by an administrator. Please contact support.')
                    return redirect('home')

            except Customer.DoesNotExist:
                # If the customer_id in the session is invalid, clear it.
                del request.session['customer_id']
                return redirect('home')

        response = self.get_response(request)
        return response