import MySQLdb

# Connect to the database
conn = MySQLdb.connect(
    host='localhost',
    user='root',
    passwd='Ishubhai@6655',
    db='course'
)

cur = conn.cursor()

print("Testing trigger_type column...")

# Check if the trigger_type column exists
cur.execute("SHOW COLUMNS FROM rental_activitylog LIKE 'trigger_type'")
result = cur.fetchone()
print('trigger_type column exists:', result is not None)

# Show recent logs with trigger_type
cur.execute("SELECT id, action_type, trigger_type, details, timestamp FROM rental_activitylog ORDER BY timestamp DESC LIMIT 10")
logs = cur.fetchall()
print("\nRecent log entries with trigger_type:")
for log in logs:
    print(f"  ID: {log[0]}, Action: {log[1]}, Trigger: {log[2]}, Details: {log[3]}, Time: {log[4]}")

cur.close()
conn.close()