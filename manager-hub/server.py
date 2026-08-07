"""
AnswerFirst AI - Local Manager Hub Server
Runs on localhost:5050 and provides lead discovery + management APIs.
"""
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
import csv
import time
import random
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
import re
from pathlib import Path

app = Flask(__name__)
CORS(app)
app.secret_key = "local-manager-hub-secret"

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "prospects.db"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

AI_INDICATORS = [
    "chatbot", "ai assistant", "artificial intelligence", "virtual assistant",
    "live chat", "automated", "bot", "ai-powered", "machine learning",
    "neural", "gpt", "claude", "gemini", "openai", "anthropic",
    "intercom", "drift", "zendesk answer bot", "tidio", "crisp",
    "conversational ai", "voice assistant", "digital assistant",
    "ai receptionist", "smart assistant", "ai chat", "automated assistant"
]

AGGREGATOR_DOMAINS = {
    'yelp.com', 'tripadvisor.com', 'tiktok.com', 'youtube.com', 'facebook.com',
    'twitter.com', 'x.com', 'linkedin.com', 'instagram.com', 'google.com',
    'maps.google.com', 'search.google.com', 'reverso.net', 'wikipedia.org',
    'reddit.com', 'pinterest.com', 'snapchat.com', 'tumblr.com', 'medium.com',
    'wordpress.com', 'blogspot.com', 'wix.com', 'squarespace.com',
    'yellowpages.com', 'whitepages.com', 'angi.com', 'thumbtack.com',
    'bbb.org', 'mapquest.com', 'citysearch.com', 'superpages.com',
    'manta.com', 'dexknows.com', 'cylex.us', 'hotfrog.com',
    'foursquare.com', 'flickr.com', 'quora.com', 'answers.com',
    'chamberofcommerce.com', 'indeed.com', 'glassdoor.com', 'monster.com',
    'craigslist.org', 'offerup.com', 'letgo.com', 'varagesale.com',
    'nextdoor.com', 'patch.com', 'local10.com', 'newsbreak.com',
    'gosht.com', 'dictionary.reverso.net', 'istairport.com',
    'restaurantji.com', 'restaurantobserver.com', 'restroworks.com',
    'rsidrivesroi.com', 'grokipedia.com', 'inspirebrands.com',
    'investopedia.com', 'therestaurantcompany.us',
    'mahoneyes.com', 'rti-inc.com', 'darden.com', 'rbi.com',
    'tripadvisor.co.uk'
}

DIRECTORY_SIGNATURES = [
    "restaurants near", "best restaurants", "restaurants in", "top restaurants",
    "restaurant reviews", "restaurant guide", "directory", "listing",
    "search results", "found", "results for", "showing",
    "hotels near", "best hotels", "hotels in",
    "contractors near", "best contractors", "contractors in",
    "dentists near", "best dentists", "dentists in",
    "lawyers near", "best lawyers", "law firms in",
    "doctors near", "best doctors", "physicians in",
    "near me", "nearby", "locations", "branches",
    "search for", "browse all", "explore"
]


def is_aggregator(url: str, title: str = '', body: str = '') -> bool:
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace('www.', '')
    if domain in AGGREGATOR_DOMAINS:
        return True
    path = parsed.path.lower()
    if any(x in path for x in ['/search', '/find', '/directory', '/listing', '/guide', '/near']):
        return True
    title_lower = title.lower()
    body_lower = body.lower()
    combined = title_lower + ' ' + body_lower
    for sig in DIRECTORY_SIGNATURES:
        if sig in combined:
            return True
    return False


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
    results = []
    queries = [
        f"{niche} {location} phone number contact",
        f"{niche} {location} email contact",
        f"best {niche} {location}",
    ]
    
    with DDGS() as ddgs:
        for query in queries:
            try:
                hits = list(ddgs.text(query, max_results=num_results))
                for hit in hits:
                    url = hit.get('href', '')
                    title = hit.get('title', '')
                    body = hit.get('body', '')
                    if not url.startswith('http'):
                        continue
                    if is_aggregator(url, title, body):
                        continue
                    if any(x in url for x in ['youtube.com', 'facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com']):
                        continue
                    results.append({'title': title, 'url': url, 'body': body})
                time.sleep(1.5)
            except Exception as e:
                print(f"Search error: {e}")
    
    seen = set()
    unique = []
    for r in results:
        domain = re.sub(r'https?://(www\.)?', '', r['url']).split('/')[0]
        if domain not in seen:
            seen.add(domain)
            unique.append(r)
    return unique


