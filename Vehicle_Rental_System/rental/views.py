from django.shortcuts import render, redirect, get_object_or_404
from .utils import dictfetchall
from django.db import connection, transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum, F
from django.contrib.auth.models import User
from django.contrib.auth import (
    authenticate, 
    login, 
    logout, 
    update_session_auth_hash
)
from django.core.cache import cache
from django.contrib.auth.hashers import make_password, check_password
from django.urls import reverse
from django.contrib.auth.forms import PasswordChangeForm
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from django.http import HttpResponse
from django.utils.dateparse import parse_datetime
from django.db import transaction
from datetime import date, timedelta, datetime
import csv
from .models import Vehicle, Customer, FeedbackReview, RentalBooking, Payment, MaintenanceRecord, CustomerActivityLog
from django.http import JsonResponse
from django.db.models import Sum
from .forms import PaymentForm, CustomerProfileForm, CustomerPictureForm
from .models import Payment
from .forms import AdminBookingForm # Import the new form
=======
from django.utils.dateparse import parse_datetime
import csv
from django.http import HttpResponse, JsonResponse
from datetime import date, timedelta, datetime
=======
from django.utils.dateparse import parse_datetime
import csv
from django.http import HttpResponse, JsonResponse
from datetime import date, timedelta, datetime
>>>>>>> Stashed changes
=======
from django.utils.dateparse import parse_datetime
import csv
from django.http import HttpResponse, JsonResponse
from datetime import date, timedelta, datetime
>>>>>>> Stashed changes
=======
from django.utils.dateparse import parse_datetime
import csv
from django.http import HttpResponse, JsonResponse
from datetime import date, timedelta, datetime
>>>>>>> Stashed changes
=======
from django.utils.dateparse import parse_datetime
import csv
from django.http import HttpResponse, JsonResponse
from datetime import date, timedelta, datetime
>>>>>>> Stashed changes

from .models import (
    Vehicle, 
    Customer, 
    FeedbackReview, 
    RentalBooking, 
    Payment, 
    MaintenanceRecord, 
    CustomerActivityLog
)
from .forms import (
    PaymentForm, 
    CustomerProfileForm, 
    CustomerPictureForm, 
    AdminBookingForm,
    MaintenanceRecordForm
)
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

@login_required
def get_dashboard_data(request):
    """
    Returns the latest dashboard data as a JSON response for AJAX requests.
    This view enables dynamic updates without a full page reload.
    """
    if not request.user.is_superuser:
        return JsonResponse({'error': 'You do not have permission to view this data.'}, status=403)

    data = {
        'total_revenue': 12345.67,
        'active_rentals': 8,
        'pending_payments': 3,
        'maintenance_vehicles': 2,
    }
    return JsonResponse(data)
# User-facing Views

def home_view(request):
    search_results = None
    if 'location' in request.GET and request.GET['location']:
        vehicle_type = request.GET.get('vehicle_type')
        location = request.GET.get('location')
        pickup_str = request.GET.get('pickup_datetime')
        return_str = request.GET.get('return_datetime')

        pickup_datetime = parse_datetime(pickup_str) if pickup_str else None
        return_datetime = parse_datetime(return_str) if return_str else None

        search_results = Vehicle.objects.filter(
            location__icontains=location,
            vehicle_type=vehicle_type,
            status='Available'
        ).exclude(
            rentalbooking__pickup_datetime__lt=return_datetime,
            rentalbooking__return_datetime__gt=pickup_datetime
        )

    featured_vehicles = Vehicle.objects.filter(status='Available').order_by('?')[:4]
    reviews = FeedbackReview.objects.select_related('customer', 'vehicle').order_by('-review_date')[:3]
    location_count = Vehicle.objects.values('location').distinct().count()
    context = {
        'search_results': search_results,
        'values': request.GET,
        'featured_vehicles': featured_vehicles,
        'reviews': reviews,
        'customer_count': Customer.objects.count(),
        'vehicle_count': Vehicle.objects.filter(status='Available').count(),
        'location_count': location_count,
    }
    return render(request, "index.html", context)
