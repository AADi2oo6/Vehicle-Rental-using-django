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

print("Creating a new payment to test triggers...")

# Create a new payment
cur.execute("""
    INSERT INTO rental_payment 
    (customer_id, booking_id, amount, payment_method, payment_status, payment_date, payment_type, processed_by) 
    VALUES 
    (1, 1, 100.00, 'Credit Card', 'Pending', %s, 'Full Payment', 'System')
""", (datetime.now(),))

conn.commit()
payment_id = cur.lastrowid
print(f'Created payment with ID: {payment_id}')

# Check the activity log for the new entry
cur.execute("""
    SELECT id, action_type, trigger_type, details, timestamp 
    FROM rental_activitylog 
    WHERE details LIKE %s 
    ORDER BY timestamp DESC 
    LIMIT 5
""", (f'%Payment ID: {payment_id}%',))

logs = cur.fetchall()
print("\nNew log entries with trigger_type:")
for log in logs:
    print(f"  ID: {log[0]}, Action: {log[1]}, Trigger: {log[2]}, Details: {log[3]}, Time: {log[4]}")

cur.close()
conn.close()