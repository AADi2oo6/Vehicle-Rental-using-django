from django.shortcuts import render, redirect, get_object_or_404
from .utils import dictfetchall
from django.db import connection, transaction
from django.contrib import messages
<<<<<<< HEAD
=======
from django.contrib.auth.decorators import login_required, user_passes_test
>>>>>>> 95b19fba1109557a00be7f13a177d5081bad2746
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum, F, Count
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.core.cache import cache
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpResponse
from django.utils.dateparse import parse_datetime
<<<<<<< HEAD
from django.db import transaction, DatabaseError
from datetime import date, timedelta, datetime
from .models import Vehicle, Customer, FeedbackReview, RentalBooking, Payment, MaintenanceRecord, ActivityLog # Import ActivityLog
from django.http import JsonResponse
from django.db.models import Sum
from .forms import PaymentForm
from decimal import Decimal
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import json

def customer_login_required(function):
    """
    Custom decorator to check if a customer is logged in.
    Checks for 'customer_id' in the session.
    """
    def wrap(request, *args, **kwargs):
        if 'customer_id' not in request.session:
            messages.error(request, "You must be logged in to view this page.")
            return redirect('home')
        return function(request, *args, **kwargs)
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
=======
from django.http import Http404
from django.utils import timezone 
from django.db import transaction, IntegrityError
from datetime import date, timedelta, datetime
from .models import Vehicle, Customer, FeedbackReview, RentalBooking, Payment, CustomerActivityLog, CustomerDetailsView
from django.http import JsonResponse
from django.db.models import Sum
from .forms import PaymentForm, CustomerProfileForm, UserUpdateForm
from .models import Payment
from .forms import AdminBookingForm # Import the new form
>>>>>>> 95b19fba1109557a00be7f13a177d5081bad2746

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
    }
    return JsonResponse(data)
<<<<<<< HEAD
=======
# User-facing Views
>>>>>>> 95b19fba1109557a00be7f13a177d5081bad2746

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

        if User.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
            return redirect('home')

        # Improved name validation: ensure at least a first and last name are provided.
        name_parts = full_name.split()
        if len(name_parts) < 2:
            messages.error(request, 'Please provide both your first and last name.')
            return redirect('home')

        try:
<<<<<<< HEAD
            first_name, last_name = full_name.split(' ', 1)
        except ValueError:
            first_name, last_name = full_name, ""
        hashed_password = make_password(password)
        
        # Create customer
        new_customer = Customer.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hashed_password,
            phone="0000000000",
        )
        
        # Create log entry
        ActivityLog.objects.create(
            customer=new_customer,
            action_type='REGISTRATION',
            details=f"New customer registered: {email}"
        )

        messages.success(request, 'Registration successful! Please log in.')
        return redirect('home')
    return redirect('home')
=======
            first_name, last_name = name_parts[0], " ".join(name_parts[1:])
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
>>>>>>> 95b19fba1109557a00be7f13a177d5081bad2746

def login_view(request):
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
<<<<<<< HEAD
        try:
            customer = Customer.objects.get(email=email)
            if not customer.is_active:
                messages.error(request, 'Your account has been deactivated. Please contact support.')
                return redirect('home')
            if check_password(password, customer.password):
                request.session['customer_id'] = customer.id
                
                # Create log entry
                ActivityLog.objects.create(
                    customer=customer,
                    action_type='LOGIN',
                    details="Customer logged in successfully."
                )

                if hasattr(customer, 'user') and customer.user.is_superuser:
                    messages.success(request, f'Welcome back, Admin!')
                    return redirect('admin_dashboard')
                messages.success(request, f'Welcome back, {customer.first_name}!')
=======

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
>>>>>>> 95b19fba1109557a00be7f13a177d5081bad2746
            else:
                messages.success(request, f'Welcome back, {user.first_name}!')
                return redirect('home')
        else:
            messages.error(request, 'Invalid email or password.')
<<<<<<< HEAD
        return redirect('home')
    return redirect('home')

def logout_view(request):
    customer_id = request.session.get('customer_id')
    if customer_id:
        try:
            customer = Customer.objects.get(id=customer_id)
            ActivityLog.objects.create(
                customer=customer,
                action_type='LOGOUT',
                details="Customer logged out."
            )
        except Customer.DoesNotExist:
            pass # Customer not found, nothing to log
    
    try:
        del request.session['customer_id']
    except KeyError:
        pass
        
=======
            return redirect('home')
    return redirect('home') # Redirect if GET request

def logout_view(request):
    logout(request)
    request.session.pop('customer_id', None) # Safely remove customer_id from session
>>>>>>> 95b19fba1109557a00be7f13a177d5081bad2746
    messages.success(request, "You have been logged out.")
    return redirect('home')

def vehicle_list_view(request):
    """
    Handles the display of all vehicles with multi-layered filtering and sorting.
    """
<<<<<<< HEAD
    customer = None
    customer_id = request.session.get('customer_id')
    if customer_id:
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            del request.session['customer_id']
=======
>>>>>>> 95b19fba1109557a00be7f13a177d5081bad2746

    # Start with a base queryset of vehicles that are not retired
    vehicle_list = Vehicle.objects.filter(status='Available')

