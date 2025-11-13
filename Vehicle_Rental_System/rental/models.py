from django.db import models
from django.contrib.auth.hashers import make_password
<<<<<<< HEAD
from django.utils import timezone
=======
from django.utils import timezone # Import timezone
from django.contrib.auth.models import User
import uuid
>>>>>>> 95b19fba1109557a00be7f13a177d5081bad2746

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
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
<<<<<<< HEAD
    profile_picture = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.jpg', blank=True, null=True)
    membership_tier = models.CharField(max_length=20, default='Bronze')
    is_subscribed_to_newsletter = models.BooleanField(default=False)
=======
    
    MEMBERSHIP_TIER_CHOICES = [
        ('Bronze', 'Bronze'), ('Silver', 'Silver'), ('Gold', 'Gold'), ('Platinum', 'Platinum'),
    ]
    membership_tier = models.CharField(max_length=10, choices=MEMBERSHIP_TIER_CHOICES, default='Bronze')
    is_subscribed_to_newsletter = models.BooleanField(default=False)
    referral_code = models.CharField(max_length=10, unique=True, blank=True, null=True)
>>>>>>> 95b19fba1109557a00be7f13a177d5081bad2746

    profile_picture = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.jpg', blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class CustomerActivityLog(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=50) # e.g., 'Registration', 'Profile Update', 'Verification'
    description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.customer.email} - {self.activity_type} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

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
    pickup_datetime = models.DateTimeField(default=timezone.now)
    return_datetime = models.DateTimeField(default=timezone.now)
    actual_return_datetime = models.DateTimeField(blank=True, null=True)
    pickup_location = models.CharField(max_length=100)
    return_location = models.CharField(max_length=100)
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
    reference_number = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    processed_by = models.CharField(max_length=50, default='System')

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

<<<<<<< HEAD
# NEW: Activity Log Model
class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('REGISTRATION', 'User Registration'),
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('BOOKING_CREATED', 'Booking Created'),
        ('PROFILE_UPDATE', 'Profile Updated'),
        ('REVIEW_CREATED', 'Review Created'),
        ('REVIEW_UPDATED', 'Review Updated'),
        ('REVIEW_DELETED', 'Review Deleted'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    details = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        customer_email = self.customer.email if self.customer else 'System'
        return f"{customer_email} - {self.action_type} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
class DetailedReview(models.Model):
    """
    This is a read-only model that maps to the 'vw_detailed_reviews' database view.
    Django will not manage this model's database table (i.e., it won't create or delete it).
    """
    review_id = models.IntegerField(primary_key=True)
    rating = models.IntegerField()
    review_text = models.TextField(blank=True, null=True)
    review_date = models.DateTimeField()
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    profile_picture = models.CharField(max_length=100, blank=True, null=True)
    vehicle_make = models.CharField(max_length=50)
    vehicle_model = models.CharField(max_length=50)

    class Meta:
        managed = False  # This is the key: tells Django not to touch this in the database
        db_table = 'vw_detailed_reviews' # Links this model to our database view


# MySQL Views for Payment Statuses
class CompletedPayment(models.Model):
    """
    Read-only model for completed payments view
    """
    PAYMENT_METHODS = [('Cash', 'Cash'), ('Credit Card', 'Credit Card'), ('Debit Card', 'Debit Card'), ('UPI', 'UPI'), ('Net Banking', 'Net Banking')]
    PAYMENT_TYPES = [('Advance', 'Advance'), ('Full Payment', 'Full Payment'), ('Security Deposit', 'Security Deposit'), ('Fine', 'Fine'), ('Refund', 'Refund')]
    PAYMENT_STATUS = [('Pending', 'Pending'), ('Completed', 'Completed'), ('Failed', 'Failed'), ('Refunded', 'Refunded')]

    id = models.IntegerField(primary_key=True)
    booking = models.ForeignKey(RentalBooking, on_delete=models.DO_NOTHING, to_field='id')
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING, to_field='id')
    payment_date = models.DateTimeField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    transaction_id = models.CharField(max_length=50, blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS)
    reference_number = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    processed_by = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'vw_completed_payments'

    def __str__(self):
        return f"Completed Payment {self.id}"


