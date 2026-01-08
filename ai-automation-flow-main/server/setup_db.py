#!/usr/bin/env python3
"""
Setup script for initializing the database with required tables
"""

import os
import psycopg2
from pathlib import Path


def run_migration(conn, migration_file):
    """Execute a migration SQL file"""
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        conn.commit()
        print(f"✓ Executed migration: {migration_file}")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"✗ Migration failed: {migration_file}")
        print(f"  Error: {e}")
        raise
    finally:
        cursor.close()


def setup_database():
    """Initialize database with all required tables"""
    db_url = os.environ.get(
        'DATABASE_URL',
        'postgresql://user:password@localhost:5432/automation_platform'
    )
    
    print("Connecting to database...")
    try:
        conn = psycopg2.connect(db_url)
        print("✓ Connected to database")
    except psycopg2.Error as e:
        print(f"✗ Failed to connect to database: {e}")
        return False
    
    try:
        # Get the directory of this script
        script_dir = Path(__file__).parent
        migrations_dir = script_dir / 'migrations'
        
        # Get all migration files in order
        migration_files = sorted(migrations_dir.glob('*.sql'))
        
        if not migration_files:
            print("No migration files found")
            return False
        
        print(f"\nExecuting {len(migration_files)} migrations...\n")
        
        for migration_file in migration_files:
            run_migration(conn, migration_file)
        
        print("\n✓ Database setup completed successfully!")
        return True
    
    finally:
        conn.close()


if __name__ == '__main__':
    import sys
    success = setup_database()
    sys.exit(0 if success else 1)
