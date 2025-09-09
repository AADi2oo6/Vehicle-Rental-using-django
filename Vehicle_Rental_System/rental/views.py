from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Vehicle, Customer, FeedbackReview, RentalBooking
from django.contrib.auth.hashers import make_password, check_password
from django.utils.dateparse import parse_datetime
from django.db.models import Q

def home_view(request):
    """
    Handles the display of the home page and vehicle search functionality.
    """
    customer = None
    customer_id = request.session.get('customer_id')
    if customer_id:
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            # Clear session if customer is not found
            del request.session['customer_id']

    search_results = None
    # Check if this is a search request by looking for a required search parameter
    if 'location' in request.GET and request.GET['location']:
        # --- Search Logic ---
        vehicle_type = request.GET.get('vehicle_type')
        location = request.GET.get('location')
        pickup_str = request.GET.get('pickup_datetime')
        return_str = request.GET.get('return_datetime')

        # Start with a base query for available vehicles
        results = Vehicle.objects.filter(status='Available')

        if vehicle_type:
            results = results.filter(vehicle_type=vehicle_type)
        
        if location:
            results = results.filter(location__icontains=location)

        # Date-based filtering for booking conflicts
        if pickup_str and return_str:
            pickup_datetime = parse_datetime(pickup_str)
            return_datetime = parse_datetime(return_str)

            # Ensure the dates are valid and the return time is after the pickup time
            if pickup_datetime and return_datetime and return_datetime > pickup_datetime:
                # Find vehicles that have conflicting bookings.
                # A conflict exists if a vehicle has ANY booking that overlaps with the requested time.
                # Overlap condition: (StartA < EndB) and (EndA > StartB)
                conflicting_vehicle_ids = RentalBooking.objects.filter(
                    pickup_datetime__lt=return_datetime,
                    return_datetime__gt=pickup_datetime
                ).values_list('vehicle_id', flat=True)

                # Exclude these conflicting vehicles from the results
                results = results.exclude(id__in=conflicting_vehicle_ids)
        
        search_results = results

    # --- Default Page Data (if not a search) ---
    featured_vehicles = Vehicle.objects.filter(status='Available')[:4]
    vehicle_count = Vehicle.objects.filter(status='Available').count()
    customer_count = Customer.objects.count()
    reviews = FeedbackReview.objects.select_related('customer', 'vehicle').order_by('-review_date')[:3]
    # More accurate location count
    location_count = Vehicle.objects.values('location').distinct().count()

    context = {
        'customer': customer,
        'search_results': search_results,
        'values': request.GET, # To pre-fill the form with previous search values
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

        # Basic Validation
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
            phone="0000000000", # Placeholder, should be collected in a profile page
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

