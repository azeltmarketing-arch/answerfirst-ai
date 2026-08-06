import sqlite3
import hashlib

db_path = r"C:\Users\azelt\answerfirst-ai\unified\portal.db"
email = "azelt.marketing@gmail.com"
new_password = "Admin1!"

password_hash = hashlib.sha256(new_password.encode("utf-8")).hexdigest()

with sqlite3.connect(db_path) as conn:
    cur = conn.cursor()
    cur.execute("UPDATE clients SET password_hash = ? WHERE email = ?", (password_hash, email))
    conn.commit()
    print("Updated password for:", email)
