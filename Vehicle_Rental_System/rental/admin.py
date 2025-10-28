from django.contrib import admin
from .models import Customer, Vehicle, RentalBooking, Payment, FeedbackReview

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'is_verified', 'is_active')
    search_fields = ('first_name', 'last_name', 'email', 'license_number')
    list_filter = ('is_active', 'is_verified', 'state')

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle_number', 'make', 'model', 'vehicle_type', 'status', 'hourly_rate') # Changed daily_rate to hourly_rate
    search_fields = ('vehicle_number', 'make', 'model')
    list_filter = ('vehicle_type', 'status', 'fuel_type', 'location')

@admin.register(RentalBooking)
class RentalBookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'vehicle', 'pickup_datetime', 'return_datetime', 'booking_status', 'total_amount') # Changed date fields
    search_fields = ('customer__first_name', 'vehicle__vehicle_number')
    list_filter = ('booking_status', 'pickup_location')
    raw_id_fields = ('customer', 'vehicle')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'customer', 'amount', 'payment_method', 'payment_status', 'payment_date')
    search_fields = ('booking__id', 'customer__first_name', 'transaction_id')
    list_filter = ('payment_method', 'payment_status', 'payment_type')

@admin.register(FeedbackReview)
class FeedbackReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'customer', 'vehicle', 'rating', 'review_date')
    search_fields = ('customer__first_name', 'vehicle__vehicle_number')
    list_filter = ('rating',)
