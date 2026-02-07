import sqlite3
from pathlib import Path

db_path = Path("backend-api/bandaru_pay.db")
if not db_path.exists():
    print(f"❌ SQLite database not found at {db_path}")
else:
    print(f"✅ SQLite database found: {db_path}")
    print(f"   Size: {db_path.stat().st_size / 1024:.2f} KB\n")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"📊 SQLITE DATABASE SUMMARY")
    print("=" * 60)
    
    total_rows = 0
    for table_name in tables:
        table = table_name[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        total_rows += count
        print(f"{table:30} │ {count:5} rows")
    
    print("=" * 60)
    print(f"{'TOTAL':30} │ {total_rows:5} rows\n")
    
    # Show key data
    print("🔍 KEY DATA DETAILS:")
    print("=" * 60)
    
    try:
        cursor.execute("SELECT COUNT(*) as count FROM users")
        print(f"Total Users: {cursor.fetchone()[0]}")
    except: pass
    
    try:
        cursor.execute("SELECT COUNT(*) as count FROM roles")
        print(f"Roles: {cursor.fetchone()[0]}")
    except: pass
    
    try:
        cursor.execute("SELECT COUNT(*) as count FROM schemes")
        print(f"Schemes: {cursor.fetchone()[0]}")
    except: pass
    
    try:
        cursor.execute("SELECT COUNT(*) as count FROM transactions")
        print(f"Transactions: {cursor.fetchone()[0]}")
    except: pass
    
    try:
        cursor.execute("SELECT COUNT(*) as count FROM mpin")
        print(f"MPINs: {cursor.fetchone()[0]}")
    except: pass
    
    try:
        cursor.execute("SELECT COUNT(*) as count FROM kyc_documents")
        print(f"KYC Documents: {cursor.fetchone()[0]}")
    except: pass
    
    try:
        cursor.execute("SELECT COUNT(*) as count FROM refresh_tokens")
        print(f"Refresh Tokens: {cursor.fetchone()[0]}")
    except: pass
    
    conn.close()
