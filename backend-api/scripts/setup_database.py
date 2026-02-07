import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def setup_database():
    try:
        # Connect to PostgreSQL server
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="root",
            host="localhost"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname='bandaru_pay'")
        exists = cur.fetchone()
        
        if not exists:
            # Create database
            cur.execute('CREATE DATABASE bandaru_pay')
            print("Database created successfully!")
        else:
            print("Database already exists!")
            
        cur.close()
        conn.close()
        
        # Test connection to the new database
        conn = psycopg2.connect(
            dbname="bandaru_pay",
            user="postgres",
            password="root",
            host="localhost"
        )
        print("Successfully connected to bandaru_pay database!")
        conn.close()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nPlease ensure:")
        print("1. PostgreSQL is installed and running")
        print("2. The user 'postgres' exists with password 'root'")
        print("3. PostgreSQL is running on localhost:5432")

if __name__ == "__main__":
    setup_database()