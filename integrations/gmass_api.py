"""
GMass Email Sending Integration for AnswerFirst AI
- Gmail-native cold email sending
- Mail merge personalization
- Follow-up sequences
- Campaign analytics
"""

import requests
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

GMASS_BASE_URL = "https://api.gmass.co/api"


class GMassAPI:
    def __init__(self, api_key: Optional[str] = None, gmail_address: Optional[str] = None):
        """
        Initialize GMass API client.
        
        Args:
            api_key: GMass API key from https://www.gmass.co/settings/api
            gmail_address: Gmail address to send from
        """
        self.api_key = api_key or os.getenv("GMASS_API_KEY", "")
        self.gmail_address = gmail_address or os.getenv("GMASS_GMAIL_ADDRESS", "azelt.marketing@gmail.com")
        if not self.api_key:
            raise ValueError("GMass API key required. Set GMASS_API_KEY env var or get from https://www.gmass.co/settings/api")
        
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
    
    # ==================== CAMPAIGNS ====================
    
    def create_campaign(self, name: str, subject: str, body: str,
                        recipients: List[Dict], follow_up_days: Optional[List[int]] = None,
                        send_hour: int = 9, send_minute: int = 0) -> Dict:
        """
        Create and send a GMass email campaign.
        
        Args:
            name: Campaign name
            subject: Email subject line
            body: Email body HTML/text
            recipients: List of {email, firstName, lastName, company} dicts
            follow_up_days: Days after first email to send follow-ups
            send_hour: Hour to send (0-23)
            send_minute: Minute to send (0-59)
        
        Returns:
            Campaign response with status and campaign ID
        """
        # Format recipients for GMass
        formatted_recipients = []
        for r in recipients:
            formatted_recipients.append({
                "email": r.get("email", ""),
                "firstName": r.get("first_name", r.get("firstName", "")),
                "lastName": r.get("last_name", r.get("lastName", "")),
                "company": r.get("company", r.get("business_name", ""))
            })
        
        # Build campaign payload
        payload = {
            "name": name,
            "subject": subject,
            "body": body,
            "fromEmail": self.gmail_address,
            "recipients": formatted_recipients,
            "sendAt": self._calculate_send_time(send_hour, send_minute),
            "trackOpens": True,
            "trackClicks": True
        }
        
        # Add follow-up sequences if specified
        if follow_up_days:
            payload["followUps"] = []
            for day in follow_up_days:
                payload["followUps"].append({
                    "type": "email",
                    "subject": f"Re: {subject}",
                    "body": self._generate_follow_up_body(day),
                    "sendAfterDays": day
                })
        
        try:
            resp = requests.post(
                f"{GMASS_BASE_URL}/campaigns",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            resp.raise_for_status()
            return {
                "status": "success",
                "campaign_id": resp.json().get("id"),
                "recipients": len(recipients),
                "data": resp.json()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "recipients": len(recipients)
            }
    
    def create_campaign_from_template(self, template: Dict, recipients: List[Dict],
                                       send_now: bool = True) -> Dict:
        """
        Create a campaign from an outreach template.
        
        Args:
            template: {subject, body, follow_up_days}
            recipients: List of lead dicts
            send_now: If False, schedule for later
        """
        subject = template.get("subject", "Quick question")
        body = template.get("body", "")
        follow_up_days = template.get("follow_up_days", [3, 7])
        
        # Personalize subject and body for each recipient
        personalized_recipients = []
        for lead in recipients:
            personalized_recipients.append({
                "email": lead.get("email", ""),
                "first_name": lead.get("owner_first_name", lead.get("first_name", "")),
                "last_name": lead.get("owner_last_name", lead.get("last_name", "")),
                "company": lead.get("business_name", "")
            })
        
        # Personalize subject
        personalized_subject = subject
        if personalized_recipients:
            company = personalized_recipients[0].get("company", "")
            personalized_subject = subject.replace("{company}", company)
        
        # Personalize body
        personalized_body = body
        for r in personalized_recipients[:1]:  # Use first recipient for template
            personalized_body = personalized_body.replace("{first_name}", r.get("first_name", "there"))
            personalized_body = personalized_body.replace("{company}", r.get("company", "your company"))
            personalized_body = personalized_body.replace("{owner_first_name}", r.get("first_name", "there"))
        
        if send_now:
            send_hour, send_minute = datetime.now().hour, datetime.now().minute + 1
        else:
            send_hour, send_minute = 9, 0
        
        return self.create_campaign(
            name=f"Outreach - {datetime.now().strftime('%Y-%m-%d')}",
            subject=personalized_subject,
            body=personalized_body,
            recipients=personalized_recipients,
            follow_up_days=follow_up_days,
            send_hour=send_hour,
            send_minute=send_minute
        )
    
    # ==================== CAMPAIGN STATUS ====================
    
    def get_campaign(self, campaign_id: str) -> Dict:
        """Get campaign status and analytics."""
        try:
            resp = requests.get(
                f"{GMASS_BASE_URL}/campaigns/{campaign_id}",
                headers=self.headers,
                timeout=30
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_campaigns(self, limit: int = 50) -> List[Dict]:
        """Get recent campaigns."""
        try:
            resp = requests.get(
                f"{GMASS_BASE_URL}/campaigns",
                headers=self.headers,
                params={"limit": limit},
                timeout=30
            )
            resp.raise_for_status()
            return resp.json().get("campaigns", [])
        except Exception as e:
            return []
    
    def get_campaign_analytics(self, campaign_id: str) -> Dict:
        """Get detailed campaign analytics."""
        try:
            resp = requests.get(
                f"{GMASS_BASE_URL}/campaigns/{campaign_id}/analytics",
                headers=self.headers,
                timeout=30
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    # ==================== LISTS ====================
    
    def create_list(self, name: str, emails: List[str]) -> Dict:
        """Create a recipient list."""
        try:
            payload = {
                "name": name,
                "emails": emails
            }
            resp = requests.post(
                f"{GMASS_BASE_URL}/lists",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    # ==================== GMAIL DRAFTS ====================
    
    def create_gmail_draft(self, to_email: str, subject: str, body: str,
                           cc: Optional[List[str]] = None) -> Dict:
        """Create a Gmail draft via GMass."""
        try:
            payload = {
                "to": to_email,
                "subject": subject,
                "body": body,
                "fromEmail": self.gmail_address
            }
            if cc:
                payload["cc"] = ",".join(cc)
            
            resp = requests.post(
                f"{GMASS_BASE_URL}/drafts",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    # ==================== ANALYTICS ====================
    
    def get_account_stats(self) -> Dict:
        """Get overall account statistics."""
        try:
            resp = requests.get(
                f"{GMASS_BASE_URL}/account/stats",
                headers=self.headers,
                timeout=30
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    # ==================== INTERNAL HELPERS ====================
    
    def _calculate_send_time(self, hour: int, minute: int) -> str:
        """Calculate ISO timestamp for scheduled send."""
        now = datetime.now()
        send_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if send_time <= now:
            send_time += timedelta(days=1)
        return send_time.isoformat() + "Z"
    
    def _generate_follow_up_body(self, day: int) -> str:
        """Generate follow-up email body."""
        templates = {
            1: "Just following up on my previous email. Do you have a few minutes to chat this week?",
            3: "I wanted to check if you had a chance to review my last message. I have some ideas that might help {company}.",
            7: "Last try - I don't want to clutter your inbox. If this isn't a priority right now, just let me know and I'll circle back later.",
            14: "Checking in one more time. If you're experiencing any of the issues I mentioned, I'd love to show you a quick solution."
        }
        return templates.get(day, templates[3])


# ==================== OUTREACH CAMPAIGNS ====================

class OutreachCampaign:
    """
    High-level campaign manager that combines HubSpot + GMass.
    """
    
    def __init__(self, gmass_api: GMassAPI, hubspot_crm=None):
        self.gmass = gmass_api
        self.hubspot = hubspot_crm
    
    def launch_campaign(self, leads: List[Dict], template: Dict, 
                        sync_to_hubspot: bool = True) -> Dict:
        """
        Launch a full outreach campaign.
        
        Args:
            leads: List of lead dicts from lead generator
            template: Email template {subject, body, follow_up_days}
            sync_to_hubspot: Whether to sync leads to HubSpot CRM
        
        Returns:
            Campaign results summary
        """
        results = {
            "campaign_name": f"Outreach - {datetime.now().strftime('%Y-%m-%d')}",
            "total_leads": len(leads),
            "sent": 0,
            "failed": 0,
            "hubspot_synced": 0,
            "gmass_campaign_id": None,
            "errors": []
        }
        
        # Sync to HubSpot first
        if sync_to_hubspot and self.hubspot:
            try:
                sync_results = self.hubspot.bulk_sync_leads(leads)
                results["hubspot_synced"] = sum(1 for r in sync_results if r.get("status") == "synced")
                results["hubspot_errors"] = [r for r in sync_results if r.get("status") == "failed"]
            except Exception as e:
                results["errors"].append(f"HubSpot sync failed: {str(e)}")
        
        # Send via GMass
        gmass_result = self.gmass.create_campaign_from_template(template, leads)
        results["gmass_campaign_id"] = gmass_result.get("campaign_id")
        results["sent"] = gmass_result.get("recipients", 0)
        results["gmass_status"] = gmass_result.get("status")
        
        if gmass_result.get("status") == "error":
            results["errors"].append(f"GMass error: {gmass_result.get('error')}")
            results["failed"] = results["total_leads"]
        
        return results
    
    def launch_sequence(self, leads: List[Dict], sequence: List[Dict]) -> List[Dict]:
        """
        Launch a multi-step sequence across multiple days.
        
        Args:
            leads: List of lead dicts
            sequence: List of {day, subject, body} dicts
        
        Returns:
            List of campaign results
        """
        results = []
        for step in sequence:
            day = step.get("day", 1)
            template = {
                "subject": step.get("subject", ""),
                "body": step.get("body", ""),
                "follow_up_days": []
            }
            
            result = self.launch_campaign(
                leads=leads,
                template=template,
                sync_to_hubspot=(day == 1)  # Only sync to HubSpot on first touch
            )
            result["sequence_day"] = day
            results.append(result)
            
            # Wait between sequence steps if sending live
            if day < len(sequence):
                time.sleep(1)  # Small delay between API calls
        
        return results


# ==================== TESTING ====================

if __name__ == "__main__":
    import sys
    api_key = sys.argv[1] if len(sys.argv) > 1 else os.getenv("GMASS_API_KEY", "")
    if not api_key:
        print("Usage: python gmass_api.py <API_KEY>")
        sys.exit(1)
    
    client = GMassAPI(api_key)
    
    # Test connection
    try:
        stats = client.get_account_stats()
        print(f"✓ Connected to GMass")
        print(f"  Account: {stats.get('email', 'N/A')}")
        print(f"  Plan: {stats.get('plan', 'N/A')}")
        
        # Test list creation
        test_list = client.create_list("Test List", ["test@example.com"])
        print(f"✓ Created test list: {test_list}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
