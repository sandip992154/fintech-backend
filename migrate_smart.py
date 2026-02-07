"""
Smart SQLite to PostgreSQL Migration with Type Conversion
Handles boolean, datetime, and other type conversions
"""

import sqlite3
from sqlalchemy import create_engine, text, Column, Integer, String, Boolean, DateTime, Float, inspect
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv("backend-api/.env")

SQLITE_DB = "backend-api/bandaru_pay.db"
POSTGRESQL_URL = os.getenv("DATABASE_URL")

if not POSTGRESQL_URL or not Path(SQLITE_DB).exists():
    print("❌ ERROR: Missing database connection or SQLite file")
    exit(1)

print("=" * 80)
print("🚀 SMART MIGRATION: SQLITE → POSTGRESQL WITH TYPE CONVERSION")
print("=" * 80)

# Connect to both databases
sqlite_conn = sqlite3.connect(SQLITE_DB)
sqlite_conn.row_factory = sqlite3.Row

pg_engine = create_engine(POSTGRESQL_URL, echo=False)
pg_inspector = inspect(pg_engine)

# Table insertion order (respecting FK constraints)
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

def convert_value(value, column_type_name):
    """Convert SQLite value to PostgreSQL compatible value"""
    if value is None:
        return None
    
    column_type = str(column_type_name).upper()
    
    # Handle boolean columns
    if 'BOOL' in column_type or 'is_' in column_type.lower():
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value != 0
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes', 'on']
        return False
    
    # Handle integer columns
    if 'INT' in column_type:
        try:
            return int(value)
        except:
            return None
    
    # Handle float columns
    if 'FLOAT' in column_type or 'DOUBLE' in column_type or 'DECIMAL' in column_type:
        try:
            return float(value)
        except:
            return None
    
    # Handle datetime columns
    if 'TIMESTAMP' in column_type or 'DATETIME' in column_type:
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                return value
        return value
    
    # String handling - escape single quotes
    if isinstance(value, str):
        return value
    
    return str(value)


migration_stats = {}
warnings_list = []

for table in insert_order:
    cursor = sqlite_conn.cursor()
    
    try:
        # Get schema info from both databases
        cursor.execute(f"PRAGMA table_info({table})")
        sqlite_cols = {col[1]: col[2] for col in cursor.fetchall()}
        column_names = list(sqlite_cols.keys())
        
        # Get PostgreSQL column types
        try:
            pg_cols = {col.name: col.type for col in pg_inspector.get_columns(table)}
        except:
            pg_cols = {}
        
        # Get rows from SQLite
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        
        row_count = len(rows)
        print(f"  {table:30} │ {row_count:5} rows", end="")
        
        if row_count == 0:
            print(" │ ⏭️  (empty)")
            migration_stats[table] = 0
            continue
        
        # Insert rows with type conversion
        success_count = 0
        error_count = 0
        
        for row_dict in rows:
            cols = []
            vals = []
            
            for col_name in column_names:
                val = row_dict[col_name]
                
                # Convert value based on column type
                pg_type = str(pg_cols.get(col_name, 'TEXT'))
                converted_val = convert_value(val, pg_type)
                
                cols.append(f'"{col_name}"')
                
                # Format value for SQL
                if converted_val is None:
                    vals.append("NULL")
                elif isinstance(converted_val, bool):
                    vals.append("TRUE" if converted_val else "FALSE")
                elif isinstance(converted_val, (int, float)):
                    vals.append(str(converted_val))
                elif isinstance(converted_val, datetime):
                    vals.append(f"'{converted_val.isoformat()}'")
                else:
                    # Escape quotes in strings
                    escaped = str(converted_val).replace("'", "''")
                    vals.append(f"'{escaped}'")
            
            insert_sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(vals)}) ON CONFLICT DO NOTHING"
            
            try:
                with pg_engine.connect() as conn:
                    conn.execute(text(insert_sql))
                    conn.commit()
                    success_count += 1
            except Exception as e:
                error_count += 1
                error_msg = str(e).split('\n')[0][:60]
                if error_msg not in [w[0] for w in warnings_list]:
                    warnings_list.append((error_msg, table))
        
        if success_count > 0:
            print(f" │ ✅ ({success_count} inserted)")
        elif error_count > 0:
            print(f" │ ⚠️  (0 inserted, type/constraint issues)")
        else:
            print(f" │ ⏭️  (skipped)")
        
        migration_stats[table] = success_count
        
    except Exception as e:
        print(f" │ ❌ ERROR: {str(e)[:40]}")
        migration_stats[table] = 0

# Verify final state
print("\n" + "=" * 80)
print("📊 MIGRATION RESULTS")
print("=" * 80)

total = sum(migration_stats.values())
tables_with_data = sum(1 for v in migration_stats.values() if v > 0)

for table, count in sorted(migration_stats.items()):
    if count > 0:
        status = "✅"
        print(f"  {status} {table:30} │ {count:5} rows migrated")

print("=" * 80)
print(f"  📦 Total Rows Migrated: {total}")
print(f"  📋 Tables Updated:      {tables_with_data}/23")

# Final verification
print("\n🔍 FINAL POSTGRESQL STATE:")
print("=" * 80)

with pg_engine.connect() as conn:
    for table in ['users', 'roles', 'schemes', 'refresh_tokens', 'transactions', 'mpin', 'kyc_documents', 'wallets']:
        try:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"  {table:30} │ {count:5} rows")
        except:
            print(f"  {table:30} │ ? rows (error reading)")

print("=" * 80)

if warnings_list:
    print(f"\n⚠️  KNOWN ISSUES ({len(set([w[1] for w in warnings_list]))} tables affected):")
    for warning, affected_table in list(set(warnings_list))[:5]:
        print(f"    • {affected_table}: {warning}")

if total > 0:
    print(f"\n✅ MIGRATION COMPLETED! {total} rows successfully migrated to PostgreSQL.\n")
else:
    print(f"\n⚠️  No data was migrated. Check database schemas and try again.\n")

sqlite_conn.close()
