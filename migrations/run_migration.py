import os
import sys
import logging
import psycopg2
from psycopg2 import sql

def run_migration():
    """Run database migrations"""
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Connected to the database successfully!")
        
        # First check if users table exists, if not create it
        cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'users'
        );
        """)
        
        users_table_exists = cursor.fetchone()[0]
        
        if not users_table_exists:
            print("Creating users table...")
            cursor.execute("""
            CREATE TABLE users (
                id VARCHAR(36) PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(256) NOT NULL,
                profile_pic VARCHAR(255) DEFAULT 'static/images/default_avatar.png',
                bio TEXT DEFAULT '',
                minecraft_username VARCHAR(50) DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            print("Users table created successfully!")
        else:
            print("Users table already exists.")
        
        # Read and execute SQL migrations
        with open('migrations/db_update.sql', 'r') as f:
            sql_script = f.read()
            
        print("Executing migrations...")
        cursor.execute(sql_script)
        print("Migrations completed successfully!")
        
        # Close the connection
        cursor.close()
        conn.close()
        print("Database connection closed.")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)