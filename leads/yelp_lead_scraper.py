"""
AnswerFirst AI — Lead Generation via Yelp Fusion API
Free tier: 5,000 calls/day
Target: HVAC and roofing contractors in Phoenix, AZ
"""

import requests
import csv
import json
import time
import random
from datetime import datetime
from urllib.parse import quote_plus

# Yelp Fusion API (free tier: 5000 calls/day)
# Get API key from: https://www.yelp.com/developers/v3/manage_app
YELP_API_KEY = ""  # Set via environment or config
YELP_BASE_URL = "https://api.yelp.com/v3"

HEADERS = {
    "Authorization": f"Bearer {YELP_API_KEY}",
    "Accept": "application/json"
}

# Search configurations
SEARCH_QUERIES = [
    "HVAC",
    "Air Conditioning",
    "Heating",
    "Roofing",
    "Roof Repair",
    "Plumbing",
    "Electricians"
]

LOCATIONS = [
    "Phoenix, AZ",
    "Scottsdale, AZ",
    "Tempe, AZ",
    "Mesa, AZ",
    "Chandler, AZ"
]

def search_yelp_businesses(term, location, limit=50):
    """Search Yelp for businesses matching term in location."""
    url = f"{YELP_BASE_URL}/businesses/search"
    params = {
        "term": term,
        "location": location,
        "limit": min(limit, 50),
        "sort_by": "review_count",
        "categories": "hvac,roofing,plumbing,electricians"
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data.get("businesses", [])
        else:
            print(f"  [!] Yelp API error: {response.status_code} - {response.text[:200]}")
            return []
    except Exception as e:
        print(f"  [!] Request failed: {e}")
        return []

def get_business_details(business_id):
    """Get detailed business info from Yelp."""
    url = f"{YELP_BASE_URL}/businesses/{business_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}

def extract_lead_from_yelp(business):
    """Convert Yelp business data to lead format."""
    lead = {
        "business_name": business.get("name", ""),
        "owner": "",  # Yelp doesn't provide owner names directly
        "phone": business.get("phone", ""),
        "email": "",  # Not available via API
        "website": business.get("url", ""),
        "address": ", ".join(filter(None, [
            business.get("location", {}).get("address1", ""),
            business.get("location", {}).get("city", ""),
            business.get("location", {}).get("state", ""),
            business.get("location", {}).get("zip_code", "")
        ])),
        "city": business.get("location", {}).get("city", ""),
        "state": business.get("location", {}).get("state", ""),
        "google_rating": 0,  # Not from Yelp
        "yelp_rating": business.get("rating", 0),
        "review_count": business.get("review_count", 0),
        "services": ", ".join([c["title"] for c in business.get("categories", [])]),
        "source": "yelp_api",
        "scraped_at": datetime.now().isoformat(),
        "score": 0,
        "status": "new"
    }
    return lead

def calculate_lead_score(lead):
    """Score lead from 0-100."""
    score = 0
    
    # Phone
    if lead.get("phone") and len(lead["phone"]) >= 10:
        score += 25
    
    # Website
    if lead.get("website") and lead["website"].startswith("http"):
        score += 20
    
    # Yelp rating
    rating = lead.get("yelp_rating", 0)
    if rating >= 4.5:
        score += 25
    elif rating >= 4.0:
        score += 20
    elif rating >= 3.5:
        score += 15
    
    # Review count
    reviews = lead.get("review_count", 0)
    if reviews >= 100:
        score += 20
    elif reviews >= 50:
        score += 15
    elif reviews >= 20:
        score += 10
    
    # Target location
    target_cities = ["phoenix", "scottsdale", "tempe", "mesa", "chandler"]
    if any(city in lead.get("city", "").lower() for city in target_cities):
        score += 10
    
    lead["score"] = score
    lead["qualified"] = score >= 60  # Slightly lower threshold for Yelp data
    
    return lead

def deduplicate_leads(leads):
    """Remove duplicates by business name."""
    seen = set()
    unique = []
    for lead in leads:
        name = lead["business_name"].lower().strip()
        if name not in seen:
            seen.add(name)
            unique.append(lead)
    return unique

def save_leads(leads, filename):
    """Save leads to CSV."""
    if not leads:
        print("[!] No leads to save")
        return
    
    fieldnames = [
        "business_name", "owner", "phone", "email", "website",
        "address", "city", "state", "yelp_rating", "review_count",
        "services", "source", "scraped_at", "score", "status"
    ]
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(leads)
    
    print(f"[+] Saved {len(leads)} leads to {filename}")

def main():
    """Main lead generation workflow."""
    print("=" * 60)
    print("AnswerFirst AI — Yelp Lead Scraper")
    print("=" * 60)
    
    if not YELP_API_KEY:
        print("[!] YELP_API_KEY not set.")
        print("[!] Get a free API key at: https://www.yelp.com/developers/v3/manage_app")
        print("[*] Running in DEMO mode with sample data...\n")
        return run_demo_mode()
    
    all_leads = []
    total_api_calls = 0
    
    for location in LOCATIONS:
        for query in SEARCH_QUERIES:
            print(f"\n[*] Searching: {query} in {location}")
            businesses = search_yelp_businesses(query, location, limit=50)
            total_api_calls += 1
            
            if businesses:
                print(f"  [+] Found {len(businesses)} businesses")
                for biz in businesses:
                    lead = extract_lead_from_yelp(biz)
                    lead = calculate_lead_score(lead)
                    all_leads.append(lead)
            else:
                print(f"  [-] No results")
            
            # Rate limiting: Yelp allows 5000/day, be conservative
            time.sleep(random.uniform(0.5, 1.5))
    
    print(f"\n[*] Total API calls made: {total_api_calls}")
    
    # Deduplicate
    unique_leads = deduplicate_leads(all_leads)
    print(f"[*] Total unique leads: {len(unique_leads)}")
    
    # Qualification breakdown
    qualified = [l for l in unique_leads if l.get("qualified")]
    print(f"[+] Qualified leads (score >= 60): {len(qualified)}")
    
    # Sort by score
    sorted_leads = sorted(unique_leads, key=lambda x: x.get("score", 0), reverse=True)
    
    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"C:/Users/azelt/answerfirst-ai/leads/yelp_leads_{timestamp}.csv"
    save_leads(sorted_leads, filename)
    
    # Print top 10
    print("\n[*] Top 10 leads by score:")
    for i, lead in enumerate(sorted_leads[:10], 1):
        print(f"  {i}. {lead['business_name']} | Score: {lead['score']} | Rating: {lead.get('yelp_rating', 'N/A')} | Reviews: {lead.get('review_count', 0)}")
    
    return sorted_leads

def run_demo_mode():
    """Run with sample data when no API key is configured."""
    sample_leads = [
        {"business_name": "ABC Heating & Cooling", "phone": "(602) 555-0101", "website": "https://abchvac.com", "city": "Phoenix", "state": "AZ", "yelp_rating": 4.5, "review_count": 150, "services": "HVAC,AC Repair", "source": "yelp_demo", "scraped_at": datetime.now().isoformat(), "score": 0, "status": "new"},
        {"business_name": "Desert Roofing Solutions", "phone": "(602) 555-0102", "website": "https://desertroofingaz.com", "city": "Scottsdale", "state": "AZ", "yelp_rating": 4.2, "review_count": 95, "services": "Roofing,Roof Repair", "source": "yelp_demo", "scraped_at": datetime.now().isoformat(), "score": 0, "status": "new"},
        {"business_name": "Phoenix Plumbing Experts", "phone": "(602) 555-0103", "website": "https://phoenixplumbing.com", "city": "Tempe", "state": "AZ", "yelp_rating": 4.0, "review_count": 67, "services": "Plumbing,Drain Cleaning", "source": "yelp_demo", "scraped_at": datetime.now().isoformat(), "score": 0, "status": "new"},
        {"business_name": "Mesa Electrical Services", "phone": "(480) 555-0104", "website": "https://mesaelectric.com", "city": "Mesa", "state": "AZ", "yelp_rating": 3.8, "review_count": 42, "services": "Electricians,Wiring", "source": "yelp_demo", "scraped_at": datetime.now().isoformat(), "score": 0, "status": "new"},
        {"business_name": "Chandler HVAC Inc", "phone": "(480) 555-0105", "website": "https://chandlerhvac.com", "city": "Chandler", "state": "AZ", "yelp_rating": 4.7, "review_count": 203, "services": "HVAC,Installation", "source": "yelp_demo", "scraped_at": datetime.now().isoformat(), "score": 0, "status": "new"},
    ]
    
    for lead in sample_leads:
        calculate_lead_score(lead)
    
    unique = deduplicate_leads(sample_leads)
    qualified = [l for l in unique if l.get("qualified")]
    
    print(f"[*] Demo mode: {len(unique)} leads, {len(qualified)} qualified")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"C:/Users/azelt/answerfirst-ai/leads/yelp_demo_{timestamp}.csv"
    save_leads(unique, filename)
    
    print("\n[*] Top leads:")
    sorted_leads = sorted(unique, key=lambda x: x.get("score", 0), reverse=True)
    for i, lead in enumerate(sorted_leads[:5], 1):
        print(f"  {i}. {lead['business_name']} | Score: {lead['score']}")
    
    return unique

if __name__ == "__main__":
    main()
