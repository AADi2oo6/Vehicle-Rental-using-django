import MySQLdb

# Connect to the database
conn = MySQLdb.connect(
    host='localhost',
    user='root',
    passwd='Ishubhai@6655',
    db='course'
)

cur = conn.cursor()

# Show all triggers
cur.execute("SHOW TRIGGERS")
results = cur.fetchall()

print("All triggers in the database:")
for row in results:
    print(f"  - {row[0]} ({row[1]} {row[2]})")

# Check for our specific triggers by pattern
trigger_patterns = [
    'tr_payment_before_insert',
    'tr_payment_after_insert',
    'tr_payment_after_update',
    'tr_payment_before_delete'
]

print("\nChecking for our specific triggers:")
for pattern in trigger_patterns:
    found = False
    for row in results:
        if pattern in row[0]:
            print(f"  {pattern}: FOUND (as {row[0]})")
            found = True
            break
    if not found:
        print(f"  {pattern}: NOT FOUND")

cur.close()
conn.close()