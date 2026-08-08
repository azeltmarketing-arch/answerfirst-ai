"""
AnswerFirst AI - Unified Public Site + Client Portal
Port: 5070
"""

from flask import Flask, render_template_string, request, jsonify, redirect, url_for, make_response, send_from_directory
from flask_cors import CORS
import jwt
import sqlite3, os, secrets, hashlib, smtplib, ssl
from datetime import datetime, timedelta
from email.mime.text import MIMEText

JWT_SECRET = os.environ.get('JWT_SECRET', secrets.token_hex(32))

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=[
    "https://answerfirst-ai.vercel.app",
    "https://*.vercel.app",
    "http://localhost:5050",
    "http://127.0.0.1:5050",
    "http://localhost:4173",
    "http://localhost:5173",
])
app.secret_key = os.environ.get("PORTAL_SECRET", secrets.token_hex(32))
DB_PATH = os.environ.get("PORTAL_DB_PATH", os.path.join(os.path.dirname(__file__), "portal.db"))


# Vercel serverless optimization
if os.environ.get('VERCEL'):
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


# ===================== SMTP / SMS =====================

SMS_CARRIER_GATEWAYS = {
    "att": "txt.att.net",
    "verizon": "vtext.com",
    "tmobile": "tmomail.net",
    "sprint": "messaging.sprintpcs.com",
    "uscellular": "email.uscc.net",
}

GMAIL_SENDER = os.environ.get("GMAIL_SENDER", "azelt.marketing@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
GMAIL_SMTP_SERVER = os.environ.get("GMAIL_SMTP_SERVER", "smtp.gmail.com")
GMAIL_SMTP_PORT = int(os.environ.get("GMAIL_SMTP_PORT", "587"))


def send_sms_via_email(to_phone: str, carrier_gateway: str, message: str):
    sender_email = GMAIL_SENDER
    sender_password = GMAIL_APP_PASSWORD
    if not sender_password:
        return {"status": "error", "error": "Gmail app password not configured."}

    gateway = SMS_CARRIER_GATEWAYS.get(carrier_gateway)
    if not gateway:
        return {"status": "error", "error": "Unsupported carrier."}

    digits = "".join(ch for ch in str(to_phone) if ch.isdigit())
    if len(digits) < 10:
        return {"status": "error", "error": "Invalid phone number."}

    to_address = f"{digits}@{gateway}"
    subject = ""
    body = message or ""
    try:
        msg = MIMEText(body)
        msg["From"] = sender_email
        msg["To"] = to_address
        msg["Subject"] = subject

        context = ssl.create_default_context()
        with smtplib.SMTP(GMAIL_SMTP_SERVER, GMAIL_SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_address, msg.as_string())

        message_id = f"<{datetime.now().timestamp()}@{GMAIL_SMTP_SERVER}>"
        return {"status": "sent", "to": to_address, "message_id": message_id, "sent_at": datetime.now().isoformat()}
    except smtplib.SMTPAuthenticationError:
        return {"status": "error", "error": "SMTP auth failed. Check app password."}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def log_activity(client_id: int, activity_type: str, title: str, body: str = "", meta: str = ""):
    try:
        db = get_db()
        db.execute(
            "INSERT INTO activities (client_id, type, title, body, meta) VALUES (?, ?, ?, ?, ?)",
            (client_id, activity_type, title, body, meta),
        )
        db.commit()
        db.close()
    except Exception:
        pass

# ===================== DATABASE =====================

def create_tables():
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
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            password_reset_token TEXT DEFAULT '',
            password_reset_expires TEXT DEFAULT '',
            sms_enabled INTEGER DEFAULT 0,
            sms_phone TEXT DEFAULT '',
            sms_carrier TEXT DEFAULT '',
            sms_notifications INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT DEFAULT '',
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            company TEXT DEFAULT '',
            volume TEXT DEFAULT '',
            source TEXT DEFAULT 'website_contact',
            status TEXT DEFAULT 'new',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
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
        CREATE TABLE IF NOT EXISTS order_intents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            email TEXT DEFAULT '',
            name TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            company TEXT DEFAULT '',
            volume TEXT DEFAULT '',
            account_token TEXT UNIQUE DEFAULT '',
            status TEXT DEFAULT 'awaiting_account',
            expires_at TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id)
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
    c.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            title TEXT DEFAULT '',
            scheduled_at TEXT DEFAULT '',
            status TEXT DEFAULT 'scheduled',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            name TEXT DEFAULT '',
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            company TEXT DEFAULT '',
            source TEXT DEFAULT '',
            campaign TEXT DEFAULT '',
            utm_source TEXT DEFAULT '',
            utm_medium TEXT DEFAULT '',
            utm_campaign TEXT DEFAULT '',
            status TEXT DEFAULT 'new',
            score INTEGER DEFAULT 0,
            assigned_to TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            follow_up_count INTEGER DEFAULT 0,
            last_contacted_at TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            subject TEXT DEFAULT '',
            body TEXT DEFAULT '',
            status TEXT DEFAULT 'open',
            priority TEXT DEFAULT 'medium',
            sla_tier TEXT DEFAULT 'standard',
            sla_deadline TEXT DEFAULT '',
            assigned_to TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            contact_name TEXT DEFAULT '',
            contact_phone TEXT DEFAULT '',
            outcome TEXT DEFAULT 'booked',
            duration_seconds INTEGER DEFAULT 0,
            transcript TEXT DEFAULT '',
            recording_url TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            type TEXT DEFAULT 'info',
            title TEXT DEFAULT '',
            body TEXT DEFAULT '',
            meta TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS onboarding (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            step_title TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            due_at TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            name TEXT DEFAULT '',
            source TEXT DEFAULT '',
            spend REAL DEFAULT 0,
            leads INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS satisfaction_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS upsell_opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            title TEXT DEFAULT '',
            description TEXT DEFAULT '',
            current_package TEXT DEFAULT 'Basic',
            suggested_package TEXT DEFAULT 'Premium',
            savings TEXT DEFAULT '',
            status TEXT DEFAULT 'new',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            filename TEXT DEFAULT '',
            file_type TEXT DEFAULT '',
            file_size INTEGER DEFAULT 0,
            file_url TEXT DEFAULT '',
            description TEXT DEFAULT '',
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)
    conn.commit()
    conn.close()
    _migrate_db()



def _migrate_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE clients ADD COLUMN password_reset_token TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE clients ADD COLUMN password_reset_expires TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE clients ADD COLUMN email_verified INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE clients ADD COLUMN email_verification_token TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE clients ADD COLUMN satisfaction_score INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE clients ADD COLUMN satisfaction_notes TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE onboarding ADD COLUMN step_key TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE onboarding ADD COLUMN description TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE onboarding ADD COLUMN updated_at TEXT DEFAULT CURRENT_TIMESTAMP")
    except Exception:
        pass
    conn.commit()
    conn.close()
    _migrate_sms_prefs()