def decode_obfuscated_email(text: str) -> str:
    """Decode common obfuscation patterns like info [at] domain [dot] com."""
    # Pattern: word [at] domain [dot] com
    m = re.search(r'([\w\.-]+)\s*[\(\[\{]\s*at\s*[\)\]\}]\s*([\w\.-]+)\s*[\(\[\{]\s*dot\s*[\)\]\}]\s*([\w\.-]+)', text, re.IGNORECASE)
    if m:
        return f"{m.group(1)}@{m.group(2)}.{m.group(3)}"
    
    # Pattern: word(at)domain(dot)com
    m = re.search(r'([\w\.-]+)\s*\(\s*at\s*\)\s*([\w\.-]+)\s*\(\s*dot\s*\)\s*([\w\.-]+)', text, re.IGNORECASE)
    if m:
        return f"{m.group(1)}@{m.group(2)}.{m.group(3)}"
    
    # Pattern: word AT domain DOT com
    m = re.search(r'([\w\.-]+)\s+AT\s+([\w\.-]+)\s+DOT\s+([\w\.-]+)', text, re.IGNORECASE)
    if m:
        return f"{m.group(1)}@{m.group(2)}.{m.group(3)}"
    
    return ''


def extract_emails_aggressive(html: str, soup=None) -> list:
    """Aggressively extract emails from HTML using every method."""
    emails = []
    
    # 1. Direct regex on raw HTML
    direct = re.findall(r'[\w\.-]+@[\w\.-]+\.\w{2,}', html)
    emails.extend(direct)
    
    # 2. Mailto links
    mailtos = re.findall(r'href="mailto:([^"]+)"', html)
    for mailto in mailtos:
        email = mailto.split('?')[0].strip()
        if email and re.match(r'[\w\.-]+@[\w\.-]+\.\w{2,}', email):
            emails.append(email)
    
    # 3. JSON-LD / schema.org
    schemas = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
    for schema in schemas:
        try:
            import json
            data = json.loads(schema)
            email = _extract_email_from_json(data)
            if email:
                emails.append(email)
        except:
            pass
    
    # 4. Obfuscated emails
    obfuscated = decode_obfuscated_email(html)
    if obfuscated:
        emails.append(obfuscated)
    
    # 5. Common patterns from text content
    if soup:
        text = soup.get_text(separator=' ', strip=True)
        # Look for "email us at ..." patterns
        m = re.search(r'email\s+us\s+at\s+([\w\.-]+@[\w\.-]+\.\w{2,})', text, re.IGNORECASE)
        if m:
            emails.append(m.group(1))
        
        # Look for "contact ...@..." patterns
        m = re.search(r'contact[:\s]+([\w\.-]+@[\w\.-]+\.\w{2,})', text, re.IGNORECASE)
        if m:
            emails.append(m.group(1))
    
    # Deduplicate
    emails = list(dict.fromkeys(emails))
    
    # Filter out bad emails
    bad_emails = {'info@example.com', 'test@test.com', 'email@example.com', 
                  'your@email.com', 'name@domain.com', 'user@domain.com',
                  'example@example.com', 'domain@domain.com', 'sentry.io',
                  'wixpress.com', 'sentry-next.wixpress.com', 'googleapis.com',
                  'schema.org', 'example.com', 'w3.org', 'creativecommons.org'}
    emails = [e for e in emails if e.lower() not in bad_emails and not e.endswith('.png') and not e.endswith('.jpg')]
    
    return emails


def _extract_email_from_json(data):
    """Recursively extract email from JSON-LD data."""
    if isinstance(data, dict):
        for key in ['email', 'contactPoint', 'contact']:
            if key in data:
                val = data[key]
                if isinstance(val, str) and re.match(r'[\w\.-]+@[\w\.-]+\.\w{2,}', val):
                    return val
                if isinstance(val, dict):
                    email = val.get('email', '')
                    if email and re.match(r'[\w\.-]+@[\w\.-]+\.\w{2,}', str(email)):
                        return str(email)
        for val in data.values():
            result = _extract_email_from_json(val)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            result = _extract_email_from_json(item)
            if result:
                return result
    return ''


def extract_phones_aggressive(html: str, soup=None) -> list:
    """Aggressively extract phone numbers from HTML."""
    phones = []
    
    # 1. Direct regex on raw HTML
    phone_patterns = [
        r'\(?\d{3}\)?[\s\.\-]\d{3}[\s\.\-]\d{4}',
        r'\+?1?[\s\-\.]\(?\d{3}\)?[\s\-\.]\d{3}[\s\-\-]\d{4}',
        r'\d{3}[\s\.\-]\d{3}[\s\.\-]\d{4}',
        r'\(\d{3}\)\s*\d{3}[-\.]\d{4}',
        r'href="tel:([^"]+)"',
    ]
    
    for pattern in phone_patterns:
        found = re.findall(pattern, html)
        phones.extend(found)
    
    # 2. From text content
    if soup:
        text = soup.get_text(separator=' ', strip=True)
        for pattern in phone_patterns:
            found = re.findall(pattern, text)
            phones.extend(found)
    
    # Deduplicate
    phones = list(dict.fromkeys(phones))
    
    # Filter bad numbers
    bad_phones = {'000-000-0000', '123-456-7890', '555-555-5555', '000-000-000',
                  '111-111-1111', '222-222-2222', '333-333-3333', '888-888-8888',
                  '999-999-9999', '000-0000000'}
    phones = [p for p in phones if p not in bad_phones and len(p) >= 10]
    
    return phones


