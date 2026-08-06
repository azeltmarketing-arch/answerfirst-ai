"""
AnswerFirst AI - Unified Public Site + Client Portal
Port: 5070
"""

from flask import Flask, render_template_string, request, jsonify, redirect, url_for, make_response, send_from_directory
from flask_cors import CORS
import sqlite3, os, secrets, hashlib, smtplib, ssl
from datetime import datetime, timedelta
from email.mime.text import MIMEText

app = Flask(__name__)
CORS(app)
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
            source TEXT DEFAULT '',
            status TEXT DEFAULT 'new',
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

# Initialize database on import
create_tables()


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
    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def create_session(client_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires = datetime.now().timestamp() + 7 * 24 * 60 * 60
    db = get_db()
    db.execute(
        "INSERT INTO sessions (token, client_id, expires_at) VALUES (?, ?, ?)",
        (token, client_id, datetime.fromtimestamp(expires).isoformat()),
    )
    db.commit()
    db.close()
    return token


def get_client_from_session(token: str):
    db = get_db()
    row = db.execute(
        "SELECT c.* FROM sessions s JOIN clients c ON s.client_id = c.id WHERE s.token = ? AND s.expires_at > ?",
        (token, datetime.now().isoformat()),
    ).fetchone()
    db.close()
    return dict(row) if row else None


def require_client():
    token = request.cookies.get("portal_token")
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
    rows = db.execute(
        'SELECT * FROM leads WHERE client_id = ? ORDER BY created_at DESC',
        (client['id'],),
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


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
    token = create_session(client['id'])
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
    token = create_session(client['id'])
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
        
        token = secrets.token_urlsafe(32)
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

# ===================== STATIC PUBLIC SITE =====================
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
