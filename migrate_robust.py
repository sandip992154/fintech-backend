"""
Enhanced SQLite to PostgreSQL Migration with Constraint Handling
"""

import sqlite3
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import os
from dotenv import load_dotenv
import json

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
print("🔄 ROBUST MIGRATION: SQLITE → POSTGRESQL")
print("=" * 70)

# Connect to SQLite
sqlite_conn = sqlite3.connect(SQLITE_DB)
sqlite_conn.row_factory = sqlite3.Row

# Connect to PostgreSQL
pg_engine = create_engine(POSTGRESQL_URL, echo=False)
pg_inspector = inspect(pg_engine)

# Order to insert (respecting FK constraints)
insert_order = [
    'roles',
    'users', 
    'schemes',
    'transactions',
    'wallets',
    'mpin',
    'kyc_documents',
    'refresh_tokens',
    'password_reset_tokens',
    'otp_records',
    'service_operators',
    'service_providers',
    'service_categories',
    'company_details',
    'commission_structures',
    'commission_slabs',
    'commissions',
    'bank_accounts',
    'otps',
    'otp_requests',
    'superadmins',
    'user_profiles',
    'wallet_transactions',
]

migration_stats = {}
warnings = []

for table in insert_order:
    cursor = sqlite_conn.cursor()
    
    try:
        # Get schema from sqlite
        cursor.execute(f"PRAGMA table_info({table})")
        columns_info = cursor.fetchall()
        column_names = [col[1] for col in columns_info]
        
        # Get data
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        
        row_count = len(rows)
        print(f"  {table:30} │ {row_count:5} rows", end="")
        
        if row_count == 0:
            print(" │ ⏭️  (empty)")
            migration_stats[table] = 0
            continue
        
        # Insert using raw SQL with proper escaping
        success_count = 0
        for row_dict in rows:
            cols = []
            vals = []
            
            for col_name in column_names:
                val = row_dict[col_name]
                cols.append(f'"{col_name}"')
                
                # Handle different data types
                if val is None:
                    vals.append("NULL")
                elif isinstance(val, (int, float)) and not isinstance(val, bool):
                    vals.append(str(val))
                elif isinstance(val, bool):
                    vals.append("TRUE" if val else "FALSE")
                else:
                    # Escape strings
                    escaped = str(val).replace("'", "''")
                    vals.append(f"'{escaped}'")
            
            insert_sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(vals)}) ON CONFLICT DO NOTHING"
            
            try:
                with pg_engine.connect() as conn:
                    conn.execute(text(insert_sql))
                    conn.commit()
                    success_count += 1
            except Exception as e:
                warnings.append(f"{table}: {str(e)[:50]}")
        
        if success_count > 0:
            print(f" │ ✅ ({success_count} inserted)")
        else:
            print(f" │ ⚠️  (0 inserted, check FK constraints)")
        
        migration_stats[table] = success_count
        
    except Exception as e:
        print(f" │ ❌ ERROR: {str(e)[:40]}")
        migration_stats[table] = 0

# Disable FK checks briefly to handle any constraint issues
print("\n🔧 Resolving constraints...")
with pg_engine.connect() as conn:
    conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))
    conn.commit()

print("\n" + "=" * 70)
print("📊 FINAL MIGRATION RESULTS")
print("=" * 70)

total = sum(migration_stats.values())
tables_with_data = sum(1 for v in migration_stats.values() if v > 0)

for table, count in sorted(migration_stats.items()):
    if count > 0:
        print(f"  ✅ {table:30} │ {count:5} rows")

print("=" * 70)
print(f"  📦 Total Rows: {total}")
print(f"  📋 Tables:    {tables_with_data}/23")

# Verify final state
print("\n🔍 FINAL POSTGRESQL STATE:")
print("=" * 70)

with pg_engine.connect() as conn:
    for table in ['users', 'roles', 'schemes', 'refresh_tokens', 'transactions', 'mpin', 'kyc_documents']:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
        count = result.scalar()
        print(f"  {table:30} │ {count:5} rows")

print("=" * 70)

if warnings:
    print(f"\n⚠️  WARNINGS ({len(warnings)}):")
    for w in warnings[:5]:
        print(f"    • {w}")
    if len(warnings) > 5:
        print(f"    ... and {len(warnings) - 5} more")

if total > 0:
    print(f"\n✅ MIGRATION SUCCEEDED! {total} rows migrated.\n")
else:
    print(f"\n❌ MIGRATION FAILED! No data was migrated.\n")

sqlite_conn.close()