def normalize_phone(phone: str) -> str:
    """Normalize phone to (555) 123-4567 format."""
    digits = re.sub(r'[^\d]', '', phone)
    if len(digits) == 11 and digits[0] == '1':
        digits = digits[1:]
    if len(digits) != 10:
        return phone
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"


def find_contact_pages(base_url: str) -> list:
    """Find potential contact pages."""
    from urllib.parse import urljoin, urlparse
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    
    paths = [
        '/contact', '/contact-us', '/reach-us', '/get-in-touch',
        '/about', '/about-us', '/staff', '/team', '/locations',
        '/phone', '/email', '/connect'
    ]
    
    found = []
    for path in paths:
        try:
            test_url = urljoin(base, path)
            resp = requests.get(test_url, headers={'User-Agent': USER_AGENT}, timeout=10, allow_redirects=True)
            if resp.status_code == 200:
                found.append(resp.url)
        except:
            continue
    return found


def scrape_website(url: str, deep_scrape: bool = True) -> dict:
    """Scrape a website and return contact info, AI detection, and pain score."""
    try:
        headers = {'User-Agent': USER_AGENT}
        resp = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
        if resp.status_code != 200:
            return {
                'content': '', 'has_ai': 0, 'pain_score': 0, 
                'email': '', 'phone': '', 'final_url': url
            }
        
        final_url = resp.url
        raw_html = resp.text
        soup = BeautifulSoup(raw_html, 'html.parser')
        
        # Get text for AI/pain analysis
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        text = soup.get_text(separator=' ', strip=True).lower()
        
        # Check for AI indicators
        has_ai = any(indicator in text for indicator in AI_INDICATORS)
        
        # Count pain indicators
        pain_score = sum(1 for indicator in PAIN_INDICATORS if indicator in text)
        
        # Extract contact info - try main page first
        emails = extract_emails_aggressive(raw_html, soup)
        phones = extract_phones_aggressive(raw_html, soup)
        
        email = emails[0] if emails else ''
        phone = normalize_phone(phones[0]) if phones else ''
        
        # Deep scrape: try contact pages if no contact info found
        if deep_scrape and (not email or not phone):
            contact_urls = find_contact_pages(final_url)
            for contact_url in contact_urls[:2]:  # Try top 2 contact pages
                try:
                    contact_resp = requests.get(contact_url, headers={'User-Agent': USER_AGENT}, timeout=15)
                    if contact_resp.status_code == 200:
                        contact_soup = BeautifulSoup(contact_resp.text, 'html.parser')
                        contact_emails = extract_emails_aggressive(contact_resp.text, contact_soup)
                        contact_phones = extract_phones_aggressive(contact_resp.text, contact_soup)
                        
                        if not email and contact_emails:
                            email = contact_emails[0]
                        if not phone and contact_phones:
                            phone = normalize_phone(contact_phones[0])
                        
                        # Add pain score from contact page
                        for script in contact_soup(["script", "style"]):
                            script.decompose()
                        contact_text = contact_soup.get_text(separator=' ', strip=True).lower()
                        pain_score += sum(1 for indicator in PAIN_INDICATORS if indicator in contact_text)
                        
                        if email and phone:
                            break
                except:
                    continue
        
        return {
            'content': text[:500],
            'has_ai': 1 if has_ai else 0,
            'pain_score': pain_score,
            'email': email,
            'phone': phone,
            'final_url': final_url
        }
    except Exception as e:
        return {
            'content': '', 'has_ai': 0, 'pain_score': 0, 
            'email': '', 'phone': '', 'final_url': url
        }


def calculate_fit_score(has_ai: int, pain_score: int, has_email: bool, has_phone: bool) -> int:
    if has_ai:
        return 0
    score = 40
    score += min(pain_score * 5, 25)
    score += 15 if has_email else 0
    score += 20 if has_phone else 0
    return min(score, 100)


@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'database': 'connected'})


