from django import forms
<<<<<<< Updated upstream
from .models import Payment, RentalBooking, Customer, Vehicle
=======
from .models import Payment, Customer
from django.contrib.auth.models import User
>>>>>>> Stashed changes

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = '__all__'

<<<<<<< Updated upstream
class AdminBookingForm(forms.ModelForm):
    class Meta:
        model = RentalBooking
        fields = [
            'customer', 'vehicle', 'pickup_datetime', 'return_datetime',
            'pickup_location', 'return_location', 'special_requests',
        ]
        widgets = {
            'pickup_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'return_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.order_by('first_name', 'last_name')
        self.fields['vehicle'].queryset = Vehicle.objects.filter(status='Available').order_by('make', 'model')
=======
class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'phone', 'date_of_birth', 'address', 'city', 'state', 'zip_code', 'license_number', 'is_subscribed_to_newsletter']
        labels = {
            'is_subscribed_to_newsletter': 'Subscribe to Newsletter'
        }
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

class CustomerPictureForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['profile_picture']
        help_texts = {
            'profile_picture': 'JPG, GIF or PNG. Max size of 2MB.',
        }
>>>>>>> Stashed changes
