from django.shortcuts import render, redirect, get_object_or_404
from django.db import connection, transaction 
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum, F
from django.db.models.functions import TruncMonth, TruncDay
from django.core.cache import cache
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.utils.dateparse import parse_datetime
from django.db import transaction
from datetime import date, timedelta, datetime
from .models import Vehicle, Customer, FeedbackReview, RentalBooking, Payment, MaintenanceRecord
from django.http import JsonResponse
from django.db.models import Sum
from .forms import PaymentForm  # Import the new form
from .models import Payment

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
                # Check if the associated user is a superuser
                if hasattr(customer, 'user') and customer.user.is_superuser:
                    messages.success(request, f'Welcome back, Admin!')
                    return redirect('admin_dashboard')

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

def vehicle_list_view(request):
    """
    Displays a filterable and paginated list of all available vehicles.
    """
    customer = None
    customer_id = request.session.get('customer_id')
    if customer_id:
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            # If customer not found, clear the session
            del request.session['customer_id']

    # Base queryset for available vehicles
    vehicle_list = Vehicle.objects.filter(status='Available').order_by('make', 'model')

    # Apply filters from GET request
    selected_type = request.GET.get('type')
    selected_fuel = request.GET.get('fuel')
    sort_by = request.GET.get('sort', 'make')

    if selected_type:
        vehicle_list = vehicle_list.filter(vehicle_type=selected_type)
    if selected_fuel:
        vehicle_list = vehicle_list.filter(fuel_type=selected_fuel)

    # Apply sorting
    if sort_by == 'price_asc':
        vehicle_list = vehicle_list.order_by('hourly_rate')
    elif sort_by == 'price_desc':
        vehicle_list = vehicle_list.order_by('-hourly_rate')
    else: # Default sort by make
        vehicle_list = vehicle_list.order_by('make', 'model')

    # Pagination
    paginator = Paginator(vehicle_list, 9) # 9 vehicles per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'customer': customer,
        'vehicles': page_obj,
        'values': request.GET, # To retain filter values in the form
    }
    return render(request, "vehicles.html", context)

@login_required
def booking_view(request, vehicle_id):
    """
    Handles the vehicle booking process.
    - GET: Displays the booking form with vehicle details.
    - POST: Creates the booking and initial payment record.
    """
    customer_id = request.session.get('customer_id')
    if not customer_id:
        messages.error(request, "You must be logged in to make a booking.")
        return redirect('home')

    customer = get_object_or_404(Customer, id=customer_id)
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    if request.method == 'POST':
        pickup_str = request.POST.get('pickup_datetime')
        return_str = request.POST.get('return_datetime')
        pickup_location = request.POST.get('pickup_location')
        return_location = request.POST.get('return_location')

        # --- Validation ---
        if not all([pickup_str, return_str, pickup_location, return_location]):
            messages.error(request, "All fields are required.")
            return redirect('booking', vehicle_id=vehicle.id)

        pickup_datetime = parse_datetime(pickup_str)
        return_datetime = parse_datetime(return_str)

        if not (pickup_datetime and return_datetime and return_datetime > pickup_datetime):
            messages.error(request, "Invalid pickup or return date.")
            return redirect('booking', vehicle_id=vehicle.id)

        try:
            with transaction.atomic():
                # Check for booking conflicts within a transaction to prevent race conditions
                conflicting_bookings = RentalBooking.objects.filter(
                    vehicle=vehicle,
                    pickup_datetime__lt=return_datetime,
                    return_datetime__gt=pickup_datetime,
                    booking_status__in=['Confirmed', 'Active']
                ).exists()

                if conflicting_bookings:
                    messages.error(request, "Sorry, this vehicle is already booked for the selected time slot.")
                    return redirect('booking', vehicle_id=vehicle.id)

                # Calculate total amount
                duration_hours = (return_datetime - pickup_datetime).total_seconds() / 3600
                total_amount = duration_hours * vehicle.hourly_rate
                security_deposit = total_amount * 0.2 # Example: 20% security deposit

                # Create the booking
                new_booking = RentalBooking.objects.create(
                    customer=customer,
                    vehicle=vehicle,
                    pickup_datetime=pickup_datetime,
                    return_datetime=return_datetime,
                    pickup_location=pickup_location,
                    return_location=return_location,
                    hourly_rate=vehicle.hourly_rate,
                    total_amount=total_amount,
                    security_deposit=security_deposit,
                    booking_status='Confirmed'
                )

                messages.success(request, f"Booking successful! Your booking ID is #{new_booking.id}.")
                return redirect('home') # Redirect to a 'My Bookings' page would be ideal

        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return redirect('booking', vehicle_id=vehicle.id)

    # For GET request
    context = {'vehicle': vehicle, 'customer': customer, 'values': request.GET}
    return render(request, "booking.html", context)

def about_us_view(request):
    """
    Renders the About Us page.
    """
    customer = None
    customer_id = request.session.get('customer_id')
    if customer_id:
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            del request.session['customer_id']
    
    context = {
        'customer': customer,
    }
    return render(request, "about_us.html", context)

@login_required
def my_profile_view(request):
    """
    Displays the logged-in user's profile information and booking history.
    """
    customer_id = request.session.get('customer_id')
    if not customer_id:
        messages.error(request, "You need to be logged in to view your profile.")
        return redirect('home')

    customer = get_object_or_404(Customer, id=customer_id)
    
    # Fetch the user's bookings
    bookings = RentalBooking.objects.filter(customer=customer).select_related('vehicle').order_by('-booking_date')

    context = {
        'customer': customer,
        'bookings': bookings,
    }
    return render(request, "my_profile.html", context)

@login_required
def my_bookings_view(request):
    """
    Displays a paginated list of all bookings for the logged-in user.
    """
    customer_id = request.session.get('customer_id')
    if not customer_id:
        messages.error(request, "You need to be logged in to view your bookings.")
        return redirect('home')

    customer = get_object_or_404(Customer, id=customer_id)
    
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


