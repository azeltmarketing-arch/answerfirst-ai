import json, requests

CRM = "http://127.0.0.1:5050"
DASHBOARD = "http://127.0.0.1:8080"

with open(r"C:\Users\azelt\answerfirst-ai\outreach\outreach_activities.json", "r", encoding="utf-8") as f:
    activities = json.load(f)

leads_path = r"C:\Users\azelt\answerfirst-ai\leads\phoenix_hvac_real_leads.csv"

import csv
with open(leads_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    leads = list(reader)

lead_map = {}
for lead in leads:
    name = lead.get("business_name", "").strip()
    if not name:
        continue
    payload = {
        "first_name": lead.get("owner_first_name", "").strip(),
        "last_name": lead.get("owner_last_name", "").strip(),
        "email": lead.get("email", "").strip(),
        "phone": lead.get("phone", "").strip(),
        "company": name,
        "source": "phoenix_hvac_scrape",
    }
    r = requests.post(f"{CRM}/api/contacts", json=payload, timeout=10)
    if r.status_code in (200, 201):
        lead_map[name] = r.json().get("id") or r.json().get("contact", {}).get("id")

print("Imported contacts:", len(lead_map))

imported = 0
for act in activities:
    lead_name = act.get("lead_id", "")
    contact_id = lead_map.get(lead_name)
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

print("Imported activities:", imported)
