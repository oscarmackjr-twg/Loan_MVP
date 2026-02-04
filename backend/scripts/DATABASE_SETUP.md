# Database Setup Guide

This guide explains how to initialize and set up the database for the loan engine application.

## Prerequisites

1. **Database Server**: PostgreSQL (recommended) or SQLite (for development)
2. **Database Created**: Create the database before running initialization
   ```sql
   -- PostgreSQL
   CREATE DATABASE loan_engine;
   
   -- SQLite (automatic, just specify path in DATABASE_URL)
   ```

3. **Environment Configuration**: Set `DATABASE_URL` in environment or `.env` file

## Initialization Methods

### Method 1: Python Script (Recommended for Development)

The simplest way to initialize tables:

```bash
cd backend
python scripts/init_db.py
```

**What it does:**
- Creates all tables from SQLAlchemy models
- Safe to run multiple times (won't recreate existing tables)
- Shows which tables were created

**Options:**
```bash
# Drop and recreate all tables (WARNING: deletes all data)
python scripts/init_db.py --drop-existing
```

### Method 2: Alembic Migrations (Recommended for Production)

For production environments, use Alembic for version-controlled migrations:

```bash
cd backend

# Create initial migration (first time only)
alembic revision --autogenerate -m "Initial schema"

# Review the generated migration in migrations/versions/
# Then apply it
alembic upgrade head
```

**Benefits:**
- Version control for schema changes
- Can rollback migrations
- Better for team collaboration
- Production-ready

### Method 3: Manual SQL Execution

If you need more control, you can execute SQL directly:

```bash
# PostgreSQL
psql -d loan_engine -f backend/scripts/create_tables.sql

# Or connect interactively
psql -d loan_engine
\i backend/scripts/create_tables.sql
```

## Database Tables

The following tables are created:

1. **users** - User accounts and authentication
2. **sales_teams** - Sales team definitions for multi-tenancy
3. **pipeline_runs** - Pipeline execution tracking
4. **loan_exceptions** - Loan validation exceptions
5. **loan_facts** - Processed loan data for analytics

## Post-Initialization Steps

### 1. Apply Sales Team Constraint (PostgreSQL)

After creating tables, apply the constraint to ensure data integrity:

```bash
psql -d loan_engine -f backend/db/migrations/add_sales_team_constraint.sql
```

This constraint ensures that users with `SALES_TEAM` role must have a `sales_team_id`.

**For SQLite**, you'll need to add this constraint manually or use Alembic.

### 2. Create Initial Admin User

```bash
python scripts/seed_admin.py
```

Default credentials:
- Username: `admin`
- Password: `admin123`
- Email: `admin@example.com`

⚠️ **Change the password after first login!**

### 3. Verify Setup

Check that everything is working:

```bash
# Test database connection
python -c "from db.connection import engine; print('✅ Database connected')"

# Check tables exist
python -c "from db.connection import Base, engine; print('Tables:', list(Base.metadata.tables.keys()))"
```

## Database Configuration

The database connection is configured via `DATABASE_URL`:

### Environment Variable
```bash
export DATABASE_URL="postgresql://user:password@host:port/database"
```

### .env File
Create `backend/.env`:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/loan_engine
```

### Default
If not set, defaults to:
```
postgresql://postgres:postgres@localhost:5432/loan_engine
```

## Troubleshooting

### "Table already exists" Error

If tables already exist and you want to recreate them:

```bash
# Using init_db.py
python scripts/init_db.py --drop-existing

# Or manually drop and recreate
python -c "from db.connection import Base, engine; Base.metadata.drop_all(engine); Base.metadata.create_all(engine)"
```

### Connection Errors

1. **Check database is running:**
   ```bash
   # PostgreSQL
   pg_isready
   
   # Or check service status
   systemctl status postgresql  # Linux
   ```

2. **Verify DATABASE_URL:**
   ```bash
   python -c "from config.settings import settings; print(settings.DATABASE_URL)"
   ```

3. **Test connection:**
   ```bash
   psql $DATABASE_URL -c "SELECT 1"
   ```

### Migration Issues

If Alembic migrations fail:

1. Check current migration status:
   ```bash
   alembic current
   alembic history
   ```

2. Check for conflicts:
   ```bash
   alembic check
   ```

3. Rollback if needed:
   ```bash
   alembic downgrade -1
   ```

## Production Deployment

For production:

1. **Use Alembic migrations** (not init_db.py)
2. **Backup database** before migrations
3. **Test migrations** in staging first
4. **Use environment variables** for DATABASE_URL (never commit credentials)
5. **Apply constraints** after initial migration
6. **Create admin user** via seed script or API

## Next Steps

After database setup:

1. ✅ Tables created
2. ✅ Constraints applied
3. ✅ Admin user created
4. 🚀 Start the application: `uvicorn api.main:app --reload`
