import MySQLdb

# Connect to the database
conn = MySQLdb.connect(
    host='localhost',
    user='root',
    passwd='Ishubhai@6655',
    db='course'
)

cur = conn.cursor()

try:
    # Create GetPaymentTrendsByMonth procedure
    cur.execute("""
        CREATE PROCEDURE GetPaymentTrendsByMonth(
            IN start_date DATE,
            IN end_date DATE
        )
        BEGIN
            SELECT 
                DATE_FORMAT(payment_date, '%Y-%m') as month,
                payment_method,
                COUNT(*) as transaction_count,
                SUM(amount) as total_amount,
                AVG(amount) as average_amount
            FROM rental_payment 
            WHERE payment_date BETWEEN start_date AND end_date
                AND payment_status = 'Completed'
            GROUP BY DATE_FORMAT(payment_date, '%Y-%m'), payment_method
            ORDER BY month DESC, total_amount DESC;
        END
    """)
    
    # Create AnalyzeCustomerPaymentBehavior procedure
    cur.execute("""
        CREATE PROCEDURE AnalyzeCustomerPaymentBehavior(
            IN customer_id INT
        )
        BEGIN
            SELECT 
                p.payment_method,
                COUNT(*) as transaction_count,
                SUM(p.amount) as total_spent,
                AVG(p.amount) as avg_transaction_value,
                MIN(p.payment_date) as first_payment_date,
                MAX(p.payment_date) as last_payment_date
            FROM rental_payment p
            WHERE p.customer_id = customer_id 
                AND p.payment_status = 'Completed'
            GROUP BY p.payment_method
            ORDER BY total_spent DESC;
        END
    """)
    
    # Create GetAdminDashboardMetrics procedure
    cur.execute("""
        CREATE PROCEDURE GetAdminDashboardMetrics()
        BEGIN
            -- Total Revenue
            SELECT 
                COALESCE(SUM(amount), 0) as total_revenue
            FROM rental_payment 
            WHERE payment_status = 'Completed';
            
            -- Pending Payments Count
            SELECT 
                COUNT(*) as pending_payments_count
            FROM rental_payment 
            WHERE payment_status = 'Pending';
            
            -- Active Rentals Count
            SELECT 
                COUNT(*) as active_rentals_count
            FROM rental_rentalbooking 
            WHERE booking_status = 'Active';
            
            -- Vehicles in Maintenance Count
            SELECT 
                COUNT(*) as maintenance_vehicles_count
            FROM rental_vehicle 
            WHERE status = 'Maintenance';
        END
    """)
    
    conn.commit()
    print("All procedures created successfully!")
    
except Exception as e:
    print(f"Error creating procedures: {e}")
finally:
    cur.close()
    conn.close()