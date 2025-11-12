import MySQLdb
from datetime import datetime

# Connect to the database
conn = MySQLdb.connect(
    host='localhost',
    user='root',
    passwd='Ishubhai@6655',
    db='course'
)

cur = conn.cursor()

print("Creating a test payment to verify activity log functionality...")

try:
    # Create a test payment
    cur.execute("""
        INSERT INTO rental_payment 
        (customer_id, booking_id, amount, payment_method, payment_status, payment_date, payment_type, processed_by) 
        VALUES 
        (1, 1, 50.00, 'Razorpay', 'Pending', %s, 'Full Payment', 'System')
    """, (datetime.now(),))

    conn.commit()
    payment_id = cur.lastrowid
    print(f'Created test payment with ID: {payment_id}')

    # Check the activity log for the new entry
    cur.execute("""
        SELECT id, action_type, trigger_type, details, timestamp 
        FROM rental_activitylog 
        WHERE details LIKE %s 
        ORDER BY timestamp DESC 
        LIMIT 1
    """, (f'%Payment ID: {payment_id}%',))

    log = cur.fetchone()
    if log:
        print(f"\nNew activity log entry:")
        print(f"  ID: {log[0]}")
        print(f"  Action Type: {log[1]}")
        print(f"  Trigger Type: {log[2]}")
        print(f"  Details: {log[3]}")
        print(f"  Timestamp: {log[4]}")
        print("\nActivity log functionality is working correctly!")
    else:
        print("No activity log entry found for the test payment")

except Exception as e:
    print(f"Error: {e}")

finally:
    cur.close()
    conn.close()