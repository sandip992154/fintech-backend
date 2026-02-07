import sqlite3
import os

db_path = r"s:\Projects\New folder\BandruPay\backend-api\bandaru_pay.db"
os.chdir(r"s:\Projects\New folder\BandruPay\backend-api")

conn = sqlite3.connect('bandaru_pay.db')
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Tables in database:')
if tables:
    for t in tables:
        print(f'  - {t[0]}')
    
    # Check if users table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cursor.fetchone():
        print('\nUsers in database:')
        cursor.execute("SELECT user_code, username, email FROM users LIMIT 20")
        users = cursor.fetchall()
        if users:
            for u in users:
                print(f'  user_code: {u[0]}, username: {u[1]}, email: {u[2]}')
        else:
            print('  No users found')
else:
    print('  No tables found')

conn.close()
