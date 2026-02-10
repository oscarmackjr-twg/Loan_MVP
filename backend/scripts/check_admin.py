"""Check if admin user exists in the database."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from db.connection import SessionLocal
from db.models import User, UserRole
from config.settings import settings


def check_admin_user():
    """Check if admin user exists."""
    print(f"Connecting to database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    db: Session = SessionLocal()
    
    try:
        # Check for admin user by username or email
        admin = db.query(User).filter(
            (User.username == "admin") | (User.email == "admin@example.com")
        ).first()
        
        if admin:
            print("\n✅ Admin user EXISTS:")
            print(f"   Username: {admin.username}")
            print(f"   Email: {admin.email}")
            print(f"   Role: {admin.role.value}")
            print(f"   Active: {admin.is_active}")
            print(f"   ID: {admin.id}")
            print("\n   You can log in with:")
            print(f"   Username: {admin.username}")
            print(f"   Password: (check with seed_admin.py or reset it)")
            return True
        else:
            print("\n❌ Admin user NOT FOUND")
            print("\n   To create the admin user, run:")
            print("   python scripts/seed_admin.py")
            print("\n   Default credentials:")
            print("   Username: admin")
            print("   Password: admin123")
            print("   Email: admin@example.com")
            return False
            
    except Exception as e:
        print(f"\n❌ Error checking admin user: {e}")
        print("\n   Possible issues:")
        print("   1. Database not running")
        print("   2. Tables not created (run: python scripts/init_db.py)")
        print("   3. DATABASE_URL incorrect (check backend/.env)")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    check_admin_user()