def register_view(request):
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        return redirect('home')

    if request.method == 'POST':
        full_name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password')

        if not all([full_name, email, password]):
            messages.error(request, 'All fields are required.')
            return redirect('home')

        if User.objects.filter(username=email).exists():
            messages.error(request, 'A user with this email (username) already exists.')
            return redirect('home')

        try:
            first_name, last_name = full_name.split(' ', 1)
        except ValueError:
            first_name, last_name = full_name, ""

        try:
            with transaction.atomic():
                # Create Django User
                user = User.objects.create_user(
                    username=email, # Use email as username for simplicity
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                # Customer profile will be created by post_save signal
                messages.success(request, 'Registration successful! Please log in.')
                return redirect('home')
        except Exception as e:
            messages.error(request, f'An error occurred during registration: {e}')
            return redirect('home')
    return redirect('home') # Redirect if GET request

def login_view(request):
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            # Use get_or_create to prevent errors if a Customer profile is missing for an existing User.
            # This is a robust way to handle cases like a superuser created via command line.
            customer, created = Customer.objects.get_or_create(
                user=user,
                defaults={'email': user.email, 'first_name': user.first_name, 'last_name': user.last_name}
            )
            request.session['customer_id'] = customer.id # Keep for legacy code if needed

            if user.is_superuser:
                messages.success(request, f'Welcome back, Admin {user.first_name}!')
                return redirect('admin_dashboard')
            else:
                messages.success(request, f'Welcome back, {user.first_name}!')
                return redirect('home')
        else:
            messages.error(request, 'Invalid email or password.')
            return redirect('home')
    return redirect('home') # Redirect if GET request

def logout_view(request):
    logout(request)
    request.session.pop('customer_id', None) # Safely remove customer_id from session
    messages.success(request, "You have been logged out.")
    return redirect('home')

def vehicle_list_view(request):
    """
    Displays a filterable and paginated list of all available vehicles.
    """

    # Base queryset for available vehicles
    vehicle_list = Vehicle.objects.filter(status='Available').order_by('make', 'model')

    # Filtering logic
    if 'type' in request.GET and request.GET['type']:
        vehicle_list = vehicle_list.filter(vehicle_type=request.GET['type'])
    if 'fuel' in request.GET and request.GET['fuel']:
        vehicle_list = vehicle_list.filter(fuel_type=request.GET['fuel'])

    # Sorting logic
    sort_by = request.GET.get('sort', 'make')
    if sort_by == 'price_asc':
        vehicle_list = vehicle_list.order_by('hourly_rate')
    elif sort_by == 'price_desc':
        vehicle_list = vehicle_list.order_by('-hourly_rate')
    else: # Default to 'make'
        vehicle_list = vehicle_list.order_by('make', 'model')

    # Pagination
    paginator = Paginator(vehicle_list, 9) # 9 vehicles per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'vehicles': page_obj,
        'values': request.GET, # To retain filter values in the form
    }
    return render(request, "vehicles.html", context)

@login_required
def booking_view(request, vehicle_id):
    """
    Handles the booking process for a specific vehicle.
    """
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    customer = get_object_or_404(Customer, user=request.user)

    if request.method == 'POST':
        # Process booking form
        pickup_datetime_str = request.POST.get('pickup_datetime')
        return_datetime_str = request.POST.get('return_datetime')
        pickup_location = request.POST.get('pickup_location')
        return_location = request.POST.get('return_location')

        pickup_datetime = parse_datetime(pickup_datetime_str)
        return_datetime = parse_datetime(return_datetime_str)

        duration_hours = (return_datetime - pickup_datetime).total_seconds() / 3600
        total_amount = duration_hours * vehicle.hourly_rate

        with transaction.atomic():
            booking = RentalBooking.objects.create(
                customer=customer,
                vehicle=vehicle,
                pickup_datetime=pickup_datetime,
                return_datetime=return_datetime,
                pickup_location=pickup_location,
                return_location=return_location,
                hourly_rate=vehicle.hourly_rate,
                total_amount=total_amount,
                security_deposit=5000, # Example fixed security deposit
                booking_status='Confirmed'
            )
            messages.success(request, f"Booking successful for {vehicle.make} {vehicle.model}!")
            return redirect('my_bookings')

    context = {
        'vehicle': vehicle,
    }
    return render(request, "booking.html", context)

def about_us_view(request):
    """
    Renders the About Us page.
    """
    # Customer object is now available via context processor if logged in
    context = {
        # 'customer' will be in context if user is authenticated
    }
    return render(request, "about_us.html", context)

@login_required
def my_profile_view(request):
    """
    Displays the logged-in user's profile information and booking history.
    """
    customer = get_object_or_404(Customer, user=request.user)

    # Fetch the user's bookings
    bookings = RentalBooking.objects.filter(customer=customer).select_related('vehicle').order_by('-booking_date')

    context = {
        'customer': customer,
        'bookings': bookings,
    }
    return render(request, "my_profile.html", context)

@login_required
def edit_profile_view(request):
    """
    Allows a logged-in user to edit their profile information.
    """
    customer = get_object_or_404(Customer, user=request.user)

    if request.method == 'POST':
        # Instantiate both forms with POST data
        profile_form = CustomerProfileForm(request.POST, instance=customer)
        picture_form = CustomerPictureForm(request.POST, request.FILES, instance=customer)

        # Check which form was submitted based on a hidden input or button name if needed,
        # but here we can just check both.
        if profile_form.is_valid() and picture_form.is_valid():
            profile_form.save()
            picture_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('my_profile')
        else:
            messages.error(request, "There was an error updating your profile. Please correct the errors below.")
    else:
        # For GET request, instantiate forms with current customer data
        profile_form = CustomerProfileForm(instance=customer)
        picture_form = CustomerPictureForm(instance=customer)

    context = {
        'customer': customer,
        'profile_form': profile_form,
        'picture_form': picture_form,
    }
    return render(request, "edit_profile.html", context)



@login_required
def my_bookings_view(request):
    """
    Displays a paginated list of all bookings for the logged-in user.
    """
    customer = get_object_or_404(Customer, user=request.user)

    # Fetch all user's bookings
    booking_list = RentalBooking.objects.filter(customer=customer).select_related('vehicle').order_by('-booking_date')

    # Pagination
    paginator = Paginator(booking_list, 5) # 5 bookings per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'customer': customer,
        'bookings': page_obj,
    }
    return render(request, "my_bookings.html", context)


