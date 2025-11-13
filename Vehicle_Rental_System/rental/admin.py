from django.contrib import admin
from .models import Customer, Vehicle, RentalBooking, Payment, MaintenanceRecord, FeedbackReview
from django.urls import path
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import HttpResponse
from django.db import connection
import csv

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'is_verified', 'is_active')
    search_fields = ('first_name', 'last_name', 'email', 'license_number')
    list_filter = ('is_active', 'is_verified', 'state')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('manage/', self.admin_site.admin_view(self.customer_list_view), name='admin_customers'),
            path('manage/<int:customer_id>/', self.admin_site.admin_view(self.customer_detail_view), name='admin_customer_detail'),
            path('export-csv/', self.admin_site.admin_view(self.export_customers_csv), name='export_customers_csv'),
        ]
        return custom_urls + urls

    def export_customers_csv(self, request):
        """
        Handles the logic for exporting filtered customer data to a CSV file.
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="customers.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'First Name', 'Last Name', 'Email', 'Phone', 'Address', 'City', 'State', 'Zip Code', 'Verified', 'Active', 'Registration Date'])

        # Get the same queryset as the list view by re-applying filters
        queryset = Customer.objects.all().order_by('id')

        search_query = request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(license_number__icontains=search_query)
            )

        city = request.GET.get('city', '')
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        state = request.GET.get('state', '')
        if state:
            queryset = queryset.filter(state__icontains=state)

        for customer in queryset.values_list('id', 'first_name', 'last_name', 'email', 'phone', 'address', 'city', 'state', 'zip_code', 'is_verified', 'is_active', 'registration_date'):
            writer.writerow(customer)

        return response

    def customer_list_view(self, request):
        # Handle Bulk Actions
        if request.method == 'POST' and request.POST.get('bulk_action'):
            action = request.POST.get('action')
            customer_ids = request.POST.getlist('customer_ids')
            queryset = Customer.objects.filter(id__in=customer_ids)

            if not queryset.exists():
                messages.warning(request, "You didn't select any customers.")
                return redirect('admin:admin_customers')

            if action == 'verify_selected':
                updated_count = queryset.update(is_verified=True)
                messages.success(request, f'Successfully verified {updated_count} customer(s).')
            elif action == 'unverify_selected':
                updated_count = queryset.update(is_verified=False)
                messages.success(request, f'Successfully un-verified {updated_count} customer(s).')
            elif action == 'activate_selected':
                updated_count = queryset.update(is_active=True)
                messages.success(request, f'Successfully activated {updated_count} customer(s).')
            elif action == 'deactivate_selected':
                updated_count = queryset.update(is_active=False)
                messages.success(request, f'Successfully deactivated {updated_count} customer(s).')
            else:
                messages.error(request, 'Invalid bulk action selected.')
            
            return redirect('admin:admin_customers')

        # Initial queryset
        queryset = Customer.objects.all()

        # Search
        search_query = request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(license_number__icontains=search_query)
            )

        # Filtering by city and state
        city = request.GET.get('city', '')
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        state = request.GET.get('state', '')
        if state:
            queryset = queryset.filter(state__icontains=state)

        # Verification status tabs
        verification_status = request.GET.get('verification_status', '')
        if verification_status == 'verified':
            queryset = queryset.filter(is_verified=True)
        elif verification_status == 'unverified':
            queryset = queryset.filter(is_verified=False)

        # Sorting
        sort_by = request.GET.get('sort', 'registration_date')
        order = request.GET.get('order', 'desc')
        if order == 'desc':
            sort_by = f'-{sort_by}'
        queryset = queryset.order_by(sort_by)

        total_customers = queryset.count() # This should be before pagination if you add it

        context = {
            'title': 'Customer Management',
            'customers': queryset,
            'total_customers': total_customers,
            'search_query': search_query,
            'city': city,
            'state': state,
            'verification_status': verification_status,
            'sort_by': request.GET.get('sort', 'registration_date'),
            'order': request.GET.get('order', 'desc'),
        }
        return render(request, 'admin/customers.html', context)

    def customer_detail_view(self, request, customer_id):
        customer = get_object_or_404(Customer, id=customer_id)
        bookings = RentalBooking.objects.filter(customer=customer).order_by('-pickup_datetime')
        payments = Payment.objects.filter(customer=customer).order_by('-payment_date')

        # --- Raw SQL Query with JOIN and Correlated Subquery ---
        analytics_data = None
        query = """
            SELECT
                COUNT(p.id) AS total_transactions,
                SUM(p.amount) AS total_spent,
                (
                    SELECT MIN(rb.booking_date)
                    FROM rental_rentalbooking rb
                    WHERE rb.customer_id = c.id
                ) AS first_booking_date
            FROM
                rental_customer c
            LEFT JOIN
                rental_payment p ON c.id = p.customer_id AND p.payment_status = 'Completed'
            WHERE
                c.id = %s
            GROUP BY
                c.id;
        """
        with connection.cursor() as cursor:
            cursor.execute(query, [customer_id])
            row = cursor.fetchone()
            if row:
                analytics_data = {'total_transactions': row[0], 'total_spent': row[1], 'first_booking_date': row[2]}

        context = {
            'title': f'Customer Details: {customer.first_name}',
            'customer': customer,
            'bookings': bookings,
            'payments': payments,
            'analytics': analytics_data,
        }
        return render(request, 'admin/customer_detail.html', context)


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

    def has_add_permission(self, request):
        """
        Disables the "Add" button and functionality for RentalBookings in the admin.
        Bookings should be created via the application's frontend workflow.
        """
        return False

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'customer', 'amount', 'payment_method', 'payment_status', 'payment_date')
    search_fields = ('booking__id', 'customer__first_name', 'transaction_id')
    list_filter = ('payment_method', 'payment_status', 'payment_type')

@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'vehicle', 'maintenance_date', 'maintenance_type', 'cost', 'status')
    search_fields = ('vehicle__vehicle_number',)
    list_filter = ('maintenance_type', 'status')

@admin.register(FeedbackReview)
class FeedbackReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'customer', 'vehicle', 'rating', 'review_date')
    search_fields = ('customer__first_name', 'vehicle__vehicle_number')
    list_filter = ('rating',)


from .models import ActivityLog

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'customer', 'action_type', 'details')
    list_filter = ('action_type', 'timestamp')
    search_fields = ('details', 'customer__email')