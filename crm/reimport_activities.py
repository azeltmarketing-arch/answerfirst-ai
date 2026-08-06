import json, requests

CRM = "http://127.0.0.1:5050"

# Get existing contacts
contacts = requests.get(f"{CRM}/api/contacts", timeout=10).json()
by_name = {c.get("company", ""): c.get("id") for c in contacts if c.get("company")}
print("Existing contacts:", len(by_name))

with open(r"C:\Users\azelt\answerfirst-ai\outreach\outreach_activities.json", "r", encoding="utf-8") as f:
    activities = json.load(f)

imported = 0
for act in activities:
    lead_name = act.get("lead_id", "")
    contact_id = by_name.get(lead_name)
    payload = {
        "contact_id": contact_id,
        "activity_type": act.get("activity_type", "email"),
        "direction": act.get("direction", "outbound"),
        "subject": act.get("subject", ""),
        "body": act.get("body", ""),
        "outcome": act.get("outcome", "sent"),
        "metadata": {"sent_at": act.get("sent_at", "")},
    }
    r = requests.post(f"{CRM}/api/activities", json=payload, timeout=10)
    if r.status_code in (200, 201):
        imported += 1
        print(f"Imported: {lead_name} -> contact_id={contact_id}")
    else:
        print(f"Failed: {lead_name} -> {r.status_code} {r.text}")

print("Total imported:", imported)
