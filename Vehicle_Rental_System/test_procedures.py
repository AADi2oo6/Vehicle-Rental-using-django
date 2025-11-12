import MySQLdb

# Connect to the database
conn = MySQLdb.connect(
    host='localhost',
    user='root',
    passwd='Ishubhai@6655',
    db='course'
)

cur = conn.cursor()

# Check if procedures exist
procedures = ['GetPaymentTrendsByMonth', 'AnalyzeCustomerPaymentBehavior', 'GetAdminDashboardMetrics']

for proc in procedures:
    cur.execute("SHOW PROCEDURE STATUS WHERE Name = %s", (proc,))
    result = cur.fetchall()
    print(f'Procedure {proc} exists: {len(result) > 0}')

cur.close()
conn.close()