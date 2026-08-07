"""AnswerFirst AI - Vercel Serverless API
This is a lightweight version of the unified backend for Vercel deployment.
"""

import os, sqlite3, secrets, hashlib, smtplib, ssl, json
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get('PORTAL_SECRET', secrets.token_hex(32))

# Vercel uses /tmp for writable filesystem
DB_PATH = os.environ.get('PORTAL_DB_PATH')
if not DB_PATH:
    # Use /tmp on Vercel, local file on Windows
    tmp_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..')
    DB_PATH = os.path.join(tmp_dir, 'portal.db')

# SMTP config
GMAIL_SENDER = os.environ.get('GMAIL_SENDER', 'azelt.marketing@gmail.com')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
GMAIL_SMTP_SERVER = os.environ.get('GMAIL_SMTP_SERVER', 'smtp.gmail.com')
GMAIL_SMTP_PORT = int(os.environ.get('GMAIL_SMTP_PORT', '587'))

SMS_CARRIER_GATEWAYS = {
    'att': 'txt.att.net',
    'verizon': 'vtext.com',
    'tmobile': 'tmomail.net',
    'sprint': 'messaging.sprintpcs.com',
    'uscellular': 'email.uscc.net',
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Create essential tables
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
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            password_reset_token TEXT DEFAULT '',
            password_reset_expires TEXT DEFAULT '',
            sms_enabled INTEGER DEFAULT 0,
            sms_phone TEXT DEFAULT '',
            sms_carrier TEXT DEFAULT '',
            sms_notifications INTEGER DEFAULT 0,
            email_verified INTEGER DEFAULT 0,
            verification_token TEXT DEFAULT ''
        )
    """)
    # Add more tables as needed...
    conn.commit()
    conn.close()

# Initialize DB on import
init_db()

# ===== AUTH ROUTES =====

@app.route('/portal/api/register', methods=['POST'])
def register():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    business_name = data.get('business_name', '')
    contact_name = data.get('name', '')
    phone = data.get('phone', '')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        db = get_db()
        db.execute(
            'INSERT INTO clients (email, password_hash, business_name, contact_name, phone) VALUES (?, ?, ?, ?, ?)',
            (email, password_hash, business_name, contact_name, phone)
        )
        db.commit()
        client_id = db.lastrowid
        db.close()
        
        token = secrets.token_urlsafe(32)
        return jsonify({'status': 'ok', 'client_id': client_id, '_session_token': token}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already registered'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/portal/api/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        db = get_db()
        client = db.execute(
            'SELECT id, email, business_name FROM clients WHERE email = ? AND password_hash = ?',
            (email, password_hash)
        ).fetchone()
        db.close()
        
        if not client:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        token = secrets.token_urlsafe(32)
        return jsonify({
            'status': 'ok',
            'client_id': client['id'],
            'email': client['email'],
            'business_name': client['business_name'],
            '_session_token': token
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/portal/api/logout', methods=['POST'])
def logout_api():
    token = None
    if request.is_json:
        token = (request.json or {}).get('token')
    if not token:
        token = request.cookies.get('portal_token')
    if token:
        try:
            db = get_db()
            db.execute('DELETE FROM sessions WHERE token = ?', (token,))
            db.commit()
            db.close()
        except Exception:
            pass
    resp = jsonify({'status': 'ok'})
    resp.delete_cookie('portal_token')
    return resp

@app.route('/portal/api/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({'error': 'Email required'}), 400
    
    # In production, send actual reset email
    # For now, just acknowledge
    return jsonify({'status': 'ok', 'message': 'If an account exists, a reset email was sent.'}), 200

@app.route('/portal/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'db': DB_PATH}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5070, debug=False)
