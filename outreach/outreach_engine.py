"""
AnswerFirst AI — Outreach Execution Engine
Manages email outreach via Gmail SMTP or GMass, CRM sync, and tracking.
"""

import json
import csv
import time
import random
from datetime import datetime, timedelta
from pathlib import Path

FREE_SEQUENCES = {
    "hvac_roofing_cold_email": [
        {
            "day": 1,
            "subject": "Quick question about {company}",
            "body": """
Hi {first_name},

I was looking at {company} and noticed you're doing great work in the area.

I help HVAC and roofing contractors fill their calendars with qualified appointments without lifting a finger. Think of it as a dedicated appointment-setter who works 24/7.

Would you be open to a 15-minute chat this week to see if this could work for {company}?

Best,
Andrew Zelt
AnswerFirst AI
""",
        },
        {
            "day": 3,
            "subject": "Re: Quick question about {company}",
            "body": """
Hi {first_name},

Just wanted to follow up on my last email. I know you're busy running {company}, so I'll be brief.

I recently helped a similar contractor add 15+ qualified appointments per month with zero extra work on their end.

If that sounds useful, let me know. No pitch - just a quick conversation.

Andrew
""",
        },
        {
            "day": 7,
            "subject": "Last check-in - {company}",
            "body": """
Hi {first_name},

I don't want to clutter your inbox, so this is my last note.

If adding qualified appointments to {company}'s calendar is a priority right now, I'm here. If not, no worries at all.

Either way, best of luck with the business.

Andrew
AnswerFirst AI
""",
        },
    ]
}


