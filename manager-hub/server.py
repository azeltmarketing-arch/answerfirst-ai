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
import sys
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
                time.sleep(1)
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


def scrape_website(url: str) -> dict:
    try:
        headers = {'User-Agent': USER_AGENT}
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        if resp.status_code != 200:
            return {'content': '', 'has_ai': 0, 'pain_score': 0, 'email': '', 'phone': ''}
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text(separator=' ', strip=True).lower()
        
        has_ai = any(indicator in text for indicator in AI_INDICATORS)
        pain_score = sum(1 for indicator in PAIN_INDICATORS if indicator in text)
        
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        email = emails[0] if emails else ''
        
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
    if has_ai:
        return 0
    score = 50
    score += min(pain_score * 5, 25)
    score += 10 if niche.lower() in ['restaurant', 'hotel', 'retail', 'healthcare', 'dentist', 'lawyer'] else 0
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
    
    # Search
    businesses = search_businesses(niche, location, num_results)
    
    # Scrape and qualify
    prospects = []
    for biz in businesses:
        scraped = scrape_website(biz['url'])
        
        if scraped['has_ai']:
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
        time.sleep(random.uniform(0.5, 1.5))
    
    # Save to DB
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
    
    return jsonify({'added': saved, 'total_scraped': len(businesses), 'prospects': prospects})


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


if __name__ == '__main__':
    init_db()
    print("🚀 Manager Hub running at http://127.0.0.1:5050")
    app.run(host='127.0.0.1', port=5050, debug=False)
