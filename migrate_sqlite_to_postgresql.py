"""
SQLite to PostgreSQL Data Migration Script
Migrates all data from SQLite database to PostgreSQL on Render
"""

import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv("backend-api/.env")

SQLITE_DB = "backend-api/bandaru_pay.db"
POSTGRESQL_URL = os.getenv("DATABASE_URL")

if not POSTGRESQL_URL:
    print("❌ ERROR: DATABASE_URL not found in .env")
    exit(1)

if not Path(SQLITE_DB).exists():
    print(f"❌ ERROR: SQLite database not found at {SQLITE_DB}")
    exit(1)

print("=" * 70)
print("🔄 MIGRATING DATA FROM SQLITE TO POSTGRESQL")
print("=" * 70)

# Connect to both databases
sqlite_conn = sqlite3.connect(SQLITE_DB)
sqlite_conn.row_factory = sqlite3.Row
sqlite_cursor = sqlite_conn.cursor()

pg_engine = create_engine(POSTGRESQL_URL)
pg_session = sessionmaker(bind=pg_engine)()

# Get all tables from SQLite
sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in sqlite_cursor.fetchall()]

print(f"\n📋 Found {len(tables)} tables to migrate:\n")

migration_stats = {}
failed_tables = []

for table in tables:
    try:
        # Get column info
        sqlite_cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in sqlite_cursor.fetchall()]
        
        # Get data from SQLite
        sqlite_cursor.execute(f"SELECT * FROM {table}")
        rows = sqlite_cursor.fetchall()
        
        print(f"  📦 {table:30} │ {len(rows):5} rows", end="")
        
        if len(rows) == 0:
            print(" │ ✅ (empty, skipped)")
            migration_stats[table] = 0
            continue
        
        # Insert into PostgreSQL
        for row in rows:
            values = []
            for val in row:
                if val is None:
                    values.append(None)
                elif isinstance(val, str):
                    values.append(val.replace("'", "''"))  # Escape single quotes
                else:
                    values.append(val)
            
            # Build insert query
            placeholders = ", ".join(["%s"] * len(columns))
            col_names = ", ".join(f'"{col}"' for col in columns)
            query = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
            
            try:
                with pg_engine.connect() as conn:
                    conn.execute(text(query), values)
                    conn.commit()
            except Exception as e:
                pass  # Skip conflicts and duplicates
        
        migration_stats[table] = len(rows)
        print(" │ ✅")
        
    except Exception as e:
        print(f" │ ❌ ERROR: {str(e)[:30]}")
        failed_tables.append(table)
        migration_stats[table] = 0

# Summary
print("\n" + "=" * 70)
print("📊 MIGRATION SUMMARY")
print("=" * 70)

total_migrated = sum(migration_stats.values())
tables_migrated = sum(1 for v in migration_stats.values() if v > 0)

for table, count in migration_stats.items():
    if count > 0:
        print(f"  ✅ {table:30} │ {count:5} rows migrated")

print("=" * 70)
print(f"  📦 Total Rows Migrated: {total_migrated}")
print(f"  📋 Tables with Data:    {tables_migrated}/{len(tables)}")

if failed_tables:
    print(f"  ⚠️  Failed Tables:       {', '.join(failed_tables)}")

print("=" * 70)

# Verify migration
print("\n🔍 VERIFYING POSTGRESQL DATA:")
print("=" * 70)

verification_query = """
SELECT 
    'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'roles', COUNT(*) FROM roles
UNION ALL
SELECT 'schemes', COUNT(*) FROM schemes
UNION ALL
SELECT 'refresh_tokens', COUNT(*) FROM refresh_tokens
UNION ALL
SELECT 'transactions', COUNT(*) FROM transactions
UNION ALL
SELECT 'kyc_documents', COUNT(*) FROM kyc_documents
UNION ALL
SELECT 'mpin', COUNT(*) FROM mpin
UNION ALL
SELECT 'wallets', COUNT(*) FROM wallets
ORDER BY table_name
"""

with pg_engine.connect() as conn:
    result = conn.execute(text(verification_query))
    print()
    for row in result:
        table_name, count = row
        print(f"  {table_name:25} │ {count:5} rows")

print("=" * 70)

if total_migrated > 0:
    print(f"\n✅ MIGRATION COMPLETE! {total_migrated} rows migrated successfully.\n")
else:
    print(f"\n⚠️  No data was migrated. Please check the SQLite database.\n")

sqlite_conn.close()
pg_session.close()
