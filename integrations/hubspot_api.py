"""
HubSpot CRM Integration for AnswerFirst AI
- Contact creation/update
- Deal pipeline management
- Company enrichment
- Pipeline reporting
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

HUBSPOT_BASE_URL = "https://api.hubapi.com"


class HubSpotCRM:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("HUBSPOT_API_KEY", "")
        if not self.api_key:
            raise ValueError("HubSpot API key required. Set HUBSPOT_API_KEY env var.")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    # ==================== COMPANIES ====================
    
    def create_company(self, name: str, domain: str = "", phone: str = "", 
                       address: str = "", industry: str = "") -> Dict:
        """Create a company in HubSpot."""
        data = {
            "properties": {
                "name": name,
                "domain": domain,
                "phone": phone,
                "address": address,
                "industry": industry
            }
        }
        resp = requests.post(
            f"{HUBSPOT_BASE_URL}/crm/v3/objects/companies",
            headers=self.headers,
            json=data
        )
        resp.raise_for_status()
        return resp.json()
    
    def search_company(self, domain: str) -> Optional[Dict]:
        """Search for company by domain."""
        data = {
            "filterGroups": [{
                "filters": [{
                    "propertyName": "domain",
                    "operator": "EQ",
                    "value": domain
                }]
            }],
            "properties": ["name", "domain", "phone", "address"]
        }
        resp = requests.post(
            f"{HUBSPOT_BASE_URL}/crm/v3/objects/companies/search",
            headers=self.headers,
            json=data
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return results[0] if results else None
    
    # ==================== CONTACTS ====================
    
    def create_contact(self, first_name: str = "", last_name: str = "",
                       email: str = "", phone: str = "", company: str = "",
                       job_title: str = "") -> Dict:
        """Create a contact in HubSpot."""
        data = {
            "properties": {
                "firstname": first_name,
                "lastname": last_name,
                "email": email,
                "phone": phone,
                "company": company,
                "jobtitle": job_title
            }
        }
        resp = requests.post(
            f"{HUBSPOT_BASE_URL}/crm/v3/objects/contacts",
            headers=self.headers,
            json=data
        )
        resp.raise_for_status()
        return resp.json()
    
    def search_contact(self, email: str) -> Optional[Dict]:
        """Search for contact by email."""
        data = {
            "filterGroups": [{
                "filters": [{
                    "propertyName": "email",
                    "operator": "EQ",
                    "value": email
                }]
            }],
            "properties": ["firstname", "lastname", "email", "phone", "company"]
        }
        resp = requests.post(
            f"{HUBSPOT_BASE_URL}/crm/v3/objects/contacts/search",
            headers=self.headers,
            json=data
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return results[0] if results else None
    
    def update_contact(self, contact_id: str, properties: Dict) -> Dict:
        """Update a contact."""
        data = {"properties": properties}
        resp = requests.patch(
            f"{HUBSPOT_BASE_URL}/crm/v3/objects/contacts/{contact_id}",
            headers=self.headers,
            json=data
        )
        resp.raise_for_status()
        return resp.json()
    
    # ==================== DEALS ====================
    
    def create_deal(self, deal_name: str, company_id: str = "", contact_id: str = "",
                    amount: float = 0, stage: str = "qualified",
                    pipeline_id: str = "default") -> Dict:
        """Create a deal in HubSpot."""
        data = {
            "properties": {
                "dealname": deal_name,
                "amount": amount,
                "pipeline": pipeline_id,
                "dealstage": self._map_stage(stage),
                "hubspot_owner_id": ""
            }
        }
        if company_id:
            data["associations"] = [{
                "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 6}],
                "to": {"id": company_id}
            }]
        if contact_id:
            data["associations"] = data.get("associations", []) + [{
                "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 3}],
                "to": {"id": contact_id}
            }]
        
        resp = requests.post(
            f"{HUBSPOT_BASE_URL}/crm/v3/objects/deals",
            headers=self.headers,
            json=data
        )
        resp.raise_for_status()
        return resp.json()
    
    def update_deal(self, deal_id: str, properties: Dict) -> Dict:
        """Update a deal."""
        data = {"properties": properties}
        resp = requests.patch(
            f"{HUBSPOT_BASE_URL}/crm/v3/objects/deals/{deal_id}",
            headers=self.headers,
            json=data
        )
        resp.raise_for_status()
        return resp.json()
    
    def move_deal_stage(self, deal_id: str, stage: str) -> Dict:
        """Move deal to a new stage."""
        return self.update_deal(deal_id, {"dealstage": self._map_stage(stage)})
    
    def get_deals(self, limit: int = 100) -> List[Dict]:
        """Get all deals."""
        params = {"limit": limit, "properties": "dealname,amount,dealstage,pipeline,createdate,closedate"}
        resp = requests.get(
            f"{HUBSPOT_BASE_URL}/crm/v3/objects/deals",
            headers=self.headers,
            params=params
        )
        resp.raise_for_status()
        return resp.json().get("results", [])
    
    # ==================== ENGAGEMENTS ====================
    
    def log_email(self, subject: str, body: str, to_email: str, 
                  from_email: str = "", status: str = "sent") -> Dict:
        """Log an email engagement."""
        data = {
            "engagement": {
                "active": True,
                "type": "EMAIL",
                "timestamp": int(datetime.now().timestamp() * 1000)
            },
            "associations": {
                "contactIds": [],
                "companyIds": [],
                "dealIds": []
            },
            "metadata": {
                "subject": subject,
                "body": body,
                "from": from_email,
                "to": to_email,
                "status": status
            }
        }
        resp = requests.post(
            f"{HUBSPOT_BASE_URL}/engagements/v1/engagements",
            headers=self.headers,
            json=data
        )
        resp.raise_for_status()
        return resp.json()
    
    def log_call(self, to_number: str, from_number: str = "", 
                 duration: int = 0, status: str = "completed", notes: str = "") -> Dict:
        """Log a call engagement."""
        data = {
            "engagement": {
                "active": True,
                "type": "CALL",
                "timestamp": int(datetime.now().timestamp() * 1000)
            },
            "metadata": {
                "toNumber": to_number,
                "fromNumber": from_number,
                "durationMilliseconds": duration * 1000,
                "status": status,
                "body": notes
            }
        }
        resp = requests.post(
            f"{HUBSPOT_BASE_URL}/engagements/v1/engagements",
            headers=self.headers,
            json=data
        )
        resp.raise_for_status()
        return resp.json()
    
    # ==================== PIPELINE HELPERS ====================
    
    def get_pipelines(self) -> List[Dict]:
        """Get all deal pipelines."""
        resp = requests.get(
            f"{HUBSPOT_BASE_URL}/crm/v3/pipelines/deals",
            headers=self.headers
        )
        resp.raise_for_status()
        return resp.json().get("results", [])
    
    def create_pipeline_stage(self, pipeline_id: str, stage_name: str, 
                              stage_probability: int = 50) -> Dict:
        """Create a custom pipeline stage."""
        data = {
            "stages": [{
                "label": stage_name,
                "probability": stage_probability
            }]
        }
        resp = requests.post(
            f"{HUBSPOT_BASE_URL}/crm/v3/pipelines/deals/{pipeline_id}/stages",
            headers=self.headers,
            json=data
        )
        resp.raise_for_status()
        return resp.json()
    
    # ==================== REPORTING ====================
    
    def get_pipeline_report(self, pipeline_id: str = "default") -> Dict:
        """Get pipeline summary."""
        deals = self.get_deals()
        stages = {}
        for deal in deals:
            stage = deal.get("properties", {}).get("dealstage", "unknown")
            stages[stage] = stages.get(stage, 0) + 1
        return {
            "total_deals": len(deals),
            "stages": stages,
            "generated_at": datetime.now().isoformat()
        }
    
    # ==================== CUSTOM PROPERTIES ====================
    
    def create_custom_property(self, object_type: str, name: str, label: str,
                               property_type: str = "string", group_name: str = "answerfirst_ai") -> Dict:
        """Create a custom CRM property."""
        data = {
            "name": name,
            "label": label,
            "type": property_type,
            "groupName": group_name,
            "fieldType": "crm_attribute"
        }
        resp = requests.post(
            f"{HUBSPOT_BASE_URL}/crm/v3/properties/{object_type}",
            headers=self.headers,
            json=data
        )
        resp.raise_for_status()
        return resp.json()
    
    # ==================== INTERNAL HELPERS ====================
    
    def _map_stage(self, stage: str) -> str:
        """Map human-readable stage to HubSpot stage IDs."""
        stage_map = {
            "qualified": "qualifiedtobuy",
            "demo_scheduled": "appointmentscheduled",
            "demo_completed": "presentationscheduled",
            "proposal_sent": "decisionmakerboughtin",
            "negotiation": "contractsent",
            "closed_won": "closedwon",
            "closed_lost": "closedlost"
        }
        return stage_map.get(stage, "qualifiedtobuy")
    
    def find_or_create_contact(self, email: str, first_name: str = "",
                               last_name: str = "", company: str = "",
                               phone: str = "") -> Dict:
        """Find existing contact or create new one."""
        existing = self.search_contact(email)
        if existing:
            return existing
        
        return self.create_contact(
            first_name=first_name,
            last_name=last_name,
            email=email,
            company=company,
            phone=phone
        )
    
    def sync_lead_to_crm(self, lead: Dict) -> Dict:
        """
        Sync a lead from our system to HubSpot CRM.
        Creates company + contact + deal in one flow.
        """
        result = {"company": None, "contact": None, "deal": None}
        
        # Create/find company
        domain = lead.get("website", "").replace("https://", "").replace("http://", "").split("/")[0]
        if domain:
            existing_company = self.search_company(domain)
            if existing_company:
                result["company"] = existing_company
            else:
                result["company"] = self.create_company(
                    name=lead.get("business_name", ""),
                    domain=domain,
                    phone=lead.get("phone", ""),
                    address=lead.get("address", "")
                )
        
        # Create/find contact
        email = lead.get("email", "")
        if email:
            result["contact"] = self.find_or_create_contact(
                email=email,
                first_name=lead.get("owner_first_name", ""),
                last_name=lead.get("owner_last_name", ""),
                company=lead.get("business_name", ""),
                phone=lead.get("phone", "")
            )
        
        # Create deal if qualified
        score = int(lead.get("score", 0))
        if score >= 65:
            company_id = result["company"]["id"] if result["company"] else ""
            contact_id = result["contact"]["id"] if result["contact"] else ""
            result["deal"] = self.create_deal(
                deal_name=f"{lead.get('business_name', 'Lead')} - {lead.get('package', 'Premium')}",
                company_id=company_id,
                contact_id=contact_id,
                amount=float(lead.get("monthly_value", 2500)),
                stage="qualified"
            )
        
        return result
    
    def bulk_sync_leads(self, leads: List[Dict]) -> List[Dict]:
        """Sync multiple leads to HubSpot."""
        results = []
        for lead in leads:
            try:
                result = self.sync_lead_to_crm(lead)
                results.append({"lead": lead.get("business_name"), "status": "synced", "data": result})
            except Exception as e:
                results.append({"lead": lead.get("business_name"), "status": "failed", "error": str(e)})
        return results


# ==================== TESTING ====================

if __name__ == "__main__":
    import sys
    api_key = sys.argv[1] if len(sys.argv) > 1 else os.getenv("HUBSPOT_API_KEY", "")
    if not api_key:
        print("Usage: python hubspot_api.py <API_KEY>")
        sys.exit(1)
    
    crm = HubSpotCRM(api_key)
    
    # Test connection
    try:
        pipelines = crm.get_pipelines()
        print(f"✓ Connected to HubSpot - {len(pipelines)} pipelines found")
        
        # Test contact creation
        contact = crm.create_contact(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            company="Test HVAC"
        )
        print(f"✓ Created test contact: {contact['id']}")
        
        # Test deal creation
        deal = crm.create_deal(
            deal_name="Test Deal - Basic",
            amount=1500,
            stage="qualified"
        )
        print(f"✓ Created test deal: {deal['id']}")
        
        # Get pipeline report
        report = crm.get_pipeline_report()
        print(f"✓ Pipeline report: {report['total_deals']} deals")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
