from django import forms
from django.contrib.auth.models import User
from .models import Payment, Customer, RentalBooking, Vehicle
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
        # CORRECTED: Order by the User's first_name and last_name
        self.fields['customer'].queryset = Customer.objects.select_related('user').order_by('user__first_name', 'user__last_name')
        self.fields['vehicle'].queryset = Vehicle.objects.filter(status='Available').order_by('make', 'model')

# NEW FORM to handle User model fields
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

# CORRECTED FORM for Customer model fields
class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = Customer
        # REMOVED: first_name, last_name, email, referral_code
        # The field on the model is 'phone'.
        fields = [
            'profile_picture', 'phone', 'date_of_birth', 'address', 
            'city', 'state', 'zip_code', 'license_number', 
            'is_subscribed_to_newsletter'
        ]
        labels = {
            'is_subscribed_to_newsletter': 'Subscribe to Newsletter',
            'profile_picture': 'Change Profile Picture',
        }
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g., 123 MG Road'}),
        }
        help_texts = {
            'profile_picture': 'JPG, GIF or PNG. Max size of 2MB.',
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