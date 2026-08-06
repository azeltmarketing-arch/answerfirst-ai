"""
AnswerFirst AI — AI Lead Enrichment Pipeline
Uses OpenAI API to enrich leads with owner names, personalization hooks, and outreach recommendations.
"""

import os
import json
import time
import random
from datetime import datetime
from pathlib import Path

# Placeholder for OpenAI API key - set via environment variable
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

def enrich_lead_with_ai(lead):
    """
    Use AI to enrich lead with owner name, personalization hook, and outreach strategy.
    
    Args:
        lead: Lead dictionary with basic info
    
    Returns:
        Enriched lead dictionary
    """
    if not OPENAI_API_KEY:
        print(f"  [!] No OpenAI API key - skipping AI enrichment for {lead.get('business_name', 'Unknown')}")
        return lead
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Build prompt
        prompt = f"""Analyze this HVAC/roofing contractor and provide:
1. Most likely owner/founder name (if not provided)
2. One specific personalization hook for outreach (based on reviews, services, or location)
3. Recommended outreach channel (email, phone, or linkedin)
4. Estimated call volume: low/medium/high
5. One specific pain point they likely have

Business Name: {lead.get('business_name', '')}
Website: {lead.get('website', '')}
Phone: {lead.get('phone', '')}
Address: {lead.get('address', '')}
Services: {lead.get('services', '')}
Google Rating: {lead.get('google_rating', 'N/A')}
Review Count: {lead.get('review_count', 'N/A')}

Return JSON format:
{{
  "owner_name": "Name or Unknown",
  "personalization_hook": "Specific hook",
  "recommended_channel": "email/phone/linkedin",
  "call_volume": "low/medium/high",
  "pain_point": "Specific pain point"
}}"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a business research assistant specializing in local service contractors. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            # Remove markdown code blocks if present
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            ai_data = json.loads(result_text)
            
            # Update lead with AI data
            if ai_data.get("owner_name") and lead.get("owner") in ["", "Unknown Owner"]:
                lead["owner"] = ai_data["owner_name"]
            
            lead["personalization_hook"] = ai_data.get("personalization_hook", "")
            lead["recommended_channel"] = ai_data.get("recommended_channel", "email")
            lead["call_volume_estimate"] = ai_data.get("call_volume", "medium")
            lead["pain_point"] = ai_data.get("pain_point", "")
            lead["ai_enriched"] = True
            lead["ai_enriched_at"] = datetime.now().isoformat()
            
            print(f"  [+] Enriched: {lead['business_name']} -> {lead.get('owner', 'Unknown')}")
            
        except json.JSONDecodeError:
            print(f"  [!] Failed to parse AI response for {lead.get('business_name', 'Unknown')}")
            lead["ai_enriched"] = False
    
    except Exception as e:
        print(f"  [!] AI enrichment error for {lead.get('business_name', 'Unknown')}: {e}")
        lead["ai_enriched"] = False
    
    return lead

def generate_outreach_message(lead, sequence_type="A"):
    """
    Generate personalized outreach message for a lead.
    
    Args:
        lead: Enriched lead dictionary
        sequence_type: A (high-intent), B (medium-intent), or C (low-intent)
    
    Returns:
        Dictionary with subject and body
    """
    if not OPENAI_API_KEY:
        return generate_template_message(lead, sequence_type)
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        business_name = lead.get("business_name", "your business")
        owner_name = lead.get("owner", "there")
        hook = lead.get("personalization_hook", "your business")
        pain_point = lead.get("pain_point", "missed calls")
        
        prompt = f"""Write a short, personalized cold outreach email for an AI appointment-setting service.

Target: {owner_name} at {business_name}
Personalization hook: {hook}
Known pain point: {pain_point}

Rules:
- Under 120 words
- One clear CTA
- No price mention
- Professional but conversational tone
- Reference the specific hook

Return JSON: {{"subject": "...", "body": "..."}}"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a copywriter specializing in B2B outreach for local service businesses. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        result_text = response.choices[0].message.content.strip()
        
        try:
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            message = json.loads(result_text)
            return message
        except json.JSONDecodeError:
            return generate_template_message(lead, sequence_type)
    
    except Exception as e:
        print(f"  [!] Message generation error: {e}")
        return generate_template_message(lead, sequence_type)

