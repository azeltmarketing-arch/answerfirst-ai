"""
AnswerFirst AI — Client Portal & Storefront
Public product pages + authenticated client portal
"""

import sqlite3
import json
import os
import secrets
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session, make_response

app = Flask(__name__)
app.secret_key = os.environ.get("PORTAL_SECRET", secrets.token_hex(32))
DB_PATH = os.path.join(os.path.dirname(__file__), "portal.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            business_name TEXT DEFAULT '',
            contact_name TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            package TEXT DEFAULT 'Basic',
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            package TEXT DEFAULT 'Basic',
            amount REAL DEFAULT 0,
            status TEXT DEFAULT 'pending',
            payment_method TEXT DEFAULT 'paypal',
            payment_link TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            rating INTEGER DEFAULT 5,
            title TEXT DEFAULT '',
            body TEXT DEFAULT '',
            status TEXT DEFAULT 'approved',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            client_id INTEGER NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)
    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    import hashlib
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def create_session(client_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires = (datetime.now().timestamp() + 7 * 24 * 60 * 60)
    db = get_db()
    db.execute("INSERT INTO sessions (token, client_id, expires_at) VALUES (?, ?, ?)", (token, client_id, datetime.fromtimestamp(expires).isoformat()))
    db.commit()
    db.close()
    return token


def get_client_from_session(token: str) -> Optional[Dict]:
    db = get_db()
    row = db.execute("SELECT c.* FROM sessions s JOIN clients c ON s.client_id = c.id WHERE s.token = ? AND s.expires_at > ?", (token, datetime.now().isoformat())).fetchone()
    db.close()
    return dict(row) if row else None


# ==================== PUBLIC PAGES ====================

PRODUCTS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AnswerFirst AI — Products</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: #0a0a0f; color: #e2e8f0; line-height: 1.6; }
        a { color: #38bdf8; text-decoration: none; }
        .container { max-width: 1200px; margin: 0 auto; padding: 0 24px; }
        header { background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(51, 65, 85, 0.4); padding: 20px 0; position: sticky; top: 0; z-index: 100; }
        nav { display: flex; justify-content: space-between; align-items: center; }
        .logo { font-size: 1.2rem; font-weight: 800; color: #f1f5f9; }
        .logo span { color: #38bdf8; }
        .nav-links { display: flex; gap: 24px; list-style: none; }
        .nav-links a { color: #94a3b8; font-weight: 500; font-size: 0.9rem; transition: color 0.2s; }
        .nav-links a:hover { color: #e2e8f0; }
        .hero { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 80px 0; text-align: center; }
        .hero h1 { font-size: 2.8rem; font-weight: 900; margin-bottom: 16px; letter-spacing: -1px; }
        .hero p { color: #cbd5e1; font-size: 1.15rem; max-width: 600px; margin: 0 auto; }
        .products { padding: 60px 0; }
        .product-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; margin-top: 40px; }
        .product-card { background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(51, 65, 85, 0.4); border-radius: 16px; padding: 32px; transition: all 0.3s ease; position: relative; }
        .product-card:hover { border-color: rgba(56, 189, 248, 0.5); transform: translateY(-4px); box-shadow: 0 25px 50px rgba(0,0,0,0.4); }
        .product-card.featured { border-color: rgba(56, 189, 248, 0.6); background: rgba(56, 189, 248, 0.05); }
        .badge { position: absolute; top: 16px; right: 16px; background: rgba(56, 189, 248, 0.15); color: #38bdf8; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; }
        .product-name { font-size: 1.4rem; font-weight: 800; color: #f1f5f9; margin-bottom: 8px; }
        .product-price { font-size: 2.8rem; font-weight: 900; color: #38bdf8; margin: 16px 0; letter-spacing: -1px; }
        .product-price span { font-size: 1rem; color: #64748b; font-weight: 500; }
        .product-features { list-style: none; margin: 24px 0; }
        .product-features li { padding: 10px 0; color: #cbd5e1; display: flex; align-items: center; gap: 10px; }
        .product-features li::before { content: "✓"; color: #10b981; font-weight: 700; }
        .btn { display: inline-block; padding: 12px 28px; border-radius: 10px; border: none; font-weight: 700; cursor: pointer; font-size: 0.95rem; transition: all 0.2s; text-align: center; }
        .btn-primary { background: #38bdf8; color: #0a0a0f; }
        .btn-primary:hover { background: #0ea5e9; transform: translateY(-1px); }
        .btn-secondary { background: rgba(51, 65, 85, 0.3); color: #e2e8f0; border: 1px solid rgba(51, 65, 85, 0.5); }
        .btn-secondary:hover { background: rgba(51, 65, 85, 0.5); }
        .reviews { padding: 60px 0; background: rgba(15, 23, 42, 0.4); }
        .reviews h2 { font-size: 2rem; font-weight: 800; text-align: center; margin-bottom: 40px; }
        .review-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .review-card { background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(51, 65, 85, 0.4); border-radius: 12px; padding: 24px; }
        .review-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .review-author { font-weight: 700; color: #f1f5f9; }
        .review-rating { color: #f59e0b; font-size: 0.9rem; }
        .review-body { color: #94a3b8; font-size: 0.95rem; }
        .review-date { color: #475569; font-size: 0.8rem; margin-top: 12px; }
        .faq { padding: 60px 0; }
        .faq h2 { font-size: 2rem; font-weight: 800; text-align: center; margin-bottom: 40px; }
        .faq-item { background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(51, 65, 85, 0.4); border-radius: 12px; padding: 24px; margin-bottom: 16px; }
        .faq-item h3 { font-size: 1.1rem; font-weight: 700; color: #f1f5f9; margin-bottom: 8px; }
        .faq-item p { color: #94a3b8; font-size: 0.95rem; }
        footer { background: #0f172a; padding: 40px 0; text-align: center; color: #64748b; font-size: 0.9rem; }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <nav>
                <div class="logo">Answer<span>First</span> AI</div>
                <ul class="nav-links">
                    <li><a href="/products">Products</a></li>
                    <li><a href="/portal">Client Portal</a></li>
                    <li><a href="/products#reviews">Reviews</a></li>
                    <li><a href="/products#faq">FAQ</a></li>
                </ul>
            </nav>
        </div>
    </header>

    <section class="hero">
        <div class="container">
            <h1>AI-Powered Appointment Setting</h1>
            <p>Fill your HVAC or roofing calendar with qualified appointments. 24/7 AI call answering, SMS follow-up, and guaranteed results.</p>
        </div>
    </section>

    <section class="products">
        <div class="container">
            <h2 style="font-size: 2rem; font-weight: 800; text-align: center; margin-bottom: 16px;">Choose Your Plan</h2>
            <p style="text-align: center; color: #94a3b8; max-width: 600px; margin: 0 auto;">No long-term contracts. Cancel anytime. 10-appointment guarantee on all plans.</p>
            <div class="product-grid">
                <div class="product-card">
                    <div class="product-name">Basic</div>
                    <div class="product-price">$1,500<span>/month</span></div>
                    <ul class="product-features">
                        <li>AI call answering</li>
                        <li>SMS follow-up</li>
                        <li>Calendar integration</li>
                        <li>Basic analytics</li>
                        <li>Email support</li>
                    </ul>
                    <a href="/portal/order?package=Basic" class="btn btn-secondary" style="width: 100%; display: block; text-align: center;">Get Started</a>
                </div>
                <div class="product-card featured">
                    <div class="badge">MOST POPULAR</div>
                    <div class="product-name">Premium</div>
                    <div class="product-price">$2,500<span>/month</span></div>
                    <ul class="product-features">
                        <li>Everything in Basic</li>
                        <li>24/7 coverage</li>
                        <li>Google Maps optimization</li>
                        <li>Bi-weekly strategy call</li>
                        <li>Priority support</li>
                    </ul>
                    <a href="/portal/order?package=Premium" class="btn btn-primary" style="width: 100%; display: block; text-align: center;">Get Started</a>
                </div>
                <div class="product-card">
                    <div class="product-name">Enterprise</div>
                    <div class="product-price">$4,000<span>/month</span></div>
                    <ul class="product-features">
                        <li>Everything in Premium</li>
                        <li>Multi-location support</li>
                        <li>Full local SEO</li>
                        <li>Paid ads management</li>
                        <li>Dedicated account manager</li>
                    </ul>
                    <a href="/portal/order?package=Enterprise" class="btn btn-secondary" style="width: 100%; display: block; text-align: center;">Get Started</a>
                </div>
            </div>
        </div>
    </section>

    <section class="reviews">
        <div class="container">
            <h2>What Clients Say</h2>
            <div class="review-grid">
                <div class="review-card">
                    <div class="review-header">
                        <div class="review-author">Mike R. — Phoenix HVAC</div>
                        <div class="review-rating">★★★★★</div>
                    </div>
                    <div class="review-body">"We went from missing 8-10 calls a day to booking 12 extra appointments in the first month. The AI sounds natural and our customers love it."</div>
                    <div class="review-date">Verified Client · Premium Plan</div>
                </div>
                <div class="review-card">
                    <div class="review-header">
                        <div class="review-author">Sarah T. — Mesa Roofing</div>
                        <div class="review-rating">★★★★★</div>
                    </div>
                    <div class="review-body">"The 24/7 coverage changed everything. We're no longer losing jobs to competitors who answer faster. ROI was clear within 2 weeks."</div>
                    <div class="review-date">Verified Client · Enterprise Plan</div>
                </div>
                <div class="review-card">
                    <div class="review-header">
                        <div class="review-author">James K. — Chandler AC</div>
                        <div class="review-rating">★★★★★</div>
                    </div>
                    <div class="review-body">"Setup was fast and the team walked us through everything. The SMS follow-up alone has recovered calls we would have never gotten back."</div>
                    <div class="review-date">Verified Client · Basic Plan</div>
                </div>
            </div>
        </div>
    </section>

    <section class="faq">
        <div class="container">
            <h2>Frequently Asked Questions</h2>
            <div class="faq-item">
                <h3>How fast can you set this up?</h3>
                <p>Most clients are fully live within 7 days. We configure your AI receptionist, connect your calendar, and test the flow before going live.</p>
            </div>
            <div class="faq-item">
                <h3>What if I don't get 10 appointments?</h3>
                <p>We guarantee 10+ qualified appointments in your first 30 days. If we miss that, you get a full refund. No hoops, no fine print.</p>
            </div>
            <div class="faq-item">
                <h3>Do I need to install anything?</h3>
                <p>No. Everything runs in the cloud. We handle the tech. You just show up to the appointments we book.</p>
            </div>
            <div class="faq-item">
                <h3>Can I cancel anytime?</h3>
                <p>Yes. No long-term contracts. Cancel whenever you want and keep everything we've built for you.</p>
            </div>
            <div class="faq-item">
                <h3>How do I access my client portal?</h3>
                <p>After signing up, you'll get login credentials to your private dashboard where you can view appointments, analytics, and support tickets.</p>
            </div>
        </div>
    </section>

    <footer>
        <div class="container">
            <p>© 2026 AnswerFirst AI. All rights reserved.</p>
            <p style="margin-top: 10px;">
                <a href="/products">Products</a> · <a href="/portal">Client Portal</a> · <a href="mailto:azelt.marketing@gmail.com">Contact</a>
            </p>
        </div>
    </footer>
</body>
</html>
"""

PORTAL_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AnswerFirst AI — Client Portal</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: #0a0a0f; color: #e2e8f0; line-height: 1.6; min-height: 100vh; display: flex; flex-direction: column; }
        a { color: #38bdf8; text-decoration: none; }
        header { background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(51, 65, 85, 0.4); padding: 20px 0; }
        nav { max-width: 1200px; margin: 0 auto; padding: 0 24px; display: flex; justify-content: space-between; align-items: center; }
        .logo { font-size: 1.2rem; font-weight: 800; color: #f1f5f9; }
        .logo span { color: #38bdf8; }
        .container { max-width: 1200px; margin: 0 auto; padding: 40px 24px; flex: 1; }
        .card { background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(51, 65, 85, 0.4); border-radius: 16px; padding: 32px; margin-bottom: 24px; }
        .card h2 { font-size: 1.4rem; font-weight: 800; margin-bottom: 16px; color: #f1f5f9; }
        .btn { display: inline-block; padding: 12px 28px; border-radius: 10px; border: none; font-weight: 700; cursor: pointer; font-size: 0.95rem; transition: all 0.2s; }
        .btn-primary { background: #38bdf8; color: #0a0a0f; }
        .btn-secondary { background: rgba(51, 65, 85, 0.3); color: #e2e8f0; border: 1px solid rgba(51, 65, 85, 0.5); }
        input, textarea, select { width: 100%; padding: 12px 16px; background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(51, 65, 85, 0.5); border-radius: 10px; color: #e2e8f0; font-family: inherit; margin-bottom: 16px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; font-size: 0.9rem; color: #cbd5e1; }
        .grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 24px; }
        .stat-value { font-size: 2.2rem; font-weight: 900; color: #38bdf8; letter-spacing: -0.5px; }
        .stat-label { color: #64748b; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; margin-top: 8px; }
        table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
        th { text-align: left; padding: 14px 12px; color: #64748b; font-weight: 600; border-bottom: 1px solid rgba(51, 65, 85, 0.5); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; }
        td { padding: 14px 12px; border-bottom: 1px solid rgba(30, 41, 59, 0.5); }
        .badge { padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
        .badge-green { background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }
        .badge-yellow { background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }
        .badge-blue { background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }
        .hidden { display: none !important; }
        .error { color: #ef4444; font-size: 0.85rem; margin-top: -8px; margin-bottom: 12px; }
        .success { color: #10b981; font-size: 0.9rem; margin-bottom: 12px; }
    </style>
</head>
<body>
    <header>
        <nav>
            <div class="logo">Answer<span>First</span> AI · Client Portal</div>
            <div id="nav-auth">
                <a href="/products" class="btn btn-secondary">← Back to Products</a>
            </div>
        </nav>
    </header>

    <div class="container">
        <!-- Auth -->
        <div id="auth-section">
            <div class="card" style="max-width: 420px; margin: 60px auto;">
                <h2 id="auth-title">Client Login</h2>
                <form id="auth-form" onsubmit="return handleAuth(event)">
                    <label>Email</label>
                    <input type="email" id="auth-email" required placeholder="you@company.com">
                    <label>Password</label>
                    <input type="password" id="auth-password" required placeholder="••••••••">
                    <div id="auth-error" class="error hidden"></div>
                    <button type="submit" class="btn btn-primary" style="width: 100%;">Log In</button>
                </form>
                <p style="text-align: center; margin-top: 16px; color: #94a3b8; font-size: 0.9rem;">
                    <a href="#" onclick="showRegister()">Create an account</a> · <a href="/products">Back to products</a>
                </p>
            </div>
        </div>

        <!-- Portal -->
        <div id="portal-section" class="hidden">
            <div class="grid-2">
                <div class="card">
                    <div class="stat-label">Current Plan</div>
                    <div class="stat-value" id="client-plan">--</div>
                </div>
                <div class="card">
                    <div class="stat-label">Status</div>
                    <div class="stat-value" id="client-status">--</div>
                </div>
                <div class="card">
                    <div class="stat-label">Member Since</div>
                    <div class="stat-value" id="client-since">--</div>
                </div>
                <div class="card">
                    <div class="stat-label">Support</div>
                    <div class="stat-value" style="font-size: 1.4rem;">azelt.marketing@gmail.com</div>
                </div>
            </div>

            <div class="card">
                <h2>Your Orders</h2>
                <div style="overflow-x: auto;">
                    <table>
                        <thead>
                            <tr><th>Order</th><th>Package</th><th>Amount</th><th>Status</th><th>Date</th></tr>
                        </thead>
                        <tbody id="orders-tbody"></tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <h2>Leave a Review</h2>
                <form onsubmit="return submitReview(event)">
                    <label>Rating</label>
                    <select id="review-rating" required>
                        <option value="5">★★★★★ (5)</option>
                        <option value="4">★★★★☆ (4)</option>
                        <option value="3">★★★☆☆ (3)</option>
                        <option value="2">★★☆☆☆ (2)</option>
                        <option value="1">★☆☆☆☆ (1)</option>
                    </select>
                    <label>Title</label>
                    <input type="text" id="review-title" required placeholder="Great service">
                    <label>Review</label>
                    <textarea id="review-body" rows="4" required placeholder="Share your experience..."></textarea>
                    <div id="review-result" class="success hidden"></div>
                    <button type="submit" class="btn btn-primary">Submit Review</button>
                </form>
            </div>

            <div style="text-align: center; margin-top: 24px;">
                <button class="btn btn-secondary" onclick="logout()">Log Out</button>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = '/portal/api';
        let currentClient = null;

        async function handleAuth(e) {
            e.preventDefault();
            const email = document.getElementById('auth-email').value.trim();
            const password = document.getElementById('auth-password').value;
            const errorEl = document.getElementById('auth-error');
            
            try {
                const resp = await fetch(`${API_BASE}/login`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email, password})
                });
                const data = await resp.json();
                if (!resp.ok) {
                    errorEl.textContent = data.error || 'Login failed';
                    errorEl.classList.remove('hidden');
                    return false;
                }
                currentClient = data.client;
                document.getElementById('auth-section').classList.add('hidden');
                document.getElementById('portal-section').classList.remove('hidden');
                loadPortal();
                return false;
            } catch (err) {
                errorEl.textContent = 'Network error';
                errorEl.classList.remove('hidden');
                return false;
            }
        }

        async function loadPortal() {
            if (!currentClient) return;
            document.getElementById('client-plan').textContent = currentClient.package || 'Basic';
            document.getElementById('client-status').textContent = currentClient.status || 'active';
            document.getElementById('client-since').textContent = currentClient.created_at ? new Date(currentClient.created_at).toLocaleDateString() : '--';
            
            // Load orders
            const ordersResp = await fetch(`${API_BASE}/orders?client_id=${currentClient.id}`);
            const orders = await ordersResp.json();
            const tbody = document.getElementById('orders-tbody');
            tbody.innerHTML = orders.map(o => `
                <tr>
                    <td>#${o.id}</td>
                    <td><span class="badge badge-blue">${o.package}</span></td>
                    <td>$${o.amount}</td>
                    <td><span class="badge ${o.status === 'paid' ? 'badge-green' : o.status === 'pending' ? 'badge-yellow' : 'badge-red'}">${o.status}</span></td>
                    <td>${o.created_at ? new Date(o.created_at).toLocaleDateString() : '--'}</td>
                </tr>
            `).join('') || '<tr><td colspan="5" style="color:#64748b;">No orders yet</td></tr>';
        }

        async function submitReview(e) {
            e.preventDefault();
            if (!currentClient) return false;
            const rating = document.getElementById('review-rating').value;
            const title = document.getElementById('review-title').value.trim();
            const body = document.getElementById('review-body').value.trim();
            const resultEl = document.getElementById('review-result');
            
            const resp = await fetch(`${API_BASE}/reviews`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({client_id: currentClient.id, rating: parseInt(rating), title, body})
            });
            const data = await resp.json();
            if (resp.ok) {
                resultEl.textContent = 'Review submitted for moderation. Thank you!';
                resultEl.classList.remove('hidden');
                document.getElementById('review-title').value = '';
                document.getElementById('review-body').value = '';
            } else {
                resultEl.textContent = data.error || 'Failed to submit review';
                resultEl.classList.remove('hidden');
            }
            return false;
        }

        async function showRegister() {
            const form = document.getElementById('auth-form');
            const title = document.getElementById('auth-title');
            const errorEl = document.getElementById('auth-error');
            errorEl.classList.add('hidden');
            
            if (title.textContent === 'Client Login') {
                title.textContent = 'Create Account';
                form.insertAdjacentHTML('beforeend', `
                    <label>Business Name</label>
                    <input type="text" id="reg-business" required placeholder="Your HVAC Company">
                    <label>Contact Name</label>
                    <input type="text" id="reg-name" required placeholder="John Smith">
                    <label>Phone</label>
                    <input type="tel" id="reg-phone" placeholder="(602) 555-0100">
                    <button type="submit" class="btn btn-primary" style="width: 100%;">Create Account</button>
                `);
                title.dataset.mode = 'register';
            } else {
                title.textContent = 'Client Login';
                const extras = form.querySelectorAll('#reg-business, #reg-name, #reg-phone');
                extras.forEach(el => el.remove());
                title.dataset.mode = 'login';
            }
            return false;
        }

        async function logout() {
            await fetch(`${API_BASE}/logout`, {method: 'POST'});
            currentClient = null;
            location.reload();
        }

        // Override form submit for register
        document.getElementById('auth-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const mode = document.getElementById('auth-title').dataset.mode || 'login';
            const email = document.getElementById('auth-email').value.trim();
            const password = document.getElementById('auth-password').value;
            const errorEl = document.getElementById('auth-error');
            
            if (mode === 'register') {
                const business = document.getElementById('reg-business').value.trim();
                const name = document.getElementById('reg-name').value.trim();
                const phone = document.getElementById('reg-phone').value.trim();
                
                const resp = await fetch(`${API_BASE}/register`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email, password, business_name: business, contact_name: name, phone})
                });
                const data = await resp.json();
                if (!resp.ok) {
                    errorEl.textContent = data.error || 'Registration failed';
                    errorEl.classList.remove('hidden');
                    return;
                }
                currentClient = data.client;
                document.getElementById('auth-section').classList.add('hidden');
                document.getElementById('portal-section').classList.remove('hidden');
                loadPortal();
            } else {
                await handleAuth(e);
            }
        });
    </script>
</body>
</html>
"""

ORDER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AnswerFirst AI — Complete Your Order</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: #0a0a0f; color: #e2e8f0; line-height: 1.6; }
        .container { max-width: 640px; margin: 0 auto; padding: 60px 24px; }
        .card { background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(51, 65, 85, 0.4); border-radius: 16px; padding: 32px; margin-bottom: 24px; }
        h1 { font-size: 1.8rem; font-weight: 900; margin-bottom: 8px; }
        .package-name { color: #38bdf8; font-size: 1.2rem; font-weight: 700; margin-bottom: 16px; }
        .price { font-size: 2.4rem; font-weight: 900; color: #f1f5f9; margin-bottom: 24px; }
        input, textarea, select { width: 100%; padding: 12px 16px; background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(51, 65, 85, 0.5); border-radius: 10px; color: #e2e8f0; font-family: inherit; margin-bottom: 16px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; font-size: 0.9rem; color: #cbd5e1; }
        .btn { display: inline-block; padding: 14px 32px; border-radius: 10px; border: none; font-weight: 700; cursor: pointer; font-size: 1rem; transition: all 0.2s; width: 100%; text-align: center; }
        .btn-primary { background: #38bdf8; color: #0a0a0f; }
        .btn-secondary { background: rgba(51, 65, 85, 0.3); color: #e2e8f0; border: 1px solid rgba(51, 65, 85, 0.5); }
        .error { color: #ef4444; font-size: 0.9rem; margin-bottom: 12px; }
        .success { color: #10b981; font-size: 0.95rem; margin-bottom: 12px; }
        .paypal-note { background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 10px; padding: 16px; margin-bottom: 16px; font-size: 0.9rem; color: #cbd5e1; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>Complete Your Order</h1>
            <div class="package-name" id="order-package">Basic</div>
            <div class="price" id="order-price">$1,500<span style="font-size:1rem;color:#64748b;font-weight:500;">/month</span></div>
            
            <div class="paypal-note">
                After submitting, you'll be redirected to <strong>https://www.paypal.com/ncp/payment/GCMFXKYWWZKG4</strong> to complete payment securely with PayPal. No payment is taken on this page.
            </div>

            <form id="order-form" onsubmit="return submitOrder(event)">
                <label>Full Name</label>
                <input type="text" id="order-name" required placeholder="John Smith">
                <label>Business Name</label>
                <input type="text" id="order-business" required placeholder="ABC HVAC">
                <label>Email</label>
                <input type="email" id="order-email" required placeholder="john@abchvac.com">
                <label>Phone</label>
                <input type="tel" id="order-phone" required placeholder="(602) 555-0100">
                <label>How did you hear about us?</label>
                <select id="order-source">
                    <option>Google Search</option>
                    <option>Referral</option>
                    <option>Social Media</option>
                    <option>Email</option>
                    <option>Other</option>
                </select>
                <label>Notes (optional)</label>
                <textarea id="order-notes" rows="3" placeholder="Anything we should know before setup?"></textarea>
                <div id="order-error" class="error hidden"></div>
                <div id="order-success" class="success hidden"></div>
                <button type="submit" class="btn btn-primary">Continue to Payment</button>
            </form>
            <p style="text-align: center; margin-top: 20px; font-size: 0.9rem; color: #64748b;">
                <a href="/products">← Back to products</a>
            </p>
        </div>
    </div>

    <script>
        const params = new URLSearchParams(location.search);
        const pkg = params.get('package') || 'Basic';
        const prices = {Basic: 1500, Premium: 2500, Enterprise: 4000};
        document.getElementById('order-package').textContent = pkg;
        document.getElementById('order-price').innerHTML = `$${prices[pkg] || 1500}<span style="font-size:1rem;color:#64748b;font-weight:500;">/month</span>`;

        async function submitOrder(e) {
            e.preventDefault();
            const data = {
                package: pkg,
                amount: prices[pkg] || 1500,
                name: document.getElementById('order-name').value.trim(),
                business_name: document.getElementById('order-business').value.trim(),
                email: document.getElementById('order-email').value.trim(),
                phone: document.getElementById('order-phone').value.trim(),
                source: document.getElementById('order-source').value,
                notes: document.getElementById('order-notes').value.trim()
            };
            
            const resp = await fetch('/portal/api/orders', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            const result = await resp.json();
            const errorEl = document.getElementById('order-error');
            const successEl = document.getElementById('order-success');
            
            if (!resp.ok) {
                errorEl.textContent = result.error || 'Order failed';
                errorEl.classList.remove('hidden');
                successEl.classList.add('hidden');
                return false;
            }
            
            const paypalLink = result.payment_link || `https://www.paypal.com/ncp/payment/GCMFXKYWWZKG4`;
            successEl.innerHTML = `Order created! Complete your payment here: <a href="${paypalLink}" target="_blank" rel="noopener">${paypalLink}</a>`;
            successEl.classList.remove('hidden');
            errorEl.classList.add('hidden');
            document.getElementById('order-form').reset();
            return false;
        }
    </script>
</body>
</html>
"""

REVIEWS_API_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AnswerFirst AI — Reviews</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: #0a0a0f; color: #e2e8f0; line-height: 1.6; }
        .container { max-width: 1000px; margin: 0 auto; padding: 60px 24px; }
        h1 { font-size: 2.2rem; font-weight: 900; margin-bottom: 8px; }
        .subtitle { color: #94a3b8; margin-bottom: 40px; }
        .review { background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(51, 65, 85, 0.4); border-radius: 12px; padding: 24px; margin-bottom: 16px; }
        .review-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .review-author { font-weight: 700; color: #f1f5f9; }
        .review-rating { color: #f59e0b; }
        .review-body { color: #cbd5e1; }
        .review-date { color: #475569; font-size: 0.85rem; margin-top: 12px; }
        .back { display: inline-block; margin-bottom: 24px; color: #94a3b8; }
        .back:hover { color: #e2e8f0; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/products" class="back">← Back to Products</a>
        <h1>Client Reviews</h1>
        <p class="subtitle">Real feedback from real clients.</p>
        <div id="reviews"></div>
    </div>
    <script>
        async function load() {
            const resp = await fetch('/portal/api/reviews/public');
            const reviews = await resp.json();
            document.getElementById('reviews').innerHTML = reviews.map(r => `
                <div class="review">
                    <div class="review-header">
                        <div class="review-author">${r.business_name || 'Client'}</div>
                        <div class="review-rating">${'★'.repeat(r.rating)}${'☆'.repeat(5-r.rating)}</div>
                    </div>
                    <div class="review-body">${r.body}</div>
                    <div class="review-date">${r.created_at ? new Date(r.created_at).toLocaleDateString() : ''}</div>
                </div>
            `).join('') || '<p style="color:#64748b;">No reviews yet.</p>';
        }
        load();
    </script>
</body>
</html>
"""

# ==================== API ROUTES ====================

@app.route("/portal")
def portal_home():
    token = request.cookies.get("portal_token")
    client = get_client_from_session(token) if token else None
    if client:
        return redirect("/portal/dashboard")
    return redirect("/portal/login")


@app.route("/portal/login")
def portal_login():
    return render_template_string(PORTAL_HTML)


@app.route("/portal/register", methods=["POST"])
def portal_register():
    data = request.json or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    business_name = data.get("business_name", "")
    contact_name = data.get("contact_name", "")
    phone = data.get("phone", "")
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    db = get_db()
    existing = db.execute("SELECT id FROM clients WHERE email = ?", (email,)).fetchone()
    if existing:
        db.close()
        return jsonify({"error": "Email already registered"}), 400
    
    db.execute(
        "INSERT INTO clients (email, password_hash, business_name, contact_name, phone) VALUES (?, ?, ?, ?, ?)",
        (email, hash_password(password), business_name, contact_name, phone)
    )
    db.commit()
    client = db.execute("SELECT * FROM clients WHERE email = ?", (email,)).fetchone()
    db.close()
    
    token = create_session(client["id"])
    resp = jsonify({"client": dict(client)})
    resp.set_cookie("portal_token", token, max_age=7*24*60*60, httponly=True, samesite="Lax")
    return resp


@app.route("/portal/login", methods=["POST"])
def portal_login_post():
    data = request.json or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    
    db = get_db()
    client = db.execute("SELECT * FROM clients WHERE email = ?", (email,)).fetchone()
    db.close()
    
    if not client or not verify_password(password, client["password_hash"]):
        return jsonify({"error": "Invalid email or password"}), 401
    
    token = create_session(client["id"])
    resp = jsonify({"client": dict(client)})
    resp.set_cookie("portal_token", token, max_age=7*24*60*60, httponly=True, samesite="Lax")
    return resp


@app.route("/portal/logout", methods=["POST"])
def portal_logout():
    token = request.cookies.get("portal_token")
    if token:
        db = get_db()
        db.execute("DELETE FROM sessions WHERE token = ?", (token,))
        db.commit()
        db.close()
    resp = jsonify({"status": "ok"})
    resp.delete_cookie("portal_token")
    return resp


@app.route("/portal/dashboard")
def portal_dashboard():
    token = request.cookies.get("portal_token")
    client = get_client_from_session(token) if token else None
    if not client:
        return redirect("/portal/login")
    return render_template_string(PORTAL_HTML, client=client)


@app.route("/portal/order")
def portal_order():
    return render_template_string(ORDER_HTML)


@app.route("/portal/reviews")
def portal_reviews():
    return render_template_string(REVIEWS_API_HTML)


@app.route("/portal/api/orders", methods=["POST"])
def portal_create_order():
    data = request.json or {}
    package = data.get("package", "Basic")
    amount = data.get("amount", 0)
    name = data.get("name", "")
    business_name = data.get("business_name", "")
    email = data.get("email", "").strip().lower()
    phone = data.get("phone", "")
    source = data.get("source", "web")
    notes = data.get("notes", "")
    
    if not email or not business_name:
        return jsonify({"error": "Email and business name required"}), 400
    
    # Create client if not exists
    db = get_db()
    existing = db.execute("SELECT id FROM clients WHERE email = ?", (email,)).fetchone()
    if not existing:
        password_hash = hash_password(secrets.token_urlsafe(12))
        db.execute(
            "INSERT INTO clients (email, password_hash, business_name, contact_name, phone, package) VALUES (?, ?, ?, ?, ?, ?)",
            (email, password_hash, business_name, name, phone, package)
        )
        db.commit()
        client = db.execute("SELECT * FROM clients WHERE email = ?", (email,)).fetchone()
        client_id = client["id"]
    else:
        client_id = existing["id"]
        db.execute("UPDATE clients SET package = ?, updated_at = ? WHERE id = ?", (package, datetime.now().isoformat(), client_id))
    
    # Create order
    payment_link = "https://www.paypal.com/ncp/payment/GCMFXKYWWZKG4"
    db.execute(
        "INSERT INTO orders (client_id, package, amount, payment_method, payment_link, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (client_id, package, amount, "paypal", payment_link, notes)
    )
    db.commit()
    order_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()
    
    # In production: send email with payment link
    # For now, return the link directly
    return jsonify({
        "status": "created",
        "order_id": order_id,
        "payment_link": payment_link,
        "message": "Order created. Payment link would be emailed in production."
    }), 201


@app.route("/portal/api/orders")
def portal_get_orders():
    client_id = request.args.get("client_id", type=int)
    if not client_id:
        return jsonify({"error": "client_id required"}), 400
    
    db = get_db()
    orders = db.execute("SELECT * FROM orders WHERE client_id = ? ORDER BY created_at DESC", (client_id,)).fetchall()
    db.close()
    return jsonify([dict(r) for r in orders])


@app.route("/portal/api/reviews", methods=["POST"])
def portal_create_review():
    data = request.json or {}
    client_id = data.get("client_id")
    rating = data.get("rating", 5)
    title = data.get("title", "")
    body = data.get("body", "")
    
    if not client_id:
        return jsonify({"error": "client_id required"}), 400
    
    db = get_db()
    db.execute(
        "INSERT INTO reviews (client_id, rating, title, body) VALUES (?, ?, ?, ?)",
        (client_id, rating, title, body)
    )
    db.commit()
    review_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()
    return jsonify({"status": "created", "review_id": review_id}), 201


@app.route("/portal/api/reviews/public")
def portal_public_reviews():
    db = get_db()
    reviews = db.execute("""
        SELECT r.*, c.business_name 
        FROM reviews r 
        JOIN clients c ON r.client_id = c.id 
        WHERE r.status = 'approved' 
        ORDER BY r.created_at DESC
    """).fetchall()
    db.close()
    return jsonify([dict(r) for r in reviews])


@app.route("/products")
def products_public():
    return render_template_string(PRODUCTS_HTML)


@app.route("/portal/api/leads/import", methods=["POST"])
def portal_import_leads():
    token = request.cookies.get("portal_token")
    client = get_client_from_session(token) if token else None
    if not client:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json or {}
    leads = data.get("leads", [])
    # Integration point: import leads into CRM
    return jsonify({"imported": len(leads), "status": "ok"})


if __name__ == "__main__":
    init_db()
    print("[+] Client portal initialized at", DB_PATH)
    app.run(host="127.0.0.1", port=5060, debug=False)
