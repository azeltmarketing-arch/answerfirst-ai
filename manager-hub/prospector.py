"""
AnswerFirst AI - Local Lead Prospecting Engine
Scrapes the internet for businesses WITHOUT AI receptionist/chatbot.
"""
import sqlite3
import csv
import re
import time
import random
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from pathlib import Path

DB_PATH = Path(__file__).parent / "prospects.db"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Keywords that indicate a business DOES have AI chatbot/receptionist
AI_INDICATORS = [
    "chatbot", "ai assistant", "artificial intelligence", "virtual assistant",
    "live chat", "automated", "bot", "ai-powered", "machine learning",
    "neural", "gpt", "claude", "gemini", "openai", "anthropic",
    "intercom", "drift", "zendesk answer bot", "tidio", "crisp",
    "conversational ai", "voice assistant", "digital assistant",
    "ai receptionist", "smart assistant", "ai chat", "automated assistant"
]

# Keywords that indicate a business NEEDS an AI receptionist
PAIN_INDICATORS = [
    "call us", "give us a call", "schedule a call", "book a call",
    "contact us", "reach out", "phone", "tel:", "call today",
    "hours of operation", "business hours", "monday-friday",
    "appointment", "booking", "schedule", "consultation"
]


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS prospects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            website TEXT UNIQUE,
            email TEXT,
            phone TEXT,
            niche TEXT,
            has_ai INTEGER DEFAULT 0,
            pain_score INTEGER DEFAULT 0,
            fit_score INTEGER DEFAULT 0,
            status TEXT DEFAULT 'new',
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def search_businesses(niche: str, location: str = "", num_results: int = 20):
    """Search DuckDuckGo for businesses in a niche/location."""
    results = []
    queries = [
        f"{niche} in {location}" if location else niche,
        f"{niche} services",
        f"{niche} company",
    ]
    
    with DDGS() as ddgs:
        for query in queries:
            try:
                hits = list(ddgs.text(query, max_results=num_results))
                for hit in hits:
                    url = hit.get('href', '')
                    if url.startswith('http') and not any(x in url for x in ['youtube.com', 'facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com']):
                        results.append({
                            'title': hit.get('title', ''),
                            'url': url,
                            'body': hit.get('body', '')
                        })
                time.sleep(1)  # Rate limit
            except Exception as e:
                print(f"Search error for '{query}': {e}")
    
    # Deduplicate by URL
    seen = set()
    unique = []
    for r in results:
        domain = re.sub(r'https?://(www\.)?', '', r['url']).split('/')[0]
        if domain not in seen:
            seen.add(domain)
            unique.append(r)
    return unique


def scrape_website(url: str) -> dict:
    """Scrape a website and check for AI indicators and pain points."""
    try:
        headers = {'User-Agent': USER_AGENT}
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        if resp.status_code != 200:
            return {'content': '', 'has_ai': 0, 'pain_score': 0, 'email': '', 'phone': ''}
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text(separator=' ', strip=True).lower()
        
        # Check for AI indicators
        has_ai = any(indicator in text for indicator in AI_INDICATORS)
        
        # Count pain indicators
        pain_score = sum(1 for indicator in PAIN_INDICATORS if indicator in text)
        
        # Extract email
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        email = emails[0] if emails else ''
        
        # Extract phone
        phones = re.findall(r'\(?\d{3}\)?[\s\.-]\d{3}[\s\.-]\d{4}', text)
        phone = phones[0] if phones else ''
        
        return {
            'content': text[:500],
            'has_ai': 1 if has_ai else 0,
            'pain_score': pain_score,
            'email': email,
            'phone': phone
        }
    except Exception as e:
        return {'content': '', 'has_ai': 0, 'pain_score': 0, 'email': '', 'phone': ''}


def calculate_fit_score(has_ai: int, pain_score: int, niche: str) -> int:
    """Calculate how good a fit this prospect is (0-100)."""
    if has_ai:
        return 0  # Already has AI, not a prospect
    
    score = 50  # Base score
    score += min(pain_score * 5, 25)  # Pain points add up to 25
    score += 10 if niche.lower() in ['restaurant', 'hotel', 'retail', 'healthcare', 'dentist', 'lawyer'] else 0
    return min(score, 100)


def prospect(niche: str, location: str = "", num_results: int = 10) -> list:
    """Main prospecting function - returns list of qualified prospects."""
    init_db()
    print(f"🔍 Scouting {num_results} businesses in {niche} {location}...")
    
    # Step 1: Search
    businesses = search_businesses(niche, location, num_results)
    print(f"   Found {len(businesses)} potential businesses")
    
    # Step 2: Scrape and qualify
    prospects = []
    for i, biz in enumerate(businesses):
        print(f"   [{i+1}/{len(businesses)}] Checking {biz['url']}...")
        scraped = scrape_website(biz['url'])
        
        if scraped['has_ai']:
            print(f"      ⏭️  Already has AI, skipping")
            continue
        
        fit = calculate_fit_score(scraped['has_ai'], scraped['pain_score'], niche)
        
        prospect_data = {
            'name': biz['title'],
            'website': biz['url'],
            'email': scraped['email'],
            'phone': scraped['phone'],
            'niche': niche,
            'has_ai': scraped['has_ai'],
            'pain_score': scraped['pain_score'],
            'fit_score': fit,
            'notes': scraped['content'][:200]
        }
        prospects.append(prospect_data)
        print(f"      ✅ Fit score: {fit}/100 | Email: {scraped['email'] or 'none'}")
        time.sleep(random.uniform(1, 3))  # Be polite
    
    # Step 3: Save to DB
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    saved = 0
    for p in prospects:
        try:
            c.execute("""
                INSERT OR IGNORE INTO prospects (name, website, email, phone, niche, has_ai, pain_score, fit_score, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (p['name'], p['website'], p['email'], p['phone'], p['niche'],
                  p['has_ai'], p['pain_score'], p['fit_score'], p['notes']))
            if c.rowcount > 0:
                saved += 1
        except Exception as e:
            print(f"      DB error: {e}")
    conn.commit()
    conn.close()
    
    print(f"\n✅ Saved {saved} new prospects")
    return prospects


def export_csv(filename: str = None) -> str:
    """Export prospects to CSV."""
    if not filename:
        filename = f"prospects_{int(time.time())}.csv"
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name, website, email, phone, niche, fit_score, pain_score, status, notes FROM prospects ORDER BY fit_score DESC")
    rows = c.fetchall()
    conn.close()
    
    filepath = Path(__file__).parent / filename
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Website', 'Email', 'Phone', 'Niche', 'Fit Score', 'Pain Score', 'Status', 'Notes'])
        writer.writerows(rows)
    
    print(f"📊 Exported {len(rows)} prospects to {filepath}")
    return str(filepath)


def get_stats() -> dict:
    """Get prospecting stats."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*), AVG(fit_score), MAX(fit_score) FROM prospects")
    total, avg_fit, max_fit = c.fetchone()
    c.execute("SELECT COUNT(*) FROM prospects WHERE status='new'")
    new_count = c.fetchone()[0]
    conn.close()
    
    return {
        'total': total or 0,
        'avg_fit': round(avg_fit or 0, 1),
        'max_fit': round(max_fit or 0, 1),
        'new_count': new_count
    }


if __name__ == '__main__':
    import sys
    niche = sys.argv[1] if len(sys.argv) > 1 else "restaurant"
    location = sys.argv[2] if len(sys.argv) > 2 else "Pico Rivera CA"
    num = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    
    prospects = prospect(niche, location, num)
    export_csv()
    print("\n📈 Stats:", get_stats())
