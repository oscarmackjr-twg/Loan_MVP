# Database Initialization and Seed Scripts

## Initialize Database Tables

Before creating users or running the application, you need to initialize the database tables.

### Option 1: Using init_db.py (Quick Setup)

For development or quick setup:

```bash
# From the backend directory
python scripts/init_db.py

# To drop and recreate all tables (WARNING: deletes all data)
python scripts/init_db.py --drop-existing
```

This script:
- Creates all tables from SQLAlchemy models
- Shows which tables were created
- Provides next steps

### Option 2: Using Alembic Migrations (Recommended for Production)

For production environments, use Alembic migrations:

```bash
# Create initial migration (first time only)
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

### Option 3: Manual SQL (PostgreSQL)

If you prefer to use raw SQL:

```sql
-- Connect to your database
psql -d loan_engine

-- Then run the table creation SQL (see below)
```

### After Initializing Tables

1. **Apply the sales team constraint** (PostgreSQL only):
   ```bash
   psql -d loan_engine -f backend/db/migrations/add_sales_team_constraint.sql
   ```

2. **Create initial admin user** (see below)

## Create Initial Admin User

To create the first admin user in your database, run:

```bash
# From the backend directory
python scripts/seed_admin.py

# Or with custom credentials
python scripts/seed_admin.py \
  --username admin \
  --password your_secure_password \
  --email admin@yourcompany.com \
  --full-name "Admin User"
```

### Database Configuration

The seed script connects to the database using the same configuration as the main application:

1. **Environment Variables** (highest priority)
   ```bash
   export DATABASE_URL="postgresql://user:password@host:port/database"
   ```

2. **`.env` file** (in the `backend/` directory)
   ```env
   DATABASE_URL=postgresql://user:password@host:port/database
   ```

3. **Default** (fallback)
   ```
   postgresql://postgres:postgres@localhost:5432/loan_engine
   ```

#### Example Database URLs

**PostgreSQL:**
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/loan_engine
```

**PostgreSQL with custom user:**
```env
DATABASE_URL=postgresql://myuser:mypassword@localhost:5432/loan_engine
```

**PostgreSQL on remote server:**
```env
DATABASE_URL=postgresql://user:password@db.example.com:5432/loan_engine
```

**SQLite (for development):**
```env
DATABASE_URL=sqlite:///./loan_engine.db
```

### Default Credentials

If you use the default settings:
- **Username**: `admin`
- **Password**: `admin123`
- **Email**: `admin@example.com`

⚠️ **Important**: Change the password immediately after first login!

### After Creating Admin User

Once you have an admin user, you can:
1. Log in to the application
2. Use the `/api/auth/register` endpoint to create additional users
3. Or use the admin interface to manage users

### Database permissions (“permission denied for table users”)

If `seed_admin.py` fails with **permission denied for table users**, the database user in `DATABASE_URL` lacks privileges.

**Option A – Run seed as superuser (quick fix)**

Use the PostgreSQL superuser (e.g. `postgres`) in `DATABASE_URL` when running the seed:

```bash
# Windows (cmd)
set DATABASE_URL=postgresql://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/cursor_db
python scripts/seed_admin.py

# Windows (PowerShell)
$env:DATABASE_URL="postgresql://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/cursor_db"
python scripts/seed_admin.py
```

**Option B – Grant privileges to your app user**

1. Identify the app user (the username in `DATABASE_URL`; e.g. `myuser` in `postgresql://myuser:pass@localhost:5432/cursor_db`).
2. Connect as superuser and grant permissions:

```bash
psql -U postgres -d cursor_db
```

```sql
-- Replace your_app_user with your DATABASE_URL username
GRANT USAGE ON SCHEMA public TO your_app_user;
GRANT SELECT ON sales_teams TO your_app_user;
GRANT SELECT, INSERT, UPDATE ON users TO your_app_user;
GRANT USAGE, SELECT ON SEQUENCE users_id_seq TO your_app_user;
```

3. Run `seed_admin.py` again using your normal `DATABASE_URL`.

**Option C – Use the grant script**

1. Open `db/migrations/grant_app_permissions.sql`.
2. Replace `YOUR_APP_USER` with your `DATABASE_URL` username.
3. Run:

```bash
psql -U postgres -d cursor_db -f db/migrations/grant_app_permissions.sql
```

## Complete Setup Guide

For detailed database setup instructions, see:
- **[DATABASE_SETUP.md](DATABASE_SETUP.md)** - Complete database initialization guide

## Available Scripts

| Script | Purpose |
|--------|---------|
| `init_db.py` | Initialize/create all database tables |
| `seed_admin.py` | Create initial admin user |
| `create_tables.sql` | SQL reference for manual table creation |
| `check_input_files.py` | Check if required input files exist |

## Quick Start

```bash
# 1. Initialize database tables
python scripts/init_db.py

# 2. Apply constraint (PostgreSQL only)
psql -d loan_engine -f backend/db/migrations/add_sales_team_constraint.sql

# 3. Create admin user
python scripts/seed_admin.py

# 4. Check input files (before running pipeline)
python scripts/check_input_files.py --folder "C:/path/to/your/input/folder"

# 5. Start application
uvicorn api.main:app --reload
```

## Check Input Files

Before running the pipeline, verify your input files are in place:

```bash
# Check default input directory
python scripts/check_input_files.py

# Check specific directory
python scripts/check_input_files.py --folder "C:/Users/omack/Intrepid/pythonFramework/loan_engine/legacy"
```

This script will:
- List all files in the `files_required/` directory
- Check for required files (Tape20Loans, SFY, PRIME, reference files)
- Show which files are missing
- Display expected file names with dates

For detailed file structure requirements, see: **[docs/FILE_STRUCTURE.md](../docs/FILE_STRUCTURE.md)**
