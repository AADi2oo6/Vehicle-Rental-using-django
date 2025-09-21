from django.db import models
from django.contrib.auth.hashers import make_password
from django.utils import timezone # Import timezone

class Customer(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128, default=make_password('12345678'))
    phone = models.CharField(max_length=15)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    license_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    credit_score = models.IntegerField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.jpg', blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.license_number:
            self.is_verified = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Vehicle(models.Model):
    VEHICLE_TYPES = [('Car', 'Car'), ('SUV', 'SUV'), ('Truck', 'Truck'), ('Motorcycle', 'Motorcycle'), ('Van', 'Van')]
    FUEL_TYPES = [('Petrol', 'Petrol'), ('Diesel', 'Diesel'), ('Electric', 'Electric'), ('Hybrid', 'Hybrid')]
    TRANSMISSION_TYPES = [('Manual', 'Manual'), ('Automatic', 'Automatic')]
    STATUS_CHOICES = [('Available', 'Available'), ('Rented', 'Rented'), ('Maintenance', 'Maintenance'), ('Retired', 'Retired')]

    vehicle_number = models.CharField(max_length=20, unique=True)
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.IntegerField()
    color = models.CharField(max_length=30, blank=True, null=True)
    vehicle_type = models.CharField(max_length=15, choices=VEHICLE_TYPES)
    fuel_type = models.CharField(max_length=10, choices=FUEL_TYPES)
    seating_capacity = models.IntegerField()
    transmission = models.CharField(max_length=10, choices=TRANSMISSION_TYPES)
    # UPDATED: Added a default value
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    mileage = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    insurance_expiry = models.DateField()
    last_service_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Available')
    created_date = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=100, default='Pune')
    vehicle_picture = models.ImageField(upload_to='vehicle_pics/', default='vehicle_pics/default.jpg', blank=True, null=True)

    def __str__(self):
        return self.vehicle_number

class RentalBooking(models.Model):
    BOOKING_STATUS = [('Confirmed', 'Confirmed'), ('Active', 'Active'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    booking_date = models.DateTimeField(auto_now_add=True)
    
    # UPDATED: Added default=timezone.now
    pickup_datetime = models.DateTimeField(default=timezone.now)
    return_datetime = models.DateTimeField(default=timezone.now)
    actual_return_datetime = models.DateTimeField(blank=True, null=True)
    
    pickup_location = models.CharField(max_length=100)
    return_location = models.CharField(max_length=100)
    
    # UPDATED: Added a default value
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2)
    booking_status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='Confirmed')
    special_requests = models.TextField(blank=True, null=True)
    created_by = models.CharField(max_length=50, default='System')

    @property
    def total_hours(self):
        if self.return_datetime and self.pickup_datetime:
            duration = self.return_datetime - self.pickup_datetime
            return duration.total_seconds() / 3600
        return 0

    def __str__(self):
        return f"Booking {self.id} for Vehicle {self.vehicle.vehicle_number}"

class Payment(models.Model):
    PAYMENT_METHODS = [('Cash', 'Cash'), ('Credit Card', 'Credit Card'), ('Debit Card', 'Debit Card'), ('UPI', 'UPI'), ('Net Banking', 'Net Banking')]
    PAYMENT_TYPES = [('Advance', 'Advance'), ('Full Payment', 'Full Payment'), ('Security Deposit', 'Security Deposit'), ('Fine', 'Fine'), ('Refund', 'Refund')]
    PAYMENT_STATUS = [('Pending', 'Pending'), ('Completed', 'Completed'), ('Failed', 'Failed'), ('Refunded', 'Refunded')]

    booking = models.ForeignKey(RentalBooking, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    payment_date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    transaction_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='Completed')
    processed_by = models.CharField(max_length=50, default='System', blank=True, null=True)
    reference_number = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    

    def __str__(self):
        return f"Payment {self.id}"

class MaintenanceRecord(models.Model):
    MAINTENANCE_TYPES = [('Regular Service', 'Regular Service'), ('Repair', 'Repair'), ('Inspection', 'Inspection'), ('Cleaning', 'Cleaning'), ('Tire Change', 'Tire Change')]
    STATUS_CHOICES = [('Scheduled', 'Scheduled'), ('In Progress', 'In Progress'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')]

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    maintenance_date = models.DateField()
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES)
    description = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    service_provider = models.CharField(max_length=100, blank=True, null=True)
    next_service_date = models.DateField(blank=True, null=True)
    mileage_at_service = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    parts_replaced = models.TextField(blank=True, null=True)
    technician_name = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Completed')
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Maintenance {self.id}"

class FeedbackReview(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    booking = models.ForeignKey(RentalBooking, on_delete=models.CASCADE)
    rating = models.IntegerField()
    review_text = models.TextField(blank=True, null=True)
    service_rating = models.IntegerField(blank=True, null=True)
    vehicle_condition_rating = models.IntegerField(blank=True, null=True)
    review_date = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=True)
    response_from_admin = models.TextField(blank=True, null=True)
    response_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Review {self.id}"