def _migrate_sms_prefs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE clients ADD COLUMN sms_enabled INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE clients ADD COLUMN sms_phone TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE clients ADD COLUMN sms_carrier TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE clients ADD COLUMN sms_notifications INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE tickets ADD COLUMN priority TEXT DEFAULT 'medium'")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE tickets ADD COLUMN sla_tier TEXT DEFAULT 'standard'")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE tickets ADD COLUMN sla_deadline TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE tickets ADD COLUMN assigned_to TEXT DEFAULT ''")
    except Exception:
        pass
    # Lead schema extensions
    lead_cols = [
        ("company", "TEXT DEFAULT ''"),
        ("campaign", "TEXT DEFAULT ''"),
        ("utm_source", "TEXT DEFAULT ''"),
        ("utm_medium", "TEXT DEFAULT ''"),
        ("utm_campaign", "TEXT DEFAULT ''"),
        ("score", "INTEGER DEFAULT 0"),
        ("assigned_to", "TEXT DEFAULT ''"),
        ("notes", "TEXT DEFAULT ''"),
        ("follow_up_count", "INTEGER DEFAULT 0"),
        ("last_contacted_at", "TEXT DEFAULT ''"),
    ]
    for col, typ in lead_cols:
        try:
            c.execute(f"ALTER TABLE leads ADD COLUMN {col} {typ}")
        except Exception:
            pass
    # Follow-up sequences table
    c.execute("""
        CREATE TABLE IF NOT EXISTS lead_sequences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            step_number INTEGER DEFAULT 1,
            template_name TEXT DEFAULT '',
            channel TEXT DEFAULT 'email',
            scheduled_at TEXT DEFAULT '',
            sent_at TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()


def score_lead(lead: dict) -> int:
    score = 0
    if lead.get('email'):
        score += 10
    if lead.get('phone'):
        score += 10
    if lead.get('company'):
        score += 10
    source = (lead.get('source') or '').lower()
    if source in {'referral', 'organic'}:
        score += 20
    elif source in {'ads', 'paid'}:
        score += 5
    campaign = (lead.get('campaign') or '').lower()
    if campaign:
        score += 5
    notes = (lead.get('notes') or '').lower()
    high_intent = ['budget','ready','buy','purchase','hire','timeline','asap','urgent']
    if any(k in notes for k in high_intent):
        score += 20
    return min(score, 100)


def route_lead(lead: dict):
    score = score_lead(lead)
    if score >= 70:
        return {'tier': 'hot', 'suggested_action': 'call_now', 'priority': 'high'}
    if score >= 40:
        return {'tier': 'warm', 'suggested_action': 'follow_up_email', 'priority': 'medium'}
    return {'tier': 'cold', 'suggested_action': 'nurture_sequence', 'priority': 'low'}


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=30000')
    except Exception:
        pass
    try:
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clients'")
        if not c.fetchone():
            create_tables()
    except Exception:
        create_tables()
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def create_jwt(client_id: int) -> str:
    payload = {
        'client_id': client_id,
        'exp': datetime.now().timestamp() + 7 * 24 * 60 * 60,
        'iat': datetime.now().timestamp()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def get_client_from_session(token: str):
    if not token:
        return None
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    except Exception:
        return None
    db = get_db()
    row = db.execute('SELECT * FROM clients WHERE id = ?', (data['client_id'],)).fetchone()
    db.close()
    return dict(row) if row else None


def require_client():
    token = request.cookies.get("portal_token") or request.headers.get("X-Portal-Token")
    client = get_client_from_session(token) if token else None
    if not client:
        return None
    return client


# ===================== DOCUMENTS API =====================

@app.route("/portal/api/documents")
def portal_get_documents():
    client = require_client()
    if not client:
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db()
    rows = db.execute(
        "SELECT * FROM documents WHERE client_id = ? ORDER BY uploaded_at DESC",
        (client["id"],),
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route("/portal/api/documents", methods=["POST"])
def portal_create_document():
    client = require_client()
    if not client:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json or {}
    filename = data.get("filename", "")
    file_type = data.get("file_type", "")
    file_size = data.get("file_size", 0)
    file_url = data.get("file_url", "")
    description = data.get("description", "")

    if not filename:
        return jsonify({"error": "filename is required"}), 400

    db = get_db()
    db.execute(
        "INSERT INTO documents (client_id, filename, file_type, file_size, file_url, description) VALUES (?, ?, ?, ?, ?, ?)",
        (client["id"], filename, file_type, file_size, file_url, description),
    )
    db.commit()
    doc_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()
    return jsonify({"status": "created", "document_id": doc_id}), 201


@app.route("/portal/api/documents/<int:doc_id>", methods=["DELETE"])
def portal_delete_document(doc_id: int):
    client = require_client()
    if not client:
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db()
    row = db.execute(
        "SELECT id FROM documents WHERE id = ? AND client_id = ?",
        (doc_id, client["id"]),
    ).fetchone()
    if not row:
        db.close()
        return jsonify({"error": "Document not found"}), 404

    db.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    db.commit()
    db.close()
    return jsonify({"status": "deleted"})


# ===================== SUPPORT TICKETS API =====================

SLA_RULES = {
    ("standard", "low"): 72,
    ("standard", "medium"): 48,
    ("standard", "high"): 24,
    ("standard", "critical"): 8,
    ("priority", "low"): 48,
    ("priority", "medium"): 24,
    ("priority", "high"): 12,
    ("priority", "critical"): 4,
    ("enterprise", "low"): 24,
    ("enterprise", "medium"): 12,
    ("enterprise", "high"): 4,
    ("enterprise", "critical"): 1,
}


def _get_sla_deadline(sla_tier: str, priority: str, created_at: str = None) -> str:
    hours = SLA_RULES.get((sla_tier or "standard", priority or "medium"), 48)
    base = datetime.fromisoformat(created_at) if created_at else datetime.now()
    return (base + timedelta(hours=hours)).isoformat()


@app.route("/portal/api/tickets", methods=["POST"])
def portal_create_ticket():
    client = require_client()
    if not client:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json or {}
    subject = data.get("subject", "").strip()
    body = data.get("body", "").strip()
    category = data.get("category", "").strip()
    priority = data.get("priority") or "medium"
    sla_tier = data.get("sla_tier") or "standard"
    assigned_to = data.get("assigned_to", "").strip()

    if not subject or not body:
        return jsonify({"error": "Subject and message are required"}), 400

    db = get_db()
    created_at = datetime.now().isoformat()
    sla_deadline = _get_sla_deadline(sla_tier, priority, created_at)

    db.execute(
        "INSERT INTO tickets (client_id, subject, body, status, priority, sla_tier, sla_deadline, assigned_to, created_at) VALUES (?, ?, ?, 'open', ?, ?, ?, ?, ?)",
        (client["id"], subject, body, priority, sla_tier, sla_deadline, assigned_to, created_at),
    )
    db.commit()
    ticket_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()
    return jsonify({"status": "created", "ticket_id": ticket_id, "sla_deadline": sla_deadline}), 201


@app.route("/portal/api/tickets")
def portal_get_tickets():
    client = require_client()
    if not client:
        return jsonify({"error": "Unauthorized"}), 401

    status = request.args.get("status")
    priority = request.args.get("priority")
    q = request.args.get("q", "").strip().lower()

    db = get_db()
    rows = db.execute("SELECT * FROM tickets WHERE client_id = ?", (client["id"],)).fetchall()
    tickets = [dict(r) for r in rows]

    if status:
        tickets = [t for t in tickets if t.get("status") == status]
    if priority:
        tickets = [t for t in tickets if t.get("priority") == priority]
    if q:
        tickets = [t for t in tickets if q in (t.get("subject") or "").lower() or q in (t.get("body") or "").lower()]

    now = datetime.now()
    for t in tickets:
        dl = t.get("sla_deadline")
        if dl:
            try:
                due = datetime.fromisoformat(dl)
                remaining = due - now
                t["sla_remaining_minutes"] = int(remaining.total_seconds() // 60)
                t["sla_overdue"] = remaining.total_seconds() < 0
            except Exception:
                t["sla_remaining_minutes"] = None
                t["sla_overdue"] = False
        else:
            t["sla_remaining_minutes"] = None
            t["sla_overdue"] = False

    db.close()
    return jsonify(tickets)


@app.route("/portal/api/tickets/<int:ticket_id>", methods=["PATCH"])
def portal_update_ticket(ticket_id: int):
    client = require_client()
    if not client:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json or {}
    db = get_db()
    ticket = db.execute("SELECT * FROM tickets WHERE id = ? AND client_id = ?", (ticket_id, client["id"])).fetchone()
    if not ticket:
        db.close()
        return jsonify({"error": "Ticket not found"}), 404

    allowed_fields = {"status", "priority", "assigned_to"}
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    if not updates:
        db.close()
        return jsonify({"error": "No valid fields to update"}), 400

    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [ticket_id]
    db.execute(f"UPDATE tickets SET {set_clause} WHERE id = ?", values)
    db.commit()
    db.close()
    return jsonify({"status": "updated", "ticket_id": ticket_id})



# ===================== SATISFACTION API =====================

@app.route("/portal/api/satisfaction", methods=["GET", "POST"])
def portal_api_satisfaction():
    client = require_client()
    if not client:
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()
    if request.method == "POST":
        data = request.json or {}
        score = data.get("score")
        notes = data.get("notes", "")
        if not score or not isinstance(score, int) or score < 1 or score > 10:
            db.close()
            return jsonify({"error": "Score must be 1-10"}), 400
        db.execute(
            "INSERT INTO satisfaction_history (client_id, score, notes) VALUES (?, ?, ?)",
            (client["id"], score, notes),
        )
        db.execute(
            "UPDATE clients SET satisfaction_score = ?, satisfaction_notes = ? WHERE id = ?",
            (score, notes, client["id"]),
        )
        db.commit()
        db.close()
        return jsonify({"status": "saved", "score": score}), 201
    rows = db.execute(
        "SELECT * FROM satisfaction_history WHERE client_id = ? ORDER BY created_at DESC",
        (client["id"],),
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


# ===================== UPSELL API =====================

@app.route("/portal/api/upsell", methods=["GET"])
def portal_get_upsell():
    client = require_client()
    if not client:
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()
    rows = db.execute(
        "SELECT * FROM upsell_opportunities WHERE client_id = ? ORDER BY created_at DESC",
        (client["id"],),
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route("/portal/api/upsell", methods=["POST"])
def portal_create_upsell():
    client = require_client()
    if not client:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json or {}
    title = data.get("title", "")
    description = data.get("description", "")
    current_package = data.get("current_package", "Basic")
    suggested_package = data.get("suggested_package", "Premium")
    savings = data.get("savings", "")
    if not title:
        db = get_db()
        db.close()
        return jsonify({"error": "title is required"}), 400
    db = get_db()
    db.execute(
        "INSERT INTO upsell_opportunities (client_id, title, description, current_package, suggested_package, savings, status) VALUES (?, ?, ?, ?, ?, ?, 'new')",
        (client["id"], title, description, current_package, suggested_package, savings),
    )
    db.commit()
    upsell_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()
    return jsonify({"status": "created", "upsell_id": upsell_id}), 201


@app.route("/portal/api/upsell/<int:upsell_id>", methods=["PATCH"])
def portal_update_upsell(upsell_id: int):
    client = require_client()
    if not client:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json or {}
    db = get_db()
    row = db.execute(
        "SELECT * FROM upsell_opportunities WHERE id = ? AND client_id = ?",
        (upsell_id, client["id"]),
    ).fetchone()
    if not row:
        db.close()
        return jsonify({"error": "Not found"}), 404
    allowed = {"status"}
    updates = {k: v for k, v in data.items() if k in allowed}
    if updates:
        set_clause = ", ".join([f"{k} = ?" for k in updates])
        values = list(updates.values()) + [upsell_id]
        db.execute(f"UPDATE upsell_opportunities SET {set_clause} WHERE id = ?", values)
        db.commit()
    db.close()
    return jsonify({"status": "updated"})


# ===================== ONBOARDING API =====================

@app.route("/portal/api/onboarding", methods=["GET", "POST"])
def portal_api_onboarding():
    client = require_client()
    if not client:
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()
    if request.method == "POST":
        data = request.json or {}
        step_title = data.get("step_title", "")
        step_key = data.get("step_key", "")
        status = data.get("status", "active")
        due_at = data.get("due_at", "")
        notes = data.get("notes", "")
        if not step_title:
            db.close()
            return jsonify({"error": "step_title is required"}), 400
        db.execute(
            "INSERT INTO onboarding (client_id, step_title, step_key, status, due_at, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (client["id"], step_title, step_key, status, due_at, notes),
        )
        db.commit()
        step_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.close()
        return jsonify({"status": "created", "step_id": step_id}), 201
    rows = db.execute(
        "SELECT * FROM onboarding WHERE client_id = ? ORDER BY created_at ASC",
        (client["id"],),
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


# ===================== SMS API =====================

@app.route("/portal/api/sms/send", methods=["POST"])
def portal_send_sms():
    client = require_client()
    if not client:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json or {}
    to_phone = data.get("to_phone", "")
    carrier = data.get("carrier", "")
    message = data.get("message", "")
    if not to_phone or not carrier or not message:
        return jsonify({"error": "to_phone, carrier, and message are required"}), 400
    db = get_db()
    row = db.execute("SELECT sms_enabled FROM clients WHERE id = ?", (client["id"],)).fetchone()
    db.close()
    if not row or not row["sms_enabled"]:
        return jsonify({"error": "SMS notifications not enabled"}), 403
    result = send_sms_via_email(to_phone, carrier, message)
    return jsonify(result)


@app.route("/portal/api/sms/reminder", methods=["POST"])
def portal_sms_reminder():
    client = require_client()
    if not client:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json or {}
    appointment_id = data.get("appointment_id")
    if not appointment_id:
        return jsonify({"error": "appointment_id is required"}), 400
    db = get_db()
    appt = db.execute(
        "SELECT * FROM appointments WHERE id = ? AND client_id = ?",
        (appointment_id, client["id"]),
    ).fetchone()
    client_row = db.execute(
        "SELECT sms_phone, sms_carrier, sms_enabled FROM clients WHERE id = ?",
        (client["id"],),
    ).fetchone()
    db.close()
    if not appt:
        return jsonify({"error": "Appointment not found"}), 404
    if not client_row or not client_row["sms_enabled"]:
        return jsonify({"error": "SMS not enabled"}), 403
    message = f"Reminder: You have an appointment scheduled for {appt['scheduled_at']}. Contact us if you need to reschedule."
    result = send_sms_via_email(client_row["sms_phone"], client_row["sms_carrier"], message)
    return jsonify(result)


# ===================== CAMPAIGN API =====================

@app.route("/portal/api/campaigns", methods=["GET", "POST"])
def portal_api_campaigns():
    client = require_client()
    if not client:
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()
    if request.method == "POST":
        data = request.json or {}
        name = data.get("name", "")
        source = data.get("source", "")
        spend = data.get("spend", 0)
        leads = data.get("leads", 0)
        if not name:
            db.close()
            return jsonify({"error": "name is required"}), 400
        db.execute(
            "INSERT INTO campaigns (client_id, name, source, spend, leads, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (client["id"], name, source, spend, leads, datetime.now().isoformat()),
        )
        db.commit()
        db.close()
        return jsonify({"status": "created"}), 201
    rows = db.execute(
        "SELECT * FROM campaigns WHERE client_id = ? ORDER BY created_at DESC",
        (client["id"],),
    ).fetchall()
    campaigns = []
    for r in rows:
        row = dict(r)
        spend = float(row.get("spend", 0) or 0)
        leads = int(row.get("leads", 0) or 0)
        row["cpl"] = round(spend / leads, 2) if leads else 0
        campaigns.append(row)
    db.close()
    return jsonify(campaigns)


# ===================== RISKS API =====================

@app.route("/portal/api/risks", methods=["GET"])
def portal_get_risks():
    client = require_client()
    if not client:
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()
    risks = []
    open_tickets = db.execute(
        "SELECT COUNT(*) as cnt FROM tickets WHERE client_id = ? AND status != 'closed'",
        (client["id"],),
    ).fetchone()
    if open_tickets and open_tickets["cnt"] > 5:
        risks.append({
            "id": "tickets_backlog",
            "level": "medium",
            "title": "Support Ticket Backlog",
            "detail": f"{open_tickets['cnt']} open tickets. Consider prioritizing resolution.",
        })
    sat = db.execute(
        "SELECT AVG(score) as avg_score FROM satisfaction_history WHERE client_id = ?",
        (client["id"],),
    ).fetchone()
    if sat and sat["avg_score"] and sat["avg_score"] < 5:
        risks.append({
            "id": "low_satisfaction",
            "level": "high",
            "title": "Low Satisfaction Score",
            "detail": f"Average score: {round(sat['avg_score'], 1)}/10. Immediate attention recommended.",
        })
    onboarding = db.execute(
        "SELECT COUNT(*) as cnt FROM onboarding WHERE client_id = ? AND status = 'completed'",
        (client["id"],),
    ).fetchone()
    if not onboarding or not onboarding["cnt"]:
        risks.append({
            "id": "no_onboarding",
            "level": "medium",
            "title": "Onboarding Not Started",
            "detail": "Complete onboarding to maximize platform value.",
        })
    if not risks:
        risks.append({
            "id": "all_clear",
            "level": "low",
            "title": "No Major Risks Detected",
            "detail": "Account health looks good.",
        })
    db.close()
    return jsonify(risks)


# ===================== AGENT PERFORMANCE API =====================

@app.route("/portal/api/agent-performance", methods=["GET"])
def portal_get_agent_performance():
    client = require_client()
    if not client:
        return jsonify({"error": "Unauthorized"}), 401
    db = get_db()
    total_calls = db.execute(
        "SELECT COUNT(*) as cnt FROM calls WHERE client_id = ?",
        (client["id"],),
    ).fetchone()
    total_tickets = db.execute(
        "SELECT COUNT(*) as cnt FROM tickets WHERE client_id = ?",
        (client["id"],),
    ).fetchone()
    resolved_tickets = db.execute(
        "SELECT COUNT(*) as cnt FROM tickets WHERE client_id = ? AND status = 'resolved'",
        (client["id"],),
    ).fetchone()
    avg_sat = db.execute(
        "SELECT AVG(score) as avg_score FROM satisfaction_history WHERE client_id = ?",
        (client["id"],),
    ).fetchone()
    db.close()
    return jsonify({
        "total_calls": total_calls["cnt"] if total_calls else 0,
        "total_tickets": total_tickets["cnt"] if total_tickets else 0,
        "resolved_tickets": resolved_tickets["cnt"] if resolved_tickets else 0,
        "avg_satisfaction": round(avg_sat["avg_score"], 1) if avg_sat and avg_sat["avg_score"] else 0,
        "resolution_rate": round((resolved_tickets["cnt"] / total_tickets["cnt"] * 100), 1) if total_tickets and total_tickets["cnt"] else 0,
    })


# ===================== ACCOUNT API =====================

@app.route('/portal/api/account', methods=['GET'])
def portal_get_account():
    client = require_client()
    if not client:
        return jsonify({'error': 'Unauthorized'}), 401
    db = get_db()
    row = db.execute('SELECT id, email, name, business_name, phone, email_verified, satisfaction_score, satisfaction_notes, sms_enabled, sms_phone, sms_carrier FROM clients WHERE id = ?', (client['id'],)).fetchone()
    db.close()
    return jsonify(dict(row)) if row else jsonify({'error': 'Not found'}), 404


@app.route('/portal/api/account', methods=['POST'])
def portal_update_account():
    client = require_client()
    if not client:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json or {}
    db = get_db()
    allowed = {'business_name','name','email','phone','sms_enabled','sms_phone','sms_carrier'}
    updates = {k: v for k, v in data.items() if k in allowed}
    if updates:
        set_clause = ', '.join([f'{k} = ?' for k in updates])
        values = list(updates.values()) + [client['id']]
        db.execute(f'UPDATE clients SET {set_clause} WHERE id = ?', values)
        db.commit()
    db.close()
    return jsonify({'status': 'saved'})


# ===================== ACTIVITIES / TIMELINE API =====================

@app.route('/portal/api/activities')
def portal_get_activities():
    client = require_client()
    if not client:
        return jsonify({'error': 'Unauthorized'}), 401
    db = get_db()
    rows = db.execute(
        'SELECT * FROM activities WHERE client_id = ? ORDER BY created_at DESC LIMIT 100',
        (client['id'],),
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route('/portal/api/revenue-timeline')
def portal_get_revenue_timeline():
    client = require_client()
    if not client:
        return jsonify({'error': 'Unauthorized'}), 401
    period = request.args.get('period', 'weekly')
    db = get_db()
    # Simplified: return last 7/30/52 days of orders
    days = {'weekly': 7, 'monthly': 30, 'yearly': 52}.get(period, 7)
    rows = db.execute(
        'SELECT amount, created_at FROM orders WHERE client_id = ? AND created_at >= ? ORDER BY created_at ASC',
        (client['id'], (datetime.now() - timedelta(days=days)).isoformat()),
    ).fetchall()
    db.close()
    labels = []
    values = []
    for r in rows:
        labels.append(r['created_at'][:10])
        values.append(float(r['amount'] or 0))
    return jsonify({'labels': labels, 'values': values})


# ===================== LEADS API =====================

@app.route('/portal/api/leads')
def portal_get_leads():
    client = require_client()
    if not client:
        return jsonify({'error': 'Unauthorized'}), 401
    db = get_db()
    status = request.args.get('status')
    source = request.args.get('source')
    q = request.args.get('q', '').strip().lower()
    rows = db.execute('SELECT * FROM leads WHERE client_id = ?', (client['id'],)).fetchall()
    leads = [dict(r) for r in rows]
    if status:
        leads = [l for l in leads if l.get('status') == status]
    if source:
        leads = [l for l in leads if l.get('source') == source]
    if q:
        leads = [l for l in leads if q in (l.get('name') or '').lower() or q in (l.get('email') or '').lower() or q in (l.get('company') or '').lower()]
    db.close()
    return jsonify(leads)


@app.route('/portal/api/leads', methods=['POST'])
def portal_create_lead():
    client = require_client()
    if not client:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    company = data.get('company', '').strip()
    source = data.get('source', '').strip()
    campaign = data.get('campaign', '').strip()
    utm_source = data.get('utm_source', '').strip()
    utm_medium = data.get('utm_medium', '').strip()
    utm_campaign = data.get('utm_campaign', '').strip()
    score = data.get('score', 0)
    notes = data.get('notes', '').strip()
    if not name and not email:
        return jsonify({'error': 'Name or email is required'}), 400
    db = get_db()
    db.execute(
        'INSERT INTO leads (client_id, name, email, phone, company, source, campaign, utm_source, utm_medium, utm_campaign, score, notes, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (client['id'], name, email, phone, company, source, campaign, utm_source, utm_medium, utm_campaign, score, notes, 'new')
    )
    db.commit()
    lead_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
    db.close()
    return jsonify({'status': 'created', 'lead_id': lead_id}), 201


@app.route('/portal/api/leads/<int:lead_id>', methods=['PATCH'])
def portal_update_lead(lead_id: int):
    client = require_client()
    if not client:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json or {}
    db = get_db()
    lead = db.execute('SELECT * FROM leads WHERE id = ? AND client_id = ?', (lead_id, client['id'])).fetchone()
    if not lead:
        db.close()
        return jsonify({'error': 'Lead not found'}), 404
    allowed_fields = {'status', 'score', 'assigned_to', 'notes', 'follow_up_count', 'last_contacted_at', 'name', 'email', 'phone', 'company'}
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    if updates:
        set_clause = ', '.join([f'{k} = ?' for k in updates])
        values = list(updates.values()) + [lead_id]
        db.execute(f'UPDATE leads SET {set_clause} WHERE id = ?', values)
        db.commit()
    db.close()
    return jsonify({'status': 'updated'})


@app.route('/portal/api/leads/<int:lead_id>', methods=['DELETE'])
def portal_delete_lead(lead_id: int):
    client = require_client()
    if not client:
        return jsonify({'error': 'Unauthorized'}), 401
    db = get_db()
    row = db.execute('SELECT id FROM leads WHERE id = ? AND client_id = ?', (lead_id, client['id'])).fetchone()
    if not row:
        db.close()
        return jsonify({'error': 'Lead not found'}), 404
    db.execute('DELETE FROM leads WHERE id = ?', (lead_id,))
    db.commit()
    db.close()
    return jsonify({'status': 'deleted'})


# Public lead capture - no auth required
@app.route('/portal/api/public/leads', methods=['POST'])
def public_capture_lead():
    data = request.json or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    company = data.get('company', '').strip()
    source = data.get('source', 'website').strip()
    campaign = data.get('campaign', '').strip()
    utm_source = data.get('utm_source', '').strip()
    utm_medium = data.get('utm_medium', '').strip()
    utm_campaign = data.get('utm_campaign', '').strip()
    notes = data.get('notes', '').strip()
    if not name and not email:
        return jsonify({'error': 'Name or email is required'}), 400
    db = get_db()
    db.execute(
        'INSERT INTO leads (client_id, name, email, phone, company, source, campaign, utm_source, utm_medium, utm_campaign, notes, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (None, name, email, phone, company, source, campaign, utm_source, utm_medium, utm_campaign, notes, 'new')
    )
    db.commit()
    lead_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
    db.close()
    return jsonify({'status': 'captured', 'lead_id': lead_id}), 201


# ===================== LEAD FOLLOW-UP SEQUENCES API =====================

@app.route('/portal/api/leads/<int:lead_id>/sequences', methods=['GET'])
def portal_get_lead_sequences(lead_id: int):
    client = require_client()
    if not client:
        return jsonify({'error': 'Unauthorized'}), 401
    db = get_db()
    lead = db.execute('SELECT id FROM leads WHERE id = ? AND client_id = ?', (lead_id, client['id'])).fetchone()
    if not lead:
        db.close()
        return jsonify({'error': 'Lead not found'}), 404
    rows = db.execute('SELECT * FROM lead_sequences WHERE lead_id = ? ORDER BY step_number ASC', (lead_id,)).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route('/portal/api/leads/<int:lead_id>/sequences', methods=['POST'])
def portal_create_lead_sequence(lead_id: int):
    client = require_client()
    if not client:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json or {}
    template_name = data.get('template_name', '').strip()
    channel = data.get('channel', 'email').strip()
    scheduled_at = data.get('scheduled_at', '').strip()
    if not template_name:
        return jsonify({'error': 'template_name is required'}), 400
    db = get_db()
    lead = db.execute('SELECT id FROM leads WHERE id = ? AND client_id = ?', (lead_id, client['id'])).fetchone()
    if not lead:
        db.close()
        return jsonify({'error': 'Lead not found'}), 404
    next_step = db.execute('SELECT MAX(step_number) as mx FROM lead_sequences WHERE lead_id = ?', (lead_id,)).fetchone()
    step_number = (next_step['mx'] or 0) + 1
    db.execute(
        'INSERT INTO lead_sequences (lead_id, step_number, template_name, channel, scheduled_at, status) VALUES (?, ?, ?, ?, ?, ?)',
        (lead_id, step_number, template_name, channel, scheduled_at, 'pending')
    )
    db.commit()
    seq_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
    db.close()
    return jsonify({'status': 'created', 'sequence_id': seq_id, 'step_number': step_number}), 201


# ===================== FOLLOW-UP EXECUTION ENGINE =====================

def _send_email(to: str, subject: str, body: str) -> dict:
    if not GMAIL_APP_PASSWORD:
        return {'status': 'error', 'error': 'SMTP not configured'}
    msg = MIMEText(body)
    msg['From'] = GMAIL_SENDER
    msg['To'] = to
    msg['Subject'] = subject
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(GMAIL_SMTP_SERVER, GMAIL_SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, to, msg.as_string())
        return {'status': 'sent', 'to': to, 'sent_at': datetime.now().isoformat()}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

SEQUENCE_TEMPLATES = {
    'new_lead_email_1': {
        'subject': 'Thanks for reaching out',
        'body': 'Hi {name}, thanks for contacting AnswerFirst AI. We received your inquiry and would love to learn more about your business. Reply to this email or book a time that works for you.'
    },
    'new_lead_email_2': {
        'subject': 'Quick question about your needs',
        'body': 'Hi {name}, following up on your recent inquiry. Are you still looking for an AI receptionist or SEO help? Let me know and I will send over a custom plan.'
    },
    'welcome_sequence': {
        'subject': 'Welcome to AnswerFirst AI',
        'body': 'Hi {name}, welcome aboard. Your onboarding checklist is ready in your portal. If you have any questions, just reply.'
    },
    're_engage': {
        'subject': 'Still interested?',
        'body': 'Hi {name}, it has been a few days since we connected. If you are ready to move forward, I am here to help.'
    }
}


@app.route('/portal/api/leads/<int:lead_id>/sequences/<int:seq_id>/send', methods=['POST'])
def portal_send_sequence_now(lead_id: int, seq_id: int):
    client = require_client()
    if not client:
        return jsonify({'error': 'Unauthorized'}), 401
    db = get_db()
    lead = db.execute('SELECT * FROM leads WHERE id = ? AND client_id = ?', (lead_id, client['id'])).fetchone()
    seq = db.execute('SELECT * FROM lead_sequences WHERE id = ? AND lead_id = ?', (seq_id, lead_id)).fetchone()
    if not lead or not seq:
        db.close()
        return jsonify({'error': 'Lead or sequence not found'}), 404
    template = SEQUENCE_TEMPLATES.get(seq['template_name'], SEQUENCE_TEMPLATES['new_lead_email_1'])
    subject = template['subject']
    body = template['body'].replace('{name}', lead['name'] or 'there')
    result = {'status': 'skipped'}
    if seq['channel'] == 'email' and lead['email']:
        result = _send_email(lead['email'], subject, body)
    db.execute('UPDATE lead_sequences SET sent_at = ?, status = ? WHERE id = ?', (datetime.now().isoformat(), result.get('status','sent'), seq_id))
    db.execute('UPDATE leads SET last_contacted_at = ?, follow_up_count = follow_up_count + 1 WHERE id = ?', (datetime.now().isoformat(), lead_id))
    db.commit()
    db.close()
    return jsonify({'status': 'executed', 'result': result})


@app.route('/portal/api/sequences/run-due', methods=['POST'])
def portal_run_due_sequences():
    client = require_client()
    if not client:
        return jsonify({'error': 'Unauthorized'}), 401
    db = get_db()
    now = datetime.now().isoformat()
    rows = db.execute('SELECT s.*, l.email, l.name FROM lead_sequences s JOIN leads l ON l.id = s.lead_id WHERE l.client_id = ? AND s.status = ? AND s.scheduled_at <= ?', (client['id'], 'pending', now)).fetchall()
    results = []
    for seq in rows:
        template = SEQUENCE_TEMPLATES.get(seq['template_name'], SEQUENCE_TEMPLATES['new_lead_email_1'])
        subject = template['subject']
        body = template['body'].replace('{name}', seq['name'] or 'there')
        result = {'status': 'skipped'}
        if seq['channel'] == 'email' and seq['email']:
            result = _send_email(seq['email'], subject, body)
        db.execute('UPDATE lead_sequences SET sent_at = ?, status = ? WHERE id = ?', (datetime.now().isoformat(), result.get('status','sent'), seq['id']))
        db.execute('UPDATE leads SET last_contacted_at = ?, follow_up_count = follow_up_count + 1 WHERE id = ?', (datetime.now().isoformat(), seq['lead_id']))
        results.append({'sequence_id': seq['id'], 'lead_id': seq['lead_id'], 'result': result})
    db.commit()
    db.close()
    return jsonify({'executed': len(results), 'results': results})


# ===================== CALLS API =====================

@app.route('/portal/api/calls')
def portal_get_calls():
    client = require_client()
    if not client:
        return jsonify({'error': 'Unauthorized'}), 401
    db = get_db()
    rows = db.execute(
        'SELECT * FROM calls WHERE client_id = ? ORDER BY created_at DESC',
        (client['id'],),
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


# ===================== APPOINTMENTS API =====================

@app.route('/portal/api/appointments')
def portal_get_appointments():
    client = require_client()
    if not client:
        return jsonify({'error': 'Unauthorized'}), 401
    db = get_db()
    rows = db.execute(
        'SELECT * FROM appointments WHERE client_id = ? ORDER BY created_at DESC',
        (client['id'],),
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


# ===================== AUTH API =====================

@app.route('/portal/register', methods=['POST'])
def portal_register():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    business_name = data.get('business_name', '')
    contact_name = data.get('contact_name', '')
    phone = data.get('phone', '')
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    db = get_db()
    existing = db.execute('SELECT id FROM clients WHERE email = ?', (email,)).fetchone()
    if existing:
        db.close()
        return jsonify({'error': 'Email already registered'}), 400
    db.execute(
        'INSERT INTO clients (email, password_hash, business_name, contact_name, phone) VALUES (?, ?, ?, ?, ?)',
        (email, hash_password(password), business_name, contact_name, phone),
    )
    db.commit()
    client = db.execute('SELECT * FROM clients WHERE email = ?', (email,)).fetchone()
    db.close()
    token = create_jwt(client['id'])
    resp = jsonify({'client': dict(client)})
    resp.set_cookie('portal_token', token, max_age=7*24*60*60, httponly=True, samesite='Lax')
    return resp


@app.route('/portal/login', methods=['POST'])
def portal_login():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    db = get_db()
    client = db.execute('SELECT * FROM clients WHERE email = ?', (email,)).fetchone()
    db.close()
    if not client or not verify_password(password, client['password_hash']):
        return jsonify({'error': 'Invalid credentials'}), 401
    token = create_jwt(client['id'])
    resp = jsonify({'client': dict(client)})
    resp.set_cookie('portal_token', token, max_age=7*24*60*60, httponly=True, samesite='Lax')
    return resp


@app.route('/portal/logout', methods=['POST'])
def portal_logout():
    token = request.cookies.get('portal_token')
    if token:
        db = get_db()
        db.execute('DELETE FROM sessions WHERE token = ?', (token,))
        db.commit()
        db.close()
    resp = jsonify({'status': 'logged_out'})
    resp.delete_cookie('portal_token')
    return resp

# ===================== PUBLIC HTML =====================

# ===================== HEALTH CHECK =====================
@app.route('/portal/api/health', methods=['GET'])
def health_check():
    try:
        db = get_db()
        db.execute('SELECT 1')
        db.close()
        return jsonify({'status': 'ok', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'detail': str(e)}), 500


# ===================== PORTAL API ROUTES =====================
@app.route('/portal/api/login', methods=['POST'])
def api_login():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        db = get_db()
        client = db.execute(
            'SELECT id, email, business_name, contact_name FROM clients WHERE email = ? AND password_hash = ?',
            (email, password_hash)
        ).fetchone()
        db.close()
        
        if not client:
            return jsonify({'error': 'Invalid email or password'}), 401
    
        token = create_jwt(client['id'])
        return jsonify({
            'status': 'ok',
            'client_id': client['id'],
            'email': client['email'],
            'business_name': client['business_name'],
            'contact_name': client['contact_name'],
            '_session_token': token
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/portal/api/register', methods=['POST'])
def api_register():
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
        c = db.cursor()
        c.execute(
            'INSERT INTO clients (email, password_hash, business_name, contact_name, phone) VALUES (?, ?, ?, ?, ?)',
            (email, password_hash, business_name, contact_name, phone)
        )
        db.commit()
        client_id = c.lastrowid
        db.close()
        
        token = create_jwt(client_id)
        resp = make_response(jsonify({'status': 'ok', 'client_id': client_id, '_session_token': token}))
        resp.set_cookie('portal_token', token, max_age=7*24*60*60, httponly=True, samesite='Lax')
        return resp, 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already registered'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/portal/api/forgot-password', methods=['POST'])
def api_forgot_password():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({'error': 'Email required'}), 400
    
    # Check if user exists
    db = get_db()
    client = db.execute('SELECT id FROM clients WHERE email = ?', (email,)).fetchone()
    db.close()
    
    if client:
        # In production: send actual reset email
        token = secrets.token_urlsafe(32)
        return jsonify({'status': 'ok', 'message': 'If an account exists, a reset email was sent.'}), 200
    else:
        # Don't reveal if email exists
        return jsonify({'status': 'ok', 'message': 'If an account exists, a reset email was sent.'}), 200

# ===================== ORDER FLOW =====================

def _plan_amount(plan: str) -> float:
    amounts = {
        'Starter': 1500, 'Growth': 2500, 'Authority': 4000,
        'SEO Starter': 497, 'SEO Growth': 997, 'SEO Authority': 1497,
        'TBD': 0
    }
    return amounts.get(plan, 0)


def _paypal_link(plan: str) -> str:
    links = {
        'Starter': 'https://www.paypal.com/ncp/payment/GCMFXKYWWZKG4',
        'Growth': 'https://www.paypal.com/ncp/payment/JN4MF8LPWSWQE',
        'Authority': 'https://www.paypal.com/ncp/payment/TZYZ5AEAWFG2E',
        'SEO Starter': 'https://www.paypal.com/ncp/payment/GCMFXKYWWZKG4',
        'SEO Growth': 'https://www.paypal.com/ncp/payment/JN4MF8LPWSWQE',
        'SEO Authority': 'https://www.paypal.com/ncp/payment/TZYZ5AEAWFG2E',
    }
    return links.get(plan, 'https://www.paypal.com/ncp/payment/GCMFXKYWWZKG4')


@app.route('/portal/api/order-intent', methods=['POST'])
def create_order_intent():
    """Step 1: Client submits contact form → create pending order intent, send email with auth link."""
    data = request.json or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    company = data.get('company', '').strip()
    volume = data.get('volume', '')
    plan = data.get('plan', '')  # optional pre-selected plan
    notes = data.get('notes', '').strip()

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    db = get_db()
    existing = db.execute('SELECT id FROM clients WHERE email = ?', (email,)).fetchone()
    client_id = existing['id'] if existing else None

    expires_at = (datetime.now() + timedelta(hours=42)).isoformat()
    db.execute(
        'INSERT INTO orders (client_id, package, amount, status, payment_method, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (client_id, plan or 'TBD', _plan_amount(plan or 'TBD'), 'order_created', 'paypal', notes or f'Volume: {volume}', datetime.now().isoformat())
    )
    order_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

    account_token = secrets.token_urlsafe(32)
    db.execute(
        'INSERT INTO order_intents (order_id, email, name, phone, company, volume, account_token, status, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (order_id, email, name, phone, company, volume, account_token, 'awaiting_account', expires_at)
    )
    db.commit()
    db.close()

    account_url = f"{request.host_url}portal-account.html?token={account_token}"
    subject = "Welcome to AnswerFirst AI — Create Your Account"
    body = f"""Dear {name or 'Valued Partner'},

Thank you for your interest in AnswerFirst AI. We're excited to show you how our AI-powered phone agents can transform your HVAC or roofing business.

**What happens next:**

1. Create your client account (takes 60 seconds)
   → {account_url}

2. Select your preferred plan
   → You'll choose from Starter, Growth, or Authority after account creation

3. Complete your order & payment
   → Secure checkout via PayPal

**Your 14-Day Guarantee**
If we don't deliver 10+ qualified appointments in your first 30 days, you get a full refund. No contracts. Cancel anytime.

**Need help?**
Reply to this email or call us at 562-259-3384 (Mon-Fri 9am-6pm PST).

We look forward to helping you fill your calendar.

Best regards,
The AnswerFirst AI Team
azelt.marketing@gmail.com"""

    email_result = _send_email(email, subject, body)
    print(f"[EMAIL] order-intent -> {email_result}")

    return jsonify({'status': 'intent_created', 'order_id': order_id, 'account_url': account_url, 'email_status': email_result.get('status'), 'email_error': email_result.get('error')}), 201


@app.route('/portal/api/order-intent/<token>')
def get_order_intent(token):
    db = get_db()
    intent = db.execute('SELECT * FROM order_intents WHERE account_token = ?', (token,)).fetchone()
    db.close()
    if not intent:
        return jsonify({'error': 'Invalid or expired link'}), 404
    if datetime.fromisoformat(intent['expires_at']) < datetime.now():
        return jsonify({'error': 'Link expired. Please contact support.'}), 410
    return jsonify({'intent': dict(intent)}), 200


@app.route('/portal/api/account/create', methods=['POST'])
def create_account_from_intent():
    data = request.json or {}
    token = data.get('token', '').strip()
    password = data.get('password', '').strip()
    business_name = data.get('business_name', '').strip()

    if not token or not password:
        return jsonify({'error': 'Token and password required'}), 400

    db = get_db()
    intent = db.execute('SELECT * FROM order_intents WHERE account_token = ?', (token,)).fetchone()
    if not intent:
        db.close()
        return jsonify({'error': 'Invalid link'}), 404
    if datetime.fromisoformat(intent['expires_at']) < datetime.now():
        db.close()
        return jsonify({'error': 'Link expired'}), 410

    email = intent['email']
    existing = db.execute('SELECT id FROM clients WHERE email = ?', (email,)).fetchone()
    if existing:
        db.close()
        return jsonify({'error': 'Account already exists. Please log in.'}), 409

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    db.execute(
        'INSERT INTO clients (email, password_hash, business_name, contact_name, phone) VALUES (?, ?, ?, ?, ?)',
        (email, password_hash, business_name or intent['company'], intent['name'], intent['phone'])
    )
    client_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

    db.execute('UPDATE orders SET client_id = ? WHERE id = ?', (client_id, intent['order_id']))
    db.execute("UPDATE order_intents SET status = 'account_created' WHERE account_token = ?", (token,))
    db.commit()
    db.close()

    token_jwt = create_jwt(client_id)
    resp = jsonify({'status': 'ok', 'client_id': client_id, 'redirect': '/portal-plans.html'})
    resp.set_cookie('portal_token', token_jwt, max_age=7*24*60*60, httponly=True, samesite='Lax')
    return resp, 201


@app.route('/portal/api/plan/select', methods=['POST'])
def select_plan():
    client = require_client()
    if not client:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json or {}
    plan = data.get('plan', '').strip()

    if plan not in ('Starter', 'Growth', 'Authority', 'SEO Starter', 'SEO Growth', 'SEO Authority'):
        return jsonify({'error': 'Invalid plan'}), 400

    db = get_db()
    order = db.execute(
        'SELECT * FROM orders WHERE client_id = ? AND status IN (?, ?) ORDER BY id DESC LIMIT 1',
        (client['id'], 'order_created', 'awaiting_payment')
    ).fetchone()
    if not order:
        db.close()
        return jsonify({'error': 'No pending order found'}), 404

    amount = _plan_amount(plan)
    paypal_link = _paypal_link(plan)
    db.execute(
        'UPDATE orders SET package = ?, amount = ?, status = ?, payment_link = ? WHERE id = ?',
        (plan, amount, 'awaiting_payment', paypal_link, order['id'])
    )
    db.execute(
        'INSERT INTO onboarding (client_id, step_title, step_key, status, notes) VALUES (?, ?, ?, ?, ?)',
        (client['id'], f'Selected {plan}', 'plan_selection', 'completed', f'Plan: {plan}, Amount: ${amount}/mo')
    )
    db.commit()
    db.close()

    return jsonify({'status': 'plan_selected', 'plan': plan, 'amount': amount, 'paypal_link': paypal_link, 'redirect': '/portal-checkout.html'}), 200


@app.route('/portal/api/checkout/submit', methods=['POST'])
def submit_checkout():
    client = require_client()
    if not client:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json or {}
    business_name = data.get('business_name', '').strip()
    phone = data.get('phone', '').strip()
    company = data.get('company', '').strip()

    db = get_db()
    order = db.execute(
        'SELECT * FROM orders WHERE client_id = ? AND status = ? ORDER BY id DESC LIMIT 1',
        (client['id'], 'awaiting_payment')
    ).fetchone()
    if not order:
        db.close()
        return jsonify({'error': 'No pending checkout found'}), 404

    db.execute(
        'UPDATE orders SET notes = ? WHERE id = ?',
        (f'Business: {business_name}\nPhone: {phone}\nCompany: {company}\n' + (order['notes'] or ''), order['id'])
    )
    db.execute(
        'UPDATE clients SET business_name = ?, contact_name = ?, phone = ? WHERE id = ?',
        (business_name, client['contact_name'], phone, client['id'])
    )
    db.commit()
    db.close()

    return jsonify({'status': 'ready', 'paypal_link': order['payment_link'], 'order_id': order['id']}), 200


@app.route('/portal/api/admin/cancel-expired', methods=['POST'])
def cancel_expired_orders():
    cutoff = (datetime.now() - timedelta(hours=42)).isoformat()
    db = get_db()
    expired = db.execute(
        'SELECT id FROM orders WHERE status = ? AND created_at < ?',
        ('order_created', cutoff)
    ).fetchall()
    count = 0
    for row in expired:
        db.execute('UPDATE orders SET status = ? WHERE id = ?', ('cancelled', row['id']))
        count += 1
    db.commit()
    db.close()
    return jsonify({'cancelled': count}), 200


# ===================== PUBLIC SITE =====================
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public-site')

@app.route('/')
def unified_root():
    return send_from_directory(PUBLIC_DIR, 'index.html')

@app.route('/<path:filename>')
def unified_static(filename):
    full = os.path.join(PUBLIC_DIR, filename)
    if os.path.isfile(full):
        return send_from_directory(PUBLIC_DIR, filename)
    return send_from_directory(PUBLIC_DIR, 'index.html')

if __name__ == '__main__':
    create_tables()
    app.run(host='0.0.0.0', port=5070, debug=False, use_reloader=False)