<<<<<<< HEAD
    # --- Availability Search (First Layer of Filtering) ---
    location = request.GET.get('location')
    pickup_str = request.GET.get('pickup_datetime')
    return_str = request.GET.get('return_datetime')

    # This block only runs if the user has provided all three availability fields
    if location and pickup_str and return_str:
        pickup_datetime = parse_datetime(pickup_str)
        return_datetime = parse_datetime(return_str)

        if pickup_datetime and return_datetime and return_datetime > pickup_datetime:
            # 1. Filter by location
            vehicle_list = vehicle_list.filter(location__icontains=location)
            
            # 2. Find IDs of vehicles with conflicting bookings in the specified time frame
            conflicting_vehicle_ids = RentalBooking.objects.filter(
                vehicle_id__in=vehicle_list.values('id'), # Check only against vehicles already filtered by location
                pickup_datetime__lt=return_datetime,
                return_datetime__gt=pickup_datetime
            ).values_list('vehicle_id', flat=True)
            
            # 3. Exclude the conflicting vehicles to get the final list of available vehicle IDs
            vehicle_list = vehicle_list.exclude(id__in=conflicting_vehicle_ids)
    
    # --- Standard Filters (Second Layer of Filtering) ---
    selected_type = request.GET.get('type')
    selected_fuel = request.GET.get('fuel')
    sort_by = request.GET.get('sort', 'make')

    if selected_type:
        vehicle_list = vehicle_list.filter(vehicle_type=selected_type)
    
    if selected_fuel:
        vehicle_list = vehicle_list.filter(fuel_type=selected_fuel)

    # --- Sorting ---
=======
    # Filtering logic
    if 'type' in request.GET and request.GET['type']:
        vehicle_list = vehicle_list.filter(vehicle_type=request.GET['type'])
    if 'fuel' in request.GET and request.GET['fuel']:
        vehicle_list = vehicle_list.filter(fuel_type=request.GET['fuel'])

    # Sorting logic
    sort_by = request.GET.get('sort', 'make')
>>>>>>> 95b19fba1109557a00be7f13a177d5081bad2746
    if sort_by == 'price_asc':
        vehicle_list = vehicle_list.order_by('hourly_rate')
    elif sort_by == 'price_desc':
        vehicle_list = vehicle_list.order_by('-hourly_rate')
<<<<<<< HEAD
    else: # Default sort
=======
    else: # Default to 'make'
>>>>>>> 95b19fba1109557a00be7f13a177d5081bad2746
        vehicle_list = vehicle_list.order_by('make', 'model')

    # --- Pagination ---
    paginator = Paginator(vehicle_list, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'vehicles': page_obj,
        'values': request.GET, # To pre-fill the form
    }
    return render(request, "vehicles.html", context)

<<<<<<< HEAD

@customer_login_required
def booking_view(request, vehicle_id):
    customer = get_object_or_404(Customer, id=request.session.get('customer_id'))
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    
    context = {
        'vehicle': vehicle, 
        'customer': customer, 
        'values': request.GET, # Pre-fill from search
        'show_payment_modal': False,
    }

    if request.method == 'POST':
        # --- This view now VALIDATES and SHOWS THE MODAL ---
        pickup_str = request.POST.get('pickup_datetime')
        return_str = request.POST.get('return_datetime')
=======
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
>>>>>>> 95b19fba1109557a00be7f13a177d5081bad2746
        pickup_location = request.POST.get('pickup_location')
        return_location = request.POST.get('return_location')
        
        # --- Validation Block ---
        if vehicle.location.lower() not in pickup_location.lower():
            messages.error(request, f"Sorry, this vehicle is not available for pickup in your selected area. It is based in {vehicle.location}.")
            return redirect('booking', vehicle_id=vehicle.id)

<<<<<<< HEAD
        if not all([pickup_str, return_str, pickup_location, return_location]):
            messages.error(request, "All fields are required.")
            return redirect('booking', vehicle_id=vehicle.id)
=======
        pickup_datetime = parse_datetime(pickup_datetime_str)
        return_datetime = parse_datetime(return_datetime_str)
>>>>>>> 95b19fba1109557a00be7f13a177d5081bad2746

        duration_hours = (return_datetime - pickup_datetime).total_seconds() / 3600
        total_amount = duration_hours * vehicle.hourly_rate

<<<<<<< HEAD
        if not (pickup_datetime and return_datetime and return_datetime > pickup_datetime):
            messages.error(request, "Invalid pickup or return date.")
            return redirect('booking', vehicle_id=vehicle.id)
        
        # --- Calculation Block ---
        try:
            duration_hours = (return_datetime - pickup_datetime).total_seconds() / 3600
            total_amount = Decimal(duration_hours) * vehicle.hourly_rate
            security_deposit = total_amount * Decimal('0.20') # 20% security deposit
        except Exception as e:
            messages.error(request, f"Could not calculate fare. Please check your dates. Error: {e}")
            return redirect('booking', vehicle_id=vehicle.id)

        # --- Show Modal ---
        # Instead of saving, we re-render the page with the modal visible
        # and pass all the confirmed data to the modal's form.
        context.update({
            'show_payment_modal': True,
            'form_data': request.POST,
            'security_deposit_amount': security_deposit.quantize(Decimal('0.01')),
            'total_amount': total_amount.quantize(Decimal('0.01')),
        })
        messages.info(request, "Please confirm your payment option to finalize the booking.")
        return render(request, "booking.html", context)

    # Standard GET request
