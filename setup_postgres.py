#!/usr/bin/env python3
"""
PostgreSQL database setup script for Options Trading application.
"""
import asyncio
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_config():
    """Get database configuration from environment variables."""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'options_trading'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'password')
    }

def create_database():
    """Create the database if it doesn't exist."""
    config = get_db_config()
    
    # Connect to PostgreSQL server (not to a specific database)
    engine = create_engine(
        f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/postgres"
    )
    
    try:
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{config['database']}'"))
            if not result.fetchone():
                # Create database
                conn.execute(text(f"CREATE DATABASE {config['database']}"))
                conn.commit()
                print(f"✅ Database '{config['database']}' created successfully")
            else:
                print(f"✅ Database '{config['database']}' already exists")
    except OperationalError as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        print("\nPlease ensure:")
        print("1. PostgreSQL is installed and running")
        print("2. Database credentials are correct in .env file")
        print("3. PostgreSQL server is accessible")
        return False
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False
    
    return True

async def test_connection():
    """Test the database connection."""
    from app.db import engine
    
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version}")
            return True
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Setting up PostgreSQL database for Options Trading application...")
    
    # Step 1: Create database
    print("\n1. Creating database...")
    if not create_database():
        sys.exit(1)
    
    # Step 2: Test connection
    print("\n2. Testing connection...")
    if not asyncio.run(test_connection()):
        sys.exit(1)
    
    print("\n✅ PostgreSQL setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the application: python run.py")
    print("2. Access the web interface: http://localhost:8000")

if __name__ == "__main__":
    main()
