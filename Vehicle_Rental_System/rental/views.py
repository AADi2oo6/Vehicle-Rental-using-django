from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, F
from django.db.models.functions import TruncMonth, TruncDay
from django.core.cache import cache
from django.contrib.auth.hashers import make_password, check_password
from django.utils.dateparse import parse_datetime
from datetime import date, timedelta
from .models import Vehicle, Customer, FeedbackReview, RentalBooking, Payment, MaintenanceRecord
from django.http import JsonResponse
from django.db.models import Sum

@login_required
def get_dashboard_data(request):
    total_revenue = Payment.objects.filter(payment_status='Completed').aggregate(total=Sum('amount'))['total'] or 0
    pending_payments_count = Payment.objects.filter(payment_status='Pending').count()
    active_rentals_count = RentalBooking.objects.filter(booking_status='Active').count()
    maintenance_vehicles_count = Vehicle.objects.filter(status='Maintenance').count()

    data = {
        'total_revenue': total_revenue,
        'pending_payments_count': pending_payments_count,
        'active_rentals_count': active_rentals_count,
        'maintenance_vehicles_count': maintenance_vehicles_count,
    }
    return JsonResponse(data)
# User-facing Views
def home_view(request):
    customer = None
    customer_id = request.session.get('customer_id')
    if customer_id:
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            del request.session['customer_id']
    search_results = None
    if 'location' in request.GET and request.GET['location']:
        vehicle_type = request.GET.get('vehicle_type')
        location = request.GET.get('location')
        pickup_str = request.GET.get('pickup_datetime')
        return_str = request.GET.get('return_datetime')
        results = Vehicle.objects.filter(status='Available')
        if vehicle_type:
            results = results.filter(vehicle_type=vehicle_type)
        if location:
            results = results.filter(location__icontains=location)
        if pickup_str and return_str:
            pickup_datetime = parse_datetime(pickup_str)
            return_datetime = parse_datetime(return_str)
            if pickup_datetime and return_datetime and return_datetime > pickup_datetime:
                conflicting_vehicle_ids = RentalBooking.objects.filter(
                    pickup_datetime__lt=return_datetime,
                    return_datetime__gt=pickup_datetime
                ).values_list('vehicle_id', flat=True)
                results = results.exclude(id__in=conflicting_vehicle_ids)
        search_results = results
    featured_vehicles = Vehicle.objects.filter(status='Available')[:4]
    vehicle_count = Vehicle.objects.filter(status='Available').count()
    customer_count = Customer.objects.count()
    reviews = FeedbackReview.objects.select_related('customer', 'vehicle').order_by('-review_date')[:3]
    location_count = Vehicle.objects.values('location').distinct().count()
    context = {
        'customer': customer,
        'search_results': search_results,
        'values': request.GET,
        'featured_vehicles': featured_vehicles,
        'vehicle_count': vehicle_count,
        'customer_count': customer_count,
        'location_count': location_count,
        'reviews': reviews,
    }
    return render(request, "index.html", context)
def register_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password')
        if not all([full_name, email, password]):
            messages.error(request, 'All fields are required.')
            return redirect('home')
        if Customer.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
            return redirect('home')
        try:
            first_name, last_name = full_name.split(' ', 1)
        except ValueError:
            first_name, last_name = full_name, ""
        hashed_password = make_password(password)
        Customer.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hashed_password,
            phone="0000000000",
        )
        messages.success(request, 'Registration successful! Please log in.')
        return redirect('home')
    return redirect('home')
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            customer = Customer.objects.get(email=email)
            if check_password(password, customer.password):
                request.session['customer_id'] = customer.id
                messages.success(request, f'Welcome back, {customer.first_name}!')
            else:
                messages.error(request, 'Invalid email or password.')
        except Customer.DoesNotExist:
            messages.error(request, 'Invalid email or password.')
        return redirect('home')
    return redirect('home')
def logout_view(request):
    try:
        del request.session['customer_id']
    except KeyError:
        pass
    messages.success(request, "You have been logged out.")
    return redirect('home')

# New custom admin dashboard views

@login_required
def admin_dashboard_view(request):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('home')
    total_revenue = Payment.objects.filter(payment_status='Completed').aggregate(total=Sum('amount'))['total'] or 0
    pending_payments_count = Payment.objects.filter(payment_status='Pending').count()
    active_rentals_count = RentalBooking.objects.filter(booking_status='Active').count()
    maintenance_vehicles_count = Vehicle.objects.filter(status='Maintenance').count()
    context = {
        'total_revenue': total_revenue,
        'pending_payments_count': pending_payments_count,
        'active_rentals_count': active_rentals_count,
        'maintenance_vehicles_count': maintenance_vehicles_count,
    }
    return render(request, "admin/dashboard.html", context)