@user_passes_test(lambda u: u.is_superuser) # Only superusers can access admin dashboard
@login_required # This decorator is still needed for user_passes_test to work
def admin_dashboard_view(request): # Renamed to avoid conflict with existing get_dashboard_data
    """
    Retrieves key metrics (revenue, counts). Attempts Stored Procedure call
    but falls back to reliable ORM calculation.
    """
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======

>>>>>>> Stashed changes
=======

>>>>>>> Stashed changes
=======

>>>>>>> Stashed changes
=======

>>>>>>> Stashed changes
=======

>>>>>>> Stashed changes
    # --- Calculate All-Time Total Revenue using the ORM ---
    total_revenue = Payment.objects.filter(
        payment_status='Completed'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # --- Remaining Django ORM Queries ---
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    pending_payments_count = Payment.objects.filter(payment_status='Pending').count()
    current_month = date.today().month
    current_year = date.today().year
    total_revenue = 0

    try:
        with connection.cursor() as cursor:
            # Stored Procedure call
            cursor.callproc('GET_MONTHLY_REVENUE', [current_year, current_month, 0])
            # Fetch the output parameter
            cursor.execute("SELECT @_GET_MONTHLY_REVENUE_2")
            result = cursor.fetchone()
            if result and result[0] is not None:
                total_revenue = result[0]
            else:
                # Fallback to ORM if procedure fails or returns NULL
                total_revenue = Payment.objects.filter(
                    payment_date__year=current_year,
                    payment_date__month=current_month
                ).aggregate(Sum('amount'))['amount__sum'] or 0
    except Exception:
        # Fallback to ORM on any exception
        total_revenue = Payment.objects.filter(
            payment_date__year=current_year,
            payment_date__month=current_month
        ).aggregate(Sum('amount'))['amount__sum'] or 0

    # Other stats using ORM
    active_rentals_count = RentalBooking.objects.filter(booking_status='Active').count()
    pending_payments_count = Payment.objects.filter(payment_status='Pending').count()
    maintenance_vehicles_count = Vehicle.objects.filter(status='Maintenance').count()
    recent_bookings = RentalBooking.objects.select_related('customer', 'vehicle').order_by('-booking_date')[:5]
    recent_payments = Payment.objects.select_related('customer').order_by('-payment_date')[:5]

    context = {
        'total_revenue': total_revenue,
        'active_rentals_count': active_rentals_count,
        'pending_payments_count': pending_payments_count,
        'maintenance_vehicles_count': maintenance_vehicles_count,
        'recent_bookings': recent_bookings,
        'recent_payments': recent_payments,
    }
    return render(request, "admin_dashboard_bootstrap.html", context)

# Add this new view for AJAX requests
@login_required
def get_dashboard_data_ajax(request): # Renamed to avoid conflict with existing get_dashboard_data
    if not request.user.is_superuser:
        return JsonResponse({'error': 'You do not have permission to view this data.'}, status=403)

    data = {
        'total_revenue': 12345.67,
        'active_rentals': 8,
        'pending_payments': 3,
        'maintenance_vehicles': 2,
    }
    return JsonResponse(data)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_maintenance_view(request):
    """
    Displays maintenance records, upcoming services, and cost analytics.
    Allows filtering maintenance history for a specific vehicle.
    Handles adding new maintenance records.
    """
<<<<<<< Updated upstream
    # Handle form submission for adding a new record
    if request.method == 'POST':
        form = MaintenanceRecordForm(request.POST)
        if form.is_valid():
            # The form's clean method now handles vehicle validation and assignment.
            # We can just save the form directly.
=======
    if request.method == 'POST':
        form = MaintenanceRecordForm(request.POST)
        if form.is_valid():
>>>>>>> Stashed changes
            maintenance_record = form.save()
            messages.success(
                request,
                f"New maintenance record for Vehicle ID {maintenance_record.vehicle.id} added successfully."
            )
<<<<<<< Updated upstream
            # Redirect to the maintenance page, filtered by the vehicle that was just added.
            return redirect(f"{reverse('admin_maintenance')}?vehicle_id={maintenance_record.vehicle.id}")
        else:
            messages.error(request, "Please correct the errors below.")
            # If form is invalid, we will fall through and re-render the page with the form containing errors.
            # The form passed to context will contain the errors for display.
    else:
        # This is a GET request, so create a blank form
        # Pre-fill vehicle if vehicle_id is in GET params
=======
            return redirect(f"{reverse('admin_maintenance')}?vehicle_id={maintenance_record.vehicle.id}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
>>>>>>> Stashed changes
        initial_data = {}
        if 'vehicle_id' in request.GET:
            initial_data['vehicle'] = request.GET.get('vehicle_id')
        form = MaintenanceRecordForm(initial=initial_data)

<<<<<<< Updated upstream
    # --- ORM Query for fetching, filtering, and sorting maintenance records ---
=======

>>>>>>> Stashed changes
    sort_by = request.GET.get('sort', 'maintenance_date')
    order = request.GET.get('order', 'desc')
    filter_vehicle_id = request.GET.get('vehicle_id')

    # Base queryset
    maintenance_records = MaintenanceRecord.objects.select_related('vehicle').all()

    # Filtering
    if filter_vehicle_id:
        maintenance_records = maintenance_records.filter(vehicle_id=filter_vehicle_id)

    # Sorting
    valid_sort_fields = ['id', 'maintenance_date', 'cost', 'status', 'vehicle_id']
    if sort_by not in valid_sort_fields:
        sort_by = 'maintenance_date'

    if order == 'desc':
        sort_by = f'-{sort_by}'
    maintenance_records = maintenance_records.order_by(sort_by)

    # --- Other Queries ---
    upcoming_maintenance = MaintenanceRecord.objects.filter(
        status='Scheduled',
        maintenance_date__gt=date.today()
    ).order_by('maintenance_date')
    cost_per_vehicle = MaintenanceRecord.objects.values('vehicle__make', 'vehicle__model').annotate(
        total_cost=Sum('cost')
    ).order_by('-total_cost')

    cost_per_vehicle = MaintenanceRecord.objects.values('vehicle__make', 'vehicle__model').annotate(
        total_cost=Sum('cost')
    ).order_by('-total_cost')

    # --- Raw SQL Query for Total Maintenance Cost ---
    # As requested, execute a raw SQL query to get the aggregate sum of all costs.
    total_maintenance_cost = 0
    with connection.cursor() as cursor:
        # This query calculates the sum of costs directly from the maintenance records table.
        cursor.execute("SELECT SUM(cost) FROM rental_maintenancerecord")
        result = cursor.fetchone()
        if result and result[0] is not None:
            total_maintenance_cost = result[0]

    cost_per_vehicle = MaintenanceRecord.objects.values('vehicle__make', 'vehicle__model').annotate(
        total_cost=Sum('cost')
    ).order_by('-total_cost')

    # --- Raw SQL Query for Total Maintenance Cost ---
    # As requested, execute a raw SQL query to get the aggregate sum of all costs.
    total_maintenance_cost = 0
    with connection.cursor() as cursor:
        # This query calculates the sum of costs directly from the maintenance records table.
        cursor.execute("SELECT SUM(cost) FROM rental_maintenancerecord")
        result = cursor.fetchone()
        if result and result[0] is not None:
            total_maintenance_cost = result[0]

    cost_per_vehicle = MaintenanceRecord.objects.values('vehicle__make', 'vehicle__model').annotate(
        total_cost=Sum('cost')
    ).order_by('-total_cost')

    # --- Raw SQL Query for Total Maintenance Cost ---
    # As requested, execute a raw SQL query to get the aggregate sum of all costs.
    total_maintenance_cost = 0
    with connection.cursor() as cursor:
        # This query calculates the sum of costs directly from the maintenance records table.
        cursor.execute("SELECT SUM(cost) FROM rental_maintenancerecord")
        result = cursor.fetchone()
        if result and result[0] is not None:
            total_maintenance_cost = result[0]

    cost_per_vehicle = MaintenanceRecord.objects.values('vehicle__make', 'vehicle__model').annotate(
        total_cost=Sum('cost')
    ).order_by('-total_cost')

    # --- Raw SQL Query for Total Maintenance Cost ---
    # As requested, execute a raw SQL query to get the aggregate sum of all costs.
    total_maintenance_cost = 0
    with connection.cursor() as cursor:
        # This query calculates the sum of costs directly from the maintenance records table.
        cursor.execute("SELECT SUM(cost) FROM rental_maintenancerecord")
        result = cursor.fetchone()
        if result and result[0] is not None:
            total_maintenance_cost = result[0]

    cost_per_vehicle = MaintenanceRecord.objects.values('vehicle__make', 'vehicle__model').annotate(
        total_cost=Sum('cost')
    ).order_by('-total_cost')

    # --- Raw SQL Query for Total Maintenance Cost ---
    # As requested, execute a raw SQL query to get the aggregate sum of all costs.
    total_maintenance_cost = 0
    with connection.cursor() as cursor:
        # This query calculates the sum of costs directly from the maintenance records table.
        cursor.execute("SELECT SUM(cost) FROM rental_maintenancerecord")
        result = cursor.fetchone()
        if result and result[0] is not None:
            total_maintenance_cost = result[0]

    context = {
        'form': form,
        'maintenance_records': maintenance_records,
        'upcoming_maintenance': upcoming_maintenance,
        'cost_per_vehicle': cost_per_vehicle,
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    }
    return render(request, "admin/maintenance.html", context)

=======
        'total_maintenance_cost': total_maintenance_cost,
        'sort_by': sort_by.lstrip('-'),
        'order': order,
        'filter_vehicle_id': filter_vehicle_id,
    }
    return render(request, "admin/maintenance.html", context)

=======
        'total_maintenance_cost': total_maintenance_cost,
        'sort_by': sort_by.lstrip('-'),
        'order': order,
        'filter_vehicle_id': filter_vehicle_id,
    }
    return render(request, "admin/maintenance.html", context)

