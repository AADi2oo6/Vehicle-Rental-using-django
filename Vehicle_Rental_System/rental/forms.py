from django import forms
from .models import Payment, RentalBooking, Customer, Vehicle

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = '__all__'

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