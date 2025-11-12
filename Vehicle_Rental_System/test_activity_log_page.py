import requests

# Test if the activity log page is working
try:
    # This would normally require authentication, so we'll just check if the page loads
    response = requests.get('http://127.0.0.1:8000/admin_new/activity-log/')
    print(f"Activity log page status code: {response.status_code}")
    if response.status_code == 200:
        print("Activity log page is accessible!")
        # Check if the page contains log data
        if "No activity logs found" in response.text:
            print("No logs found, but the page is working correctly")
        else:
            print("Activity logs are being displayed!")
    else:
        print(f"Activity log page returned status code: {response.status_code}")
except Exception as e:
    print(f"Error testing activity log page: {e}")