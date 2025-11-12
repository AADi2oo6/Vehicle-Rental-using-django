import MySQLdb

# Connect to the database
conn = MySQLdb.connect(
    host='localhost',
    user='root',
    passwd='Ishubhai@6655',
    db='course'
)

cur = conn.cursor()

# Show table structure
cur.execute("DESCRIBE rental_activitylog")
results = cur.fetchall()

print("Activity Log Table Structure:")
for row in results:
    print(f"  {row[0]}: {row[1]} (nullable: {row[2]}, default: {row[4]}, key: {row[3]})")

cur.close()
conn.close()