=======
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
>>>>>>> 95b19fba1109557a00be7f13a177d5081bad2746
    return render(request, "booking.html", context)
 

@customer_login_required
def confirm_booking_pay_later(request, vehicle_id):
    """
    Handles the final "Pay Later" confirmation from the modal.
    This view performs the ATOMIC transaction.
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request.")
        return redirect('booking', vehicle_id=vehicle_id)

    customer = get_object_or_404(Customer, id=request.session.get('customer_id'))
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    # --- DBMS Concept: ACID Transaction ---
    # We are performing THREE database inserts. All must succeed,
    # or none of them will. transaction.atomic() guarantees this.
    try:
        with transaction.atomic():
            # 1. Get all the data from the hidden form fields
            pickup_datetime = parse_datetime(request.POST.get('pickup_datetime'))
            return_datetime = parse_datetime(request.POST.get('return_datetime'))
            pickup_location = request.POST.get('pickup_location')
            return_location = request.POST.get('return_location')
            total_amount = Decimal(request.POST.get('total_amount'))
            security_deposit = Decimal(request.POST.get('security_deposit_amount'))

            # --- Query 1: INSERT into RentalBooking ---
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
                booking_status='Pending'
            )

            # --- Query 2: INSERT into Payment (Security Deposit) ---
            Payment.objects.create(
                booking=new_booking,
                customer=customer,
                amount=security_deposit,
                payment_method='Cash', # Placeholder, as it's 'Pay Later'
                payment_type='Security Deposit',
                payment_status='Pending' # DBMS Concept: Using a constraint
            )

            # --- Query 3: INSERT into Payment (Full Amount) ---
            Payment.objects.create(
                booking=new_booking,
                customer=customer,
                amount=total_amount,
                payment_method='Cash',
                payment_type='Full Payment',
                payment_status='Pending'
            )

            # --- Query 4: INSERT into ActivityLog ---
            ActivityLog.objects.create(
                customer=customer,
                action_type='BOOKING_CREATED',
                details=f"Created booking #{new_booking.id} (Pay Later) for vehicle {vehicle.vehicle_number}."
            )

        # If the transaction.atomic() block succeeds, we commit and redirect.
        messages.success(request, f"Booking #{new_booking.id} confirmed! Please pay at the counter.")
        return redirect('my_bookings')

    except DatabaseError as e:
        # If the trigger fails (e.g., booking conflict)
        if 'Booking conflict' in str(e):
            messages.error(request, "Sorry, this vehicle was just booked by someone else. Please try a different time.")
        else:
            messages.error(request, f"A database error occurred. Please try again.")
        return redirect('booking', vehicle_id=vehicle.id)
    except Exception as e:
        # If any other error occurs (e.g., data conversion), the transaction is rolled back.
        messages.error(request, f"An unexpected error occurred: {e}")
        return redirect('booking', vehicle_id=vehicle_id)


@customer_login_required
def booking_detail_view(request, booking_id):
    """
    Displays a detailed view of a single booking.
    Demonstrates efficient data retrieval using select_related and prefetch_related.
    """
    customer = get_object_or_404(Customer, id=request.session.get('customer_id'))

    # --- DBMS Concept: Query Optimization (select_related) ---
    # We are fetching the booking and its related Vehicle in a single,
    # efficient query (using a SQL JOIN) instead of two separate queries.
    booking = get_object_or_404(
        RentalBooking.objects.select_related('vehicle'),
        id=booking_id,
        customer=customer  # Ensures the user can only see their own bookings
    )

    # --- DBMS Concept: Query Optimization (prefetch_related) ---
    # After fetching the booking, we often need related items (like payments or reviews).
    # 'prefetch_related' fetches these in a separate, efficient query (e.g., SELECT ... WHERE booking_id = 123)
    # This avoids the "N+1 query problem"
    booking_payments = booking.payment_set.all()
    
    # We use a 'try/except' here because a review is optional
    try:
        booking_review = booking.feedbackreview_set.get()
    except FeedbackReview.DoesNotExist:
        booking_review = None

    # Calculate grand total for display
    grand_total = booking.total_amount + booking.security_deposit

    context = {
        'customer': customer,
        'booking': booking,
        'booking_payments': booking_payments,
        'booking_review': booking_review,
        'grand_total': grand_total,
    }
    return render(request, "booking_detail.html", context)


def about_us_view(request):
<<<<<<< HEAD
    customer = None
    customer_id = request.session.get('customer_id')
    if customer_id:
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            del request.session['customer_id']
    context = {'customer': customer}
=======
    """
    Renders the About Us page.
    """
    # Customer object is now available via context processor if logged in
    context = {
        # 'customer' will be in context if user is authenticated
    }
>>>>>>> 95b19fba1109557a00be7f13a177d5081bad2746
    return render(request, "about_us.html", context)

@customer_login_required
def my_profile_view(request):
<<<<<<< HEAD
    customer_id = request.session.get('customer_id')
    if not customer_id:
        messages.error(request, "You need to be logged in to view your profile.")
        return redirect('home')
    customer = get_object_or_404(Customer, id=customer_id)
    bookings = RentalBooking.objects.filter(customer=customer).select_related('vehicle').order_by('-booking_date')
=======
    """
    Displays the logged-in user's profile information and booking history.
    """
    # --- MODIFIED: Fetching customer data using a raw SQL query ---
    # This replaces: customer = get_object_or_404(Customer, user=request.user)
    # We use `Customer.objects.raw()` to execute a raw query but still get a model instance back.
    customer_query = "SELECT * FROM rental_customer WHERE user_id = %s"
    customers = list(Customer.objects.raw(customer_query, [request.user.id]))

    if not customers:
        raise Http404("Customer profile not found for the logged-in user.")
    customer = customers[0]

    # --- MODIFIED: Fetching bookings using a raw SQL query with a JOIN ---
    # This replaces: RentalBooking.objects.filter(customer=customer).select_related('vehicle').order_by('-booking_date')
    # This raw query performs an INNER JOIN to get vehicle details in a single database trip.
    bookings_query = """
        SELECT
            rb.id, rb.booking_date, rb.pickup_datetime, rb.return_datetime, rb.booking_status,
            v.make, v.model
        FROM
            rental_rentalbooking rb
        INNER JOIN
            rental_vehicle v ON rb.vehicle_id = v.id
        WHERE
            rb.customer_id = %s
        ORDER BY
            rb.booking_date DESC
    """
    
    # We execute this and build a list of objects that the template can use.
    # The template expects `booking.vehicle.make`, so we create a simple nested structure.
    bookings = []
    with connection.cursor() as cursor:
        cursor.execute(bookings_query, [customer.id])
        for row in cursor.fetchall():
            bookings.append({
                'id': row[0],
                'booking_date': row[1],
                'pickup_datetime': row[2],
                'return_datetime': row[3],
                'booking_status': row[4],
                'vehicle': {'make': row[5], 'model': row[6]}
            })

>>>>>>> 95b19fba1109557a00be7f13a177d5081bad2746
    context = {
        'customer': customer,
        'bookings': bookings,
    }
    return render(request, "my_profile.html", context)

<<<<<<< HEAD

@customer_login_required
def edit_profile_view(request):
    """
    Handles displaying and updating the customer's profile.
    """
    customer = get_object_or_404(Customer, id=request.session.get('customer_id'))

    if request.method == 'POST':
        # --- DBMS Concept: ACID Transaction ---
        # We wrap the update in a transaction. If any part fails
        # (e.g., the ActivityLog save fails), the customer profile
        # update will be rolled back, ensuring data consistency.
        try:
            with transaction.atomic():
                # --- DBMS Concept: CRUD (Update) ---
                # This block performs the SQL UPDATE query.
                customer.first_name = request.POST.get('first_name')
                customer.last_name = request.POST.get('last_name')
                customer.phone = request.POST.get('phone')
                customer.address = request.POST.get('address')
                customer.city = request.POST.get('city')
                customer.state = request.POST.get('state')
                customer.zip_code = request.POST.get('zip_code')
                customer.license_number = request.POST.get('license_number')
                
                dob = request.POST.get('date_of_birth')
                if dob:
                    customer.date_of_birth = dob
                else:
                    customer.date_of_birth = None # Handle empty date
                
                # Handle profile picture upload
                if 'profile_picture' in request.FILES:
                    customer.profile_picture = request.FILES['profile_picture']
                
                customer.save() # This is when the UPDATE query runs and our Trigger fires

                # --- Application-Level Log ---
                # This log is simpler and shows the action was initiated by the app.
                # The database trigger will log the *specific details*.
                ActivityLog.objects.create(
                    customer=customer,
                    action_type='PROFILE_UPDATE',
                    details="Profile updated via web form."
                )

            messages.success(request, "Your profile has been updated successfully!")
            return redirect('my_profile')
        except Exception as e:
            messages.error(request, f"An error occurred while updating your profile: {e}")

    # --- DBMS Concept: CRUD (Read) ---
    # This block handles the GET request, performing a SQL SELECT.
    return render(request, "edit_profile.html", {'customer': customer})


@customer_login_required
def my_bookings_view(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        messages.error(request, "You need to be logged in to view your bookings.")
        return redirect('home')
    customer = get_object_or_404(Customer, id=customer_id)
=======
@login_required
def edit_profile_view(request):
    """
    Allows a logged-in user to edit their profile information.
    """
    # We still need the ORM to get the initial object for the form.
    # The raw SQL part is in the POST handling.
    customer = get_object_or_404(Customer, user=request.user) 

    if request.method == 'POST':
        # Instantiate both forms with POST data and files
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = CustomerProfileForm(request.POST, request.FILES, instance=customer)

        if user_form.is_valid() and profile_form.is_valid():
            # --- MODIFIED: Using raw SQL for the UPDATE operation ---
            # This replaces the simple .save() calls with explicit transaction
            # control and raw UPDATE queries.
            try:
                with transaction.atomic(): # Guarantees atomicity
                    # 1. Update the auth_user table
                    user_data = user_form.cleaned_data
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            UPDATE auth_user 
                            SET first_name = %s, last_name = %s, email = %s 
                            WHERE id = %s
                            """,
                            [user_data['first_name'], user_data['last_name'], user_data['email'], request.user.id]
                        )

                    # 2. Update the rental_customer table
                    profile_data = profile_form.cleaned_data
                    with connection.cursor() as cursor:
                        # Note: Handling profile_picture requires saving the file first,
                        # which the form does automatically. We just get the path.
                        profile_form.save(commit=False) # Process file upload without saving to DB
                        
                        cursor.execute(
                            """
                            UPDATE rental_customer 
                            SET phone = %s, date_of_birth = %s, address = %s, city = %s, 
                                state = %s, zip_code = %s, license_number = %s, 
                                is_subscribed_to_newsletter = %s, profile_picture = %s
                            WHERE id = %s
                            """,
                            [
                                profile_data['phone'], profile_data['date_of_birth'],
                                profile_data['address'], profile_data['city'], profile_data['state'],
                                profile_data['zip_code'], profile_data['license_number'],
                                profile_data['is_subscribed_to_newsletter'],
                                customer.profile_picture.name, # Use the path from the saved form instance
                                customer.id
                            ]
                        )
                
                messages.success(request, "Your profile has been updated successfully using raw SQL!")
                return redirect('my_profile')
            except IntegrityError as e:
                # This will catch database-level errors, like from your triggers
                messages.error(request, f"A database error occurred: {e}")
            except Exception as e:
                messages.error(request, f"An unexpected error occurred: {e}")
        else:
            messages.error(request, "There was an error updating your profile. Please correct the errors below.")
    else:
        # For GET request, instantiate forms with current customer data
        user_form = UserUpdateForm(instance=request.user)
        profile_form = CustomerProfileForm(instance=customer)

    context = {
        'customer': customer,
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, "edit_profile.html", context)



