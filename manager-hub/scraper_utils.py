import requests
from urllib.parse import urljoin, urlparse
import re
import socket
import whois
from bs4 import BeautifulSoup

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
]

COMMON_EMAIL_PREFIXES = [
    "info", "contact", "support", "sales", "hello", "admin", "office", "help",
    "general", "mail", "enquiries", "inquiry", "service", "customer", "webmaster",
    "manager", "team", "press", "media", "marketing", "billing", "accounts",
    "hr", "jobs", "careers", "info", "contactus", "contact", "email"
]

def get_random_headers():
    return {
        'User-Agent': USER_AGENTS[hash(__import__('time').time()) % len(USER_AGENTS)],
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }

def extract_emails_from_text(text: str) -> list:
    """Extract emails from plain text using multiple patterns."""
    emails = set()
    
    # Standard email pattern
    standard = re.findall(r'[\w\.-]+@[\w\.-]+\.[\w]{2,}', text)
    emails.update(standard)
    
    # Obfuscated patterns
    obf = re.findall(r'([\w\.-]+)\s*(?:@|at|AT)\s*([\w\.-]+)\s*(?:\.|dot|DOT)\s*([\w]{2,})', text, re.IGNORECASE)
    for m in obf:
        emails.add(f"{m[0]}@{m[1]}.{m[2]}")
    
    # HTML entity encoded
    entity = re.findall(r'[\w\.-]+&#64;[\w\.-]+\.[\w]{2,}', text)
    emails.update(entity)
    
    # JavaScript obfuscation patterns
    js_obf = re.findall(r'["\']([\w\.-]+)\s*@\s*([\w\.-]+)\s*\.\s*([\w]{2,})["\']', text)
    for m in js_obf:
        emails.add(f"{m[0]}@{m[1]}.{m[2]}")
    
    return list(emails)

def extract_emails_from_meta(soup) -> list:
    """Extract emails from meta tags."""
    emails = set()
    meta_tags = soup.find_all('meta')
    for tag in meta_tags:
        content = tag.get('content', '')
        if '@' in content and '.' in content:
            found = re.findall(r'[\w\.-]+@[\w\.-]+\.[\w]{2,}', content)
            emails.update(found)
    return list(emails)

def extract_emails_from_comments(soup) -> list:
    """Extract emails from HTML comments."""
    emails = set()
    comments = soup.find_all(string=lambda text: isinstance(text, type(soup).Comment))
    for comment in comments:
        if '@' in comment:
            found = re.findall(r'[\w\.-]+@[\w\.-]+\.[\w]{2,}', comment)
            emails.update(found)
    return list(emails)

def extract_emails_from_inline_styles(soup) -> list:
    """Extract emails from inline styles (sometimes used for obfuscation)."""
    emails = set()
    elements = soup.find_all(style=True)
    for el in elements:
        style = el.get('style', '')
        if '@' in style:
            found = re.findall(r'[\w\.-]+@[\w\.-]+\.[\w]{2,}', style)
            emails.update(found)
    return list(emails)

def extract_emails_from_jsonld(soup) -> list:
    """Extract emails from JSON-LD structured data."""
    emails = set()
    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        try:
            import json
            data = json.loads(script.string)
            if isinstance(data, dict):
                if 'email' in data:
                    emails.add(data['email'])
                if 'contactPoint' in data and isinstance(data['contactPoint'], dict):
                    emails.add(data['contactPoint'].get('email', ''))
        except:
            pass
    return list(emails)

def extract_emails_from_microdata(soup) -> list:
    """Extract emails from microdata attributes."""
    emails = set()
    elements = soup.find_all(itemtype=re.compile('schema.org', re.IGNORECASE))
    for el in elements:
        if 'itemprop' in el.attrs and el['itemprop'] == 'email':
            emails.add(el.get_text(strip=True))
        if el.get('itemtype', '').lower().find('person') != -1 or el.get('itemtype', '').lower().find('organization') != -1:
            email_el = el.find(itemprop='email')
            if email_el:
                emails.add(email_el.get_text(strip=True))
    return list(emails)