class PendingPayment(models.Model):
    """
    Read-only model for pending payments view
    """
    PAYMENT_METHODS = [('Cash', 'Cash'), ('Credit Card', 'Credit Card'), ('Debit Card', 'Debit Card'), ('UPI', 'UPI'), ('Net Banking', 'Net Banking')]
    PAYMENT_TYPES = [('Advance', 'Advance'), ('Full Payment', 'Full Payment'), ('Security Deposit', 'Security Deposit'), ('Fine', 'Fine'), ('Refund', 'Refund')]
    PAYMENT_STATUS = [('Pending', 'Pending'), ('Completed', 'Completed'), ('Failed', 'Failed'), ('Refunded', 'Refunded')]

    id = models.IntegerField(primary_key=True)
    booking = models.ForeignKey(RentalBooking, on_delete=models.DO_NOTHING, to_field='id')
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING, to_field='id')
    payment_date = models.DateTimeField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    transaction_id = models.CharField(max_length=50, blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS)
    reference_number = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    processed_by = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'vw_pending_payments'

    def __str__(self):
        return f"Pending Payment {self.id}"


class RefundedPayment(models.Model):
    """
    Read-only model for refunded payments view
    """
    PAYMENT_METHODS = [('Cash', 'Cash'), ('Credit Card', 'Credit Card'), ('Debit Card', 'Debit Card'), ('UPI', 'UPI'), ('Net Banking', 'Net Banking')]
    PAYMENT_TYPES = [('Advance', 'Advance'), ('Full Payment', 'Full Payment'), ('Security Deposit', 'Security Deposit'), ('Fine', 'Fine'), ('Refund', 'Refund')]
    PAYMENT_STATUS = [('Pending', 'Pending'), ('Completed', 'Completed'), ('Failed', 'Failed'), ('Refunded', 'Refunded')]

    id = models.IntegerField(primary_key=True)
    booking = models.ForeignKey(RentalBooking, on_delete=models.DO_NOTHING, to_field='id')
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING, to_field='id')
    payment_date = models.DateTimeField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    transaction_id = models.CharField(max_length=50, blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS)
    reference_number = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    processed_by = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'vw_refunded_payments'

    def __str__(self):
        return f"Refunded Payment {self.id}"


class FailedPayment(models.Model):
    """
    Read-only model for failed payments view
    """
    PAYMENT_METHODS = [('Cash', 'Cash'), ('Credit Card', 'Credit Card'), ('Debit Card', 'Debit Card'), ('UPI', 'UPI'), ('Net Banking', 'Net Banking')]
    PAYMENT_TYPES = [('Advance', 'Advance'), ('Full Payment', 'Full Payment'), ('Security Deposit', 'Security Deposit'), ('Fine', 'Fine'), ('Refund', 'Refund')]
    PAYMENT_STATUS = [('Pending', 'Pending'), ('Completed', 'Completed'), ('Failed', 'Failed'), ('Refunded', 'Refunded')]

    id = models.IntegerField(primary_key=True)
    booking = models.ForeignKey(RentalBooking, on_delete=models.DO_NOTHING, to_field='id')
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING, to_field='id')
    payment_date = models.DateTimeField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    transaction_id = models.CharField(max_length=50, blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS)
    reference_number = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    processed_by = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'vw_failed_payments'

    def __str__(self):
        return f"Failed Payment {self.id}"
=======

class CustomerDetailsView(models.Model):
    """
    This is an UNMANAGED model that represents the V_CustomerDetails database view.
    'managed = False' tells Django not to create, modify, or delete the
    underlying database table/view for this model. We manage it manually
    with SQL in our migration files.
    """
    id = models.IntegerField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    registration_date = models.DateTimeField()
    is_verified = models.BooleanField()
    membership_tier = models.CharField(max_length=10)
    profile_picture = models.CharField(max_length=100, blank=True, null=True)
    license_number = models.CharField(max_length=20, blank=True, null=True)
    total_bookings = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'V_CustomerDetails' # The name of our database view

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
>>>>>>> 95b19fba1109557a00be7f13a177d5081bad2746
