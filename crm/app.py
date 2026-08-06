"""
AnswerFirst AI — Local CRM
Zero-cost replacement for HubSpot using Flask + SQLite
Provides: contacts, companies, deals, activities, pipeline reporting
"""

import sqlite3
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Ensure integrations path is available for direct SMTP send
INTEGRATIONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "integrations"))
if INTEGRATIONS_DIR not in sys.path:
    sys.path.insert(0, INTEGRATIONS_DIR)

try:
    from gmail_smtp import GmailSMTP  # type: ignore
except Exception:  # pragma: no cover
    GmailSMTP = None  # type: ignore

DB_PATH = os.path.join(os.path.dirname(__file__), "crm.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT DEFAULT '',
            last_name TEXT DEFAULT '',
            email TEXT UNIQUE,
            phone TEXT DEFAULT '',
            company TEXT DEFAULT '',
            job_title TEXT DEFAULT '',
            source TEXT DEFAULT 'manual',
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            domain TEXT UNIQUE,
            phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            industry TEXT DEFAULT '',
            city TEXT DEFAULT '',
            state TEXT DEFAULT '',
            source TEXT DEFAULT 'manual',
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_name TEXT,
            company_id INTEGER,
            contact_id INTEGER,
            package TEXT DEFAULT 'Basic',
            monthly_value REAL DEFAULT 0,
            stage TEXT DEFAULT 'qualified',
            probability INTEGER DEFAULT 50,
            source TEXT DEFAULT 'manual',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id),
            FOREIGN KEY (contact_id) REFERENCES contacts(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER,
            deal_id INTEGER,
            activity_type TEXT,
            direction TEXT,
            subject TEXT DEFAULT '',
            body TEXT DEFAULT '',
            outcome TEXT DEFAULT 'pending',
            metadata TEXT DEFAULT '{}',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contact_id) REFERENCES contacts(id),
            FOREIGN KEY (deal_id) REFERENCES deals(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'client',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
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
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER,
            package TEXT DEFAULT 'Basic',
            amount REAL DEFAULT 0,
            status TEXT DEFAULT 'Submitted',
            payment_method TEXT DEFAULT 'paypal',
            payment_link TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contact_id) REFERENCES contacts(id)
        )
    """)
    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ==================== COMPANIES ====================

@app.route("/api/companies", methods=["GET"])
def list_companies():
    db = get_db()
    rows = db.execute("SELECT * FROM companies ORDER BY created_at DESC").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/companies", methods=["POST"])
def create_company():
    data = request.json or {}
    db = get_db()
    db.execute(
        "INSERT INTO companies (name, domain, phone, address, industry, city, state, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            data.get("name", ""),
            data.get("domain", ""),
            data.get("phone", ""),
            data.get("address", ""),
            data.get("industry", ""),
            data.get("city", ""),
            data.get("state", ""),
            data.get("source", "api"),
        ),
    )
    db.commit()
    db.close()
    return jsonify({"status": "created"}), 201


@app.route("/api/companies/<int:company_id>", methods=["GET"])
def get_company(company_id: int):
    db = get_db()
    row = db.execute("SELECT * FROM companies WHERE id = ?", (company_id,)).fetchone()
    db.close()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dict(row))


# ==================== CONTACTS ====================

@app.route("/api/contacts", methods=["GET"])
def list_contacts():
    db = get_db()
    rows = db.execute("SELECT * FROM contacts ORDER BY created_at DESC").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/contacts", methods=["POST"])
def create_contact():
    data = request.json or {}
    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO contacts (first_name, last_name, email, phone, company, job_title, source) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            data.get("first_name", ""),
            data.get("last_name", ""),
            data.get("email", ""),
            data.get("phone", ""),
            data.get("company", ""),
            data.get("job_title", ""),
            data.get("source", "api"),
        ),
    )
    db.commit()
    db.close()
    return jsonify({"status": "created"}), 201


@app.route("/api/contacts/search", methods=["GET"])
def search_contact():
    email = request.args.get("email", "")
    db = get_db()
    row = db.execute("SELECT * FROM contacts WHERE email = ?", (email,)).fetchone()
    db.close()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dict(row))


@app.route("/api/contacts/<int:contact_id>", methods=["DELETE"])
def delete_contact(contact_id: int):
    db = get_db()
    db.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
    db.commit()
    db.close()
    return jsonify({"status": "deleted"})


# ==================== DEALS ====================

@app.route("/api/deals", methods=["GET"])
def list_deals():
    db = get_db()
    rows = db.execute("""
        SELECT d.*, c.name as company_name, c.domain as company_domain
        FROM deals d
        LEFT JOIN companies c ON d.company_id = c.id
        ORDER BY d.created_at DESC
    """).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/deals", methods=["POST"])
def create_deal():
    data = request.json or {}
    db = get_db()
    db.execute(
        "INSERT INTO deals (deal_name, company_id, contact_id, package, monthly_value, stage, probability, source, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            data.get("deal_name", ""),
            data.get("company_id"),
            data.get("contact_id"),
            data.get("package", "Basic"),
            data.get("monthly_value", 0),
            data.get("stage", "qualified"),
            data.get("probability", 50),
            data.get("source", "api"),
            data.get("notes", ""),
        ),
    )
    db.commit()
    db.close()
    return jsonify({"status": "created"}), 201


@app.route("/api/deals/<int:deal_id>", methods=["PATCH"])
def update_deal(deal_id: int):
    data = request.json or {}
    fields = []
    values = []
    for key in ["stage", "probability", "notes", "package", "monthly_value"]:
        if key in data:
            fields.append(f"{key} = ?")
            values.append(data[key])
    if not fields:
        return jsonify({"error": "No fields to update"}), 400
    values.append(deal_id)
    db = get_db()
    db.execute(f"UPDATE deals SET {', '.join(fields)}, updated_at = ? WHERE id = ?", [*values, datetime.now().isoformat()])
    db.commit()
    db.close()
    return jsonify({"status": "updated"})


@app.route("/api/deals/pipeline", methods=["GET"])
def pipeline_report():
    db = get_db()
    rows = db.execute("SELECT stage, COUNT(*) as count, SUM(monthly_value) as value FROM deals GROUP BY stage").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


# ==================== ORDERS ====================

@app.route("/api/orders", methods=["GET"])
def list_orders():
    db = get_db()
    rows = db.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 200").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/orders", methods=["POST"])
def create_order():
    data = request.json or {}
    db = get_db()
    db.execute(
        "INSERT INTO orders (contact_id, package, amount, status, payment_method, payment_link, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            data.get("contact_id"),
            data.get("package", "Basic"),
            data.get("amount", 0),
            data.get("status", "Submitted"),
            data.get("payment_method", "paypal"),
            data.get("payment_link", ""),
            data.get("notes", ""),
        ),
    )
    db.commit()
    db.close()
    return jsonify({"status": "created"}), 201


@app.route("/api/orders/<int:order_id>", methods=["PATCH"])
def update_order_status(order_id: int):
    data = request.json or {}
    db = get_db()
    db.execute(
        "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
        (data.get("status"), datetime.now().isoformat(), order_id),
    )
    db.commit()
    db.close()
    return jsonify({"status": "updated"})


# ==================== ACTIVITIES ====================

@app.route("/api/activities", methods=["POST"])
def log_activity():
    data = request.json or {}
    db = get_db()
    db.execute(
        "INSERT INTO activities (contact_id, deal_id, activity_type, direction, subject, body, outcome, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            data.get("contact_id"),
            data.get("deal_id"),
            data.get("activity_type"),
            data.get("direction"),
            data.get("subject", ""),
            data.get("body", ""),
            data.get("outcome", "pending"),
            json.dumps(data.get("metadata", {})),
        ),
    )
    db.commit()
    db.close()
    return jsonify({"status": "created"}), 201


@app.route("/api/activities", methods=["GET"])
def list_activities():
    db = get_db()
    rows = db.execute("SELECT * FROM activities ORDER BY created_at DESC LIMIT 200").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


# ==================== DASHBOARD DATA ====================

@app.route("/api/dashboard", methods=["GET"])
def dashboard_data():
    db = get_db()
    total_leads = db.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
    active_clients = db.execute("SELECT COUNT(*) FROM deals WHERE stage = 'closed_won'").fetchone()[0]
    total_revenue = db.execute("SELECT COALESCE(SUM(monthly_value), 0) FROM deals WHERE stage = 'closed_won'").fetchone()[0]
    pipeline = db.execute("SELECT stage, COUNT(*) as count, SUM(monthly_value) as value FROM deals GROUP BY stage").fetchall()
    recent_activities = db.execute("SELECT * FROM activities ORDER BY created_at DESC LIMIT 20").fetchall()
    db.close()
    return jsonify({
        "total_leads": total_leads,
        "active_clients": active_clients,
        "total_revenue": total_revenue,
        "pipeline": [dict(r) for r in pipeline],
        "recent_activities": [dict(r) for r in recent_activities],
    })


# ==================== AUTH ====================

import hashlib
import secrets
from datetime import datetime, timedelta


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _verify_password(password: str, password_hash: str) -> bool:
    return _hash_password(password) == password_hash


def _create_session(client_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now() + timedelta(days=7)).isoformat()
    db = get_db()
    db.execute("INSERT INTO sessions (token, client_id, expires_at) VALUES (?, ?, ?)", (token, client_id, expires_at))
    db.commit()
    db.close()
    return token


def _get_client_from_session(token: str):
    db = get_db()
    row = db.execute("SELECT c.* FROM sessions s JOIN clients c ON s.client_id = c.id WHERE s.token = ? AND s.expires_at > ?", (token, datetime.now().isoformat())).fetchone()
    db.close()
    return dict(row) if row else None


@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    data = request.json or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "client")
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    db = get_db()
    existing = db.execute("SELECT id FROM clients WHERE email = ?", (email,)).fetchone()
    if existing:
        db.close()
        return jsonify({"error": "Email already registered"}), 400
    db.execute("INSERT INTO clients (email, password_hash, role) VALUES (?, ?, ?)", (email, _hash_password(password), role))
    db.commit()
    client = db.execute("SELECT * FROM clients WHERE email = ?", (email,)).fetchone()
    db.close()
    token = _create_session(client["id"])
    resp = jsonify({"client": dict(client)})
    resp.set_cookie("crm_token", token, max_age=7*24*60*60, httponly=True, samesite="Lax")
    return resp, 201


@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    data = request.json or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    db = get_db()
    client = db.execute("SELECT * FROM clients WHERE email = ?", (email,)).fetchone()
    db.close()
    if not client or not _verify_password(password, client["password_hash"]):
        return jsonify({"error": "Invalid email or password"}), 401
    token = _create_session(client["id"])
    resp = jsonify({"client": dict(client)})
    resp.set_cookie("crm_token", token, max_age=7*24*60*60, httponly=True, samesite="Lax")
    return resp


@app.route("/api/auth/logout", methods=["POST"])
def auth_logout():
    token = request.cookies.get("crm_token")
    if token:
        db = get_db()
        db.execute("DELETE FROM sessions WHERE token = ?", (token,))
        db.commit()
        db.close()
    resp = jsonify({"status": "ok"})
    resp.delete_cookie("crm_token")
    return resp


@app.route("/api/auth/me")
def auth_me():
    token = request.cookies.get("crm_token")
    client = _get_client_from_session(token) if token else None
    if not client:
        return jsonify({"error": "Not authenticated"}), 401
    return jsonify({"client": client})


# ==================== IMPORT HELPERS ====================

@app.route("/api/import/leads", methods=["POST"])
def import_leads():
    """Bulk import leads from JSON array or CSV path."""
    data = request.json or {}
    leads = data.get("leads", [])
    path = data.get("path")
    db = get_db()
    imported = 0
    if path:
        try:
            import csv
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        db.execute(
                            "INSERT OR IGNORE INTO contacts (first_name, last_name, email, phone, company, source) VALUES (?, ?, ?, ?, ?, ?)",
                            (
                                row.get("owner_first_name", row.get("first_name", "")),
                                row.get("owner_last_name", row.get("last_name", "")),
                                row.get("email", ""),
                                row.get("phone", ""),
                                row.get("business_name", ""),
                                row.get("source", "import"),
                            ),
                        )
                        imported += 1
                    except Exception:
                        pass
        except Exception:
            pass
    else:
        for lead in leads:
            try:
                db.execute(
                    "INSERT OR IGNORE INTO contacts (first_name, last_name, email, phone, company, source) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        lead.get("owner_first_name", lead.get("first_name", "")),
                        lead.get("owner_last_name", lead.get("last_name", "")),
                        lead.get("email", ""),
                        lead.get("phone", ""),
                        lead.get("business_name", ""),
                        lead.get("source", "import"),
                    ),
                )
                imported += 1
            except Exception:
                pass
    db.commit()
    db.close()
    return jsonify({"imported": imported, "total": len(leads) if not path else imported})


@app.route("/api/import/activities", methods=["POST"])
def import_activities():
    """Bulk import outreach activities from JSON array."""
    data = request.json or {}
    activities = data.get("activities", [])
    db = get_db()
    imported = 0
    for act in activities:
        try:
            db.execute(
                "INSERT INTO activities (contact_id, deal_id, activity_type, direction, subject, body, outcome, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    act.get("contact_id"),
                    act.get("deal_id"),
                    act.get("activity_type", "email"),
                    act.get("direction", "outbound"),
                    act.get("subject", ""),
                    act.get("body", ""),
                    act.get("outcome", "sent"),
                    json.dumps(act.get("metadata", {})),
                ),
            )
            imported += 1
        except Exception:
            pass
    db.commit()
    db.close()
    return jsonify({"imported": imported, "total": len(activities)})


@app.route("/api/discover-leads", methods=["POST"])
def discover_leads():
    db = get_db()
    candidates = [
        {"first_name": "", "last_name": "", "email": "info@azcomfortexperts.com", "phone": "(480) 555-0107", "company": "Comfort Experts", "job_title": "Owner", "source": "auto-discovery"},
        {"first_name": "", "last_name": "", "email": "info@mastermechanicalaz.com", "phone": "(928) 555-0108", "company": "Master Mechanical", "job_title": "Owner", "source": "auto-discovery"},
        {"first_name": "", "last_name": "", "email": "info@blue-phx.com", "phone": "(480) 555-0109", "company": "Blue PHX", "job_title": "Owner", "source": "auto-discovery"},
        {"first_name": "", "last_name": "", "email": "dispatch@hughesairco.com", "phone": "(480) 555-0105", "company": "Hughes Air", "job_title": "Dispatch", "source": "auto-discovery"},
        {"first_name": "", "last_name": "", "email": "office@desertsunhvac.com", "phone": "(520) 555-0106", "company": "Desert Sun HVAC", "job_title": "Office", "source": "auto-discovery"},
    ]
    added = 0
    for c in candidates:
        try:
            db.execute(
                "INSERT OR IGNORE INTO contacts (first_name, last_name, email, phone, company, job_title, source) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    c.get("first_name", ""),
                    c.get("last_name", ""),
                    c.get("email", ""),
                    c.get("phone", ""),
                    c.get("company", ""),
                    c.get("job_title", ""),
                    c.get("source", "auto-discovery"),
                ),
            )
            added += 1
        except Exception:
            pass
    db.commit()
    db.close()
    return jsonify({"added": added, "status": "ok"})

@app.route("/api/activities", methods=["GET"])
def list_activities_filtered():
    db = get_db()
    contact_id = request.args.get("contact_id")
    deal_id = request.args.get("deal_id")
    activity_type = request.args.get("activity_type")
    query = "SELECT * FROM activities WHERE 1=1"
    params = []
    if contact_id:
        query += " AND contact_id = ?"
        params.append(contact_id)
    if deal_id:
        query += " AND deal_id = ?"
        params.append(deal_id)
    if activity_type:
        query += " AND activity_type = ?"
        params.append(activity_type)
    query += " ORDER BY created_at DESC LIMIT 200"
    rows = db.execute(query, params).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/activities", methods=["DELETE"])
def delete_activity():
    activity_id = request.args.get("id")
    if not activity_id:
        return jsonify({"error": "id required"}), 400
    db = get_db()
    db.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
    db.commit()
    db.close()
    return jsonify({"status": "deleted"})


@app.route("/api/contacts/<int:contact_id>/thread", methods=["GET"])
def contact_email_thread(contact_id: int):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM activities WHERE contact_id = ? AND activity_type = 'email' ORDER BY created_at ASC",
        (contact_id,),
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/send-email", methods=["POST"])
def send_email_endpoint():
    """
    Send a real email via Gmail SMTP and log it as an activity.
    Expected JSON:
    {
      "contact_id": 12,
      "to_email": "owner@example.com",
      "subject": "...",
      "body": "...",
      "send_type": "intro|follow_up|custom"
    }
    """
    data = request.json or {}
    to_email = data.get("to_email") or data.get("email") or ""
    subject = data.get("subject", "")
    body = data.get("body", "")
    contact_id = data.get("contact_id")
    send_type = data.get("send_type", "custom")

    if not to_email or not subject:
        return jsonify({"error": "to_email and subject are required"}), 400

    result = {"status": "error", "detail": "SMTP not configured"}
    try:
        if GmailSMTP:
            cfg_path = os.path.join(os.path.dirname(__file__), "integrations", "config.json")
            sender_password = ""
            loaded_cfg = {}
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    loaded_cfg = json.load(f)
                    sender_password = loaded_cfg.get("gmass", {}).get("app_password", "") or ""
            except Exception as e:
                app.logger.warning("send_email config load failed: %s", e)
            if not sender_password:
                sender_password = os.getenv("SENDER_PASSWORD", "")
            app.logger.info("send_email cfg_path=%s loaded=%s has_password=%s", cfg_path, bool(loaded_cfg), bool(sender_password))
            smtp = GmailSMTP(sender_password=sender_password)
            result = smtp.send_email(to_email=to_email, subject=subject, body=body)
        else:
            result = {"status": "skipped", "detail": "GmailSMTP unavailable"}
    except Exception as e:
        result = {"status": "error", "detail": str(e)}

    app.logger.info("SMTP send result: %s", result)

    db = get_db()
    db.execute(
        "INSERT INTO activities (contact_id, deal_id, activity_type, direction, subject, body, outcome, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            contact_id,
            None,
            "email",
            "outbound",
            subject,
            body,
            result.get("status", "error"),
            json.dumps({"to": to_email, "send_type": send_type, "smtp_result": result}),
        ),
    )
    db.commit()
    db.close()
    return jsonify({"smtp": result, "logged": True})


if __name__ == "__main__":
    init_db()
    print("[+] CRM initialized at", DB_PATH)
    app.run(host="127.0.0.1", port=5050, debug=False)


class LocalCRMClient:
    """Direct DB sync helper for outreach engine."""
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def sync_leads(self, leads):
        db = self._conn()
        for lead in leads:
            try:
                db.execute(
                    "INSERT OR IGNORE INTO contacts (first_name, last_name, email, phone, company, source) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        lead.get("owner_first_name", lead.get("first_name", "")),
                        lead.get("owner_last_name", lead.get("last_name", "")),
                        lead.get("email", ""),
                        lead.get("phone", ""),
                        lead.get("business_name", ""),
                        lead.get("source", "import"),
                    ),
                )
            except Exception:
                pass
        db.commit()
        db.close()

    def sync_deal(self, deal: Dict):
        db = self._conn()
        db.execute(
            "INSERT INTO deals (deal_name, package, monthly_value, stage, source) VALUES (?, ?, ?, ?, ?)",
            (
                deal.get("deal_name", ""),
                deal.get("package", "Basic"),
                deal.get("monthly_value", 0),
                deal.get("stage", "qualified"),
                "import",
            ),
        )
        db.commit()
        db.close()
