import MySQLdb

# Connect to the database
conn = MySQLdb.connect(
    host='localhost',
    user='root',
    passwd='Ishubhai@6655',
    db='course'
)

cur = conn.cursor()

# Show indexes on rental_payment table
cur.execute("SHOW INDEX FROM rental_payment")
results = cur.fetchall()

print("Indexes on rental_payment table:")
for row in results:
    print(f"  - {row[2]}")

# Check if our specific indexes exist
index_names = [
    'idx_payment_customer_id',
    'idx_payment_booking_id', 
    'idx_payment_payment_date',
    'idx_payment_payment_status',
    'idx_payment_payment_method',
    'idx_payment_transaction_id',
    'idx_payment_status_date',
    'idx_payment_customer_status',
    'idx_payment_customer_date',
    'idx_payment_method_status'
]

print("\nChecking for our specific indexes:")
for index_name in index_names:
    found = any(row[2] == index_name for row in results)
    print(f"  {index_name}: {'FOUND' if found else 'NOT FOUND'}")

cur.close()
conn.close()