@login_required
def my_bookings_view(request):
    """
    Displays a paginated list of all bookings for the logged-in user.
    """
    customer = get_object_or_404(Customer, user=request.user)

    # Fetch all user's bookings
>>>>>>> 95b19fba1109557a00be7f13a177d5081bad2746
    booking_list = RentalBooking.objects.filter(customer=customer).select_related('vehicle').order_by('-booking_date')
    paginator = Paginator(booking_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'customer': customer,
        'bookings': page_obj,
    }
    return render(request, "my_bookings.html", context)

from django.http import JsonResponse
from .models import DetailedReview # Make sure to import the new model

<<<<<<< HEAD
@customer_login_required
def add_review(request, booking_id):
=======
@user_passes_test(lambda u: u.is_superuser) # Only superusers can access admin dashboard
@login_required # This decorator is still needed for user_passes_test to work
def admin_dashboard_view(request): # Renamed to avoid conflict with existing get_dashboard_data
>>>>>>> 95b19fba1109557a00be7f13a177d5081bad2746
    """
    Handles the creation of a new review for a specific booking.
    Demonstrates: CRUD (Create), ACID Transactions.
    """
<<<<<<< HEAD
    customer = get_object_or_404(Customer, id=request.session.get('customer_id'))
    booking = get_object_or_404(RentalBooking, id=booking_id, customer=customer)

    # Prevent re-reviewing
    if FeedbackReview.objects.filter(booking=booking).exists():
        messages.error(request, "You have already reviewed this booking.")
        return redirect('booking_detail', booking_id=booking.id)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        review_text = request.POST.get('review_text')

        if not rating:
            messages.error(request, "A rating is required.")
            return redirect('booking_detail', booking_id=booking.id)