>>>>>>> Stashed changes
=======
        'total_maintenance_cost': total_maintenance_cost,
        'sort_by': sort_by.lstrip('-'),
        'order': order,
        'filter_vehicle_id': filter_vehicle_id,
    }
    return render(request, "admin/maintenance.html", context)

>>>>>>> Stashed changes
=======
        'total_maintenance_cost': total_maintenance_cost,
        'sort_by': sort_by.lstrip('-'),
        'order': order,
        'filter_vehicle_id': filter_vehicle_id,
    }
    return render(request, "admin/maintenance.html", context)

>>>>>>> Stashed changes
=======
        'total_maintenance_cost': total_maintenance_cost,
        'sort_by': sort_by.lstrip('-'),
        'order': order,
        'filter_vehicle_id': filter_vehicle_id,
    }
    return render(request, "admin/maintenance.html", context)

>>>>>>> Stashed changes
@login_required
@user_passes_test(lambda u: u.is_superuser)
def update_maintenance_status_view(request, maintenance_id):
    """
    Updates the status of a specific maintenance record.
    This view is intended to be called via POST from the maintenance list.
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('admin_maintenance')

    record = get_object_or_404(MaintenanceRecord, id=maintenance_id)
    new_status = request.POST.get('status')

    # Get the valid status choices directly from the model to ensure correctness
    valid_statuses = [choice[0] for choice in MaintenanceRecord.MAINTENANCE_STATUS_CHOICES]

    if new_status in valid_statuses:
        try:
            with transaction.atomic():
                record.status = new_status
                record.save(update_fields=['status'])

                # Business Logic: If maintenance is completed, make the vehicle available
                if new_status == 'Completed' and record.vehicle.status == 'Maintenance':
                    record.vehicle.status = 'Available'
                    record.vehicle.save(update_fields=['status'])

            messages.success(request, f"Status for record #{record.id} updated to '{new_status}'.")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
    else:
        messages.error(request, f"Invalid status '{new_status}'.")

    return redirect('admin_maintenance')
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_queries_view(request):
    queries = cache.get('all_sql_queries', [])
    
    # Set a flag on the request to prevent the middleware from logging this page's queries
    setattr(request, '_viewing_queries', True)

    context = {
        'queries': queries
    }
    return render(request, "queries.html", context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_payments_view(request):
    """
    Handles payments list, filtering, sorting, and aggregation.
    """

    # --- Base Query ---
    payments = Payment.objects.select_related('customer', 'booking__vehicle').order_by('-payment_date')

    # --- Filtering ---
    search_query = request.GET.get('q', '').strip()
    start_date_str = request.GET.get('start_date', '').strip()
    end_date_str = request.GET.get('end_date', '').strip()
    selected_status = request.GET.get('status', '').strip()

    if search_query:
        payments = payments.filter(
            Q(customer__first_name__icontains=search_query) |
            Q(customer__last_name__icontains=search_query) |
            Q(booking__vehicle__vehicle_number__icontains=search_query) |
            Q(id__icontains=search_query) |
            Q(transaction_id__icontains=search_query)
        )

    if start_date_str:
        payments = payments.filter(payment_date__gte=start_date_str)
    if end_date_str:
        payments = payments.filter(payment_date__lte=end_date_str)
    if selected_status:
        payments = payments.filter(payment_status=selected_status)

    # --- Sorting ---
    sort_by = request.GET.get('sort', '-payment_date')
    order = request.GET.get('order', 'desc')
    if order == 'desc':
        sort_by = f"-{sort_by.lstrip('-')}"
    else:
        sort_by = sort_by.lstrip('-')

    valid_sort_fields = ['id', 'amount', 'payment_date']
    if sort_by.strip('-') in valid_sort_fields:
        payments = payments.order_by(sort_by)

    # --- Aggregation ---
    total_payments = payments.count()
    total_amount = payments.aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        'payments': payments,
        'total_payments': total_payments,
        'total_amount': total_amount,
        'search_query': search_query,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'selected_status': selected_status,
        'sort_by': sort_by.strip('-'),
        'order': order,
    }
    return render(request, "admin/payments.html", context)

def payment_form_view(request, payment_id=None):
    if not request.user.is_superuser: # This view should also be restricted to superusers
        messages.error(request, "You do not have permission to access this page.")
        return redirect('home')
    payment = None
    if payment_id:
        payment = get_object_or_404(Payment, id=payment_id)

    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, f"Payment {'updated' if payment else 'added'} successfully.")
            return redirect('admin_payments')
    else:
        form = PaymentForm(instance=payment)

    return render(request, 'admin/payment_form.html', {'form': form, 'payment': payment})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def payment_delete_view(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    if request.method == 'POST':
        payment.delete()
        messages.success(request, "Payment record deleted successfully.")
    return redirect('admin_payments')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def payment_analytics_view(request):
    """
    Executes and consolidates the results of Self-Join, Correlated Query,
    and Set Operations for advanced payment analytics.
    """
    # --- 1. Self-Join Query (Repeated Transactions) ---
    self_join_query = """
    SELECT
        p1.customer_id,
        c.first_name,
        c.last_name,
        p1.amount,
        COUNT(p1.id) AS transaction_count
    FROM
        rental_payment p1
    JOIN
        rental_payment p2 ON p1.customer_id = p2.customer_id AND p1.amount = p2.amount AND p1.id <> p2.id
    JOIN
        rental_customer c ON p1.customer_id = c.id
    GROUP BY
        p1.customer_id, c.first_name, c.last_name, p1.amount
    HAVING
        COUNT(p1.id) > 1
    ORDER BY
        transaction_count DESC;
    """

    # --- 2. Correlated Subquery (Payments above customer's average) ---
    correlated_query = """
    SELECT
        p.id,
        p.amount,
        c.first_name,
        c.last_name,
        (SELECT AVG(p_inner.amount) FROM rental_payment p_inner WHERE p_inner.customer_id = p.customer_id) AS customer_avg_payment
    FROM
        rental_payment p
    JOIN
        rental_customer c ON p.customer_id = c.id
    WHERE
        p.amount > (SELECT AVG(p_sub.amount) FROM rental_payment p_sub WHERE p_sub.customer_id = p.customer_id)
    ORDER BY
        p.customer_id, p.amount DESC;
    """

    # --- 3. Set Operation (Customers with bookings but no payments) ---
    set_op_query = """
    SELECT id, first_name, last_name, email FROM rental_customer
    WHERE id IN (
        SELECT customer_id FROM rental_rentalbooking
        EXCEPT
        SELECT customer_id FROM rental_payment
    );
    """

    with connection.cursor() as cursor:
        cursor.execute(self_join_query)
        repeated_transactions = cursor.fetchall()

        cursor.execute(correlated_query)
        above_avg_payments = cursor.fetchall()

        cursor.execute(set_op_query)
        customers_no_payments = cursor.fetchall()

    data = {
        'repeated_transactions': repeated_transactions,
        'above_avg_payments': above_avg_payments,
        'customers_no_payments': customers_no_payments,
    }
    return render(request, 'admin/payment_self_join_report.html', data)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def return_vehicle_view(request, booking_id):
    """
    Handles the calculation of the final bill using the Stored Procedure,
    updates the database, and redirects the admin.
    """
    booking = get_object_or_404(RentalBooking, id=booking_id)

    if request.method == 'POST':
        actual_return_datetime_str = request.POST.get('actual_return_datetime')
        final_payment_method = request.POST.get('final_payment_method')

        if not actual_return_datetime_str:
            messages.error(request, "Actual return date and time are required.")
            return redirect('return_vehicle', booking_id=booking_id)

        actual_return_datetime = parse_datetime(actual_return_datetime_str)

        try:
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            with connection.cursor() as cursor:
                # Call the stored procedure
                cursor.callproc('CALCULATE_FINAL_BILL', [booking.id, actual_return_datetime, 0.0])
                # Fetch the output parameter
                cursor.execute("SELECT @_CALCULATE_FINAL_BILL_2")
                result = cursor.fetchone()
                final_charge = result[0] if result else 0.0
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            with transaction.atomic():
                final_charge = 0.0
                # --- Call Stored Procedure ---
                with connection.cursor() as cursor:
                    # Using cursor.callproc is fine, but we need to fetch the output parameter correctly.
                    # The name of the output parameter depends on the MySQL version and connection settings.
                    # A common pattern is to use session variables.
                    cursor.execute("SET @final_bill = 0.0;")
                    cursor.callproc('CALCULATE_FINAL_BILL', [booking.id, actual_return_datetime, '@final_bill'])
                    cursor.execute("SELECT @final_bill;")
                    result = cursor.fetchone()
                    final_charge = result[0] if result and result[0] is not None else 0.0
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

            with transaction.atomic():
                # Update booking status and actual return time
                booking.booking_status = 'Completed'
                booking.actual_return_datetime = actual_return_datetime
                booking.save()

                # Update vehicle status to 'Available'
                booking.vehicle.status = 'Available'
                booking.vehicle.save()

                # Create a new payment record for the final charge if it's positive
                if final_charge > 0:
                    Payment.objects.create(
                        booking=booking,
                        customer=booking.customer,
                        amount=final_charge,
                        payment_method=final_payment_method,
                        payment_type='Fine', # Or 'Final Settlement'
                        payment_status='Completed'
                    )

            messages.success(request, f"Booking #{booking.id} completed. Final charge/fee of ₹{final_charge:.2f} processed.")
            return redirect('bookings_management')

        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return redirect('return_vehicle', booking_id=booking_id)

    context = {
        'booking': booking
    }
    return render(request, 'admin/return_vehicle_form.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser) # Only superusers can change admin passwords
def change_password_view(request):
    """
    Allows a logged-in admin to change their password.
    """
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Prevents the user from being logged out
            messages.success(request, 'Your password was successfully updated!')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(user=request.user)

    context = {'form': form}
    return render(request, 'admin/change_password.html', context)

@login_required # This view should be accessible to any logged-in user to change their own password
def user_change_password_view(request):
    """
    Allows a logged-in regular user to change their password.
    """
    if not request.user.is_authenticated:
        messages.error(request, "You do not have permission to change passwords.")
        return redirect('admin_dashboard')

    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Prevents the user from being logged out
            messages.success(request, 'Your password was successfully updated!')
            return redirect('my_profile') # Redirect to user profile
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(user=request.user)

    context = {'form': form}
    return render(request, 'change_password.html', context) # Use a user-facing template


@login_required
@user_passes_test(lambda u: u.is_superuser)
def bookings_management_view(request):
    """
    Provides a comprehensive view for managing rental bookings.
    - Displays all bookings in a filterable and sortable table.
    - Includes multi-table data from Customer and Vehicle.
    """
    # Start with a base queryset, prefetching related data for efficiency
    bookings = RentalBooking.objects.select_related('customer', 'vehicle').order_by('-booking_date')

    # --- Filtering ---
    search_query = request.GET.get('q', '').strip()
    start_date_str = request.GET.get('start_date', '').strip()
    end_date_str = request.GET.get('end_date', '').strip()
    selected_status = request.GET.get('status', '').strip()

    if search_query:
        bookings = bookings.filter(
            Q(id__icontains=search_query) |
            Q(customer__first_name__icontains=search_query) |
            Q(customer__last_name__icontains=search_query) |
            Q(vehicle__make__icontains=search_query) |
            Q(vehicle__model__icontains=search_query) |
            Q(vehicle__vehicle_number__icontains=search_query)
        )

    if start_date_str:
        bookings = bookings.filter(pickup_datetime__gte=start_date_str)
    if end_date_str:
        bookings = bookings.filter(return_datetime__lte=end_date_str)
    if selected_status:
        bookings = bookings.filter(booking_status=selected_status)

    # --- Sorting ---
    sort_by = request.GET.get('sort', 'booking_date')
    order = request.GET.get('order', 'desc')
    if order == 'desc':
        sort_by = f"-{sort_by.lstrip('-')}"
    else:
        sort_by = sort_by.lstrip('-')
    
    valid_sort_fields = ['booking_date', 'pickup_datetime', 'return_datetime', 'total_amount', 'booking_status']
    if sort_by.strip('-') in valid_sort_fields:
        bookings = bookings.order_by(sort_by)

    # CSV Export
    if 'export' in request.GET and request.GET['export'] == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="bookings.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Customer Name', 'Customer ID', 'Vehicle', 'Vehicle Number', 'Pickup Date', 'Return Date', 'Total Amount', 'Status'])
        for booking in bookings: # Use the filtered queryset
            writer.writerow([
                booking.id,
                f"{booking.customer.first_name} {booking.customer.last_name}",
                booking.customer.id,
                f"{booking.vehicle.make} {booking.vehicle.model}",
                booking.vehicle.vehicle_number,
                booking.pickup_datetime.strftime('%Y-%m-%d %H:%M'),
                booking.return_datetime.strftime('%Y-%m-%d %H:%M'),
                booking.total_amount,
                booking.booking_status
            ])
        return response
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    valid_sort_fields = ['booking_date', 'pickup_datetime', 'return_datetime', 'total_amount', 'booking_status']
    if sort_by.strip('-') in valid_sort_fields:
        bookings = bookings.order_by(sort_by)

    # --- Bulk Actions ---
    if request.method == 'POST' and request.POST.get('bulk_action'):
        booking_ids = request.POST.getlist('booking_ids')
        action = request.POST.get('action')

        if not booking_ids:
            messages.warning(request, "Please select at least one booking to perform a bulk action.")
        else:
            if action == 'mark_completed':
                updated_count = RentalBooking.objects.filter(id__in=booking_ids).update(booking_status='Completed')
                messages.success(request, f"{updated_count} bookings marked as Completed.")
            elif action == 'cancel_selected':
                updated_count = RentalBooking.objects.filter(id__in=booking_ids).update(booking_status='Cancelled')
                messages.success(request, f"{updated_count} bookings have been cancelled.")
            return redirect('bookings_management')

    # --- Pagination ---
    paginator = Paginator(bookings, 10) # 10 bookings per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'bookings': page_obj,
        'search_query': search_query,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'selected_status': selected_status,
        'sort_by': sort_by.strip('-'),
        'order': order,
    }
    return render(request, "admin/rental_bookings.html", context)

@login_required
def booking_detail_view(request, booking_id):
    """
    Displays detailed information about a single booking for the admin.
    """
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('home')

    booking = get_object_or_404(
        RentalBooking.objects.select_related('customer', 'vehicle'),
        id=booking_id
    )
    
    # Fetch related payments for this booking
    payments = Payment.objects.filter(booking=booking).order_by('-payment_date')

    context = {
        'booking': booking,
        'payments': payments,
    }
    return render(request, 'admin/booking_detail.html', context)

@login_required
def admin_add_booking_view(request):
    """
    Admin view to add a new booking.
    """
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to add bookings.")
        return redirect('home')

    if request.method == 'POST':
        form = AdminBookingForm(request.POST)
        if form.is_valid():
            customer = form.cleaned_data['customer']
            vehicle = form.cleaned_data['vehicle']
            pickup_datetime = form.cleaned_data['pickup_datetime']
            return_datetime = form.cleaned_data['return_datetime']
            pickup_location = form.cleaned_data['pickup_location']
            return_location = form.cleaned_data['return_location']
            special_requests = form.cleaned_data['special_requests']

            # Basic validation
            if return_datetime <= pickup_datetime:
                messages.error(request, "Return date/time must be after pickup date/time.")
                return render(request, 'admin/add_booking.html', {'form': form})

            try:
                with transaction.atomic():
                    # Check for booking conflicts
                    conflicting_bookings = RentalBooking.objects.filter(
                        vehicle=vehicle,
                        pickup_datetime__lt=return_datetime,
                        return_datetime__gt=pickup_datetime,
                        booking_status__in=['Confirmed', 'Active']
                    ).exists()

                    if conflicting_bookings:
                        messages.error(request, "This vehicle is not available for the selected time slot.")
                        return render(request, 'admin/add_booking.html', {'form': form})

                    # Calculate total amount and security deposit
                    duration_hours = (return_datetime - pickup_datetime).total_seconds() / 3600
                    hourly_rate = vehicle.hourly_rate # Use vehicle's current hourly rate
                    total_amount = duration_hours * hourly_rate
                    security_deposit = total_amount * 0.2 # Example: 20% security deposit

                    new_booking = form.save(commit=False)
                    new_booking.hourly_rate = hourly_rate
                    new_booking.total_amount = total_amount
                    new_booking.security_deposit = security_deposit
                    new_booking.booking_status = 'Confirmed' # Admin adds confirmed booking
                    new_booking.created_by = request.user.username # Or a more specific admin identifier
                    new_booking.save()

                    messages.success(request, f"Booking #{new_booking.id} added successfully!")
                    return redirect('bookings_management')

            except Exception as e:
                messages.error(request, f"An error occurred while adding booking: {e}")
        # If form is not valid, errors will be displayed by the template
    else:
        form = AdminBookingForm()

    context = {'form': form}
    return render(request, 'admin/add_booking.html', context)

@login_required
def cancel_booking_view(request, booking_id):
    """
    Admin action to cancel a confirmed booking.
    """
    if not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('home')

    booking = get_object_or_404(RentalBooking, id=booking_id)
    if booking.booking_status in ['Confirmed', 'Active']:
        with transaction.atomic():
            booking.booking_status = 'Cancelled'
            booking.save()
            # Make the vehicle available again
            booking.vehicle.status = 'Available'
            booking.vehicle.save()
        messages.success(request, f"Booking #{booking.id} has been cancelled.")
    else:
        messages.warning(request, f"Booking #{booking.id} cannot be cancelled as it is already {booking.booking_status}.")
    return redirect('bookings_management')

@login_required
def activate_booking_view(request, booking_id):
    """
    Admin action to mark a booking as active when the customer picks up the vehicle.
    """
    if not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('home')

    booking = get_object_or_404(RentalBooking, id=booking_id)
    if booking.booking_status == 'Confirmed':
        with transaction.atomic():
            booking.booking_status = 'Active'
            booking.save()
            booking.save(update_fields=['booking_status'])
            booking.vehicle.status = 'Rented'
            booking.vehicle.save()
            booking.vehicle.save(update_fields=['status'])
        messages.success(request, f"Booking #{booking.id} is now active.")
    else:
        messages.warning(request, f"Booking #{booking.id} cannot be activated (Status: {booking.booking_status}).")
    return redirect('bookings_management')
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream

@login_required
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
@user_passes_test(lambda u: u.is_superuser)
def admin_customers_view(request):
    """
    Displays a filterable, sortable, and paginated list of all customers
    for the admin panel.
    """
    # Base queryset
    customer_list = Customer.objects.all()

    # Universal Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        customer_list = customer_list.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(license_number__icontains=search_query)
        )

    # Filtering by status
    verification_status = request.GET.get('verification_status')
    if verification_status == 'verified':
        customer_list = customer_list.filter(is_verified=True)
    elif verification_status == 'unverified':
        customer_list = customer_list.filter(is_verified=False)
    membership_tier = request.GET.get('membership_tier')
    if membership_tier:
        customer_list = customer_list.filter(membership_tier=membership_tier)

    # Sorting logic
    sort_by = request.GET.get('sort', '-registration_date')
    valid_sort_fields = ['first_name', 'email', 'registration_date', 'credit_score']
    if sort_by.strip('-') in valid_sort_fields:
        customer_list = customer_list.order_by(sort_by)
    else:
        # Fallback to default sort to prevent errors
        sort_by = '-registration_date'
        customer_list = customer_list.order_by(sort_by)

    # Pagination
    paginator = Paginator(customer_list, 10) # 10 customers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'customers': page_obj,
        'total_customers': paginator.count,
        'search_query': search_query,
        'sort_by': sort_by,
        'verification_status': verification_status,
        'membership_tier': membership_tier,
    }
    return render(request, "admin/customers.html", context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def verify_customer_view(request, customer_id):
    """
    Admin view to mark a customer as verified.
    Performs a targeted UPDATE.
    """
    customer = get_object_or_404(Customer, id=customer_id)

    if not customer.is_verified:
        customer.is_verified = True
        customer.save(update_fields=['is_verified']) # Only update this field
        CustomerActivityLog.objects.create(
            customer=customer,
            activity_type='Account Verification',
            description=f'Customer account verified by admin {request.user.email}'
        )
        messages.success(request, f"Customer {customer.email} has been verified.")
    else:
        messages.info(request, f"Customer {customer.email} is already verified.")
    return redirect('admin_customers')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def unverify_customer_view(request, customer_id):
    """
    Admin view to mark a customer as unverified.
    """
    customer = get_object_or_404(Customer, id=customer_id)

    if customer.is_verified:
        customer.is_verified = False
        customer.save(update_fields=['is_verified'])
        messages.success(request, f"Customer {customer.email}'s verification has been revoked.")
    else:
        messages.info(request, f"Customer {customer.email} is already unverified.")
    
<<<<<<< Updated upstream
    return redirect('admin_customers')
=======
    return redirect('admin_customers')
