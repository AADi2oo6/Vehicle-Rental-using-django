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
from django.utils.dateparse import parse_datetime # Keep this for existing uses
import csv # Added for CSV export in bookings_management_view
from django.db import transaction
from datetime import date, timedelta, datetime
from .models import Vehicle, Customer, FeedbackReview, RentalBooking, Payment, MaintenanceRecord
from django.http import JsonResponse
from django.db.models import Sum
from .forms import PaymentForm  # Import the new form
from .models import Payment
from .forms import AdminBookingForm # Import the new form

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


@login_required
def admin_dashboard_view(request):
    """
    Retrieves key metrics (revenue, counts). Attempts Stored Procedure call
    but falls back to reliable ORM calculation.
    """
    
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('home')

    # --- Calculate All-Time Total Revenue using the ORM ---
    total_revenue = Payment.objects.filter(
        payment_status='Completed'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # --- Remaining Django ORM Queries ---
    pending_payments_count = Payment.objects.filter(payment_status='Pending').count()
    active_rentals_count = RentalBooking.objects.filter(booking_status='Active').count()
    maintenance_vehicles_count = Vehicle.objects.filter(status='Maintenance').count()
    
    recent_payments = Payment.objects.select_related('customer').order_by('-payment_date')[:5]
    recent_bookings = RentalBooking.objects.select_related('customer', 'vehicle').order_by('-booking_date')[:5]
    
    context = {
        'total_revenue': total_revenue, 
        'pending_payments_count': pending_payments_count,
        'active_rentals_count': active_rentals_count,
        'maintenance_vehicles_count': maintenance_vehicles_count,
        'recent_payments': recent_payments,
        'recent_bookings': recent_bookings,
    }
    return render(request, "admin_dashboard_bootstrap.html", context)
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

@login_required
def admin_payments_view(request): 
    """
    Handles payments list, filtering, sorting, and aggregation.
    """
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('home')
    
    # --- Base Query ---
    payments = Payment.objects.select_related('customer', 'booking__vehicle').order_by('-payment_date')
    
    # --- Filtering Variables ---
    search_query = request.GET.get('q', '').strip()
    payment_status = request.GET.get('status')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    # --- 1. Apply Universal Search (Text) ---
    if search_query:
        payments = payments.filter(
            Q(id__icontains=search_query) |
            Q(customer__first_name__icontains=search_query) |
            Q(customer__last_name__icontains=search_query) |
            Q(transaction_id__icontains=search_query) |
            Q(booking__vehicle__vehicle_number__icontains=search_query)
        )

    # --- 2. Apply Date Range Filter ---
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() + timedelta(days=1)
            payments = payments.filter(payment_date__gte=start_date, payment_date__lt=end_date)
            
        except ValueError:
            messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")

    # --- 3. Apply Status Filter ---
    if payment_status:
        payments = payments.filter(payment_status=payment_status)
    
    # --- 4. Apply Sorting ---
    sort_by = request.GET.get('sort', 'payment_date')
    order = request.GET.get('order', 'desc')
    if order == 'asc':
        payments = payments.order_by(sort_by)
    else:
        payments = payments.order_by(f'-{sort_by}')

    # --- 5. Aggregation for Reports ---
    monthly_revenue = Payment.objects.filter(payment_status='Completed').annotate(
        month=TruncMonth('payment_date')
    ).values('month').annotate(total_revenue=Sum('amount')).order_by('month')
    top_customers = Payment.objects.filter(payment_status='Completed').values(
        'customer__first_name', 'customer__last_name'
    ).annotate(total_spent=Sum('amount')).order_by('-total_spent')[:10]
    
    context = {
        'payments': payments,
        'monthly_revenue': monthly_revenue,
        'top_customers': top_customers,
        'selected_status': payment_status,
        'sort_by': sort_by,
        'order': order,
        'search_query': search_query,
        'start_date': start_date_str,
        'end_date': end_date_str,
    }
    return render(request, "admin/payments.html", context)

def payment_form_view(request, payment_id=None):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('home')

    payment = None
    if payment_id:
        payment = get_object_or_404(Payment, id=payment_id)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, "Payment saved successfully.")
            return redirect('admin_payments')
    else:
        form = PaymentForm(instance=payment)
    
    context = {'form': form}
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
    return redirect('admin_payments')
    pass
