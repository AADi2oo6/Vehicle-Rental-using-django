from django import forms
from django.contrib.auth.models import User
from .models import Payment, Customer, RentalBooking, Vehicle, MaintenanceRecord
from datetime import date

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

    def clean_license_number(self):
        """
        Custom validation for the license_number field.
        """
        license_number = self.cleaned_data.get('license_number')
        if license_number:
            license_number = license_number.strip()
            if len(license_number) != 15:
                raise forms.ValidationError("License number must be exactly 15 characters long.")
            if Customer.objects.filter(license_number=license_number).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("This license number is already in use by another account.")
        return license_number

    def clean_date_of_birth(self):
        """
        Custom validation to ensure the customer is at least 18 years old.
        """
        date_of_birth = self.cleaned_data.get('date_of_birth')
        if date_of_birth:
            today = date.today()
            age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
            if age < 18:
                raise forms.ValidationError("Customer must be at least 18 years old.")
        return date_of_birth

class MaintenanceRecordForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRecord
        fields = [
            'vehicle', 'maintenance_date', 'maintenance_type', 'description',
            'cost', 'service_provider', 'next_service_date', 'mileage_at_service',
            'parts_replaced', 'technician_name', 'status'
        ]
        widgets = {
            'maintenance_date': forms.DateInput(attrs={'type': 'date'}),
            'next_service_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'parts_replaced': forms.Textarea(attrs={'rows': 2}),
        }

class CustomerPictureForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['profile_picture']
        help_texts = {
            'profile_picture': 'JPG, GIF or PNG. Max size of 2MB.',
        }