class OutreachEngine:
    """Manages outreach execution and tracking."""
    
    def __init__(self, leads_file=None, gmass_api=None, hubspot_crm=None, gmail_smtp=None, local_crm=None):
        self.leads = []
        self.activities = []
        self.gmass = gmass_api
        self.hubspot = hubspot_crm
        self.gmail_smtp = gmail_smtp
        self.local_crm = local_crm
        self.sequence_name = "hvac_roofing_cold_email"
        self.load_leads(leads_file)
    def load_leads(self, filename):
        """Load leads from JSON or CSV."""
        if not filename:
            leads_dir = Path("C:/Users/azelt/answerfirst-ai/leads")
            json_files = sorted(leads_dir.glob("enriched_leads_*.json"), reverse=True)
            csv_files = sorted(leads_dir.glob("*.csv"), reverse=True)
            
            if json_files:
                filename = json_files[0]
            elif csv_files:
                filename = csv_files[0]
            else:
                print("[!] No leads found")
                return
        
        print(f"[*] Loading leads from: {Path(filename).name}")
        
        if filename.suffix == ".json":
            with open(filename, "r", encoding="utf-8") as f:
                self.leads = json.load(f)
        else:
            import csv as csv_module
            with open(filename, "r", encoding="utf-8") as f:
                reader = csv_module.DictReader(f)
                self.leads = list(reader)
        
        print(f"[+] Loaded {len(self.leads)} leads")
    
    def get_ready_for_outreach(self):
        """Get leads that are qualified and not yet contacted."""
        return [
            l for l in self.leads 
            if int(l.get("score", 0)) >= 65 and l.get("status") in ["new", "nurture"]
        ]
    
    def prepare_outreach_batch(self, batch_size=10):
        """
        Prepare personalized outreach for a batch of leads.
        Returns list of outreach-ready messages.
        """
        ready = self.get_ready_for_outreach()
        batch = ready[:batch_size]
        
        print(f"[*] Preparing outreach for {len(batch)} leads")
        
        outreach_batch = []
        for lead in batch:
            sequence = lead.get("sequence_assigned", self.sequence_name)
            subject = lead.get("outreach_subject", f"Quick question about {lead.get('business_name', '')}")
            body = lead.get("outreach_body", "")
            channel = lead.get("recommended_channel", "email")
            
            outreach_batch.append({
                "lead_id": lead.get("business_name", ""),
                "channel": channel,
                "subject": subject,
                "body": body,
                "sequence": sequence,
                "scheduled_date": (datetime.now() + timedelta(days=0)).isoformat(),
                "status": "pending"
            })
        
        return outreach_batch
    
    def generate_gmass_csv(self, batch, filename="outreach_batch.csv"):
        """Generate CSV for GMass cold email sending."""
        if not batch:
            print("[!] No batch to export")
            return
        
        fieldnames = ["email", "subject", "body", "lead_id", "sequence", "scheduled_date"]
        
        email_rows = []
        lead_map = {l["business_name"]: l for l in self.leads}
        
        for item in batch:
            lead = lead_map.get(item["lead_id"], {})
            email = lead.get("email", "")
            
            if not email:
                print(f"  [!] No email for {item['lead_id']}")
                continue
            
            email_rows.append({
                "email": email,
                "subject": item["subject"],
                "body": item["body"],
                "lead_id": item["lead_id"],
                "sequence": item["sequence"],
                "scheduled_date": item["scheduled_date"]
            })
        
        filepath = f"C:/Users/azelt/answerfirst-ai/outreach/{filename}"
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(email_rows)
        
        print(f"[+] Exported {len(email_rows)} emails to {filepath}")
        return filepath
    
    def log_activity(self, lead_id, activity_type, direction, subject="", body="", outcome="no_response"):
        """Log an outreach activity."""
        activity = {
            "lead_id": lead_id,
            "activity_type": activity_type,
            "direction": direction,
            "subject": subject,
            "body": body,
            "sent_at": datetime.now().isoformat(),
            "outcome": outcome,
            "created_at": datetime.now().isoformat()
        }
        self.activities.append(activity)
        return activity
    
    def save_activities(self, filename="outreach_activities.json"):
        """Save activity log."""
        filepath = f"C:/Users/azelt/answerfirst-ai/outreach/{filename}"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.activities, f, indent=2, ensure_ascii=False)
        print(f"[+] Saved {len(self.activities)} activities to {filepath}")
    
    def run_outreach_simulation(self, batch_size=5):
        """
        Run outreach using available backend: Gmail SMTP, GMass, or fallback simulation.
        """
        batch = self.prepare_outreach_batch(batch_size)
        
        if not batch:
            print("[!] No leads ready for outreach")
            return
        
        print(f"\n[*] Preparing outreach for {len(batch)} leads")
        print("=" * 60)
        
        # Build recipients
        lead_map = {l["business_name"]: l for l in self.leads}
        recipients = []
        for item in batch:
            lead = lead_map.get(item["lead_id"], {})
            recipients.append({
                "email": lead.get("email", ""),
                "first_name": lead.get("owner_first_name", lead.get("first_name", "")),
                "last_name": lead.get("owner_last_name", lead.get("last_name", "")),
                "company": lead.get("business_name", ""),
                "business_name": lead.get("business_name", ""),
                "outreach_subject": item["subject"],
                "outreach_body": item["body"]
            })
        
        template = {
            "subject": batch[0]["subject"],
            "body": batch[0]["body"],
        }
        
        # Gmail SMTP path
        if self.gmail_smtp:
            sequence_key = self.sequence_name if self.sequence_name in FREE_SEQUENCES else "hvac_roofing_cold_email"
            seq = FREE_SEQUENCES.get(sequence_key, FREE_SEQUENCES["hvac_roofing_cold_email"])
            results = self.gmail_smtp.send_sequence(recipients, seq)
            total_sent = sum(step.get("sent_count", 0) for step in results)
            total_errors = sum(step.get("error_count", 0) for step in results)
            print(f"[+] Gmail SMTP send complete. sent={total_sent} errors={total_errors}")
            
            if self.local_crm:
                self.local_crm.sync_leads(self.leads)
                print("[+] Synced leads to local CRM")
            
            for lead in recipients:
                self.log_activity(
                    lead_id=lead.get("business_name", ""),
                    activity_type="email",
                    direction="outbound",
                    subject=template["subject"],
                    body=template["body"],
                    outcome="sent"
                )
                for source_lead in self.leads:
                    if source_lead.get("business_name") == lead.get("business_name"):
                        source_lead["status"] = "contacted"
                        source_lead["last_contacted"] = datetime.now().isoformat()
                        source_lead["next_follow_up"] = (datetime.now() + timedelta(days=3)).isoformat()
                        break
            
            self.save_activities()
            self.export_updated_leads()
            return
        
        # GMass path
        if self.gmass:
            result = self.gmass.create_campaign_from_template(
                template={**template, "follow_up_days": [3, 7]},
                recipients=recipients
            )
            print(f"[+] GMass campaign status: {result.get('status')}")
            print(f"[+] Recipients targeted: {result.get('recipients')}")
            print(f"[+] Campaign ID: {result.get('campaign_id')}")
            
            for lead in recipients:
                self.log_activity(
                    lead_id=lead.get("business_name", ""),
                    activity_type="email",
                    direction="outbound",
                    subject=template["subject"],
                    body=template["body"],
                    outcome=result.get("status", "error")
                )
                for source_lead in self.leads:
                    if source_lead.get("business_name") == lead.get("business_name"):
                        source_lead["status"] = "contacted"
                        source_lead["last_contacted"] = datetime.now().isoformat()
                        source_lead["next_follow_up"] = (datetime.now() + timedelta(days=3)).isoformat()
                        break
            
            self.save_activities()
            self.export_updated_leads()
            return
        
        # Simulated path
        print(f"\n[*] Simulating outreach for {len(batch)} leads")
        for i, item in enumerate(batch, 1):
            lead_id = item["lead_id"]
            channel = item["channel"]
            subject = item["subject"]
            body = item["body"]
            
            print(f"\n[{i}/{len(batch)}] Outreach to: {lead_id}")
            print(f"  Channel: {channel}")
            print(f"  Subject: {subject}")
            print(f"  Body preview: {body[:100]}...")
            
            if channel == "email":
                print(f"  [SIMULATED] Email sent")
                outcome = random.choice(["sent", "sent", "sent", "bounced"])
            elif channel == "phone":
                print(f"  [SIMULATED] Call attempted")
                outcome = random.choice(["voicemail", "no_answer", "connected"])
            else:
                print(f"  [SIMULATED] LinkedIn message sent")
                outcome = "sent"
            
            self.log_activity(
                lead_id=lead_id,
                activity_type=channel,
                direction="outbound",
                subject=subject,
                body=body,
                outcome=outcome
            )
            
            for lead in self.leads:
                if lead.get("business_name") == lead_id:
                    lead["status"] = "contacted"
                    lead["last_contacted"] = datetime.now().isoformat()
                    lead["next_follow_up"] = (datetime.now() + timedelta(days=3)).isoformat()
                    break
            
            time.sleep(random.uniform(1, 3))
        
        print(f"\n[+] Outreach simulation complete")
        print(f"[+] Activities logged: {len(self.activities)}")
        
        self.save_activities()
        self.export_updated_leads()
    
    def export_updated_leads(self, filename="leads_updated.csv"):
        """Export updated leads with status changes."""
        filepath = f"C:/Users/azelt/answerfirst-ai/outreach/{filename}"
        
        if not self.leads:
            return
        
        fieldnames = [
            "business_name", "owner", "phone", "email", "website",
            "address", "city", "state", "yelp_rating", "review_count",
            "services", "source", "score", "status", "last_contacted",
            "next_follow_up", "personalization_hook", "recommended_channel",
            "sequence_assigned"
        ]
        
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(self.leads)
        
        print(f"[+] Exported updated leads to {filepath}")