def generate_template_message(lead, sequence_type="A"):
    """Generate outreach message using templates (fallback when no API key)."""
    business_name = lead.get("business_name", "your business")
    owner_name = lead.get("owner", "there")
    
    templates = {
        "A": {
            "subject": f"Quick question about {business_name}",
            "body": f"Hi {owner_name},\n\nI came across {business_name} and noticed you have a solid reputation in the area.\n\nI help HVAC contractors recover 15-20 missed calls per week using AI-powered call answering that books appointments 24/7.\n\nWould you be open to a 10-minute call this week?\n\nBest,\n[Your Name]\nAnswerFirst AI"
        },
        "B": {
            "subject": f"Quick question about {business_name}",
            "body": f"Hi {owner_name},\n\nI'm researching HVAC contractors in the area and found {business_name}.\n\nQuick question: how do you currently handle after-hours calls? Most contractors I talk to say it's their biggest pain point.\n\nWould love to hear your take.\n\nBest,\n[Your Name]\nAnswerFirst AI"
        },
        "C": {
            "subject": f"Quick question about {business_name}",
            "body": f"Hi {owner_name},\n\nI found {business_name} while researching HVAC services in the area.\n\nI'm curious: what's your biggest challenge right now? Is it finding good techs, managing scheduling, or something else?\n\nNo pitch—just trying to understand the market better.\n\nBest,\n[Your Name]\nAnswerFirst AI"
        }
    }
    
    return templates.get(sequence_type, templates["A"])

def process_leads_batch(leads, batch_size=10):
    """
    Process leads in batches with rate limiting.
    
    Args:
        leads: List of lead dictionaries
        batch_size: Number of leads to process before pause
    
    Returns:
        List of enriched leads
    """
    enriched_leads = []
    total = len(leads)
    
    print(f"[*] Processing {total} leads in batches of {batch_size}")
    
    for i, lead in enumerate(leads, 1):
        print(f"  [{i}/{total}] Processing: {lead.get('business_name', 'Unknown')}")
        
        # Enrich with AI
        lead = enrich_lead_with_ai(lead)
        
        # Generate personalized message
        sequence = "A" if lead.get("score", 0) >= 80 else "B" if lead.get("score", 0) >= 70 else "C"
        message = generate_outreach_message(lead, sequence)
        lead["outreach_subject"] = message.get("subject", "")
        lead["outreach_body"] = message.get("body", "")
        lead["sequence_assigned"] = sequence
        
        enriched_leads.append(lead)
        
        # Rate limiting
        if i % batch_size == 0:
            delay = random.uniform(2, 5)
            print(f"  [*] Pausing {delay:.1f}s to respect rate limits...")
            time.sleep(delay)
    
    print(f"[+] Enriched {len(enriched_leads)} leads")
    return enriched_leads

def save_enriched_leads(leads, filename):
    """Save enriched leads to JSON for later use."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved enriched leads to {filename}")

def main():
    """Main enrichment pipeline."""
    print("=" * 60)
    print("AnswerFirst AI — Lead Enrichment Pipeline")
    print("=" * 60)
    
    # Find most recent leads CSV
    leads_dir = Path("C:/Users/azelt/answerfirst-ai/leads")
    csv_files = sorted(leads_dir.glob("*.csv"), reverse=True)
    
    if not csv_files:
        print("[!] No lead CSVs found. Run scraper first.")
        return []
    
    latest_csv = csv_files[0]
    print(f"[*] Loading leads from: {latest_csv.name}")
    
    # Load leads
    import csv as csv_module
    leads = []
    with open(latest_csv, "r", encoding="utf-8") as f:
        reader = csv_module.DictReader(f)
        for row in reader:
            leads.append(dict(row))
    
    print(f"[+] Loaded {len(leads)} leads")
    
    # Filter qualified leads
    qualified = [l for l in leads if int(l.get("score", 0)) >= 60]
    print(f"[+] Qualified leads: {len(qualified)}")
    
    if not qualified:
        print("[!] No qualified leads to process")
        return []
    
    # Process in batches
    enriched = process_leads_batch(qualified, batch_size=5)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"C:/Users/azelt/answerfirst-ai/leads/enriched_leads_{timestamp}.json"
    save_enriched_leads(enriched, json_filename)
    
    # Print summary
    print("\n[*] Enrichment Summary:")
    ai_enriched = sum(1 for l in enriched if l.get("ai_enriched"))
    print(f"  [+] AI enriched: {ai_enriched}/{len(enriched)}")
    print(f"  [+] Sequences assigned: A={sum(1 for l in enriched if l.get('sequence_assigned')=='A')}, B={sum(1 for l in enriched if l.get('sequence_assigned')=='B')}, C={sum(1 for l in enriched if l.get('sequence_assigned')=='C')}")
    
    return enriched

if __name__ == "__main__":
    enriched_leads = main()
