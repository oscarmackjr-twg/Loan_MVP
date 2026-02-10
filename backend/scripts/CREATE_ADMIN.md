# Create Admin User - Quick Guide

If you cannot log in, follow these steps to check if the admin user exists and create it if needed.

---

## Step 1: Check if Admin User Exists

```powershell
cd backend
python scripts/check_admin.py
```

**If admin exists**: You'll see the username, email, and role. Try logging in with:
- **Username**: `admin`
- **Password**: `admin123` (or whatever was set when created)

**If admin does NOT exist**: Continue to Step 2.

---

## Step 2: Create Admin User

```powershell
cd backend
python scripts/seed_admin.py
```

This will:
- Create admin user with default credentials
- Show you the username and password
- Handle database permission errors with helpful messages

**Default credentials**:
- **Username**: `admin`
- **Password**: `admin123`
- **Email**: `admin@example.com`

---

## Step 3: Verify Creation

Run the check script again:

```powershell
python scripts/check_admin.py
```

You should see "✅ Admin user EXISTS" with the details.

---

## Troubleshooting

### "Table users does not exist"

**Fix**: Create database tables first:

```powershell
python scripts/init_db.py
```

Then run `seed_admin.py` again.

### "Permission denied for table users"

**Fix**: The database user lacks privileges. Options:

**Option A - Use superuser** (quickest):

```powershell
# PowerShell
$env:DATABASE_URL="postgresql://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/your_database"
python scripts/seed_admin.py
```

**Option B - Grant privileges** (see `scripts/README.md` section "Database permissions")

### "Database connection failed"

**Fix**: 
1. Check PostgreSQL is running
2. Verify `DATABASE_URL` in `backend/.env` or environment variable
3. Test connection: `psql $DATABASE_URL -c "SELECT 1"`

---

## Custom Credentials

To create admin with custom credentials:

```powershell
python scripts/seed_admin.py --username myadmin --password MySecurePass123 --email admin@mycompany.com
```

---

## Reset Admin Password

If you need to reset the admin password back to default (`admin123`):

```powershell
cd backend
python scripts/reset_admin_password.py
```

Or set a custom password:

```powershell
python scripts/reset_admin_password.py --password MyNewPassword123
```

Or reset password for a different username:

```powershell
python scripts/reset_admin_password.py --username myadmin --password admin123
```

## Quick Commands Summary

```powershell
# Check if admin exists
cd backend
python scripts/check_admin.py

# Create admin (if missing)
python scripts/seed_admin.py

# Reset admin password
python scripts/reset_admin_password.py

# Verify
python scripts/check_admin.py
```
