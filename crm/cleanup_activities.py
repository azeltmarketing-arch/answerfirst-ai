import requests

CRM = "http://127.0.0.1:5050"

for activity_id in [1, 2, 3, 4, 5]:
    r = requests.delete(f"{CRM}/api/activities?id={activity_id}", timeout=10)
    print(f"Delete {activity_id}: {r.status_code} {r.text}")