@login_required
def payment_analytics_view(request):
    """
    Executes and consolidates the results of Self-Join, Correlated Query, 
    and Set Operations for advanced payment analytics.
    """
    if not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('admin_dashboard')

    # --- 1. Self-Join Query (Repeated Transactions) ---
    self_join_query = """
    SELECT 
        P1.customer_id,
        C.first_name,
        C.last_name,
        P1.payment_method,
        COUNT(P1.id) AS transaction_count,
        SUM(P1.amount) AS total_spent
    FROM 
        rental_payment P1
    JOIN 
        rental_customer C ON P1.customer_id = C.id
    GROUP BY 
        P1.customer_id, P1.payment_method
    HAVING 
        COUNT(P1.id) > 1 
    ORDER BY 
        total_spent DESC
    LIMIT 10;
    """
    
    # --- 2. Correlated Subquery: Find First Payment Date ---
    correlated_query = """
    SELECT
        C.first_name,
        SUM(P.amount) AS total_spent,
        (
            SELECT MIN(payment_date) 
            FROM rental_payment P_inner
            WHERE P_inner.customer_id = P.customer_id AND P_inner.payment_status = 'Completed'
        ) AS first_payment_date
    FROM rental_payment P
    JOIN rental_customer C ON P.customer_id = C.id
    WHERE P.payment_status = 'Completed'
    GROUP BY C.id, C.first_name
    ORDER BY total_spent DESC
    LIMIT 5;
    """
    
    # --- 3. Set Operation: UNION (Credit Card OR Refunded) ---
    union_query = """
    (
        SELECT id, customer_id, amount, 'Credit Card' AS category, payment_date
        FROM rental_payment
        WHERE payment_method = 'Credit Card'
    )
    UNION
    (
        SELECT id, customer_id, amount, 'Refunded Payment' AS category, payment_date
        FROM rental_payment
        WHERE payment_status = 'Refunded'
    )
    ORDER BY payment_date DESC
    LIMIT 5;
    """

    # Execute all queries
    data = {}
    try:
        with connection.cursor() as cursor:
            # Execute Self-Join
            cursor.execute(self_join_query)
            columns = [col[0] for col in cursor.description]
            data['repeated_transactions'] = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Execute Correlated Query
            cursor.execute(correlated_query)
            columns = [col[0] for col in cursor.description]
            data['correlated_results'] = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Execute UNION Query
            cursor.execute(union_query)
            columns = [col[0] for col in cursor.description]
            data['union_results'] = [dict(zip(columns, row)) for row in cursor.fetchall()]

    except Exception as e:
        messages.error(request, f"Advanced SQL Query Failed. Check if AuditLog table exists. Error: {e}")
        data = {
            'repeated_transactions': [], 'correlated_results': [], 'union_results': [],
            'error_message': str(e)
        }

    return render(request, 'admin/payment_self_join_report.html', data)

@login_required
def return_vehicle_view(request, booking_id):
    """
    Handles the calculation of the final bill using the Stored Procedure,
    updates the database, and redirects the admin.
    """
    if not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('admin_dashboard')

    booking = get_object_or_404(RentalBooking, id=booking_id)

    if request.method == 'POST':
        actual_return_dt_str = request.POST.get('actual_return_datetime')
        final_payment_method = request.POST.get('final_payment_method')
        
        if not actual_return_dt_str:
            messages.error(request, "Actual return time is required.")
            return redirect(request.path)

        actual_return_dt = datetime.strptime(actual_return_dt_str, '%Y-%m-%dT%H:%M')

        try:
            with transaction.atomic():
                final_amount = 0.00
                
                # --- 1. Call Procedure (Lab Assignment 6) ---
                with connection.cursor() as cursor:
                    cursor.execute("SET @final_bill = 0;") 
                    
                    # Call procedure using cursor.execute to ensure it's logged
                    cursor.execute("CALL CALCULATE_FINAL_BILL(%s, %s, %s, @final_bill);", [
                        booking.id, 
                        actual_return_dt_str, 
                        final_payment_method
                    ])

                    # Retrieve the final amount
                    cursor.execute("SELECT @final_bill;")
                    result = cursor.fetchone()
                    
                    if result and result[0] is not None:
                        final_amount = result[0]

                # --- 2. Create Payment Record (for any late fee/balance) ---
                if final_amount > 0:
                    Payment.objects.create(
                        booking=booking,
                        customer=booking.customer,
                        amount=final_amount,
                        payment_method=final_payment_method,
                        payment_type='Fine', # Use 'Fine' for simplicity of the final charge
                        payment_status='Completed'
                    )
                
                # Note: The Stored Procedure handles updating booking_status and vehicle status.
                
            messages.success(request, f"Booking #{booking.id} finalized. Final amount charged: ₹{final_amount:.2f}")
            
            # FIX: Use the correct, defined URL name for bookings management
            return redirect('bookings_management')

        except Exception as e:
            # Catch any lingering database/Python errors and report them
            messages.error(request, f"A critical error occurred after procedure execution. Check DB logs. Error: {e}")
            return redirect(request.path)

    # --- GET Request: Display Form ---
    context = {
        'booking': booking,
        # Ensure that PAYMENT_METHODS are available if needed for the form (though not strictly necessary here)
        'PAYMENT_METHODS': Payment.PAYMENT_METHODS if hasattr(Payment, 'PAYMENT_METHODS') else [('Credit Card', 'Credit Card')], 
    }
    return render(request, 'admin/return_vehicle_form.html', context)


