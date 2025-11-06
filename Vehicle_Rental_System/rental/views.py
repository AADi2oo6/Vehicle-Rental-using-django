from django.shortcuts import render, redirect, get_object_or_404
from .utils import dictfetchall
from django.db import connection, transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum, F
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.core.cache import cache
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpResponse
from django.utils.dateparse import parse_datetime
from django.db import transaction
from datetime import date, timedelta, datetime, timezone
import csv, decimal
from .models import Vehicle, Customer, FeedbackReview, RentalBooking, Payment, MaintenanceRecord, CustomerActivityLog, AdminBookingListView, AdminCustomerListView
from django.http import JsonResponse
from django.db.models import Sum
from .forms import PaymentForm, CustomerProfileForm

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

        if User.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
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
            # Check if the error is a database operational error from our trigger
            if isinstance(e, transaction.TransactionManagementError) and hasattr(e.__cause__, 'args') and e.__cause__.args[0] == 45000:
                messages.error(request, e.__cause__.args[1]) # Display the trigger's custom message
            else:
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
            # Step 1: Create the booking with a 'Pending' status (this is now the model's default)
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
            )

            # Step 2: Create a corresponding 'Pending' payment record for the advance amount
            Payment.objects.create(
                booking=booking,
                customer=customer,
                amount=total_amount * Decimal('0.2'), # Example: 20% advance payment
                payment_method='UPI', # Default method, can be changed on payment page
                payment_type='Advance',
                payment_status='Pending' # Crucial: The payment is pending
            )

            messages.info(request, f"Your booking for {vehicle.make} {vehicle.model} is pending. Please complete the payment to confirm.")
            return redirect('my_bookings')

    context = {
        'vehicle': vehicle,
    }
    return render(request, "booking.html", context)

