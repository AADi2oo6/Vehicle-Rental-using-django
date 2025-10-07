from django import forms
from .models import Payment, RentalBooking, Customer, Vehicle, MaintenanceRecord
from django.contrib.auth.models import User

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

class MaintenanceRecordForm(forms.ModelForm):
    vehicle_id = forms.IntegerField(label="Vehicle ID", widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter Vehicle ID'}))

    class Meta:
        model = MaintenanceRecord
        # Use exclude to automatically include all model fields except 'vehicle', which is handled by the vehicle_id field.
        exclude = ['vehicle']
        widgets = {
            'maintenance_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'next_service_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def clean(self):
        """
        Custom validation to find the Vehicle from vehicle_id and attach it.
        This is the correct way to handle a raw ID field for a ForeignKey in a ModelForm.
        """
        cleaned_data = super().clean()
        vehicle_id = cleaned_data.get("vehicle_id")

        if vehicle_id:
            try:
                vehicle = Vehicle.objects.get(id=vehicle_id)
                self.instance.vehicle = vehicle  # Attach the vehicle instance to the model instance
            except Vehicle.DoesNotExist:
                self.add_error('vehicle_id', f"A vehicle with ID {vehicle_id} does not exist.")
        return cleaned_data

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
        model = Customer
        fields = ['profile_picture']
        help_texts = {
            'profile_picture': 'JPG, GIF or PNG. Max size of 2MB.',
        }
