import sys
sys.path.insert(0, r"C:\Users\azelt\answerfirst-ai\crm")
import app
db = app.get_db()
new_hash = app._hash_password('Admin1!')
db.execute("UPDATE clients SET password_hash = ?, updated_at = ? WHERE email = ?", (new_hash, app.datetime.now().isoformat(), 'azelt.marketing@gmail.com'))
db.commit()
row = db.execute("SELECT id,email,role FROM clients WHERE email=?", ('azelt.marketing@gmail.com',)).fetchone()
print('Updated:', dict(row))
db.close()