def main():
    """Run outreach engine."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    
    print("=" * 60)
    print("AnswerFirst AI — Outreach Engine")
    print("=" * 60)
    
    live = "--live" in sys.argv
    smtp = None
    if live:
        from integrations.gmail_smtp import GmailSMTP
        smtp = GmailSMTP(sender_password="igrwszbcytqrxycx")
    
    engine = OutreachEngine(gmail_smtp=smtp)
    
    if not engine.leads:
        print("[!] No leads loaded. Run scraper first.")
        return
    
    ready = engine.get_ready_for_outreach()
    print(f"\n[*] Pipeline Summary:")
    print(f"  Total leads: {len(engine.leads)}")
    print(f"  Ready for outreach: {len(ready)}")
    print(f"  Already contacted: {sum(1 for l in engine.leads if l.get('status') == 'contacted')}")
    print(f"  Responded: {sum(1 for l in engine.leads if l.get('status') == 'responded')}")
    print(f"  Demo booked: {sum(1 for l in engine.leads if l.get('status') == 'demo_booked')}")
    
    print(f"\n[*] Starting outreach...")
    engine.run_outreach_simulation(batch_size=5)
    
    batch = engine.prepare_outreach_batch(batch_size=10)
    if batch:
        engine.generate_gmass_csv(batch)
    
    print("\n[+] Outreach engine complete")


if __name__ == "__main__":
    main()
