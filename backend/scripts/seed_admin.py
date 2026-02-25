"""Seed script to create initial admin user.

Database Connection:
The script uses the same database configuration as the main application:
1. Environment variable DATABASE_URL (highest priority)
2. .env file in backend/ directory
3. Default: postgresql://postgres:postgres@localhost:5432/loan_engine

To change the database, set DATABASE_URL environment variable or create a .env file:
    DATABASE_URL=postgresql://user:password@host:port/database
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from db.connection import SessionLocal
from db.models import User, UserRole
from auth.security import get_password_hash, BCRYPT_MAX_PASSWORD_BYTES
from config.settings import settings


def create_admin_user(
    username: str = "admin",
    password: str = "admin123",
    email: str = "admin@example.com",
    full_name: str = "Administrator"
):
    """Create initial admin user.
    
    Args:
        username: Admin username
        password: Admin password (will be hashed)
        email: Admin email address
        full_name: Admin full name
    """
    # Bcrypt limits passwords to 72 bytes
    pwd_bytes = password.encode("utf-8")
    if len(pwd_bytes) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError(
            f"Password is too long ({len(pwd_bytes)} bytes). "
            f"Bcrypt allows at most {BCRYPT_MAX_PASSWORD_BYTES} bytes."
        )

    print(f"Connecting to database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    db: Session = SessionLocal()
    
    try:
        # Check if admin already exists
        existing = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing:
            print(f"User already exists: {existing.username} ({existing.email})")
            return existing
        
        # Create admin user
        admin_user = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"✅ Admin user created successfully!")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print(f"\n⚠️  Please change the password after first login!")
        
        return admin_user
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admin user: {e}")

        # Provide helpful guidance for permission errors
        err_str = str(e).lower()
        if "permission denied" in err_str or "insufficientprivilege" in err_str:
            _print_permission_help()
        raise
    finally:
        db.close()


def create_user_if_missing(
    username: str,
    password: str,
    email: str,
    full_name: str,
    role: UserRole = UserRole.ANALYST,
):
    pwd_bytes = password.encode("utf-8")
    if len(pwd_bytes) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError(
            f"Password is too long ({len(pwd_bytes)} bytes). "
            f"Bcrypt allows at most {BCRYPT_MAX_PASSWORD_BYTES} bytes."
        )

    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing:
            print(f"User already exists: {existing.username} ({existing.email})")
            return existing

        user = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role=role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ User created: {username} ({email}) [role={role.value}]")
        return user
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating user {username}: {e}")
        raise
    finally:
        db.close()


def _print_permission_help():
    """Print guidance when database permission errors occur."""
    print("\n" + "=" * 60)
    print("DATABASE PERMISSION ERROR")
    print("=" * 60)
    print("The database user in DATABASE_URL lacks privileges on the tables.")
    print("\nOptions:")
    print("1. Run seed_admin using a superuser (e.g. postgres):")
    print("   CMD:  set DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/cursor_db")
    print("   PS:   $env:DATABASE_URL=\"postgresql://postgres:YOUR_PASSWORD@localhost:5432/cursor_db\"")
    print("   Then: python scripts/seed_admin.py")
    print("\n2. Grant privileges (run as superuser, e.g. psql -U postgres -d cursor_db):")
    print("   -- Replace 'your_app_user' with the user from your DATABASE_URL")
    print("   GRANT USAGE ON SCHEMA public TO your_app_user;")
    print("   GRANT SELECT ON sales_teams TO your_app_user;")
    print("   GRANT SELECT, INSERT, UPDATE ON users TO your_app_user;")
    print("   GRANT USAGE, SELECT ON SEQUENCE users_id_seq TO your_app_user;")
    print("\n3. See scripts/README.md section 'Database permissions' for full GRANT examples.")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create initial admin user and default team users")
    parser.add_argument("--username", default="admin", help="Admin username")
    parser.add_argument("--password", default="admin123", help="Admin password")
    parser.add_argument("--email", default="admin@example.com", help="Admin email")
    parser.add_argument("--full-name", default="Administrator", help="Admin full name")
    
    args = parser.parse_args()

    admin = create_admin_user(
        username=args.username,
        password=args.password,
        email=args.email,
        full_name=args.full_name
    )

    # Seed additional default users with initial password twg123
    default_password = "twg123"
    additional_users = [
        ("nparakh", "nparakh@example.com", "nparakh"),
        ("jbalaji", "jbalaji@example.com", "jbalaji"),
        ("gdehankar", "gdehankar@example.com", "gdehankar"),
        ("hkhandelwal", "hkhandelwal@example.com", "hkhandelwal"),
    ]

    for username, email, full_name in additional_users:
        try:
            create_user_if_missing(
                username=username,
                password=default_password,
                email=email,
                full_name=full_name,
                role=UserRole.ANALYST,
            )
        except Exception:
            # Errors are printed inside create_user_if_missing; continue with others
            continue
