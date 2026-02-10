"""Reset admin user password.

This script updates the password for an existing admin user.
Useful if you forgot the password or need to reset it to default.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from db.connection import SessionLocal
from db.models import User
from auth.security import get_password_hash, BCRYPT_MAX_PASSWORD_BYTES
from config.settings import settings


def reset_admin_password(
    username: str = "admin",
    new_password: str = "admin123"
):
    """Reset admin user password.
    
    Args:
        username: Admin username to reset (default: "admin")
        new_password: New password to set (default: "admin123")
    """
    # Validate password length
    pwd_bytes = new_password.encode("utf-8")
    if len(pwd_bytes) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError(
            f"Password is too long ({len(pwd_bytes)} bytes). "
            f"Bcrypt allows at most {BCRYPT_MAX_PASSWORD_BYTES} bytes."
        )

    print(f"Connecting to database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    db: Session = SessionLocal()
    
    try:
        # Find admin user
        admin = db.query(User).filter(User.username == username).first()
        
        if not admin:
            print(f"\n❌ User '{username}' not found!")
            print("\n   Available options:")
            print("   1. Check if admin exists: python scripts/check_admin.py")
            print("   2. Create admin user: python scripts/seed_admin.py")
            return False
        
        # Update password
        admin.hashed_password = get_password_hash(new_password)
        admin.is_active = True  # Ensure user is active
        
        db.commit()
        db.refresh(admin)
        
        print(f"\n✅ Password reset successfully!")
        print(f"   Username: {admin.username}")
        print(f"   Email: {admin.email}")
        print(f"   New Password: {new_password}")
        print(f"   Role: {admin.role.value}")
        print(f"\n   You can now log in with:")
        print(f"   Username: {admin.username}")
        print(f"   Password: {new_password}")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error resetting password: {e}")
        
        # Provide helpful guidance for permission errors
        err_str = str(e).lower()
        if "permission denied" in err_str or "insufficientprivilege" in err_str:
            print("\n" + "=" * 60)
            print("DATABASE PERMISSION ERROR")
            print("=" * 60)
            print("The database user lacks UPDATE privileges on the users table.")
            print("\nOptions:")
            print("1. Run script using a superuser (e.g. postgres):")
            print("   PowerShell: $env:DATABASE_URL=\"postgresql://postgres:YOUR_PASSWORD@localhost:5432/your_db\"")
            print("   Then: python scripts/reset_admin_password.py")
            print("\n2. Grant UPDATE privilege (as superuser):")
            print("   GRANT UPDATE ON users TO your_app_user;")
            print("=" * 60)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Reset admin user password")
    parser.add_argument(
        "--username",
        default="admin",
        help="Admin username to reset (default: admin)"
    )
    parser.add_argument(
        "--password",
        default="admin123",
        help="New password (default: admin123)"
    )
    
    args = parser.parse_args()
    
    reset_admin_password(
        username=args.username,
        new_password=args.password
    )
