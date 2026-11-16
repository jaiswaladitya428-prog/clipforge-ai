import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "clipforge.db"

def show_users():
    if not db_path.exists():
        print(f"Database file not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    print("\n" + "="*80)
    print(f"CLIPFORGE AI - USER DATABASE ({db_path})")
    print("="*80)
    
    cur.execute("""
        SELECT u.id, u.name, u.email, u.password_hash, u.created_at, COUNT(p.id)
        FROM users u
        LEFT JOIN projects p ON p.user_id = u.id
        GROUP BY u.id
        ORDER BY u.created_at DESC
    """)
    rows = cur.fetchall()
    
    if not rows:
        print("No registered users found.")
    else:
        for r in rows:
            user_id, name, email, pw_hash, created_at, proj_count = r
            print(f"Name         : {name}")
            print(f"Email        : {email}")
            print(f"Projects     : {proj_count}")
            print(f"Registered At: {created_at}")
            print(f"Password Hash: {pw_hash}  (Bcrypt encrypted)")
            print("-" * 80)
    
    conn.close()

if __name__ == "__main__":
    show_users()
