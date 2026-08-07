from pathlib import Path

text = Path('C:/Users/azelt/answerfirst-ai/unified/app.py').read_text()

# 1. Add JWT_SECRET after imports
old_import = "from flask_cors import CORS\n"
new_import = "from flask_cors import CORS\nJWT_SECRET = os.environ.get('JWT_SECRET', secrets.token_hex(32))\n"
text = text.replace(old_import, new_import)

# 2. Replace create_session -> create_jwt
old_create = '''def create_session(client_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires = datetime.now().timestamp() + 7 * 24 * 60 * 60
    db = get_db()
    db.execute(
        "INSERT INTO sessions (token, client_id, expires_at) VALUES (?, ?, ?)",
        (token, client_id, datetime.fromtimestamp(expires).isoformat()),
    )
    db.commit()
    db.close()
    return token'''
new_create = '''def create_jwt(client_id: int) -> str:
    payload = {
        'client_id': client_id,
        'exp': datetime.now().timestamp() + 7 * 24 * 60 * 60,
        'iat': datetime.now().timestamp()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')'''
text = text.replace(old_create, new_create)

# 3. Replace get_client_from_session to use JWT
old_gc = '''def get_client_from_session(token: str):
    db = get_db()
    row = db.execute(
        "SELECT c.* FROM sessions s JOIN clients c ON s.client_id = c.id WHERE s.token = ? AND s.expires_at > ?",
        (token, datetime.now().isoformat()),
    ).fetchone()
    db.close()
    return dict(row) if row else None'''
new_gc = '''def get_client_from_session(token: str):
    if not token:
        return None
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    except Exception:
        return None
    db = get_db()
    row = db.execute('SELECT * FROM clients WHERE id = ?', (data['client_id'],)).fetchone()
    db.close()
    return dict(row) if row else None'''
text = text.replace(old_gc, new_gc)

# 4. Replace require_client to use header fallback
old_rc = '''def require_client():
    token = request.cookies.get("portal_token")
    client = get_client_from_session(token) if token else None
    if not client:
        return None
    return client'''
new_rc = '''def require_client():
    token = request.cookies.get('portal_token') or request.headers.get('X-Portal-Token')
    client = get_client_from_session(token) if token else None
    if not client:
        return None
    return client'''
text = text.replace(old_rc, new_rc)

# 5. Fix call sites: create_session -> create_jwt
text = text.replace('create_session(', 'create_jwt(')

# 6. Fix login/register responses to set cookie
old_login_resp = '''    token = create_session(client['id'])
    return jsonify({
        'status': 'ok',
        'client_id': client['id'],
        'email': client['email'],
        'business_name': client['business_name'],
        'contact_name': client['contact_name'],
        '_session_token': token
    }), 200'''
new_login_resp = '''    token = create_jwt(client['id'])
    resp = make_response(jsonify({
        'status': 'ok',
        'client_id': client['id'],
        'email': client['email'],
        'business_name': client['business_name'],
        'contact_name': client['contact_name'],
        '_session_token': token
    }))
    resp.set_cookie('portal_token', token, max_age=7*24*60*60, httponly=True, samesite='Lax')
    return resp, 200'''
text = text.replace(old_login_resp, new_login_resp)

old_reg_resp = '''        token = create_jwt(client_id)
        return jsonify({'status': 'ok', 'client_id': client_id, '_session_token': token}), 201'''
new_reg_resp = '''        token = create_jwt(client_id)
        resp = make_response(jsonify({'status': 'ok', 'client_id': client_id, '_session_token': token}))
        resp.set_cookie('portal_token', token, max_age=7*24*60*60, httponly=True, samesite='Lax')
        return resp, 201'''
text = text.replace(old_reg_resp, new_reg_resp)

Path('C:/Users/azelt/answerfirst-ai/unified/app.py').write_text(text)
print('Auth fully converted to JWT')