# Add this new view for AJAX requests
@login_required
def get_dashboard_data(request):
    """
    Returns the latest dashboard data as a JSON response for AJAX requests.
    This view enables dynamic updates without a full page reload.
    """
    if not request.user.is_superuser:
        return JsonResponse({'error': 'You do not have permission to view this data.'}, status=403)
    
    total_revenue = Payment.objects.filter(payment_status='Completed').aggregate(total=Sum('amount'))['total'] or 0
    pending_payments_count = Payment.objects.filter(payment_status='Pending').count()
    active_rentals_count = RentalBooking.objects.filter(booking_status='Active').count()
    maintenance_vehicles_count = Vehicle.objects.filter(status='Maintenance').count()
    
    data = {
        'total_revenue': total_revenue,
        'pending_payments_count': pending_payments_count,
        'active_rentals_count': active_rentals_count,
        'maintenance_vehicles_count': maintenance_vehicles_count,
    }
    return JsonResponse(data)
@login_required
def admin_maintenance_view(request):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('home')
    maintenance_records = MaintenanceRecord.objects.select_related('vehicle').order_by('-maintenance_date')
    upcoming_maintenance = MaintenanceRecord.objects.filter(
        status='Scheduled',
        maintenance_date__gte=date.today()
    ).order_by('maintenance_date')
    cost_per_vehicle = MaintenanceRecord.objects.values('vehicle__make', 'vehicle__model').annotate(
        total_cost=Sum('cost')
    ).order_by('-total_cost')
    context = {
        'maintenance_records': maintenance_records,
        'upcoming_maintenance': upcoming_maintenance,
        'cost_per_vehicle': cost_per_vehicle,
    }
    return render(request, "admin/maintenance.html", context)
@login_required
def admin_queries_view(request):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('home')
    queries = cache.get('all_sql_queries', [])
    context = {
        'queries': queries
    }
    return render(request, "queries.html", context)

# Combined Payments Management View
@login_required
def payments_management_view(request):
    """
    Combines all professional views for the Payment table into a single view.
    - Single Table Read-Only
    - Multi-table View
    - Aggregate Functions
    - CRUD Operations (links for add/edit/delete)
    """
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('home')
    
    # This handles the main list view and multi-table data
    payments = Payment.objects.select_related('customer', 'booking__vehicle').order_by('-payment_date')
    
    # Filtering and Sorting logic
    sort_by = request.GET.get('sort', 'payment_date')
    order = request.GET.get('order', 'desc')
    if order == 'asc':
        payments = payments.order_by(sort_by)
    else:
        payments = payments.order_by(f'-{sort_by}')
    payment_status = request.GET.get('status')
    if payment_status:
        payments = payments.filter(payment_status=payment_status)

    # Aggregation for reports
    monthly_revenue = Payment.objects.filter(payment_status='Completed').annotate(
        month=TruncMonth('payment_date')
    ).values('month').annotate(
        total_revenue=Sum('amount')
    ).order_by('month')
    top_customers = Payment.objects.filter(payment_status='Completed').values(
        'customer__first_name', 'customer__last_name'
    ).annotate(
        total_spent=Sum('amount')
    ).order_by('-total_spent')[:10]

    context = {
        'payments': payments,
        'monthly_revenue': monthly_revenue,
        'top_customers': top_customers,
        'selected_status': payment_status,
        'sort_by': sort_by,
        'order': order,
    }
    return render(request, "admin/payments.html", context)

@login_required
def payment_form_view(request, payment_id=None):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('home')

    payment = None
    if payment_id:
        payment = get_object_or_404(Payment, id=payment_id)
    
    if request.method == 'POST':
        # Get data from the POST request
        booking_id = request.POST.get('booking')
        customer_id = request.POST.get('customer')
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method')
        payment_status = request.POST.get('payment_status')

        try:
            # Retrieve the related objects from the database
            booking = get_object_or_404(RentalBooking, id=booking_id)
            customer = get_object_or_404(Customer, id=customer_id)

            if payment_id:
                # Update existing payment instance
                payment.booking = booking
                payment.customer = customer
                payment.amount = amount
                payment.payment_method = payment_method
                payment.payment_status = payment_status
                payment.save()
                messages.success(request, "Payment updated successfully.")
            else:
                # Create a new Payment instance
                Payment.objects.create(
                    booking=booking,
                    customer=customer,
                    amount=amount,
                    payment_method=payment_method,
                    payment_status=payment_status,
                )
                messages.success(request, "New payment added successfully.")
            
            return redirect('payments_management')

        except (RentalBooking.DoesNotExist, Customer.DoesNotExist):
            messages.error(request, "One or more provided IDs (Booking or Customer) do not exist. Please check your input.")
            return redirect(request.path) # Stay on the same page with an error message

    context = {'payment': payment}
    return render(request, "admin/payment_form.html", context)

@login_required
def payment_delete_view(request, payment_id):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('home')
    payment = get_object_or_404(Payment, id=payment_id)
    if request.method == 'POST':
        payment.delete()
        messages.success(request, f"Payment ID {payment.id} deleted successfully.")
    return redirect('payments_management')
    pass