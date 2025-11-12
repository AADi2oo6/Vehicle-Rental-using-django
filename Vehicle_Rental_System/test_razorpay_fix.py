import os
import django
import MySQLdb
from datetime import datetime

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Vehicle_Rental_System.settings')
django.setup()

from rental.models import Customer, Vehicle, RentalBooking, Payment

# Connect to the database directly to test the trigger
conn = MySQLdb.connect(
    host='localhost',
    user='root',
    passwd='Ishubhai@6655',
    db='course'
)

cur = conn.cursor()

print("Testing Razorpay payment trigger fix...")

try:
    # Try to create a payment with Razorpay as payment method
    cur.execute("""
        INSERT INTO rental_payment 
        (customer_id, booking_id, amount, payment_method, payment_status, payment_date, payment_type, processed_by) 
        VALUES 
        (1, 1, 100.00, 'Razorpay', 'Pending', %s, 'Full Payment', 'System')
    """, (datetime.now(),))

    conn.commit()
    payment_id = cur.lastrowid
    print(f'Successfully created payment with Razorpay method. Payment ID: {payment_id}')

    # Check the activity log for the new entry
    cur.execute("""
        SELECT id, action_type, trigger_type, details, timestamp 
        FROM rental_activitylog 
        WHERE details LIKE %s 
        ORDER BY timestamp DESC 
        LIMIT 5
    """, (f'%Payment ID: {payment_id}%',))

    logs = cur.fetchall()
    print("\nNew log entries:")
    for log in logs:
        print(f"  ID: {log[0]}, Action: {log[1]}, Trigger: {log[2]}, Details: {log[3]}, Time: {log[4]}")

except Exception as e:
    print(f"Error: {e}")

finally:
    cur.close()
    conn.close()