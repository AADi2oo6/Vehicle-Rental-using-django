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
from django.db import transaction, DatabaseError
from datetime import date, timedelta, datetime
from .models import Vehicle, Customer, FeedbackReview, RentalBooking, Payment, MaintenanceRecord, ActivityLog # Import ActivityLog
from django.http import JsonResponse
from django.db.models import Sum
from .forms import PaymentForm
from decimal import Decimal

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

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            customer = Customer.objects.get(email=email)
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
            else:
                messages.error(request, 'Invalid email or password.')
        except Customer.DoesNotExist:
            messages.error(request, 'Invalid email or password.')
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
        
    messages.success(request, "You have been logged out.")
    return redirect('home')

def vehicle_list_view(request):
    """
    Handles the display of all vehicles with multi-layered filtering and sorting.
    """
    customer = None
    customer_id = request.session.get('customer_id')
    if customer_id:
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            del request.session['customer_id']

    # Start with a base queryset of vehicles that are not retired
    vehicle_list = Vehicle.objects.filter(status='Available')

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
    if sort_by == 'price_asc':
        vehicle_list = vehicle_list.order_by('hourly_rate')
    elif sort_by == 'price_desc':
        vehicle_list = vehicle_list.order_by('-hourly_rate')
    else: # Default sort
        vehicle_list = vehicle_list.order_by('make', 'model')

    # --- Pagination ---
    paginator = Paginator(vehicle_list, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'customer': customer,
        'vehicles': page_obj,
        'values': request.GET, # To pre-fill the form
    }
    return render(request, "vehicles.html", context)


@login_required
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
        pickup_location = request.POST.get('pickup_location')
        return_location = request.POST.get('return_location')
        
        # --- Validation Block ---
        if vehicle.location.lower() not in pickup_location.lower():
            messages.error(request, f"Sorry, this vehicle is not available for pickup in your selected area. It is based in {vehicle.location}.")
            return redirect('booking', vehicle_id=vehicle.id)

        if not all([pickup_str, return_str, pickup_location, return_location]):
            messages.error(request, "All fields are required.")
            return redirect('booking', vehicle_id=vehicle.id)

        pickup_datetime = parse_datetime(pickup_str)
        return_datetime = parse_datetime(return_str)

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
    return render(request, "booking.html", context)
 

@login_required
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
                booking_status='Confirmed' # Confirmed, but pending payment
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


@login_required
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
    customer = None
    customer_id = request.session.get('customer_id')
    if customer_id:
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            del request.session['customer_id']
    context = {'customer': customer}
    return render(request, "about_us.html", context)

@login_required
def my_profile_view(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        messages.error(request, "You need to be logged in to view your profile.")
        return redirect('home')
    customer = get_object_or_404(Customer, id=customer_id)
    bookings = RentalBooking.objects.filter(customer=customer).select_related('vehicle').order_by('-booking_date')
    context = {
        'customer': customer,
        'bookings': bookings,
    }
    return render(request, "my_profile.html", context)


@login_required
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


@login_required
def my_bookings_view(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        messages.error(request, "You need to be logged in to view your bookings.")
        return redirect('home')
    customer = get_object_or_404(Customer, id=customer_id)
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

@login_required
def add_review(request, booking_id):
    """
    Handles the creation of a new review for a specific booking.
    Demonstrates: CRUD (Create), ACID Transactions.
    """
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

        try:
            # --- DBMS Concept: ACID Transaction ---
            with transaction.atomic():
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

@login_required
def edit_review(request, review_id):
    """
    Handles the updating of an existing review.
    Demonstrates: CRUD (Update), ACID Transactions.
    """
    customer = get_object_or_404(Customer, id=request.session.get('customer_id'))
    review = get_object_or_404(FeedbackReview, id=review_id, customer=customer)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        review_text = request.POST.get('review_text')

        if not rating:
            messages.error(request, "A rating is required.")
            return redirect('booking_detail', booking_id=review.booking.id)

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

@login_required
def delete_review(request, review_id):
    """
    Handles the deletion of an existing review.
    Demonstrates: CRUD (Delete), ACID Transactions.
    """
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