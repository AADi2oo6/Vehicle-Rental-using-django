from django import forms
from .models import Payment, Customer, RentalBooking
from django.contrib.auth.models import User
from datetime import date
from django.core.exceptions import ValidationError

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = '__all__'

class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['profile_picture', 'first_name', 'last_name', 'phone', 'date_of_birth', 'address', 'city', 'state', 'zip_code', 'license_number', 'is_subscribed_to_newsletter']
        labels = {
            'is_subscribed_to_newsletter': 'Subscribe to Newsletter'
        }
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_date_of_birth(self):
        """
        Custom validation to ensure the user is at least 18 years old.
        This logic is moved from the database trigger to the form for better
        field-specific error handling.
        """
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                raise ValidationError("User must be 18 or older.")
        return dob

    def clean_license_number(self):
        """
        Custom validation to ensure the license number is exactly 15 characters long.
        """
        license_number = self.cleaned_data.get('license_number')
        if license_number and len(license_number) != 15:
            raise ValidationError("Enter a valid 15-character license number.")
        return license_number
