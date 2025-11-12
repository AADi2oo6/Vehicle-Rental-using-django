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

print("Updating a payment to test UPDATE trigger...")

# Update the payment status with transaction ID
cur.execute("""
    UPDATE rental_payment 
    SET payment_status = 'Completed', transaction_id = 'txn_123456789' 
    WHERE id = 102
""")

conn.commit()
print('Updated payment status to Completed with transaction ID')

# Check the activity log for the new entry
cur.execute("""
    SELECT id, action_type, trigger_type, details, timestamp 
    FROM rental_activitylog 
    WHERE details LIKE %s 
    ORDER BY timestamp DESC 
    LIMIT 5
""", ('%Status changed%',))

logs = cur.fetchall()
print("\nNew log entries with trigger_type:")
for log in logs:
    print(f"  ID: {log[0]}, Action: {log[1]}, Trigger: {log[2]}, Details: {log[3]}, Time: {log[4]}")

cur.close()
conn.close()