def change_password_view(request):
    """
    Allows a logged-in admin to change their password.
    """
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to change passwords.")
        return redirect('admin_dashboard')

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

@login_required
def bookings_management_view(request):
    """
    Provides a comprehensive view for managing rental bookings.
    - Displays all bookings in a filterable and sortable table.
    - Includes multi-table data from Customer and Vehicle.
    """
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('home')

    # Start with a base queryset, prefetching related data for efficiency
    bookings = RentalBooking.objects.select_related('customer', 'vehicle').order_by('-booking_date')

    # Universal Search
    search_query = request.GET.get('q', '')
    if search_query:
        bookings = bookings.filter(
            Q(id__icontains=search_query) |
            Q(customer__first_name__icontains=search_query) |
            Q(customer__last_name__icontains=search_query) |
            Q(vehicle__make__icontains=search_query) |
            Q(vehicle__model__icontains=search_query)
        )

    # Date Range Filtering
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    if start_date_str and end_date_str:
        bookings = bookings.filter(booking_date__range=[start_date_str, end_date_str])

    # Filtering logic
    booking_status = request.GET.get('status')
    if booking_status:
        bookings = bookings.filter(booking_status=booking_status)

    # CSV Export
    if 'export' in request.GET and request.GET['export'] == 'csv':
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="bookings.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Customer', 'Vehicle', 'Pickup Date', 'Return Date', 'Total Amount', 'Status'])
        for booking in bookings: # Use the filtered queryset
            writer.writerow([
                booking.id,
                f"{booking.customer.first_name} {booking.customer.last_name}",
                f"{booking.vehicle.make} {booking.vehicle.model}",
                booking.pickup_datetime,
                booking.return_datetime,
                booking.total_amount,
                booking.booking_status
            ])
        return response

    # Bulk Actions
    if request.method == 'POST' and 'bulk_action' in request.POST:
        booking_ids = request.POST.getlist('booking_ids')
        action = request.POST.get('action')
        if booking_ids and action:
            selected_bookings = RentalBooking.objects.filter(id__in=booking_ids)
            if action == 'mark_completed':
                updated_count = selected_bookings.update(booking_status='Completed')
                messages.success(request, f"{updated_count} bookings marked as completed.")
            elif action == 'cancel_selected':
                updated_count = selected_bookings.update(booking_status='Cancelled')
                messages.success(request, f"{updated_count} bookings have been cancelled.")
            return redirect('bookings_management')

    total_bookings_count = bookings.count()
    confirmed_bookings_count = bookings.filter(booking_status='Confirmed').count()
    active_bookings_count = bookings.filter(booking_status='Active').count()
    completed_bookings_count = bookings.filter(booking_status='Completed').count()

    # Sorting logic
    sort_by = request.GET.get('sort', 'booking_date')
    order = request.GET.get('order', 'desc') # Default to descending
    valid_sort_fields = ['booking_date', 'pickup_date', 'return_date', 'total_amount', 'booking_status']
    if sort_by in valid_sort_fields:
        if order == 'asc':
            bookings = bookings.order_by(sort_by)
        else:
            bookings = bookings.order_by(f'-{sort_by}')

    # Pagination logic
    paginator = Paginator(bookings, 15) # Show 15 bookings per page
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        'bookings': page_obj, # Pass the paginated object to the template
        'selected_status': booking_status,
        'total_bookings_count': total_bookings_count,
        'confirmed_bookings_count': confirmed_bookings_count,
        'active_bookings_count': active_bookings_count,
        'completed_bookings_count': completed_bookings_count,
        'sort_by': sort_by,
        'order': order,
        'search_query': search_query,
        'start_date': start_date_str,
        'end_date': end_date_str,
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
            booking.vehicle.status = 'Rented'
            booking.vehicle.save()
        messages.success(request, f"Booking #{booking.id} is now active.")
    else:
        messages.warning(request, f"Booking #{booking.id} cannot be activated (Status: {booking.booking_status}).")
    return redirect('bookings_management')
