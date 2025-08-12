from django.contrib import admin
from .models import Customer, Vehicle, RentalBooking, Payment, MaintenanceRecord, FeedbackReview

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email', 'phone', 'is_active')
    search_fields = ('first_name', 'last_name', 'email', 'license_number')

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('id', 'vehicle_number', 'make', 'model', 'status', 'daily_rate')
    list_filter = ('vehicle_type', 'fuel_type', 'status')

@admin.register(RentalBooking)
class RentalBookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'vehicle', 'pickup_date', 'return_date', 'booking_status')
    list_filter = ('booking_status',)
    search_fields = ('customer__first_name', 'vehicle__vehicle_number')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'customer', 'amount', 'payment_type', 'payment_status')
    list_filter = ('payment_status', 'payment_type', 'payment_method')

@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'vehicle', 'maintenance_date', 'maintenance_type', 'cost', 'status')

@admin.register(FeedbackReview)
class FeedbackReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'vehicle', 'rating', 'review_date', 'is_public')
    list_filter = ('is_public',)
