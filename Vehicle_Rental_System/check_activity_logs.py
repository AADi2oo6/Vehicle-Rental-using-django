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

print("Checking activity logs in database...")

# Check if there are any activity logs
cur.execute("SELECT COUNT(*) FROM rental_activitylog")
count = cur.fetchone()[0]
print(f"Total activity logs in database: {count}")

if count > 0:
    # Show recent logs
    cur.execute("""
        SELECT id, action_type, trigger_type, details, timestamp, customer_id 
        FROM rental_activitylog 
        ORDER BY timestamp DESC 
        LIMIT 10
    """)
    logs = cur.fetchall()
    print("\nRecent activity logs:")
    print("ID\tAction Type\t\tTrigger Type\tCustomer ID\tDetails")
    print("-" * 80)
    for log in logs:
        print(f"{log[0]}\t{log[1]}\t\t{log[2] or 'N/A'}\t\t{log[5] or 'N/A'}\t\t{log[3][:50]}...")
else:
    print("No activity logs found in database")

cur.close()
conn.close()