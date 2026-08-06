import sys
sys.path.insert(0, r"C:\Users\azelt\answerfirst-ai\crm")
import app
db = app.get_db()
print(app._hash_password('Admin1!'))
db.execute("INSERT OR IGNORE INTO clients (email, password_hash, role) VALUES (?, ?, ?)", ('azelt.marketing@gmail.com', app._hash_password('Admin1!'), 'admin'))
db.commit()
row = db.execute("SELECT id,email,role FROM clients WHERE email=?", ('azelt.marketing@gmail.com',)).fetchone()
print(dict(row))
db.close()
