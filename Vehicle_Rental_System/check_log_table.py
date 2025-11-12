import MySQLdb

# Connect to the database
conn = MySQLdb.connect(
    host='localhost',
    user='root',
    passwd='Ishubhai@6655',
    db='course'
)

cur = conn.cursor()

# Check if the activity log table exists
cur.execute("SHOW TABLES LIKE 'rental_activitylog'")
result = cur.fetchall()
print('ActivityLog table exists:', len(result) > 0)

# If it exists, show some sample data
if len(result) > 0:
    try:
        cur.execute("SELECT COUNT(*) FROM rental_activitylog")
        count = cur.fetchone()[0]
        print(f"Total log entries: {count}")
        
        # Show recent logs
        cur.execute("SELECT * FROM rental_activitylog ORDER BY timestamp DESC LIMIT 5")
        logs = cur.fetchall()
        print("Recent log entries:")
        for log in logs:
            print(f"  {log}")
    except Exception as e:
        print(f"Error reading log data: {e}")
else:
    print("ActivityLog table does not exist in the database")

cur.close()
conn.close()