@app.route('/api/discover-leads', methods=['POST'])
def discover_leads():
    data = request.json or {}
    niche = data.get('niche', 'restaurant')
    location = data.get('location', 'Pico Rivera CA')
    num_results = data.get('num_results', 10)
    
    init_db()
    businesses = search_businesses(niche, location, num_results * 3)
    
    prospects = []
    skipped_ai = 0
    skipped_no_contact = 0
    
    for biz in businesses:
        scraped = scrape_website(biz['url'], deep_scrape=True)
        
        if scraped['has_ai']:
            skipped_ai += 1
            continue
        
        has_email = bool(scraped['email'])
        has_phone = bool(scraped['phone'])
        
        if not has_email and not has_phone:
            skipped_no_contact += 1
            continue
        
        fit = calculate_fit_score(scraped['has_ai'], scraped['pain_score'], has_email, has_phone)
        final_url = scraped.get('final_url', biz['url'])
        
        prospect_data = {
            'name': biz['title'],
            'website': final_url,
            'email': scraped['email'],
            'phone': scraped['phone'],
            'niche': niche,
            'has_ai': scraped['has_ai'],
            'pain_score': scraped['pain_score'],
            'fit_score': fit,
            'notes': scraped['content'][:200]
        }
        prospects.append(prospect_data)
        time.sleep(random.uniform(0.8, 2.0))
    
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
            print(f"DB error: {e}")
    conn.commit()
    conn.close()
    
    return jsonify({
        'added': saved,
        'total_scraped': len(businesses),
        'skipped_ai': skipped_ai,
        'skipped_no_contact': skipped_no_contact,
        'prospects': prospects
    })


@app.route('/api/leads')
def get_leads():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM prospects ORDER BY fit_score DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)


@app.route('/api/leads', methods=['POST'])
def update_lead():
    data = request.json or {}
    lead_id = data.get('id')
    if not lead_id:
        return jsonify({'error': 'id required'}), 400
    
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    updates = {}
    for field in ['name', 'email', 'phone', 'status', 'notes', 'fit_score']:
        if field in data:
            updates[field] = data[field]
    
    if updates:
        set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [lead_id]
        c.execute(f"UPDATE prospects SET {set_clause} WHERE id = ?", values)
        conn.commit()
    
    conn.close()
    return jsonify({'updated': True})


@app.route('/api/leads/<int:lead_id>')
def get_lead_detail(lead_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM prospects WHERE id = ?", (lead_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return jsonify(dict(row))
    return jsonify({'error': 'Lead not found'}), 404


@app.route('/api/import/leads', methods=['POST'])
def import_leads():
    data = request.json or {}
    path = data.get('path', 'leads.csv')
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        init_db()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        imported = 0
        for row in rows:
            try:
                c.execute("""
                    INSERT OR IGNORE INTO prospects (name, website, email, phone, niche, fit_score, status, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('Name', row.get('name', '')),
                    row.get('Website', row.get('website', '')),
                    row.get('Email', row.get('email', '')),
                    row.get('Phone', row.get('phone', '')),
                    row.get('Niche', row.get('niche', '')),
                    int(row.get('Fit Score', row.get('fit_score', 0))),
                    row.get('Status', row.get('status', 'new')),
                    row.get('Notes', row.get('notes', ''))
                ))
                if c.rowcount > 0:
                    imported += 1
            except Exception:
                pass
        conn.commit()
        conn.close()
        return jsonify({'imported': imported, 'total': len(rows)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/leads')
def export_leads():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name, website, email, phone, niche, fit_score, pain_score, status, notes FROM prospects ORDER BY fit_score DESC")
    rows = c.fetchall()
    conn.close()
    
    output = BASE_DIR / f"prospects_export_{int(time.time())}.csv"
    with open(output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Website', 'Email', 'Phone', 'Niche', 'Fit Score', 'Pain Score', 'Status', 'Notes'])
        writer.writerows(rows)
    
    return send_from_directory(BASE_DIR, output.name, as_attachment=True)


@app.route('/api/stats')
def stats():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*), AVG(fit_score), MAX(fit_score) FROM prospects")
    total, avg_fit, max_fit = c.fetchone()
    c.execute("SELECT COUNT(*) FROM prospects WHERE status='new'")
    new_count = c.fetchone()[0]
    conn.close()
    
    return jsonify({
        'total': total or 0,
        'avg_fit': round(avg_fit or 0, 1),
        'max_fit': round(max_fit or 0, 1),
        'new_count': new_count
    })


@app.route('/shutdown', methods=['GET', 'POST'])
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        return jsonify({'error': 'Not running with Werkzeug'}), 400
    func()
    return jsonify({'status': 'shutting down'})


if __name__ == '__main__':
    init_db()
    print("🚀 Manager Hub running at http://127.0.0.1:5050")
    app.run(host='127.0.0.1', port=5050, debug=False)
