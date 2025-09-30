from django.shortcuts import render
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
from django.db import transaction
from datetime import date, timedelta, datetime
from rental.models import Vehicle , RentalBooking, Payment, MaintenanceRecord
from django.http import JsonResponse
from django.db.models import Sum
from rental.forms import PaymentForm  # Import the new form
from rental.models import Payment
# Create your views here.
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
@login_required
def admin_dashboard_view(request):
    """
    Retrieves key metrics (revenue, counts). Attempts Stored Procedure call
    but falls back to reliable ORM calculation.
    """
    
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('home')

    current_month = date.today().month
    current_year = date.today().year
    total_revenue = 0
    
    # --- Fallback Calculation (The reliable truth value) ---
    # We calculate this first so we always have the correct number if the procedure fails.
    orm_revenue = Payment.objects.filter(
        payment_status='Completed',
        payment_date__year=current_year,
        payment_date__month=current_month
    ).aggregate(total=Sum('amount'))['total'] or 0
    total_revenue = orm_revenue # Start with the correct ORM value

    try:
        # --- STIPULATED STORED PROCEDURE CALL (For Assignment Demonstration) ---
        with connection.cursor() as cursor:
            # 1. Set the MySQL session variable to 0
            cursor.execute("SET @p_total_revenue = 0;") 
            
            # 2. Execute the Stored Procedure
            cursor.callproc('GET_TOTAL_REVENUE', [current_year, current_month, 0])
            
            # 3. Retrieve the OUT parameter
            cursor.execute("SELECT @p_total_revenue;")
            result = cursor.fetchone()
            
            # 4. If the result is a non-zero value, use it. Otherwise, rely on ORM.
            if result and result[0] is not None and float(result[0]) > 0:
                total_revenue = result[0]
                messages.success(request, "Revenue calculated via PL/SQL Procedure.")
            else:
                 raise Exception("success orm")


    except Exception as e:
        # If the procedure fails entirely (e.g., deleted), the ORM value is already set above.
        print(f"orm {e}")
        
        
        # total_revenue is already set to orm_revenue before the try block.

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
                    
                    # Call procedure
                    cursor.callproc('CALCULATE_FINAL_BILL', [
                        booking.id, 
                        actual_return_dt_str, 
                        final_payment_method, # Pass payment method
                        0 # Placeholder for OUT parameter
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
    import csv
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