=======
    # --- Calculate All-Time Total Revenue using the ORM ---
    total_revenue = Payment.objects.filter(
        payment_status='Completed'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # --- Remaining Django ORM Queries ---
    active_rentals_count = RentalBooking.objects.filter(booking_status='Active').count()
    pending_payments_count = Payment.objects.filter(payment_status='Pending').count()
    recent_bookings = RentalBooking.objects.select_related('customer', 'vehicle').order_by('-booking_date')[:5]
    recent_payments = Payment.objects.select_related('customer').order_by('-payment_date')[:5]

    context = {
        'total_revenue': total_revenue,
        'active_rentals_count': active_rentals_count,
        'pending_payments_count': pending_payments_count,
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
    }
    return JsonResponse(data)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_vehicles_view(request):
    vehicles = Vehicle.objects.all()
    return render(request, 'admin/vehicles.html', {'vehicles': vehicles})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_queries_view(request):
    queries = cache.get('all_sql_queries', [])
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
    booking = get_object_or_404(RentalBooking.objects.select_related('vehicle'), id=booking_id)
    from decimal import Decimal

    if request.method == 'POST':
        actual_return_datetime_str = request.POST.get('actual_return_datetime')
        final_payment_method = request.POST.get('final_payment_method')

        if not all([actual_return_datetime_str, final_payment_method]):
            messages.error(request, "Actual return date and time are required.")
            return redirect('return_vehicle', booking_id=booking_id)

        actual_return_datetime = parse_datetime(actual_return_datetime_str)
        # Make the naive datetime from the form aware of the current timezone
        if timezone.is_naive(actual_return_datetime):
            actual_return_datetime = timezone.make_aware(actual_return_datetime, timezone.get_current_timezone())


        # Ensure actual return is after pickup
        if actual_return_datetime <= booking.pickup_datetime:
            messages.error(request, "Actual return time must be after the pickup time.")
            return redirect('return_vehicle', booking_id=booking_id)
>>>>>>> 95b19fba1109557a00be7f13a177d5081bad2746

        try:
            # --- DBMS Concept: ACID Transaction ---
            with transaction.atomic():
<<<<<<< HEAD
                # Step 1: Create the review (INSERT query)
                new_review = FeedbackReview.objects.create(
                    customer=customer,
                    vehicle=booking.vehicle,
                    booking=booking,
                    rating=rating,
                    review_text=review_text
                )
                
                # Step 2: Log the action (INSERT query)
                ActivityLog.objects.create(
                    customer=customer,
                    action_type='REVIEW_CREATED',
                    details=f"Created review #{new_review.id} (Rating: {rating}) for booking #{booking.id}."
                )
            
            messages.success(request, "Your review has been submitted successfully!")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
        
    return redirect('booking_detail', booking_id=booking.id)

@customer_login_required
def edit_review(request, review_id):
=======
                final_charge = 0.0
                # --- ORM-based Late Fee Calculation ---
                # Check if the vehicle was returned late
                if actual_return_datetime > booking.return_datetime:
                    late_duration = actual_return_datetime - booking.return_datetime
                    # Calculate late hours, rounding up to the next full hour
                    late_hours = (late_duration.total_seconds() + 3599) // 3600
                    
                    # Define a late fee rate (e.g., 150% of the hourly rate)
                    late_fee_rate = booking.hourly_rate * Decimal('1.5')
                    final_charge = Decimal(late_hours) * late_fee_rate

                # Update booking status and actual return time
                booking.booking_status = 'Completed'
                booking.actual_return_datetime = actual_return_datetime
                booking.save(update_fields=['booking_status', 'actual_return_datetime'])

                # Update vehicle status to 'Available'
                booking.vehicle.status = 'Available'
                booking.vehicle.save(update_fields=['status'])

                # Create a new payment record for the final charge if it's positive
                if final_charge > 0:
                    Payment.objects.create(
                        booking=booking,
                        customer=booking.customer,
                        amount=round(final_charge, 2),
                        payment_method=final_payment_method,
                        payment_type='Fine',
                        payment_status='Completed'
                    )
                    messages.success(request, f"Booking #{booking.id} completed. A late fee of ₹{final_charge:.2f} was processed.")
                else:
                    messages.success(request, f"Booking #{booking.id} completed successfully with no late fees.")

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
>>>>>>> 95b19fba1109557a00be7f13a177d5081bad2746
    """
    Handles the updating of an existing review.
    Demonstrates: CRUD (Update), ACID Transactions.
    """
<<<<<<< HEAD
    customer = get_object_or_404(Customer, id=request.session.get('customer_id'))
    review = get_object_or_404(FeedbackReview, id=review_id, customer=customer)

=======
>>>>>>> 95b19fba1109557a00be7f13a177d5081bad2746
    if request.method == 'POST':
        rating = request.POST.get('rating')
        review_text = request.POST.get('review_text')

        if not rating:
            messages.error(request, "A rating is required.")
            return redirect('booking_detail', booking_id=review.booking.id)

<<<<<<< HEAD
        try:
            # --- DBMS Concept: ACID Transaction ---
            with transaction.atomic():
                # Step 1: Update the review (UPDATE query)
                review.rating = rating
                review.review_text = review_text
                review.save() # This fires the UPDATE query

                # Step 2: Log the action (INSERT query)
                ActivityLog.objects.create(
                    customer=customer,
                    action_type='REVIEW_UPDATED',
                    details=f"Updated review #{review.id} for booking #{review.booking.id}."
                )
            
            messages.success(request, "Your review has been updated.")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")

    return redirect('booking_detail', booking_id=review.booking.id)

@customer_login_required
def delete_review(request, review_id):
=======
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
>>>>>>> 95b19fba1109557a00be7f13a177d5081bad2746
    """
    Handles the deletion of an existing review.
    Demonstrates: CRUD (Delete), ACID Transactions.
    """
<<<<<<< HEAD
    customer = get_object_or_404(Customer, id=request.session.get('customer_id'))
    review = get_object_or_404(FeedbackReview, id=review_id, customer=customer)
    booking_id = review.booking.id # Save the booking ID before we delete

    if request.method == 'POST':
        try:
            # --- DBMS Concept: ACID Transaction ---
            with transaction.atomic():
                # Step 1: Delete the review (DELETE query)
                review.delete()

                # Step 2: Log the action (INSERT query)
                ActivityLog.objects.create(
                    customer=customer,
                    action_type='REVIEW_DELETED',
                    details=f"Deleted review #{review.id} for booking #{booking_id}."
                )
            
            messages.success(request, "Your review has been deleted.")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
    
    return redirect('booking_detail', booking_id=booking_id)




def all_reviews_api(request):
    """
    An API endpoint that returns all detailed reviews from our database VIEW.
    The data is returned in JSON format.
    """
    # We query the read-only model just like a regular one.
    # The .values() method converts the queryset into a list of dictionaries.
    reviews = DetailedReview.objects.all().order_by('-review_date').values()
    
    # Convert the queryset to a list and return as a JSON response
    return JsonResponse(list(reviews), safe=False)


@customer_login_required
def initiate_razorpay_payment(request, vehicle_id):
    """
    Initiates a Razorpay payment for a new booking.
    This view is called when user clicks the "Pay Now" button in the booking modal.
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('booking', vehicle_id=vehicle_id)
    
    customer = get_object_or_404(Customer, id=request.session.get('customer_id'))
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    
    try:
        # Get all the data from the hidden form fields (similar to confirm_booking_pay_later)
        pickup_datetime = parse_datetime(request.POST.get('pickup_datetime'))
        return_datetime = parse_datetime(request.POST.get('return_datetime'))
        pickup_location = request.POST.get('pickup_location')
        return_location = request.POST.get('return_location')
        total_amount = Decimal(request.POST.get('total_amount'))
        security_deposit = Decimal(request.POST.get('security_deposit_amount'))
        
        # --- DBMS Concept: ACID Transaction --- 
        # We are performing database inserts. All must succeed,
        # or none of them will. transaction.atomic() guarantees this.
        with transaction.atomic():
            # Create the booking first
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
                booking_status='Pending'
            )
            
            # Create payment records
            Payment.objects.create(
                booking=new_booking,
                customer=customer,
                amount=security_deposit,
                payment_method='Razorpay', 
                payment_type='Security Deposit',
                payment_status='Pending'
            )
            
            Payment.objects.create(
                booking=new_booking,
                customer=customer,
                amount=total_amount,
                payment_method='Razorpay',
                payment_type='Full Payment', 
                payment_status='Pending'
            )
            
            # Create activity log
            ActivityLog.objects.create(
                customer=customer,
                action_type='BOOKING_CREATED',
                details=f"Created booking #{new_booking.id} (Razorpay Payment) for vehicle {vehicle.vehicle_number}."
            )
            
        # Initialize Razorpay client with test keys from settings
        client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET_KEY))
        
        # Convert amount to paise (smallest currency unit) and ensure it's an integer
        # For testing, we'll use the security deposit amount
        amount_in_paise = int(security_deposit * 100)
        
        # Create Razorpay order
        order_data = {
            'amount': amount_in_paise,
            'currency': 'INR',
            'payment_capture': 1  # Auto-capture payment
        }
        
        order = client.order.create(data=order_data)
        
        # Store order details in session for verification
        request.session['razorpay_order_id'] = order['id']
        request.session['razorpay_amount'] = amount_in_paise
        request.session['booking_id'] = new_booking.id
        
        # Pass order details to template
        context = {
            'order_id': order['id'],
            'amount': amount_in_paise,
            'currency': 'INR',
            'booking': new_booking,
            'razorpay_key': settings.RAZORPAY_API_KEY,
            'customer': customer
        }
        
        return render(request, 'payment/razorpay_checkout.html', context)
        
    except Exception as e:
        messages.error(request, f"Error initiating payment: {str(e)}")
        return redirect('booking', vehicle_id=vehicle_id)


@csrf_exempt
def razorpay_payment_callback(request):
    """
    Handles Razorpay payment callback.
    """
    if request.method == 'POST':
        try:
            # Get payment details from POST data
            payment_data = json.loads(request.body)
            
            # Verify payment signature
            client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET_KEY))
            
            # Verify the payment signature
            params_dict = {
                'razorpay_order_id': payment_data.get('razorpay_order_id'),
                'razorpay_payment_id': payment_data.get('razorpay_payment_id'),
                'razorpay_signature': payment_data.get('razorpay_signature')
            }
            
            try:
                # Verify the payment signature
                client.utility.verify_payment_signature(params_dict)
                
                # Payment is successful, update booking and payment records
                booking_id = request.session.get('booking_id')
                if booking_id:
                    booking = RentalBooking.objects.get(id=booking_id)
                    customer = booking.customer
                    
                    # Update booking status
                    booking.booking_status = 'Confirmed'
                    booking.save()
                    
                    # Update payment records
                    payments = Payment.objects.filter(booking=booking)
                    razorpay_transaction_id = payment_data.get('razorpay_payment_id')
                    
                    # Update each payment with a unique transaction ID
                    for i, payment in enumerate(payments):
                        payment.payment_status = 'Completed'
                        # Create a unique transaction ID for each payment
                        # If it's the first payment, use the original Razorpay transaction ID
                        # For subsequent payments, append a suffix
                        if i == 0:
                            transaction_id = razorpay_transaction_id
                        else:
                            transaction_id = f"{razorpay_transaction_id}_{i+1}"
                        
                        # Check if this transaction ID already exists
                        existing_payment = Payment.objects.filter(transaction_id=transaction_id).first()
                        if not existing_payment:
                            payment.transaction_id = transaction_id
                        else:
                            # If it still exists, create a more unique ID
                            import uuid
                            unique_suffix = str(uuid.uuid4())[:8]
                            payment.transaction_id = f"{razorpay_transaction_id}_{unique_suffix}"
                        
                        payment.save()
                    
                    # Create success message
                    messages.success(request, 'Payment successful! Your booking is confirmed.')
                    return JsonResponse({'status': 'success', 'redirect_url': f'/booking/{booking_id}/'})
                else:
                    return JsonResponse({'status': 'error', 'message': 'Booking not found'})
                    
            except razorpay.errors.SignatureVerificationError:
                return JsonResponse({'status': 'error', 'message': 'Invalid payment signature'})
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
=======
    # Start with a base queryset, prefetching related data for efficiency
    # DBMS VIEW & JOIN Concept: .select_related('customer', 'vehicle') performs an INNER JOIN
    # on the customer and vehicle tables to fetch related data in a single query,
    # acting like a pre-defined VIEW for booking details.
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

    # DBMS JOIN Concept: .select_related() performs an INNER JOIN to fetch customer
    # and vehicle data along with the booking in one database query.
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
            booking.vehicle.status = 'Rented'
            booking.vehicle.save()
        messages.success(request, f"Booking #{booking.id} is now active.")
    else:
        messages.warning(request, f"Booking #{booking.id} cannot be activated (Status: {booking.booking_status}).")
    return redirect('bookings_management')
@user_passes_test(lambda u: u.is_superuser)
def admin_customers_view(request):
    """
    Displays a filterable, sortable, and paginated list of all customers
    for the admin panel.
    """
    # --- Simplified Query using the Database View ---
    # We now query the unmanaged CustomerDetailsView model.
    # The complex JOIN and COUNT logic is handled by the V_CustomerDetails
    # view in the database, making the Python code much cleaner.
    customer_list = CustomerDetailsView.objects.all()

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
    membership_tier = request.GET.get('membership_tier')

    if verification_status == 'verified':
        customer_list = customer_list.filter(is_verified=True)
    elif verification_status == 'unverified':
        customer_list = customer_list.filter(is_verified=False)
    if membership_tier:
        customer_list = customer_list.filter(membership_tier=membership_tier)

    # Sorting logic
    sort_by = request.GET.get('sort', '-registration_date')
    valid_sort_fields = ['first_name', 'email', 'registration_date', 'total_bookings']
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

    # Pass choices for the dropdown to the template
    membership_tier_choices = Customer.MEMBERSHIP_TIER_CHOICES

    context = {
        'customers': page_obj,
        'total_customers': paginator.count,
        'search_query': search_query,
        'sort_by': sort_by,
        'verification_status': verification_status,
        'membership_tier': membership_tier,
        'membership_tier_choices': membership_tier_choices,
    }
    return render(request, "admin/customers.html", context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def get_booking_details_ajax(request, booking_id):
    """
    Returns booking details as JSON for the modal view.
    """
    try:
        # DBMS JOIN Concept: .select_related() performs an INNER JOIN to fetch customer
        # and vehicle data along with the booking in one database query.
        booking = RentalBooking.objects.select_related('customer', 'vehicle').get(id=booking_id)
        data = {
            'id': booking.id,
            'customer_name': f"{booking.customer.first_name} {booking.customer.last_name}",
            'vehicle_name': f"{booking.vehicle.make} {booking.vehicle.model}",
            'vehicle_number': booking.vehicle.vehicle_number,
            'pickup_datetime': booking.pickup_datetime.strftime('%b %d, %Y, %I:%M %p'),
            'return_datetime': booking.return_datetime.strftime('%b %d, %Y, %I:%M %p'),
            'pickup_location': booking.pickup_location,
            'return_location': booking.return_location,
            'total_amount': f"₹{booking.total_amount:,.2f}",
            'security_deposit': f"₹{booking.security_deposit:,.2f}",
            'status': booking.booking_status,
            'special_requests': booking.special_requests or 'None',
        }
        return JsonResponse(data)
    except RentalBooking.DoesNotExist:
        return JsonResponse({'error': 'Booking not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




@login_required
@user_passes_test(lambda u: u.is_superuser)
def update_customer_verification_view(request, customer_id, action):
    """
    Admin view to mark a customer as 'verified' or 'unverified'.
    Consolidates verification logic into a single view.
    """
    customer = get_object_or_404(Customer, id=customer_id)
    
    if action == 'verify':
        if not customer.is_verified:
            customer.is_verified = True
            customer.save(update_fields=['is_verified'])
            CustomerActivityLog.objects.create(
                customer=customer,
                activity_type='Account Verification',
                description=f'Customer account verified by admin {request.user.email}'
            )
            messages.success(request, f"Customer {customer.email} has been verified.")
        else:
            messages.info(request, f"Customer {customer.email} is already verified.")
    elif action == 'unverify':
        if customer.is_verified:
            customer.is_verified = False
            customer.save(update_fields=['is_verified'])
            messages.success(request, f"Customer {customer.email}'s verification has been revoked.")
        else:
            messages.info(request, f"Customer {customer.email} is already unverified.")
    else:
        messages.error(request, "Invalid action specified.")
        
    return redirect('admin_customers')
>>>>>>> 95b19fba1109557a00be7f13a177d5081bad2746