def guess_emails_from_domain(domain: str) -> list:
    """Generate likely email addresses for a domain."""
    emails = set()
    base_domain = domain.replace('www.', '')
    for prefix in COMMON_EMAIL_PREFIXES:
        emails.add(f"{prefix}@{base_domain}")
    return list(emails)

def get_whois_email(domain: str) -> str:
    """Try to get email from WHOIS registrant data."""
    try:
        w = whois.whois(domain)
        if w.emails:
            if isinstance(w.emails, list):
                return w.emails[0]
            return w.emails
        if w.registrant_email:
            return w.registrant_email
        if w.admin_email:
            return w.admin_email
    except:
        pass
    return ''

def find_sitemaps(base_url: str) -> list:
    """Find sitemap URLs."""
    from urllib.parse import urljoin, urlparse
    sitemaps = []
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    
    sitemap_paths = ['/sitemap.xml', '/sitemap_index.xml', '/sitemaps.xml', '/robots.txt']
    for path in sitemap_paths:
        try:
            url = urljoin(base, path)
            headers = get_random_headers()
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                if path.endswith('robots.txt'):
                    for line in resp.text.split('\n'):
                        if line.lower().startswith('sitemap:'):
                            sitemaps.append(line.split(':', 1)[1].strip())
                else:
                    sitemaps.append(url)
        except:
            continue
    return sitemaps

def crawl_sitemap_for_emails(sitemap_url: str, max_urls: int = 20) -> list:
    """Parse sitemap and crawl pages for emails."""
    emails = set()
    try:
        headers = get_random_headers()
        resp = requests.get(sitemap_url, headers=headers, timeout=20)
        if resp.status_code != 200:
            return []
        
        soup = BeautifulSoup(resp.text, 'xml')
        urls = [loc.text for loc in soup.find_all('loc')][:max_urls]
        
        for page_url in urls:
            try:
                page_resp = requests.get(page_url, headers=headers, timeout=15)
                if page_resp.status_code == 200:
                    page_soup = BeautifulSoup(page_resp.text, 'html.parser')
                    emails.update(extract_all_emails_from_page(page_resp.text, page_soup, page_url))
                time.sleep(0.5)
            except:
                continue
    except:
        pass
    return list(emails)

def extract_all_emails_from_page(html: str, soup, base_url: str) -> list:
    """Extract emails from every possible source on a page."""
    emails = set()
    
    if not soup:
        soup = BeautifulSoup(html, 'html.parser')
    
    # All extraction methods
    emails.update(extract_emails_from_text(html))
    emails.update(extract_emails_from_meta(soup))
    emails.update(extract_emails_from_comments(soup))
    emails.update(extract_emails_from_inline_styles(soup))
    emails.update(extract_emails_from_jsonld(soup))
    emails.update(extract_emails_from_microdata(soup))
    
    # Extract from href attributes
    for tag in soup.find_all(href=True):
        href = tag['href']
        if href.startswith('mailto:'):
            email = href.replace('mailto:', '').split('?')[0].strip()
            if re.match(r'[\w\.-]+@[\w\.-]+\.[\w]{2,}', email):
                emails.add(email)
    
    # Domain guessing
    parsed = urlparse(base_url)
    domain = parsed.netloc.replace('www.', '')
    emails.update(guess_emails_from_domain(domain))
    
    # Filter bad emails
    bad = {'info@example.com', 'test@test.com', 'email@example.com', 'your@email.com',
           'name@domain.com', 'user@domain.com', 'example@example.com', 'domain@domain.com',
           'sentry.io', 'wixpress.com', 'googleapis.com', 'schema.org', 'w3.org',
           'creativecommons.org', 'example.com', 'sentry-next.wixpress.com'}
    
    filtered = [e for e in emails if e.lower() not in bad and not e.endswith('.png') and not e.endswith('.jpg')]
    return list(set(filtered))
