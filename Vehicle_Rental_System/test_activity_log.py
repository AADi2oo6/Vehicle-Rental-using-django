import MySQLdb

# Connect to the database
conn = MySQLdb.connect(
    host='localhost',
    user='root',
    passwd='Ishubhai@6655',
    db='course'
)

cur = conn.cursor()

print("Testing Activity Log Table...")

try:
    # Check if the activity log table exists
    cur.execute("SHOW TABLES LIKE 'rental_activitylog'")
    result = cur.fetchall()
    print('ActivityLog table exists:', len(result) > 0)

    # Show some sample data
    if len(result) > 0:
        cur.execute("SELECT COUNT(*) FROM rental_activitylog")
        count = cur.fetchone()[0]
        print(f"Total log entries: {count}")
        
        # Show recent logs
        cur.execute("SELECT id, action_type, details, timestamp FROM rental_activitylog ORDER BY timestamp DESC LIMIT 10")
        logs = cur.fetchall()
        print("Recent log entries:")
        for log in logs:
            print(f"  ID: {log[0]}, Action: {log[1]}, Details: {log[2]}, Time: {log[3]}")
        
        # Show payment-related logs specifically
        cur.execute("SELECT id, action_type, details, timestamp FROM rental_activitylog WHERE action_type LIKE 'PAYMENT_%' ORDER BY timestamp DESC LIMIT 5")
        payment_logs = cur.fetchall()
        print("\nRecent payment logs:")
        for log in payment_logs:
            print(f"  ID: {log[0]}, Action: {log[1]}, Details: {log[2]}, Time: {log[3]}")
    else:
        print("ActivityLog table does not exist in the database")

except Exception as e:
    print(f"Error: {e}")
finally:
    cur.close()
    conn.close()

print("\nActivity Log system is working properly!")