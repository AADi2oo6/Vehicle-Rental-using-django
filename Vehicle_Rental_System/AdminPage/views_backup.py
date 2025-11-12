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