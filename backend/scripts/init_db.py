"""Initialize database tables.

This script creates all database tables from the SQLAlchemy models.
It's useful for initial setup or development environments.

For production, use Alembic migrations instead.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.connection import Base, engine
from db.models import *  # noqa: F401, F403
from config.settings import settings


def init_database(drop_existing: bool = False):
    """Initialize database tables.
    
    Args:
        drop_existing: If True, drop all existing tables before creating new ones.
                      WARNING: This will delete all data!
    """
    print(f"Connecting to database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    
    if drop_existing:
        print("WARNING: Dropping all existing tables...")
        response = input("This will delete all data. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return
    
    try:
        if drop_existing:
            print("Dropping existing tables...")
            Base.metadata.drop_all(bind=engine)
        
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        print("Database tables created successfully!")
        print("\nTables created:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
        
        print("\nNext steps:")
        print("1. Apply the sales team constraint migration:")
        print("   psql -d loan_engine -f backend/db/migrations/add_sales_team_constraint.sql")
        print("   OR if using SQLite, run the constraint manually")
        print("2. Create initial admin user:")
        print("   python scripts/seed_admin.py")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize database tables")
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop existing tables before creating new ones (WARNING: deletes all data)"
    )
    
    args = parser.parse_args()
    
    init_database(drop_existing=args.drop_existing)
