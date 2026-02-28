from database.database import engine
from sqlalchemy import text

try:
    conn = engine.connect()
    print("PostgreSQL connected OK")
    
    # List tables
    rows = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'")).fetchall()
    print("Tables:", [r[0] for r in rows])
    
    # Check users
    users = conn.execute(text("SELECT id, username, email, role_id, is_active FROM users LIMIT 5")).fetchall()
    print(f"\nUsers ({len(users)}):")
    for u in users:
        print(f"  id={u[0]}, username={u[1]}, email={u[2]}, role_id={u[3]}, is_active={u[4]}")
    
    # Check roles
    roles = conn.execute(text("SELECT id, name FROM roles")).fetchall()
    print(f"\nRoles ({len(roles)}):")
    for r in roles:
        print(f"  id={r[0]}, name={r[1]}")

    # Check superadmin password hash exists
    sa = conn.execute(text("SELECT username, password_hash FROM users WHERE username='superadmin'")).fetchone()
    if sa:
        print(f"\nSuperadmin password_hash exists: {bool(sa[1])}")
        print(f"  Hash starts with: {sa[1][:30]}..." if sa[1] else "  Hash is NULL/empty")
    else:
        print("\nSuperadmin user NOT FOUND!")
    
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
