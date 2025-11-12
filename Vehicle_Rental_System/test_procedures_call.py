import MySQLdb
from datetime import date, timedelta

# Connect to the database
conn = MySQLdb.connect(
    host='localhost',
    user='root',
    passwd='Ishubhai@6655',
    db='course'
)

cur = conn.cursor()

try:
    # Test GetAdminDashboardMetrics procedure
    print("Testing GetAdminDashboardMetrics procedure:")
    cur.callproc('GetAdminDashboardMetrics')
    
    # Fetch all result sets
    results = []
    counter = 0
    while True:
        try:
            result = cur.fetchall()
            results.append(result)
            print(f"Result set {counter}: {len(result)} rows")
            counter += 1
            if not cur.nextset():
                break
        except:
            break
    
    print(f"Total result sets: {len(results)}")
    
    # Test GetPaymentTrendsByMonth procedure
    print("\nTesting GetPaymentTrendsByMonth procedure:")
    end_date = date.today()
    start_date = end_date - timedelta(days=365)
    
    cur.callproc('GetPaymentTrendsByMonth', [start_date, end_date])
    trends_result = cur.fetchall()
    print(f"Payment trends result: {len(trends_result)} rows")
    if trends_result:
        print("First row:", trends_result[0])
    
except Exception as e:
    print(f"Error calling procedures: {e}")
finally:
    cur.close()
    conn.close()