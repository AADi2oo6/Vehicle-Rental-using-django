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
from rental.models import Vehicle, Customer, FeedbackReview, RentalBooking, Payment, MaintenanceRecord, ActivityLog
from rental.models import CompletedPayment, PendingPayment, RefundedPayment, FailedPayment  # Add this import
from django.http import JsonResponse
from rental.forms import PaymentForm  # Import the new form

@login_required
def admin_dashboard_view(request):
    """
    Retrieves key metrics using Stored Procedure for better performance.
    """
    
    # Check if user is authenticated and is a superuser
    if not request.user.is_authenticated or not request.user.is_superuser:
        messages.error(request, "You must log in to access the admin panel.")
        return redirect('admin_login')

    try:
        # Use the new stored procedure to get all dashboard metrics
        with connection.cursor() as cursor:
            cursor.callproc('GetAdminDashboardMetrics')
            
            # Fetch all result sets
            results = []
            while True:
                try:
                    result = cursor.fetchall()
                    results.append(result)
                    if not cursor.nextset():
                        break
                except:
                    break
            
            # Process results
            total_revenue = results[0][0][0] if results and len(results) > 0 and len(results[0]) > 0 else 0
            pending_payments_count = results[1][0][0] if len(results) > 1 and len(results[1]) > 0 else 0
            active_rentals_count = results[2][0][0] if len(results) > 2 and len(results[2]) > 0 else 0
            maintenance_vehicles_count = results[3][0][0] if len(results) > 3 and len(results[3]) > 0 else 0
            
            # Get recent data using ORM (as procedures don't handle this)
            recent_payments = Payment.objects.select_related('customer').order_by('-payment_date')[:5]
            recent_bookings = RentalBooking.objects.select_related('customer', 'vehicle').order_by('-booking_date')[:5]
            
    except Exception as e:
        # Fallback to ORM queries if procedure fails
        messages.warning(request, "Using fallback queries for dashboard data.")
        
        # Use simple ORM queries to get dashboard data
        total_revenue = Payment.objects.filter(
            payment_status='Completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
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
    # Check if user is authenticated and is a superuser
    if not request.user.is_authenticated or not request.user.is_superuser:
        return JsonResponse({'error': 'You do not have permission to view this data.'}, status=403)
    
    # Use simple ORM queries to get dashboard data
    # Get total revenue (sum of all completed payments)
    total_revenue = Payment.objects.filter(
        payment_status='Completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Get count of pending payments
    pending_payments_count = Payment.objects.filter(payment_status='Pending').count()
    
    # Get count of active rentals
    active_rentals_count = RentalBooking.objects.filter(booking_status='Active').count()
    
    # Get count of vehicles in maintenance
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
    
    # --- Base Query using MySQL Views ---
    # Get the selected payment status view
    payment_status = request.GET.get('status', '').lower()
    
    if payment_status == 'completed':
        payments = CompletedPayment.objects.select_related('customer', 'booking__vehicle').order_by('-payment_date')
    elif payment_status == 'pending':
        payments = PendingPayment.objects.select_related('customer', 'booking__vehicle').order_by('-payment_date')
    elif payment_status == 'refunded':
        payments = RefundedPayment.objects.select_related('customer', 'booking__vehicle').order_by('-payment_date')
    elif payment_status == 'failed':
        payments = FailedPayment.objects.select_related('customer', 'booking__vehicle').order_by('-payment_date')
    else:
        # Default to all payments using the original model
        payments = Payment.objects.select_related('customer', 'booking__vehicle').order_by('-payment_date')
        payment_status = 'all'  # Set to 'all' for template
    
    # --- Filtering Variables ---
    search_query = request.GET.get('q', '').strip()
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    # --- 1. Apply Universal Search (Text) ---
    if search_query:
        if payment_status in ['completed', 'pending', 'refunded', 'failed']:
            # For view-based queries, use simpler search that leverages indexes
            payments = payments.extra(
                where=["""(id LIKE %s OR 
                          customer_id IN (SELECT id FROM rental_customer WHERE first_name LIKE %s OR last_name LIKE %s) OR
                          booking_id IN (SELECT id FROM rental_rentalbooking WHERE vehicle_id IN (SELECT id FROM rental_vehicle WHERE vehicle_number LIKE %s)) OR
                          transaction_id LIKE %s)"""],
                params=[f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', f'%{search_query}%']
            )
        else:
            # For the main Payment model, use the existing search
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

    # --- 4. Apply Sorting ---
    sort_by = request.GET.get('sort', 'payment_date')
    order = request.GET.get('order', 'desc')
    if order == 'asc':
        payments = payments.order_by(sort_by)
    else:
        payments = payments.order_by(f'-{sort_by}')

    # --- 5. Aggregation for Reports ---
    # Use the original Payment model for aggregations since views don't support aggregation well
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
        'selected_status': payment_status.capitalize() if payment_status != 'all' else 'All',
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
        try:
            # Check if payment is completed - prevent deletion
            if payment.payment_status == 'Completed':
                messages.error(request, "Cannot delete completed payments. Please refund the payment instead.")
                return redirect('admin_payments')
            
            # If not completed, proceed with deletion
            payment_details = f"Payment ID {payment.id} for {payment.customer.first_name} {payment.customer.last_name}"
            payment.delete()
            messages.success(request, f"Payment {payment_details} deleted successfully.")
            
        except Exception as e:
            # Handle any database errors (including trigger errors)
            error_message = str(e)
            if "Cannot delete completed payments" in error_message:
                messages.error(request, "Cannot delete completed payments. Please refund the payment instead.")
            else:
                messages.error(request, f"Failed to delete payment: {error_message}")
                
        return redirect('admin_payments')
    
    # For GET requests, show confirmation page
    context = {'payment': payment}
    return render(request, "admin/payment_confirm_delete.html", context)

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

@login_required
def payment_trends_view(request):
    """
    Display payment trends using the stored procedure.
    """
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('home')
    
    # Default to last 12 months
    from datetime import date, timedelta
    end_date = date.today()
    start_date = end_date - timedelta(days=365)
    
    # Get dates from request
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    try:
        with connection.cursor() as cursor:
            cursor.callproc('GetPaymentTrendsByMonth', [start_date, end_date])
            trends_data = cursor.fetchall()
            
            # Process data for charting
            trends_dict = {}
            for row in trends_data:
                month, method, count, total, avg = row
                if month not in trends_dict:
                    trends_dict[month] = {}
                trends_dict[month][method] = {
                    'count': count,
                    'total': float(total),
                    'avg': float(avg)
                }
            
    except Exception as e:
        messages.error(request, f"Failed to retrieve payment trends: {e}")
        trends_dict = {}
    
    context = {
        'trends_data': trends_dict,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, "admin/payment_trends.html", context)

@login_required
def activity_log_view(request):
    """
    Display activity logs for payment and other system events.
    """
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('home')
    
    # Get filter parameters
    action_type = request.GET.get('action_type', '')
    trigger_type = request.GET.get('trigger_type', '')
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')
    
    try:
        # Build the query for activity logs
        with connection.cursor() as cursor:
            # Base query - now includes trigger_type
            query = """
                SELECT 
                    al.id,
                    al.action_type,
                    al.trigger_type,
                    al.details,
                    al.timestamp,
                    al.customer_id
                FROM rental_activitylog al
                WHERE 1=1
            """
            params = []
            
            # Apply filters
            if action_type:
                query += " AND al.action_type = %s"
                params.append(action_type)
                
            if trigger_type:
                query += " AND al.trigger_type = %s"
                params.append(trigger_type)
                
            if start_date_str:
                query += " AND al.timestamp >= %s"
                params.append(start_date_str)
                
            if end_date_str:
                query += " AND al.timestamp <= %s"
                params.append(end_date_str + ' 23:59:59')
            
            query += " ORDER BY al.timestamp DESC LIMIT 100"
            
            cursor.execute(query, params)
            logs = cursor.fetchall()
            
            # Process logs into a more usable format
            processed_logs = []
            for log in logs:
                processed_logs.append({
                    'id': log[0],
                    'action_type': log[1],
                    'trigger_type': log[2],
                    'details': log[3],
                    'timestamp': log[4],
                    'customer_id': log[5]
                })
            
            # Get action type choices for filter dropdown
            action_choices = [
                ('PAYMENT_CREATED', 'Payment Created'),
                ('PAYMENT_STATUS_CHANGED', 'Payment Status Changed'),
                ('PAYMENT_AMOUNT_CHANGED', 'Payment Amount Changed'),
                ('PAYMENT_DELETE_ATTEMPT', 'Payment Delete Attempt'),
                ('REGISTRATION', 'User Registration'),
                ('LOGIN', 'User Login'),
                ('LOGOUT', 'User Logout'),
                ('BOOKING_CREATED', 'Booking Created'),
                ('PROFILE_UPDATE', 'Profile Updated'),
            ]
            
            # Get trigger type choices for filter dropdown
            trigger_choices = [
                ('INSERT', 'Insert'),
                ('UPDATE', 'Update'),
                ('DELETE', 'Delete'),
            ]
            
    except Exception as e:
        messages.error(request, f"Failed to retrieve activity logs: {e}")
        processed_logs = []
        action_choices = []
        trigger_choices = []
    
    context = {
        'activity_logs': processed_logs,
        'action_choices': action_choices,
        'trigger_choices': trigger_choices,
        'selected_action': action_type,
        'selected_trigger': trigger_type,
        'start_date': start_date_str,
        'end_date': end_date_str,
    }
    return render(request, "admin/activity_log.html", context)

def test_mysql_views(request):
    """
    Test view to check if MySQL views are working properly
    """
    if not request.user.is_authenticated or not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        # Test each view
        completed_count = CompletedPayment.objects.count()
        pending_count = PendingPayment.objects.count()
        refunded_count = RefundedPayment.objects.count()
        failed_count = FailedPayment.objects.count()
        
        # Test a sample query from each view
        completed_sample = list(CompletedPayment.objects.all()[:3].values('id', 'amount', 'payment_status'))
        pending_sample = list(PendingPayment.objects.all()[:3].values('id', 'amount', 'payment_status'))
        
        return JsonResponse({
            'completed_count': completed_count,
            'pending_count': pending_count,
            'refunded_count': refunded_count,
            'failed_count': failed_count,
            'completed_sample': completed_sample,
            'pending_sample': pending_sample,
            'status': 'success'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)