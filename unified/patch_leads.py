from pathlib import Path

text = Path('C:/Users/azelt/answerfirst-ai/unified/app.py').read_text()

old = '''# ===================== LEADS API =====================

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

# ===================== CALLS API ====================='''

new = '''# ===================== LEADS API =====================

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

# ===================== CALLS API ====================='''

if old in text:
    text = text.replace(old, new)
    Path('C:/Users/azelt/answerfirst-ai/unified/app.py').write_text(text)
    print('Patched leads API')
else:
    print('ERROR: old block not found')