@login_required
def confirm_payment_view(request, booking_id):
    """
    Simulates a successful payment, updating the booking and payment status.
    """
    booking = get_object_or_404(RentalBooking, id=booking_id, customer__user=request.user)
    with transaction.atomic():
        booking.payment_set.filter(payment_status='Pending').update(payment_status='Completed')
        booking.booking_status = 'Confirmed'
        booking.save()
    messages.success(request, f"Payment successful! Your booking #{booking.id} is now confirmed.")
    return redirect('my_bookings')

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
        # Instantiate the form with POST data and files for the image
        form = CustomerProfileForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            # Instead of form.save(), we will call the stored procedure
            # to ensure both User and Customer models are updated atomically.
            try:
                with connection.cursor() as cursor:
                    # The form handles the profile picture upload separately
                    if 'profile_picture' in request.FILES:
                        customer.profile_picture = request.FILES['profile_picture']
                        customer.save(update_fields=['profile_picture'])

                    # Call the stored procedure for all other text-based fields
                    cursor.callproc('sp_UpdateUserProfile', [
                        customer.id,
                        form.cleaned_data['first_name'],
                        form.cleaned_data['last_name'],
                        form.cleaned_data['phone'],
                        form.cleaned_data['address'],
                        form.cleaned_data['city'],
                        form.cleaned_data['state'],
                        form.cleaned_data['zip_code'],
                        form.cleaned_data['date_of_birth'],
                        form.cleaned_data['license_number'],
                        form.cleaned_data['is_subscribed_to_newsletter']
                    ])
                
                messages.success(request, "Your profile has been updated successfully!")
                return redirect('my_profile')
            except Exception as e:
                # Specifically catch the OperationalError from the database
                if isinstance(e, transaction.TransactionManagementError) and hasattr(e.__cause__, 'args') and e.__cause__.args[0] == 45000:
                    # The actual MySQL error is wrapped. We extract its custom message.
                    error_message = e.__cause__.args[1]
                    messages.error(request, error_message)
                else:
                    # For any other type of error, show a generic message
                    messages.error(request, f"An error occurred while updating your profile: {e}")

        else:
            messages.error(request, "There was an error updating your profile. Please correct the errors below.")
    else:
        # For GET request, instantiate forms with current customer data
        form = CustomerProfileForm(instance=customer)

    context = {
        'customer': customer,
        'form': form,
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
    # --- Calculate All-Time Total Revenue using the ORM ---
    total_revenue = Payment.objects.filter(
        payment_status='Completed'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # --- Remaining Django ORM Queries ---
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
    maintenance_records = MaintenanceRecord.objects.select_related('vehicle').order_by('-maintenance_date')
    upcoming_maintenance = MaintenanceRecord.objects.filter(
        status='Scheduled',
        maintenance_date__gt=date.today()
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
    booking = get_object_or_404(RentalBooking, id=booking_id)

    if request.method == 'POST':
        actual_return_datetime_str = request.POST.get('actual_return_datetime')
        final_payment_method = request.POST.get('final_payment_method')

        if not actual_return_datetime_str:
            messages.error(request, "Actual return date and time are required.")
            return redirect('return_vehicle', booking_id=booking_id)

        actual_return_datetime = parse_datetime(actual_return_datetime_str)

        try:
            with connection.cursor() as cursor:
                # Call the stored procedure
                cursor.callproc('CALCULATE_FINAL_BILL', [booking.id, actual_return_datetime, 0.0])
                # Fetch the output parameter
                cursor.execute("SELECT @_CALCULATE_FINAL_BILL_2")
                result = cursor.fetchone()
                final_charge = result[0] if result else 0.0

            with transaction.atomic():
                # Update booking status and actual return time
                booking.booking_status = 'Completed'
                booking.actual_return_datetime = actual_return_datetime
                booking.save()

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
    - UPDATED: Now uses specific stored procedures for each status filter.
    """
    # --- Get filter and sort parameters from the request ---
    customer_name = request.GET.get('customer_name') or None
    booking_date_str = request.GET.get('booking_date') or None
    selected_status = request.GET.get('status') or None
    
    sort_by = request.GET.get('sort', 'booking_date')
    order = 'DESC' if request.GET.get('order', 'desc') == 'desc' else 'ASC'

    # Whitelist valid sort fields to prevent SQL injection
    valid_sort_fields = ['booking_date', 'pickup_datetime', 'return_datetime', 'total_amount', 'booking_status']
    if sort_by not in valid_sort_fields:
        sort_by = 'booking_date' # Default sort

    # --- Determine which Stored Procedure to call based on the selected status ---
    if selected_status == 'Confirmed':
        procedure_name = 'sp_GetConfirmedBookings'
    elif selected_status == 'Active':
        procedure_name = 'sp_GetActiveBookings'
    elif selected_status == 'Completed':
        procedure_name = 'sp_GetCompletedBookings'
    elif selected_status == 'Cancelled':
        procedure_name = 'sp_GetCancelledBookings'
    else: # Default to "All"
        procedure_name = 'sp_GetAllBookings'

    with connection.cursor() as cursor:
        cursor.callproc(procedure_name, [
            customer_name,
            booking_date_str,
            sort_by,
            order
        ])
        # The dictfetchall utility converts the raw results into a list of dictionaries,
        # which is easy to work with in the template.
        bookings = dictfetchall(cursor)

    # CSV Export
    if 'export' in request.GET and request.GET['export'] == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="bookings.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Customer Name', 'Customer ID', 'Vehicle', 'Vehicle Number', 'Pickup Date', 'Return Date', 'Total Amount', 'Status'])
        for booking in bookings: # The raw results can be used directly here
            writer.writerow([
                booking.get('booking_id'),
                booking.get('customer_full_name'),
                booking.get('customer_id'),
                booking.get('vehicle_name'),
                booking.get('vehicle_number'),
                booking.get('pickup_datetime').strftime('%Y-%m-%d %H:%M'),
                booking.get('return_datetime').strftime('%Y-%m-%d %H:%M'),
                booking.get('total_amount'),
                booking.get('booking_status')
            ])
        return response

    # --- Bulk Actions ---
    if request.method == 'POST' and request.POST.get('bulk_action'):
        booking_ids = request.POST.getlist('booking_ids')
        action = request.POST.get('action')

        if not booking_ids:
            messages.warning(request, "Please select at least one booking to perform a bulk action.")
        else:
            try:
                # Convert list of IDs to a comma-separated string for the stored procedure
                booking_ids_str = ",".join(booking_ids)
                new_status = ""
                
                if action == 'mark_completed':
                    new_status = 'Completed'
                elif action == 'cancel_selected':
                    new_status = 'Cancelled'

                if new_status:
                    with connection.cursor() as cursor:
                        cursor.callproc('sp_AdminBulkUpdateBookingStatus', [booking_ids_str, new_status, request.user.id])
                    messages.success(request, f"{len(booking_ids)} bookings have been updated to '{new_status}'.")
            except Exception as e:
                messages.error(request, f"An error occurred during the bulk update: {e}")
            
            return redirect('bookings_management')
    # --- Pagination ---
    paginator = Paginator(bookings, 10) # 10 bookings per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'bookings': page_obj,
        'customer_name': customer_name,
        'booking_date': booking_date_str,
        'selected_status': selected_status or '',
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
    try:
        with connection.cursor() as cursor:
            # Call the stored procedure that returns multiple result sets
            cursor.callproc('sp_GetBookingDetails', [booking_id])

            # Fetch the first result set (booking details)
            booking_details = dictfetchall(cursor)
            if not booking_details:
                messages.error(request, f"Booking with ID {booking_id} not found.")
                return redirect('bookings_management')
            booking = booking_details[0]

            # Fetch the second result set (payments)
            cursor.nextset()
            payments = dictfetchall(cursor)

    except Exception as e:
        messages.error(request, f"An error occurred while fetching booking details: {e}")
        return redirect('bookings_management')

    context = {
        'booking': booking,
        'payments': payments,
    }
    return render(request, 'admin/booking_detail.html', context)

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

@login_required
def complete_booking_view(request, booking_id):
    """
    Admin action to directly mark a booking as completed.
    This is a shortcut for when the full return/billing process is not needed.
    """
    if not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('home')

    booking = get_object_or_404(RentalBooking, id=booking_id)
    if booking.booking_status in ['Active', 'Confirmed']:
        with transaction.atomic():
            booking.booking_status = 'Completed'
            # If the actual return time isn't set, default it to the scheduled return time.
            if not booking.actual_return_datetime:
                booking.actual_return_datetime = booking.return_datetime
            booking.save()
        messages.success(request, f"Booking #{booking.id} has been marked as Completed.")
    else:
        messages.warning(request, f"Booking #{booking.id} cannot be completed (Status: {booking.booking_status}).")
    return redirect('bookings_management')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_customers_view(request):
    """
    Displays a filterable and sortable list of customers using raw SQL queries.
    """
    # --- Build Raw SQL Query based on filters ---
    base_query = "SELECT * FROM vw_AdminCustomerList"
    where_clauses = []
    params = []

    # Get filter values from the request
    search_query = request.GET.get('q', '').strip()
    verification_status = request.GET.get('verification_status', '').strip()
    membership_tier = request.GET.get('membership_tier', '').strip()
    city = request.GET.get('city', '').strip()
    state = request.GET.get('state', '').strip()

    # Dynamically build the WHERE clause with parameterization
    if search_query:
        like_query = f"%{search_query}%"
        where_clauses.append("(first_name LIKE %s OR last_name LIKE %s OR email LIKE %s OR phone LIKE %s OR license_number LIKE %s)")
        params.extend([like_query] * 5)

    if verification_status == 'verified':
        where_clauses.append("is_verified = TRUE")
    elif verification_status == 'unverified':
        where_clauses.append("is_verified = FALSE")

    if membership_tier:
        where_clauses.append("membership_tier = %s")
        params.append(membership_tier)

    if city:
        where_clauses.append("city LIKE %s")
        params.append(f"%{city}%")

    if state:
        where_clauses.append("state LIKE %s")
        params.append(f"%{state}%")

    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)

    # Add sorting to the query
    sort_by = request.GET.get('sort', 'registration_date')
    order = 'DESC' if request.GET.get('order', 'desc') == 'desc' else 'ASC'
    valid_sort_fields = ['first_name', 'email', 'registration_date']
    if sort_by not in valid_sort_fields:
        sort_by = 'registration_date'
    base_query += f" ORDER BY {sort_by} {order}"

    # Execute the raw query
    customer_list = list(AdminCustomerListView.objects.raw(base_query, params))

    # --- Bulk Actions ---
    if request.method == 'POST' and 'bulk_action' in request.POST:
        customer_ids = request.POST.getlist('customer_ids')
        action = request.POST.get('action')

        if not customer_ids:
            messages.warning(request, "Please select at least one customer.")
        else:
            try:
                customer_ids_str = ",".join(customer_ids)
                if action in ['verify_selected', 'unverify_selected']:
                    new_status = (action == 'verify_selected')
                    with connection.cursor() as cursor:
                        cursor.callproc('sp_AdminBulkUpdateVerificationStatus', [customer_ids_str, new_status, request.user.id])
                    status_text = "verified" if new_status else "un-verified"
                    messages.success(request, f"{len(customer_ids)} customers have been {status_text}.")
                elif action in ['activate_selected', 'deactivate_selected']:
                    new_status = (action == 'activate_selected')
                    with connection.cursor() as cursor:
                        cursor.callproc('sp_AdminBulkUpdateCustomerStatus', [customer_ids_str, new_status, request.user.id])
                    status_text = "activated" if new_status else "deactivated"
                    messages.success(request, f"{len(customer_ids)} customers have been {status_text}.")
            except Exception as e:
                messages.error(request, f"An error occurred during the bulk update: {e}")
        return redirect('admin_customers')

    # Pagination
    paginator = Paginator(customer_list, 10) # 10 customers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'customers': page_obj,
        'total_customers': paginator.count,
        'search_query': search_query,
        'sort_by': sort_by.strip('-'),
        'order': order,
        'verification_status': verification_status,
        'membership_tier': membership_tier,
        'city': city,
        'state': state,
    }
    return render(request, "admin/customers.html", context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def export_customers_csv_view(request):
    """
    Exports a filtered list of customers to a CSV file using a raw, parameterized SQL query.
    """
    # --- Build Raw SQL Query based on filters ---
    base_query = "SELECT * FROM vw_AdminCustomerList"
    where_clauses = []
    params = []

    # Get all the same filter values from the request
    search_query = request.GET.get('q', '')
    verification_status = request.GET.get('verification_status', '')
    membership_tier = request.GET.get('membership_tier', '')
    city = request.GET.get('city', '')
    state = request.GET.get('state', '')

    if search_query:
        like_query = f"%{search_query}%"
        where_clauses.append("(first_name LIKE %s OR last_name LIKE %s OR email LIKE %s OR phone LIKE %s OR license_number LIKE %s)")
        params.extend([like_query] * 5)

    if verification_status == 'verified':
        where_clauses.append("is_verified = TRUE")
    elif verification_status == 'unverified':
        where_clauses.append("is_verified = FALSE")

    if membership_tier:
        where_clauses.append("membership_tier = %s")
        params.append(membership_tier)

    if city:
        where_clauses.append("city LIKE %s")
        params.append(f"%{city}%")

    if state:
        where_clauses.append("state LIKE %s")
        params.append(f"%{state}%")

    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)

    # Add sorting to the query
    sort_by = request.GET.get('sort', 'registration_date')
    order = 'DESC' if request.GET.get('order', 'desc') == 'desc' else 'ASC'
    valid_sort_fields = ['first_name', 'email', 'registration_date']
    if sort_by not in valid_sort_fields:
        sort_by = 'registration_date'
    base_query += f" ORDER BY {sort_by} {order}"

    # Execute the raw query
    customer_list = list(AdminCustomerListView.objects.raw(base_query, params))

    # --- Bulk Actions ---
    if request.method == 'POST' and 'bulk_action' in request.POST:
        customer_ids = request.POST.getlist('customer_ids')
        action = request.POST.get('action')

        if not customer_ids:
            messages.warning(request, "Please select at least one customer.")
        else:
            try:
                customer_ids_str = ",".join(customer_ids)
                if action in ['verify_selected', 'unverify_selected']:
                    new_status = (action == 'verify_selected')
                    with connection.cursor() as cursor:
                        cursor.callproc('sp_AdminBulkUpdateVerificationStatus', [customer_ids_str, new_status, request.user.id])
                    status_text = "verified" if new_status else "un-verified"
                    messages.success(request, f"{len(customer_ids)} customers have been {status_text}.")
                elif action in ['activate_selected', 'deactivate_selected']:
                    new_status = (action == 'activate_selected')
                    with connection.cursor() as cursor:
                        cursor.callproc('sp_AdminBulkUpdateCustomerStatus', [customer_ids_str, new_status, request.user.id])
                    status_text = "activated" if new_status else "deactivated"
                    messages.success(request, f"{len(customer_ids)} customers have been {status_text}.")
            except Exception as e:
                messages.error(request, f"An error occurred during the bulk update: {e}")
        return redirect('admin_customers')

    # Pagination
    paginator = Paginator(customer_list, 10) # 10 customers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'customers': page_obj,
        'total_customers': paginator.count,
        'search_query': search_query,
        'sort_by': sort_by.strip('-'),
        'order': order,
        'verification_status': verification_status,
        'membership_tier': membership_tier,
        'city': city,
        'state': state,
    }
    return render(request, "admin/customers.html", context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def export_customers_csv_view(request):
    """
    Exports a filtered list of customers to a CSV file using a raw, parameterized SQL query.
    """
    # --- Build Raw SQL Query based on filters ---
    base_query = "SELECT * FROM vw_AdminCustomerList"
    where_clauses = []
    params = []

    # Get all the same filter values from the request
    search_query = request.GET.get('q', '')
    verification_status = request.GET.get('verification_status', '')
    membership_tier = request.GET.get('membership_tier', '')
    city = request.GET.get('city', '')
    state = request.GET.get('state', '')

    # Dynamically build the WHERE clause with parameterization
    if search_query:
        like_query = f"%{search_query}%"
        where_clauses.append("(first_name LIKE %s OR last_name LIKE %s OR email LIKE %s OR phone LIKE %s OR license_number LIKE %s)")
        params.extend([like_query] * 5)

    if verification_status == 'verified':
        where_clauses.append("is_verified = TRUE")
    elif verification_status == 'unverified':
        where_clauses.append("is_verified = FALSE")

    if membership_tier:
        where_clauses.append("membership_tier = %s")
        params.append(membership_tier)

    if city:
        where_clauses.append("city LIKE %s")
        params.append(f"%{city}%")

    if state:
        where_clauses.append("state LIKE %s")
        params.append(f"%{state}%")

    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)

    # Execute the raw query using a direct database cursor
    with connection.cursor() as cursor:
        cursor.execute(base_query, params)
        customers = dictfetchall(cursor)

    # Generate the CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="customers.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'First Name', 'Last Name', 'Email', 'Phone', 'City', 'State', 'Membership', 'Verified'])
    for customer in customers:
        writer.writerow([
            customer['id'], customer['first_name'], customer['last_name'], customer['email'],
            customer['phone'], customer['city'], customer['state'], customer['membership_tier'],
            customer['is_verified']
        ])
    return response

@login_required
@user_passes_test(lambda u: u.is_superuser)
def verify_customer_view(request, customer_id):
    """
    Admin view to mark a customer as verified.
    Performs a targeted UPDATE.
    UPDATED: Now calls the `sp_AdminVerifyUser` stored procedure to enforce database-level validation.
    """
    customer = get_object_or_404(Customer, id=customer_id)
 
    if customer.is_verified:
        messages.info(request, f"Customer {customer.email} is already verified.")
        return redirect('admin_customers')
 
    try:
        with connection.cursor() as cursor:
            # Call the stored procedure to perform the verification and its checks
            cursor.callproc('sp_AdminVerifyUser', [customer.id])
        
        # The AFTER UPDATE trigger on the database now handles the admin audit log automatically.
        messages.success(request, f"Customer {customer.email} has been successfully verified.")

    except Exception as e:
        # This will catch the SIGNAL from the stored procedure if validation fails.
        messages.error(request, f"Verification failed: {e}")

    return redirect('admin_customers')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def unverify_customer_view(request, customer_id):
    """
    Admin view to mark a customer as unverified.
    """
    customer = get_object_or_404(Customer, id=customer_id)

    if customer.is_verified:
        try:
            with connection.cursor() as cursor:
                # Call the stored procedure, passing the admin's user ID for auditing
                cursor.callproc('sp_AdminUnverifyUser', [customer.id, request.user.id])
            messages.success(request, f"Customer {customer.email}'s verification has been revoked.")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
    else:
        messages.info(request, f"Customer {customer.email} is already unverified.")
    
    return redirect('admin_customers')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_customer_detail_ajax_view(request, customer_id):
    """
    Fetches detailed customer data via a stored procedure and returns it as JSON
    for use in an AJAX-powered modal.
    """
    try:
        with connection.cursor() as cursor:
            cursor.callproc('sp_GetCustomerDetails', [customer_id])

            # Fetch customer details
            customer_details = dictfetchall(cursor)
            if not customer_details:
                return JsonResponse({'error': 'Customer not found'}, status=404)
            
            customer = customer_details[0]
            # Convert non-serializable types to strings
            for key, value in customer.items():
                if isinstance(value, (datetime, date)):
                    customer[key] = value.isoformat()

            # Fetch booking history
            cursor.nextset()
            bookings = dictfetchall(cursor)
            for booking in bookings:
                for key, value in booking.items():
                    if isinstance(value, (datetime, date)):
                        booking[key] = value.isoformat()
                    elif isinstance(value, decimal.Decimal):
                        booking[key] = str(value)

            # The third result set (payments) is not needed for this modal view

            return JsonResponse({'customer': customer, 'bookings': bookings})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_customer_detail_view(request, customer_id):
    """
    Displays a detailed view of a single customer, including their bookings and payments,
    by calling the `sp_GetCustomerDetails` stored procedure.
    """
    try:
        with connection.cursor() as cursor:
            # Call the stored procedure that returns multiple result sets
            cursor.callproc('sp_GetCustomerDetails', [customer_id])

            # Fetch the first result set (customer details)
            customer_details = dictfetchall(cursor)
            if not customer_details:
                messages.error(request, f"Customer with ID {customer_id} not found.")
                return redirect('admin_customers')
            customer = customer_details[0]

            # Fetch the second result set (bookings)
            cursor.nextset()
            bookings = dictfetchall(cursor)

            # Fetch the third result set (payments)
            cursor.nextset()
            payments = dictfetchall(cursor)

    except Exception as e:
        messages.error(request, f"An error occurred while fetching customer details: {e}")
        return redirect('admin_customers')

    context = {
        'customer': customer,
        'bookings': bookings,
        'payments': payments,
    }
    return render(request, 'admin/customer_detail.html', context)