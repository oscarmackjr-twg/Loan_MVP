\# Task: Generate the complete project scaffold for the Loan Engine application



You are building a structured finance loan processing platform called "Loan Engine."

Generate the full project scaffold with all configuration files, directory structure,

and skeleton code. Every file must be syntactically valid and the project must start

successfully (returning 200 on /health) with no additional code beyond what you generate.



---



\## Tech Stack



| Layer            | Technology                                          |

|------------------|-----------------------------------------------------|

| Backend          | Python 3.11+, FastAPI 0.100+, Pydantic v2           |

| ORM              | SQLAlchemy 2.0 (async, postgresql+asyncpg)           |

| Migrations       | Alembic (async-compatible)                           |

| Auth             | OAuth2 password bearer, python-jose (JWT), bcrypt    |

| Database         | PostgreSQL 15 (RDS in prod, local in dev)            |

| Storage          | S3 (prod) / local filesystem (dev), boto3            |

| Task Scheduler   | APScheduler                                          |

| Frontend         | React 18, Vite, React Router v6                     |

| Containerization | Docker, docker-compose                               |

| Infrastructure   | AWS ECS Fargate, ALB, RDS, ECR, S3, Secrets Manager |

| CI/CD            | GitHub Actions                                       |

| Testing          | pytest, httpx (AsyncClient), pytest-asyncio          |



---



\## Directory Structure



Generate exactly this structure. Every file listed must be created with complete,

working code. No placeholder comments like "# TODO" or "# implement later."



```

loan-engine/

├── backend/

│   ├── \_\_init\_\_.py

│   ├── config.py                    # Settings via pydantic-settings (BaseSettings)

│   ├── database.py                  # Async SQLAlchemy engine, session factory, Base

│   ├── models.py                    # SQLAlchemy ORM models (all tables)

│   ├── seed\_data.py                 # Idempotent reference data seeding (sales teams)

│   │

│   ├── api/

│   │   ├── \_\_init\_\_.py

│   │   ├── main.py                  # FastAPI app, CORS, lifespan (auto-create in dev), routers

│   │   ├── routes.py                # Stub routes: pipeline, runs, summary, exceptions, loans, sales-teams, config

│   │   ├── files.py                 # Stub routes: file list, upload, download, url, delete, mkdir

│   │   └── dependencies.py          # Shared dependencies (get\_db, get\_storage, get\_current\_user)

│   │

│   ├── auth/

│   │   ├── \_\_init\_\_.py

│   │   ├── routes.py                # Stub routes: login, register, me, users, update

│   │   ├── security.py              # JWT create/verify, password hash/verify, get\_current\_user dep

│   │   ├── schemas.py               # Auth Pydantic models (UserCreate, UserResponse, Token, etc.)

│   │   ├── validators.py            # Role-based access validators (admin\_required, etc.)

│   │   └── create\_admin.py          # Idempotent admin user creation (runnable as \_\_main\_\_)

│   │

│   ├── schemas/

│   │   ├── \_\_init\_\_.py

│   │   └── api.py                   # API Pydantic models (RunCreate, RunResponse, etc.)

│   │

│   ├── storage/

│   │   ├── \_\_init\_\_.py

│   │   ├── base.py                  # Abstract StorageBackend class

│   │   ├── local.py                 # LocalStorage implementation

│   │   └── s3.py                    # S3Storage implementation (boto3)

│   │

│   ├── scheduler/

│   │   ├── \_\_init\_\_.py

│   │   └── job\_scheduler.py         # APScheduler setup (skeleton)

│   │

│   ├── utils/

│   │   ├── \_\_init\_\_.py

│   │   └── path\_utils.py            # Path sanitization, safe join utilities

│   │

│   └── tests/

│       ├── \_\_init\_\_.py

│       ├── conftest.py              # Test fixtures: in-memory DB, test client, auth tokens

│       ├── test\_health.py           # Tests for /, /health, /health/ready

│       └── pytest.ini               # pytest configuration

│

├── frontend/

│   ├── package.json                 # React 18 + Vite + React Router + Axios

│   ├── vite.config.js               # Proxy /api to backend:8000

│   ├── index.html                   # Vite entry point

│   ├── src/

│   │   ├── main.jsx                 # React root render

│   │   ├── App.jsx                  # Router with auth-protected routes

│   │   ├── api/

│   │   │   └── client.js            # Axios instance with JWT interceptor

│   │   ├── components/

│   │   │   └── Layout.jsx           # App shell (nav, sidebar, content area)

│   │   ├── pages/

│   │   │   ├── LoginPage.jsx        # Login form

│   │   │   ├── DashboardPage.jsx    # Run list / overview

│   │   │   ├── RunDetailPage.jsx    # Single run detail

│   │   │   ├── ExceptionsPage.jsx   # Exception browser

│   │   │   ├── FilesPage.jsx        # File manager

│   │   │   └── UsersPage.jsx        # Admin user management

│   │   ├── hooks/

│   │   │   └── useAuth.js           # Auth context hook (login, logout, token mgmt)

│   │   └── context/

│   │       └── AuthContext.jsx       # Auth provider (JWT storage, user state)

│   └── public/

│       └── favicon.ico

│

├── deploy/

│   ├── Dockerfile                   # Multi-stage: build frontend, serve with FastAPI

│   ├── .dockerignore

│   ├── docker-compose.yml           # Local dev: backend + postgres + frontend

│   └── entrypoint.sh               # Container entrypoint: migrate → seed → serve

│

├── terraform/

│   ├── main.tf                      # Provider, backend state config

│   ├── variables.tf                 # All parameterized inputs

│   ├── terraform.tfvars             # Test environment defaults

│   ├── outputs.tf                   # ALB URL, ECR URI, RDS endpoint

│   └── modules/

│       ├── networking/

│       │   ├── main.tf

│       │   ├── variables.tf

│       │   └── outputs.tf

│       ├── ecs/

│       │   ├── main.tf

│       │   ├── variables.tf

│       │   └── outputs.tf

│       ├── rds/

│       │   ├── main.tf

│       │   ├── variables.tf

│       │   └── outputs.tf

│       ├── alb/

│       │   ├── main.tf

│       │   ├── variables.tf

│       │   └── outputs.tf

│       ├── iam/

│       │   ├── main.tf

│       │   ├── variables.tf

│       │   └── outputs.tf

│       └── secrets/

│           ├── main.tf

│           ├── variables.tf

│           └── outputs.tf

│

├── .github/

│   └── workflows/

│       └── deploy.yml               # Build → ECR push → ECS deploy

│

├── specs/

│   └── openapi-spec.json            # (reference only, not generated)

│

├── alembic/

│   ├── alembic.ini                  # Points to DATABASE\_URL\_SYNC

│   ├── env.py                       # Async-aware env, imports Base.metadata

│   ├── script.py.mako               # Migration template

│   └── versions/

│       └── 001\_initial\_schema.py    # Initial migration: all tables

│

├── scripts/

│   ├── start-backend.ps1            # uvicorn backend.api.main:app --reload --port 8000

│   ├── start-frontend.ps1           # cd frontend \&\& npm run dev

│   └── init-db.ps1                  # alembic upgrade head → create admin → seed data

│

├── pyproject.toml                   # Python project config with all dependencies

├── requirements.txt                 # Pinned dependencies (generated from pyproject.toml)

├── .env.example                     # Template for all environment variables

├── .gitignore

└── README.md                        # Setup instructions, architecture overview

```



---



\## Database Lifecycle



The database initialization strategy differs by environment. All three paths

must be generated and must produce identical table schemas.



\### Environment Matrix



| Environment   | Engine                   | Table Creation          | Seeding              | Trigger                          |

|---------------|--------------------------|-------------------------|----------------------|----------------------------------|

| \*\*Development\*\* | PostgreSQL (local)       | Alembic migrations AND auto-create in lifespan | scripts/init-db.ps1  | Developer runs init script once, then lifespan auto-creates on each restart |

| \*\*Testing\*\*     | SQLite in-memory (aiosqlite) | `Base.metadata.create\_all()` in conftest.py | Pytest fixtures       | Every test session               |

| \*\*AWS (ECS)\*\*   | RDS PostgreSQL           | Alembic migrations only | deploy/entrypoint.sh  | Every container start            |



\### backend/database.py



```python

"""

Async SQLAlchemy engine, session factory, and declarative base.

All models inherit from Base. The engine is configured from settings.DATABASE\_URL.

"""

from sqlalchemy.ext.asyncio import create\_async\_engine, async\_sessionmaker, AsyncSession

from sqlalchemy.orm import DeclarativeBase

from sqlalchemy import text

from typing import AsyncGenerator

from backend.config import get\_settings



settings = get\_settings()



engine = create\_async\_engine(

&nbsp;   settings.DATABASE\_URL,

&nbsp;   echo=settings.DEBUG,

&nbsp;   pool\_pre\_ping=True,

)



async\_session\_factory = async\_sessionmaker(engine, expire\_on\_commit=False)



class Base(DeclarativeBase):

&nbsp;   pass



async def get\_db() -> AsyncGenerator\[AsyncSession, None]:

&nbsp;   """FastAPI dependency that provides a database session per request."""

&nbsp;   async with async\_session\_factory() as session:

&nbsp;       try:

&nbsp;           yield session

&nbsp;           await session.commit()

&nbsp;       except Exception:

&nbsp;           await session.rollback()

&nbsp;           raise



async def check\_db\_connection() -> bool:

&nbsp;   """Check database connectivity. Used by /health/ready."""

&nbsp;   try:

&nbsp;       async with engine.connect() as conn:

&nbsp;           await conn.execute(text("SELECT 1"))

&nbsp;       return True

&nbsp;   except Exception:

&nbsp;       return False

```



\### backend/api/main.py — Lifespan with Auto-Create



```python

from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from fastapi.staticfiles import StaticFiles

from pathlib import Path

from datetime import datetime, timezone



from backend.database import engine, Base, check\_db\_connection

from backend.config import get\_settings



\# CRITICAL: Import models so Base.metadata registers all tables

import backend.models  # noqa: F401



@asynccontextmanager

async def lifespan(app: FastAPI):

&nbsp;   settings = get\_settings()



&nbsp;   # Development only: auto-create tables that don't exist yet.

&nbsp;   # In production and test, Alembic migrations are the sole authority.

&nbsp;   if settings.ENVIRONMENT == "development":

&nbsp;       async with engine.begin() as conn:

&nbsp;           await conn.run\_sync(Base.metadata.create\_all)



&nbsp;   yield



&nbsp;   await engine.dispose()



app = FastAPI(

&nbsp;   title="Loan Engine API",

&nbsp;   description="API for processing loans for structured finance products",

&nbsp;   version="1.0.0",

&nbsp;   lifespan=lifespan,

)



settings = get\_settings()

app.add\_middleware(

&nbsp;   CORSMiddleware,

&nbsp;   allow\_origins=settings.CORS\_ORIGINS,

&nbsp;   allow\_credentials=True,

&nbsp;   allow\_methods=\["\*"],

&nbsp;   allow\_headers=\["\*"],

)



\# --- Include routers ---

from backend.auth.routes import router as auth\_router

from backend.api.routes import router as api\_router

from backend.api.files import router as file\_router



app.include\_router(auth\_router, prefix="/api/auth", tags=\["authentication"])

app.include\_router(api\_router, prefix="/api", tags=\["api"])

app.include\_router(file\_router, prefix="/api/files", tags=\["files"])



\# --- Mount frontend SPA if build exists ---

frontend\_dist = Path(\_\_file\_\_).parent.parent.parent / "frontend" / "dist"

if frontend\_dist.is\_dir():

&nbsp;   app.mount("/assets", StaticFiles(directory=frontend\_dist / "assets"), name="assets")



\# --- Infrastructure endpoints (fully implemented) ---



@app.get("/")

async def root():

&nbsp;   index\_file = frontend\_dist / "index.html" if frontend\_dist.is\_dir() else None

&nbsp;   if index\_file and index\_file.exists():

&nbsp;       from fastapi.responses import HTMLResponse

&nbsp;       return HTMLResponse(index\_file.read\_text())

&nbsp;   return {"message": "Loan Engine API", "docs": "/docs"}



@app.get("/health")

async def health\_check():

&nbsp;   return {

&nbsp;       "status": "ok",

&nbsp;       "timestamp": datetime.now(timezone.utc).isoformat(),

&nbsp;   }



@app.get("/health/ready")

async def health\_ready():

&nbsp;   db\_ok = await check\_db\_connection()

&nbsp;   status\_code = 200 if db\_ok else 503

&nbsp;   from fastapi.responses import JSONResponse

&nbsp;   return JSONResponse(

&nbsp;       status\_code=status\_code,

&nbsp;       content={

&nbsp;           "status": "ready" if db\_ok else "unavailable",

&nbsp;           "database": "connected" if db\_ok else "disconnected",

&nbsp;           "timestamp": datetime.now(timezone.utc).isoformat(),

&nbsp;       },

&nbsp;   )

```



\### alembic/env.py



```python

"""

Alembic migration environment. Uses synchronous database URL (DATABASE\_URL\_SYNC)

because Alembic's migration runner is synchronous.

Imports Base.metadata from backend.models to detect all tables.

"""

from logging.config import fileConfig

from sqlalchemy import engine\_from\_config, pool

from alembic import context



\# Import Base and ALL models so metadata is populated

from backend.database import Base

import backend.models  # noqa: F401



from backend.config import get\_settings



config = context.config

settings = get\_settings()



\# Override sqlalchemy.url from environment (never hardcode credentials)

config.set\_main\_option("sqlalchemy.url", settings.DATABASE\_URL\_SYNC)



if config.config\_file\_name is not None:

&nbsp;   fileConfig(config.config\_file\_name)



target\_metadata = Base.metadata





def run\_migrations\_offline():

&nbsp;   """Run migrations in 'offline' mode (emit SQL to script output)."""

&nbsp;   url = config.get\_main\_option("sqlalchemy.url")

&nbsp;   context.configure(

&nbsp;       url=url,

&nbsp;       target\_metadata=target\_metadata,

&nbsp;       literal\_binds=True,

&nbsp;       dialect\_opts={"paramstyle": "named"},

&nbsp;   )

&nbsp;   with context.begin\_transaction():

&nbsp;       context.run\_migrations()





def run\_migrations\_online():

&nbsp;   """Run migrations in 'online' mode (connect to database)."""

&nbsp;   connectable = engine\_from\_config(

&nbsp;       config.get\_section(config.config\_ini\_section, {}),

&nbsp;       prefix="sqlalchemy.",

&nbsp;       poolclass=pool.NullPool,

&nbsp;   )

&nbsp;   with connectable.connect() as connection:

&nbsp;       context.configure(connection=connection, target\_metadata=target\_metadata)

&nbsp;       with context.begin\_transaction():

&nbsp;           context.run\_migrations()





if context.is\_offline\_mode():

&nbsp;   run\_migrations\_offline()

else:

&nbsp;   run\_migrations\_online()

```



\### alembic/alembic.ini



```ini

\[alembic]

script\_location = alembic

\# sqlalchemy.url is overridden by env.py from settings

sqlalchemy.url = postgresql://localhost/loan\_engine



\[loggers]

keys = root,sqlalchemy,alembic



\[handlers]

keys = console



\[formatters]

keys = generic



\[logger\_root]

level = WARN

handlers = console



\[logger\_sqlalchemy]

level = WARN

handlers =

qualname = sqlalchemy.engine



\[logger\_alembic]

level = INFO

handlers =

qualname = alembic



\[handler\_console]

class = StreamHandler

args = (sys.stderr,)

level = NOTSET

formatter = generic



\[formatter\_generic]

format = %(levelname)-5.5s \[%(name)s] %(message)s

datefmt = %H:%M:%S

```



\### alembic/versions/001\_initial\_schema.py



Generate a complete Alembic migration that creates ALL tables defined in

backend/models.py. This must match Base.metadata.create\_all() exactly.



```python

"""Initial schema — all tables.



Revision ID: 001

Create Date: 2026-02-20

"""

from alembic import op

import sqlalchemy as sa



revision = "001"

down\_revision = None

branch\_labels = None

depends\_on = None





def upgrade():

&nbsp;   # --- users ---

&nbsp;   op.create\_table(

&nbsp;       "users",

&nbsp;       sa.Column("id", sa.Integer, primary\_key=True, autoincrement=True),

&nbsp;       sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),

&nbsp;       sa.Column("username", sa.String(100), unique=True, nullable=False, index=True),

&nbsp;       sa.Column("hashed\_password", sa.String(255), nullable=False),

&nbsp;       sa.Column("full\_name", sa.String(255), nullable=True),

&nbsp;       sa.Column("role", sa.String(20), nullable=False, server\_default="analyst"),

&nbsp;       sa.Column("sales\_team\_id", sa.Integer, sa.ForeignKey("sales\_teams.id"), nullable=True),

&nbsp;       sa.Column("is\_active", sa.Boolean, nullable=False, server\_default=sa.text("true")),

&nbsp;       sa.Column("created\_at", sa.DateTime(timezone=True), server\_default=sa.func.now()),

&nbsp;   )



&nbsp;   # --- sales\_teams ---

&nbsp;   op.create\_table(

&nbsp;       "sales\_teams",

&nbsp;       sa.Column("id", sa.Integer, primary\_key=True, autoincrement=True),

&nbsp;       sa.Column("name", sa.String(100), unique=True, nullable=False),

&nbsp;       sa.Column("created\_at", sa.DateTime(timezone=True), server\_default=sa.func.now()),

&nbsp;   )



&nbsp;   # --- pipeline\_runs ---

&nbsp;   op.create\_table(

&nbsp;       "pipeline\_runs",

&nbsp;       sa.Column("id", sa.Integer, primary\_key=True, autoincrement=True),

&nbsp;       sa.Column("run\_id", sa.String(36), unique=True, nullable=False, index=True),

&nbsp;       sa.Column("status", sa.String(50), nullable=False, server\_default="pending"),

&nbsp;       sa.Column("sales\_team\_id", sa.Integer, sa.ForeignKey("sales\_teams.id"), nullable=True),

&nbsp;       sa.Column("total\_loans", sa.Integer, nullable=False, server\_default=sa.text("0")),

&nbsp;       sa.Column("total\_balance", sa.Float, nullable=False, server\_default=sa.text("0.0")),

&nbsp;       sa.Column("exceptions\_count", sa.Integer, nullable=False, server\_default=sa.text("0")),

&nbsp;       sa.Column("run\_weekday", sa.Integer, nullable=True),

&nbsp;       sa.Column("run\_weekday\_name", sa.String(20), nullable=True),

&nbsp;       sa.Column("pdate", sa.String(20), nullable=True),

&nbsp;       sa.Column("last\_phase", sa.String(100), nullable=True),

&nbsp;       sa.Column("output\_dir", sa.String(500), nullable=True),

&nbsp;       sa.Column("started\_at", sa.DateTime(timezone=True), nullable=True),

&nbsp;       sa.Column("completed\_at", sa.DateTime(timezone=True), nullable=True),

&nbsp;       sa.Column("created\_at", sa.DateTime(timezone=True), server\_default=sa.func.now()),

&nbsp;   )



&nbsp;   # --- loan\_exceptions ---

&nbsp;   op.create\_table(

&nbsp;       "loan\_exceptions",

&nbsp;       sa.Column("id", sa.Integer, primary\_key=True, autoincrement=True),

&nbsp;       sa.Column("run\_id", sa.String(36), sa.ForeignKey("pipeline\_runs.run\_id"), nullable=False, index=True),

&nbsp;       sa.Column("seller\_loan\_number", sa.String(50), nullable=False, index=True),

&nbsp;       sa.Column("exception\_type", sa.String(100), nullable=False),

&nbsp;       sa.Column("exception\_category", sa.String(100), nullable=False),

&nbsp;       sa.Column("severity", sa.String(20), nullable=False),

&nbsp;       sa.Column("message", sa.Text, nullable=True),

&nbsp;       sa.Column("rejection\_criteria", sa.String(200), nullable=True),

&nbsp;       sa.Column("created\_at", sa.DateTime(timezone=True), server\_default=sa.func.now()),

&nbsp;   )



&nbsp;   # --- loan\_facts ---

&nbsp;   op.create\_table(

&nbsp;       "loan\_facts",

&nbsp;       sa.Column("id", sa.Integer, primary\_key=True, autoincrement=True),

&nbsp;       sa.Column("run\_id", sa.String(36), sa.ForeignKey("pipeline\_runs.run\_id"), nullable=False, index=True),

&nbsp;       sa.Column("seller\_loan\_number", sa.String(50), nullable=False, index=True),

&nbsp;       sa.Column("disposition", sa.String(20), nullable=True),

&nbsp;       sa.Column("loan\_data", sa.JSON, nullable=True),

&nbsp;       sa.Column("created\_at", sa.DateTime(timezone=True), server\_default=sa.func.now()),

&nbsp;   )





def downgrade():

&nbsp;   op.drop\_table("loan\_facts")

&nbsp;   op.drop\_table("loan\_exceptions")

&nbsp;   op.drop\_table("pipeline\_runs")

&nbsp;   op.drop\_table("sales\_teams")

&nbsp;   op.drop\_table("users")

```



NOTE: The `sales\_teams` table must be created BEFORE `users` because `users`

has a foreign key to `sales\_teams`. Reorder the `upgrade()` function accordingly:

sales\_teams → users → pipeline\_runs → loan\_exceptions → loan\_facts.



\### backend/auth/create\_admin.py



```python

"""

Create the initial admin user. Idempotent — skips if admin already exists.

Run as: python -m backend.auth.create\_admin

"""

import asyncio

from sqlalchemy import select

from backend.database import async\_session\_factory, engine, Base

from backend.models import User

from backend.auth.security import hash\_password



\# Ensure tables exist (handles first-run case)

import backend.models  # noqa: F401



async def create\_admin():

&nbsp;   # In case tables haven't been created yet (dev environment)

&nbsp;   async with engine.begin() as conn:

&nbsp;       await conn.run\_sync(Base.metadata.create\_all)



&nbsp;   async with async\_session\_factory() as session:

&nbsp;       result = await session.execute(

&nbsp;           select(User).where(User.username == "admin")

&nbsp;       )

&nbsp;       existing = result.scalar\_one\_or\_none()



&nbsp;       if existing:

&nbsp;           print("Admin user already exists, skipping.")

&nbsp;           return



&nbsp;       admin = User(

&nbsp;           email="admin@loanengine.local",

&nbsp;           username="admin",

&nbsp;           hashed\_password=hash\_password("changeme"),

&nbsp;           full\_name="System Administrator",

&nbsp;           role="admin",

&nbsp;           is\_active=True,

&nbsp;       )

&nbsp;       session.add(admin)

&nbsp;       await session.commit()

&nbsp;       print("Admin user created successfully.")

&nbsp;       print("  Username: admin")

&nbsp;       print("  Password: changeme")

&nbsp;       print("  \*\* Change this password immediately in production \*\*")



if \_\_name\_\_ == "\_\_main\_\_":

&nbsp;   asyncio.run(create\_admin())

```



\### backend/seed\_data.py



```python

"""

Seed reference data (sales teams, lookup tables).

Idempotent — only inserts records that don't already exist.

Run as: python -m backend.seed\_data

"""

import asyncio

from sqlalchemy import select

from backend.database import async\_session\_factory, engine, Base

from backend.models import SalesTeam



import backend.models  # noqa: F401



SALES\_TEAMS = \[

&nbsp;   {"name": "Team Alpha"},

&nbsp;   {"name": "Team Beta"},

&nbsp;   {"name": "Team Gamma"},

]



async def seed():

&nbsp;   async with engine.begin() as conn:

&nbsp;       await conn.run\_sync(Base.metadata.create\_all)



&nbsp;   async with async\_session\_factory() as session:

&nbsp;       for team\_data in SALES\_TEAMS:

&nbsp;           result = await session.execute(

&nbsp;               select(SalesTeam).where(SalesTeam.name == team\_data\["name"])

&nbsp;           )

&nbsp;           if not result.scalar\_one\_or\_none():

&nbsp;               session.add(SalesTeam(\*\*team\_data))

&nbsp;               print(f"  Created: {team\_data\['name']}")

&nbsp;           else:

&nbsp;               print(f"  Exists:  {team\_data\['name']}")

&nbsp;       await session.commit()

&nbsp;   print("Seed data complete.")



if \_\_name\_\_ == "\_\_main\_\_":

&nbsp;   asyncio.run(seed())

```



\### scripts/init-db.ps1



```powershell

\# scripts/init-db.ps1

\# Initialize the database: run migrations, create admin, seed reference data.

\# Run once after first clone, or after pulling new migrations.



param(

&nbsp;   \[switch]$SkipMigrations,

&nbsp;   \[switch]$SkipAdmin,

&nbsp;   \[switch]$SkipSeed

)



$ErrorActionPreference = "Stop"

Write-Host "=== Loan Engine Database Initialization ===" -ForegroundColor Cyan



\# Step 1: Alembic migrations

if (-not $SkipMigrations) {

&nbsp;   Write-Host "`nStep 1: Running Alembic migrations..." -ForegroundColor Yellow

&nbsp;   alembic upgrade head

&nbsp;   if ($LASTEXITCODE -ne 0) {

&nbsp;       Write-Host "ERROR: Migrations failed. Is PostgreSQL running?" -ForegroundColor Red

&nbsp;       Write-Host "  Start it with: docker-compose -f deploy/docker-compose.yml up db" -ForegroundColor Gray

&nbsp;       exit 1

&nbsp;   }

&nbsp;   Write-Host "  Migrations applied successfully." -ForegroundColor Green

} else {

&nbsp;   Write-Host "`nStep 1: Skipped migrations (--SkipMigrations)" -ForegroundColor Gray

}



\# Step 2: Create admin user

if (-not $SkipAdmin) {

&nbsp;   Write-Host "`nStep 2: Creating admin user..." -ForegroundColor Yellow

&nbsp;   python -m backend.auth.create\_admin

&nbsp;   if ($LASTEXITCODE -ne 0) {

&nbsp;       Write-Host "ERROR: Admin user creation failed." -ForegroundColor Red

&nbsp;       exit 1

&nbsp;   }

&nbsp;   Write-Host "  Admin user ready." -ForegroundColor Green

} else {

&nbsp;   Write-Host "`nStep 2: Skipped admin creation (--SkipAdmin)" -ForegroundColor Gray

}



\# Step 3: Seed reference data

if (-not $SkipSeed) {

&nbsp;   Write-Host "`nStep 3: Seeding reference data..." -ForegroundColor Yellow

&nbsp;   python -m backend.seed\_data

&nbsp;   if ($LASTEXITCODE -ne 0) {

&nbsp;       Write-Host "ERROR: Seed data failed." -ForegroundColor Red

&nbsp;       exit 1

&nbsp;   }

&nbsp;   Write-Host "  Reference data ready." -ForegroundColor Green

} else {

&nbsp;   Write-Host "`nStep 3: Skipped seed data (--SkipSeed)" -ForegroundColor Gray

}



Write-Host "`n=== Database initialization complete ===" -ForegroundColor Cyan

Write-Host "Start the backend: uvicorn backend.api.main:app --reload --port 8000" -ForegroundColor White

```



\### deploy/entrypoint.sh



```bash

\#!/bin/bash

\# Container entrypoint for ECS deployment.

\# Runs migrations and seeding before starting the application.

\# Alembic is the SOLE authority for schema changes in non-dev environments.

set -e



echo "============================================"

echo "Loan Engine — Container Startup"

echo "Environment: ${ENVIRONMENT:-production}"

echo "============================================"



echo ""

echo "\[1/3] Running database migrations..."

alembic upgrade head

echo "  Migrations complete."



echo ""

echo "\[2/3] Ensuring admin user exists..."

python -m backend.auth.create\_admin

echo "  Admin user check complete."



echo ""

echo "\[3/3] Seeding reference data..."

python -m backend.seed\_data

echo "  Seed data complete."



echo ""

echo "============================================"

echo "Starting application server..."

echo "============================================"

exec uvicorn backend.api.main:app --host 0.0.0.0 --port 8000

```



---



\## SQLAlchemy ORM Models (backend/models.py)



Generate all ORM models using SQLAlchemy 2.0 `Mapped\[]` + `mapped\_column()` syntax.

These models are the single source of truth for table structure. Both Alembic and

`Base.metadata.create\_all()` derive schemas from these definitions.



```python

"""

SQLAlchemy ORM models. All table definitions live here.

Import this module anywhere table metadata must be registered

(main.py lifespan, alembic/env.py, create\_admin.py, seed\_data.py).

"""

from datetime import datetime

from typing import Optional

from sqlalchemy import String, Integer, Float, Boolean, Text, JSON, DateTime, ForeignKey, func

from sqlalchemy.orm import Mapped, mapped\_column, relationship

from backend.database import Base





class SalesTeam(Base):

&nbsp;   \_\_tablename\_\_ = "sales\_teams"



&nbsp;   id: Mapped\[int] = mapped\_column(Integer, primary\_key=True, autoincrement=True)

&nbsp;   name: Mapped\[str] = mapped\_column(String(100), unique=True, nullable=False)

&nbsp;   created\_at: Mapped\[datetime] = mapped\_column(DateTime(timezone=True), server\_default=func.now())



&nbsp;   # Relationships

&nbsp;   users: Mapped\[list\["User"]] = relationship(back\_populates="sales\_team", lazy="selectin")





class User(Base):

&nbsp;   \_\_tablename\_\_ = "users"



&nbsp;   id: Mapped\[int] = mapped\_column(Integer, primary\_key=True, autoincrement=True)

&nbsp;   email: Mapped\[str] = mapped\_column(String(255), unique=True, nullable=False, index=True)

&nbsp;   username: Mapped\[str] = mapped\_column(String(100), unique=True, nullable=False, index=True)

&nbsp;   hashed\_password: Mapped\[str] = mapped\_column(String(255), nullable=False)

&nbsp;   full\_name: Mapped\[Optional\[str]] = mapped\_column(String(255), nullable=True)

&nbsp;   role: Mapped\[str] = mapped\_column(String(20), nullable=False, server\_default="analyst")

&nbsp;   sales\_team\_id: Mapped\[Optional\[int]] = mapped\_column(

&nbsp;       Integer, ForeignKey("sales\_teams.id"), nullable=True

&nbsp;   )

&nbsp;   is\_active: Mapped\[bool] = mapped\_column(Boolean, nullable=False, server\_default="true")

&nbsp;   created\_at: Mapped\[datetime] = mapped\_column(DateTime(timezone=True), server\_default=func.now())



&nbsp;   # Relationships

&nbsp;   sales\_team: Mapped\[Optional\["SalesTeam"]] = relationship(back\_populates="users", lazy="selectin")





class PipelineRun(Base):

&nbsp;   \_\_tablename\_\_ = "pipeline\_runs"



&nbsp;   id: Mapped\[int] = mapped\_column(Integer, primary\_key=True, autoincrement=True)

&nbsp;   run\_id: Mapped\[str] = mapped\_column(String(36), unique=True, nullable=False, index=True)

&nbsp;   status: Mapped\[str] = mapped\_column(String(50), nullable=False, server\_default="pending")

&nbsp;   sales\_team\_id: Mapped\[Optional\[int]] = mapped\_column(

&nbsp;       Integer, ForeignKey("sales\_teams.id"), nullable=True

&nbsp;   )

&nbsp;   total\_loans: Mapped\[int] = mapped\_column(Integer, nullable=False, server\_default="0")

&nbsp;   total\_balance: Mapped\[float] = mapped\_column(Float, nullable=False, server\_default="0.0")

&nbsp;   exceptions\_count: Mapped\[int] = mapped\_column(Integer, nullable=False, server\_default="0")

&nbsp;   run\_weekday: Mapped\[Optional\[int]] = mapped\_column(Integer, nullable=True)

&nbsp;   run\_weekday\_name: Mapped\[Optional\[str]] = mapped\_column(String(20), nullable=True)

&nbsp;   pdate: Mapped\[Optional\[str]] = mapped\_column(String(20), nullable=True)

&nbsp;   last\_phase: Mapped\[Optional\[str]] = mapped\_column(String(100), nullable=True)

&nbsp;   output\_dir: Mapped\[Optional\[str]] = mapped\_column(String(500), nullable=True)

&nbsp;   started\_at: Mapped\[Optional\[datetime]] = mapped\_column(DateTime(timezone=True), nullable=True)

&nbsp;   completed\_at: Mapped\[Optional\[datetime]] = mapped\_column(DateTime(timezone=True), nullable=True)

&nbsp;   created\_at: Mapped\[datetime] = mapped\_column(DateTime(timezone=True), server\_default=func.now())



&nbsp;   # Relationships

&nbsp;   exceptions: Mapped\[list\["LoanException"]] = relationship(back\_populates="run", lazy="selectin")

&nbsp;   loan\_facts: Mapped\[list\["LoanFact"]] = relationship(back\_populates="run", lazy="selectin")





class LoanException(Base):

&nbsp;   \_\_tablename\_\_ = "loan\_exceptions"



&nbsp;   id: Mapped\[int] = mapped\_column(Integer, primary\_key=True, autoincrement=True)

&nbsp;   run\_id: Mapped\[str] = mapped\_column(

&nbsp;       String(36), ForeignKey("pipeline\_runs.run\_id"), nullable=False, index=True

&nbsp;   )

&nbsp;   seller\_loan\_number: Mapped\[str] = mapped\_column(String(50), nullable=False, index=True)

&nbsp;   exception\_type: Mapped\[str] = mapped\_column(String(100), nullable=False)

&nbsp;   exception\_category: Mapped\[str] = mapped\_column(String(100), nullable=False)

&nbsp;   severity: Mapped\[str] = mapped\_column(String(20), nullable=False)

&nbsp;   message: Mapped\[Optional\[str]] = mapped\_column(Text, nullable=True)

&nbsp;   rejection\_criteria: Mapped\[Optional\[str]] = mapped\_column(String(200), nullable=True)

&nbsp;   created\_at: Mapped\[datetime] = mapped\_column(DateTime(timezone=True), server\_default=func.now())



&nbsp;   # Relationships

&nbsp;   run: Mapped\["PipelineRun"] = relationship(back\_populates="exceptions", lazy="selectin")





class LoanFact(Base):

&nbsp;   \_\_tablename\_\_ = "loan\_facts"



&nbsp;   id: Mapped\[int] = mapped\_column(Integer, primary\_key=True, autoincrement=True)

&nbsp;   run\_id: Mapped\[str] = mapped\_column(

&nbsp;       String(36), ForeignKey("pipeline\_runs.run\_id"), nullable=False, index=True

&nbsp;   )

&nbsp;   seller\_loan\_number: Mapped\[str] = mapped\_column(String(50), nullable=False, index=True)

&nbsp;   disposition: Mapped\[Optional\[str]] = mapped\_column(String(20), nullable=True)

&nbsp;   loan\_data: Mapped\[Optional\[dict]] = mapped\_column(JSON, nullable=True)

&nbsp;   created\_at: Mapped\[datetime] = mapped\_column(DateTime(timezone=True), server\_default=func.now())



&nbsp;   # Relationships

&nbsp;   run: Mapped\["PipelineRun"] = relationship(back\_populates="loan\_facts", lazy="selectin")

```



---



\## Pydantic Schemas



\### Auth Schemas (backend/auth/schemas.py)



```python

from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr



class UserRole(str, Enum):

&nbsp;   admin = "admin"

&nbsp;   analyst = "analyst"

&nbsp;   sales\_team = "sales\_team"



class UserCreate(BaseModel):

&nbsp;   email: EmailStr

&nbsp;   username: str

&nbsp;   password: str

&nbsp;   full\_name: str

&nbsp;   role: UserRole = UserRole.analyst

&nbsp;   sales\_team\_id: int | None = None



class UserUpdate(BaseModel):

&nbsp;   email: EmailStr | None = None

&nbsp;   username: str | None = None

&nbsp;   full\_name: str | None = None

&nbsp;   role: UserRole | None = None

&nbsp;   sales\_team\_id: int | None = None

&nbsp;   is\_active: bool | None = None

&nbsp;   password: str | None = None



class UserResponse(BaseModel):

&nbsp;   id: int

&nbsp;   email: str

&nbsp;   username: str

&nbsp;   full\_name: str | None

&nbsp;   role: UserRole

&nbsp;   sales\_team\_id: int | None

&nbsp;   is\_active: bool

&nbsp;   model\_config = ConfigDict(from\_attributes=True)



class Token(BaseModel):

&nbsp;   access\_token: str

&nbsp;   token\_type: str

&nbsp;   user: dict

```



\### API Schemas (backend/schemas/api.py)



```python

from datetime import datetime

from pydantic import BaseModel, ConfigDict



class RunCreate(BaseModel):

&nbsp;   pdate: str | None = None

&nbsp;   irr\_target: float = 8.05

&nbsp;   folder: str = ""



class RunResponse(BaseModel):

&nbsp;   id: int

&nbsp;   run\_id: str

&nbsp;   status: str

&nbsp;   sales\_team\_id: int | None

&nbsp;   total\_loans: int

&nbsp;   total\_balance: float

&nbsp;   exceptions\_count: int

&nbsp;   run\_weekday: int | None = None

&nbsp;   run\_weekday\_name: str | None = None

&nbsp;   pdate: str | None = None

&nbsp;   last\_phase: str | None = None

&nbsp;   started\_at: datetime | None

&nbsp;   completed\_at: datetime | None

&nbsp;   created\_at: datetime

&nbsp;   model\_config = ConfigDict(from\_attributes=True)



class SummaryResponse(BaseModel):

&nbsp;   run\_id: str

&nbsp;   total\_loans: int

&nbsp;   total\_balance: float

&nbsp;   exceptions\_count: int

&nbsp;   eligibility\_checks: dict



class ExceptionResponse(BaseModel):

&nbsp;   id: int

&nbsp;   seller\_loan\_number: str

&nbsp;   exception\_type: str

&nbsp;   exception\_category: str

&nbsp;   severity: str

&nbsp;   message: str | None

&nbsp;   rejection\_criteria: str | None = None

&nbsp;   created\_at: datetime

&nbsp;   model\_config = ConfigDict(from\_attributes=True)

```



---



\## Configuration (backend/config.py)



```python

from functools import lru\_cache

from pydantic\_settings import BaseSettings, SettingsConfigDict



class Settings(BaseSettings):

&nbsp;   # Application

&nbsp;   APP\_NAME: str = "loan-engine"

&nbsp;   ENVIRONMENT: str = "development"

&nbsp;   DEBUG: bool = True



&nbsp;   # Database

&nbsp;   DATABASE\_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/loan\_engine"

&nbsp;   DATABASE\_URL\_SYNC: str = "postgresql://postgres:postgres@localhost:5432/loan\_engine"



&nbsp;   # Auth

&nbsp;   SECRET\_KEY: str = "dev-secret-key-change-in-production"

&nbsp;   JWT\_ALGORITHM: str = "HS256"

&nbsp;   ACCESS\_TOKEN\_EXPIRE\_MINUTES: int = 480



&nbsp;   # Storage

&nbsp;   STORAGE\_TYPE: str = "local"

&nbsp;   LOCAL\_STORAGE\_PATH: str = "./storage"

&nbsp;   S3\_BUCKET\_NAME: str = ""

&nbsp;   S3\_REGION: str = "us-east-1"

&nbsp;   AWS\_ACCESS\_KEY\_ID: str = ""

&nbsp;   AWS\_SECRET\_ACCESS\_KEY: str = ""



&nbsp;   # CORS

&nbsp;   CORS\_ORIGINS: list\[str] = \["http://localhost:5173", "http://localhost:3000"]



&nbsp;   model\_config = SettingsConfigDict(

&nbsp;       env\_file=".env",

&nbsp;       env\_file\_encoding="utf-8",

&nbsp;       case\_sensitive=True,

&nbsp;   )



@lru\_cache

def get\_settings() -> Settings:

&nbsp;   return Settings()

```



---



\## Storage Abstraction (backend/storage/)



\### backend/storage/base.py



```python

from abc import ABC, abstractmethod

from fastapi import UploadFile

from fastapi.responses import StreamingResponse



class StorageBackend(ABC):

&nbsp;   @abstractmethod

&nbsp;   async def list\_files(self, path: str, recursive: bool = False, area: str = "inputs") -> list\[dict]:

&nbsp;       ...

&nbsp;   @abstractmethod

&nbsp;   async def upload\_file(self, file: UploadFile, destination: str, area: str = "inputs") -> dict:

&nbsp;       ...

&nbsp;   @abstractmethod

&nbsp;   async def download\_file(self, path: str, area: str = "inputs") -> StreamingResponse:

&nbsp;       ...

&nbsp;   @abstractmethod

&nbsp;   async def delete\_file(self, path: str, area: str = "inputs") -> dict:

&nbsp;       ...

&nbsp;   @abstractmethod

&nbsp;   async def create\_directory(self, path: str, area: str = "inputs") -> dict:

&nbsp;       ...

&nbsp;   @abstractmethod

&nbsp;   async def get\_presigned\_url(self, path: str, expires\_in: int = 3600, area: str = "inputs") -> str:

&nbsp;       ...

```



\### backend/storage/local.py



Implement `LocalStorage(StorageBackend)` using `pathlib` and `aiofiles`.

Storage root is `settings.LOCAL\_STORAGE\_PATH` with subdirectories: `inputs/`, `outputs/`, `output\_share/`.

All path operations must validate against directory traversal attacks using `path\_utils.safe\_join()`.



\### backend/storage/s3.py



Implement `S3Storage(StorageBackend)` using `boto3`.

Bucket is `settings.S3\_BUCKET\_NAME` with key prefixes: `inputs/`, `outputs/`, `output\_share/`.

`get\_presigned\_url()` generates S3 presigned URLs with configurable expiration.



---



\## Endpoint Stubs



In this scaffold phase, implement only the 3 infrastructure endpoints with real logic

(shown in main.py above). All other endpoints should be stub routes that return

proper status codes and placeholder responses matching their schemas.



\### Auth Stubs (backend/auth/routes.py) — 5 routes



```

POST /login          → Return Token with dummy values

GET  /me             → Return UserResponse (requires auth dependency)

POST /register       → Return UserResponse (requires admin\_required dependency)

PUT  /users/{user\_id} → Return UserResponse (requires admin\_required dependency)

GET  /users          → Return List\[UserResponse] with skip/limit/role/sales\_team\_id params

```



\### API Stubs (backend/api/routes.py) — 12 routes



```

POST /pipeline/run                                    → Return RunResponse

GET  /runs                                            → Return List\[RunResponse] with skip/limit/status/run\_weekday

GET  /runs/{run\_id}                                   → Return RunResponse

GET  /runs/{run\_id}/notebook-outputs                  → Return \[]

GET  /runs/{run\_id}/notebook-outputs/{output\_key}/download → Return 404

GET  /runs/{run\_id}/archive                           → Return {}

GET  /runs/{run\_id}/archive/download                  → Return 404 (query param: path)

GET  /summary/{run\_id}                                → Return SummaryResponse

GET  /exceptions                                      → Return List\[ExceptionResponse]

GET  /exceptions/export                               → Return empty CSV response

GET  /loans                                           → Return \[] (query params: run\_id, disposition, skip, limit)

GET  /sales-teams                                     → Return \[]

GET  /config                                          → Return {"storage\_type": settings.STORAGE\_TYPE}

```



\### File Stubs (backend/api/files.py) — 6 routes



```

GET    /list                    → Return {"files": \[]}

POST   /upload                  → Return {"filename": "test.csv", "status": "uploaded"}

GET    /download/{file\_path:path} → Return 404

GET    /url/{file\_path:path}    → Return {"url": "http://placeholder"}

DELETE /{file\_path:path}        → Return {"status": "deleted"}

POST   /mkdir                   → Return {"status": "created"}

```



Every stub must:

\- Use the correct HTTP method and path

\- Accept the correct parameters (path, query, body) matching the OpenAPI spec

\- Include the security dependency where marked (OAuth2PasswordBearer)

\- Return the correct response schema shape

\- Return appropriate status codes (200, 201, 404, 422)



---



\## Auth Security (backend/auth/security.py)



```python

"""

JWT token creation/verification and password hashing.

Provides FastAPI dependencies: get\_current\_user, admin\_required.

"""

from datetime import datetime, timedelta, timezone

from typing import Optional

from fastapi import Depends, HTTPException, status

from fastapi.security import OAuth2PasswordBearer

from jose import JWTError, jwt

from passlib.context import CryptContext

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession



from backend.config import get\_settings

from backend.database import get\_db



pwd\_context = CryptContext(schemes=\["bcrypt"], deprecated="auto")

oauth2\_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")



def hash\_password(password: str) -> str:

&nbsp;   return pwd\_context.hash(password)



def verify\_password(plain\_password: str, hashed\_password: str) -> bool:

&nbsp;   return pwd\_context.verify(plain\_password, hashed\_password)



def create\_access\_token(data: dict, expires\_delta: Optional\[timedelta] = None) -> str:

&nbsp;   settings = get\_settings()

&nbsp;   to\_encode = data.copy()

&nbsp;   expire = datetime.now(timezone.utc) + (expires\_delta or timedelta(minutes=settings.ACCESS\_TOKEN\_EXPIRE\_MINUTES))

&nbsp;   to\_encode.update({"exp": expire})

&nbsp;   return jwt.encode(to\_encode, settings.SECRET\_KEY, algorithm=settings.JWT\_ALGORITHM)



async def get\_current\_user(

&nbsp;   token: str = Depends(oauth2\_scheme),

&nbsp;   db: AsyncSession = Depends(get\_db),

):

&nbsp;   """Decode JWT and return the authenticated User object."""

&nbsp;   from backend.models import User  # avoid circular import

&nbsp;   settings = get\_settings()

&nbsp;   credentials\_exception = HTTPException(

&nbsp;       status\_code=status.HTTP\_401\_UNAUTHORIZED,

&nbsp;       detail="Could not validate credentials",

&nbsp;       headers={"WWW-Authenticate": "Bearer"},

&nbsp;   )

&nbsp;   try:

&nbsp;       payload = jwt.decode(token, settings.SECRET\_KEY, algorithms=\[settings.JWT\_ALGORITHM])

&nbsp;       username: str = payload.get("sub")

&nbsp;       if username is None:

&nbsp;           raise credentials\_exception

&nbsp;   except JWTError:

&nbsp;       raise credentials\_exception



&nbsp;   result = await db.execute(select(User).where(User.username == username))

&nbsp;   user = result.scalar\_one\_or\_none()

&nbsp;   if user is None or not user.is\_active:

&nbsp;       raise credentials\_exception

&nbsp;   return user



async def admin\_required(current\_user=Depends(get\_current\_user)):

&nbsp;   """Dependency that ensures the current user has admin role."""

&nbsp;   if current\_user.role != "admin":

&nbsp;       raise HTTPException(

&nbsp;           status\_code=status.HTTP\_403\_FORBIDDEN,

&nbsp;           detail="Admin access required",

&nbsp;       )

&nbsp;   return current\_user

```



---



\## Docker Configuration



\### deploy/Dockerfile



```dockerfile

\# Stage 1: Build frontend

FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend

COPY frontend/package\*.json ./

RUN npm ci

COPY frontend/ ./

RUN npm run build



\# Stage 2: Python backend + built frontend

FROM python:3.11-slim

WORKDIR /app



\# Install system dependencies for asyncpg

RUN apt-get update \&\& apt-get install -y --no-install-recommends \\

&nbsp;   gcc libpq-dev \&\& rm -rf /var/lib/apt/lists/\*



COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt



COPY backend/ ./backend/

COPY alembic/ ./alembic/

COPY alembic.ini .

COPY deploy/entrypoint.sh .

RUN chmod +x entrypoint.sh



COPY --from=frontend-build /app/frontend/dist ./frontend/dist



EXPOSE 8000

ENTRYPOINT \["./entrypoint.sh"]

```



\### deploy/docker-compose.yml



```yaml

version: "3.8"



services:

&nbsp; db:

&nbsp;   image: postgres:15-alpine

&nbsp;   environment:

&nbsp;     POSTGRES\_DB: loan\_engine

&nbsp;     POSTGRES\_USER: postgres

&nbsp;     POSTGRES\_PASSWORD: postgres

&nbsp;   ports:

&nbsp;     - "5432:5432"

&nbsp;   volumes:

&nbsp;     - pgdata:/var/lib/postgresql/data

&nbsp;   healthcheck:

&nbsp;     test: \["CMD-SHELL", "pg\_isready -U postgres"]

&nbsp;     interval: 5s

&nbsp;     timeout: 5s

&nbsp;     retries: 5



&nbsp; backend:

&nbsp;   build:

&nbsp;     context: ..

&nbsp;     dockerfile: deploy/Dockerfile

&nbsp;   ports:

&nbsp;     - "8000:8000"

&nbsp;   environment:

&nbsp;     ENVIRONMENT: development

&nbsp;     DATABASE\_URL: postgresql+asyncpg://postgres:postgres@db:5432/loan\_engine

&nbsp;     DATABASE\_URL\_SYNC: postgresql://postgres:postgres@db:5432/loan\_engine

&nbsp;     STORAGE\_TYPE: local

&nbsp;     LOCAL\_STORAGE\_PATH: /app/storage

&nbsp;     SECRET\_KEY: docker-dev-secret-key

&nbsp;     CORS\_ORIGINS: '\["http://localhost:5173","http://localhost:3000"]'

&nbsp;   depends\_on:

&nbsp;     db:

&nbsp;       condition: service\_healthy

&nbsp;   volumes:

&nbsp;     - app\_storage:/app/storage



&nbsp; frontend:

&nbsp;   image: node:20-alpine

&nbsp;   working\_dir: /app

&nbsp;   command: sh -c "npm install \&\& npm run dev -- --host 0.0.0.0"

&nbsp;   ports:

&nbsp;     - "5173:5173"

&nbsp;   volumes:

&nbsp;     - ../frontend:/app

&nbsp;   environment:

&nbsp;     - VITE\_API\_URL=http://localhost:8000



volumes:

&nbsp; pgdata:

&nbsp; app\_storage:

```



---



\## Environment Template (.env.example)



```env

\# ============================================

\# Loan Engine — Environment Configuration

\# ============================================

\# Copy to .env and update values for your environment.



\# --- Application ---

APP\_NAME=loan-engine

ENVIRONMENT=development          # development | test | production

DEBUG=true



\# --- Database ---

DATABASE\_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/loan\_engine

DATABASE\_URL\_SYNC=postgresql://postgres:postgres@localhost:5432/loan\_engine



\# --- Authentication ---

SECRET\_KEY=change-this-to-a-random-64-char-string

JWT\_ALGORITHM=HS256

ACCESS\_TOKEN\_EXPIRE\_MINUTES=480



\# --- Storage ---

STORAGE\_TYPE=local               # local | s3

LOCAL\_STORAGE\_PATH=./storage

S3\_BUCKET\_NAME=

S3\_REGION=us-east-1

AWS\_ACCESS\_KEY\_ID=

AWS\_SECRET\_ACCESS\_KEY=



\# --- CORS ---

CORS\_ORIGINS=\["http://localhost:5173","http://localhost:3000"]

```



---



\## AWS Infrastructure (terraform/)



\### terraform/variables.tf



```hcl

variable "app\_name"          { default = "loan-engine" }

variable "environment"       { default = "test" }

variable "region"            { default = "us-east-1" }

variable "db\_instance\_class" { default = "db.t3.micro" }

variable "db\_name"           { default = "loan\_engine" }

variable "db\_username"       { default = "postgres" }

variable "container\_port"    { default = 8000 }

variable "vpc\_cidr"          { default = "10.0.0.0/16" }

```



Generate all 6 modules per the infrastructure spec:

\- \*\*networking\*\*: VPC, 2 public + 2 private subnets (multi-AZ), NAT gateway, route tables, 3 security groups (ALB → ECS → RDS chain)

\- \*\*ecs\*\*: Cluster, Fargate service, task definition referencing ECR image + Secrets Manager ARNs, CloudWatch log group (/ecs/loan-engine-test, 30-day retention)

\- \*\*rds\*\*: PostgreSQL 15 instance in private subnets, db subnet group, no public access

\- \*\*alb\*\*: Application load balancer in public subnets, target group (port 8000), HTTP listener, health check on /health/ready

\- \*\*iam\*\*: ecsTaskExecutionRole (ECR pull + Secrets Manager read + CloudWatch logs), ecsTaskRole (S3 read/write)

\- \*\*secrets\*\*: DATABASE\_URL and SECRET\_KEY in Secrets Manager



Resource naming pattern: `{app\_name}-{environment}-{resource}`



---



\## GitHub Actions (.github/workflows/deploy.yml)



```yaml

name: Deploy to AWS ECS

on:

&nbsp; push:

&nbsp;   branches: \[main]

&nbsp; workflow\_dispatch:



env:

&nbsp; AWS\_REGION: us-east-1

&nbsp; ECR\_REPOSITORY: loan-engine

&nbsp; ECS\_CLUSTER: loan-engine-test

&nbsp; ECS\_SERVICE: loan-engine-test



jobs:

&nbsp; test:

&nbsp;   runs-on: ubuntu-latest

&nbsp;   steps:

&nbsp;     - uses: actions/checkout@v4

&nbsp;     - uses: actions/setup-python@v5

&nbsp;       with:

&nbsp;         python-version: "3.11"

&nbsp;     - run: pip install -e ".\[dev]"

&nbsp;     - run: pytest backend/tests/ -v



&nbsp; build-and-deploy:

&nbsp;   needs: test

&nbsp;   runs-on: ubuntu-latest

&nbsp;   steps:

&nbsp;     - uses: actions/checkout@v4

&nbsp;     - uses: aws-actions/configure-aws-credentials@v4

&nbsp;       with:

&nbsp;         aws-access-key-id: ${{ secrets.AWS\_ACCESS\_KEY\_ID }}

&nbsp;         aws-secret-access-key: ${{ secrets.AWS\_SECRET\_ACCESS\_KEY }}

&nbsp;         aws-region: ${{ env.AWS\_REGION }}

&nbsp;     - uses: aws-actions/amazon-ecr-login@v2

&nbsp;       id: ecr

&nbsp;     - name: Build and push Docker image

&nbsp;       run: |

&nbsp;         docker build -f deploy/Dockerfile -t ${{ steps.ecr.outputs.registry }}/${{ env.ECR\_REPOSITORY }}:latest .

&nbsp;         docker push ${{ steps.ecr.outputs.registry }}/${{ env.ECR\_REPOSITORY }}:latest

&nbsp;     - name: Update ECS service

&nbsp;       run: |

&nbsp;         aws ecs update-service --cluster ${{ env.ECS\_CLUSTER }} --service ${{ env.ECS\_SERVICE }} --force-new-deployment

```



---



\## Test Configuration



\### backend/tests/conftest.py



```python

import pytest

import pytest\_asyncio

from httpx import AsyncClient, ASGITransport

from sqlalchemy.ext.asyncio import create\_async\_engine, async\_sessionmaker



from backend.database import Base, get\_db

from backend.models import User, SalesTeam  # noqa: F401 — register models

from backend.auth.security import hash\_password, create\_access\_token

from backend.api.main import app



\# In-memory SQLite for tests — no migrations needed

TEST\_DATABASE\_URL = "sqlite+aiosqlite:///:memory:"



@pytest\_asyncio.fixture(scope="session")

async def test\_engine():

&nbsp;   engine = create\_async\_engine(TEST\_DATABASE\_URL, echo=False)

&nbsp;   async with engine.begin() as conn:

&nbsp;       await conn.run\_sync(Base.metadata.create\_all)

&nbsp;   yield engine

&nbsp;   await engine.dispose()



@pytest\_asyncio.fixture

async def test\_db(test\_engine):

&nbsp;   session\_factory = async\_sessionmaker(test\_engine, expire\_on\_commit=False)

&nbsp;   async with session\_factory() as session:

&nbsp;       yield session

&nbsp;       await session.rollback()



@pytest\_asyncio.fixture

async def async\_client(test\_engine):

&nbsp;   session\_factory = async\_sessionmaker(test\_engine, expire\_on\_commit=False)



&nbsp;   async def override\_get\_db():

&nbsp;       async with session\_factory() as session:

&nbsp;           yield session



&nbsp;   app.dependency\_overrides\[get\_db] = override\_get\_db

&nbsp;   transport = ASGITransport(app=app)

&nbsp;   async with AsyncClient(transport=transport, base\_url="http://test") as client:

&nbsp;       yield client

&nbsp;   app.dependency\_overrides.clear()



@pytest\_asyncio.fixture

async def admin\_user(test\_db):

&nbsp;   user = User(

&nbsp;       email="admin@test.com", username="admin",

&nbsp;       hashed\_password=hash\_password("adminpass"),

&nbsp;       full\_name="Test Admin", role="admin", is\_active=True,

&nbsp;   )

&nbsp;   test\_db.add(user)

&nbsp;   await test\_db.commit()

&nbsp;   await test\_db.refresh(user)

&nbsp;   return user



@pytest\_asyncio.fixture

async def analyst\_user(test\_db):

&nbsp;   user = User(

&nbsp;       email="analyst@test.com", username="analyst",

&nbsp;       hashed\_password=hash\_password("analystpass"),

&nbsp;       full\_name="Test Analyst", role="analyst", is\_active=True,

&nbsp;   )

&nbsp;   test\_db.add(user)

&nbsp;   await test\_db.commit()

&nbsp;   await test\_db.refresh(user)

&nbsp;   return user



@pytest\_asyncio.fixture

def admin\_token(admin\_user):

&nbsp;   return create\_access\_token(data={"sub": admin\_user.username})



@pytest\_asyncio.fixture

def analyst\_token(analyst\_user):

&nbsp;   return create\_access\_token(data={"sub": analyst\_user.username})

```



\### backend/tests/test\_health.py



```python

import pytest

from httpx import AsyncClient



@pytest.mark.asyncio

async def test\_root(async\_client: AsyncClient):

&nbsp;   response = await async\_client.get("/")

&nbsp;   assert response.status\_code == 200



@pytest.mark.asyncio

async def test\_health(async\_client: AsyncClient):

&nbsp;   response = await async\_client.get("/health")

&nbsp;   assert response.status\_code == 200

&nbsp;   data = response.json()

&nbsp;   assert data\["status"] == "ok"

&nbsp;   assert "timestamp" in data



@pytest.mark.asyncio

async def test\_health\_ready(async\_client: AsyncClient):

&nbsp;   response = await async\_client.get("/health/ready")

&nbsp;   # May be 200 or 503 depending on DB in test context

&nbsp;   assert response.status\_code in (200, 503)

&nbsp;   data = response.json()

&nbsp;   assert "status" in data

&nbsp;   assert "database" in data

```



\### backend/tests/pytest.ini



```ini

\[pytest]

asyncio\_mode = auto

testpaths = backend/tests

python\_files = test\_\*.py

python\_functions = test\_\*

```



---



\## pyproject.toml



```toml

\[project]

name = "loan-engine"

version = "1.0.0"

description = "Structured finance loan processing pipeline"

requires-python = ">=3.11"

dependencies = \[

&nbsp;   "fastapi>=0.100.0",

&nbsp;   "uvicorn\[standard]>=0.23.0",

&nbsp;   "sqlalchemy\[asyncio]>=2.0.0",

&nbsp;   "asyncpg>=0.28.0",

&nbsp;   "alembic>=1.12.0",

&nbsp;   "pydantic>=2.0.0",

&nbsp;   "pydantic-settings>=2.0.0",

&nbsp;   "python-jose\[cryptography]>=3.3.0",

&nbsp;   "passlib\[bcrypt]>=1.7.4",

&nbsp;   "python-multipart>=0.0.6",

&nbsp;   "boto3>=1.28.0",

&nbsp;   "aioboto3>=11.0.0",

&nbsp;   "aiofiles>=23.0.0",

&nbsp;   "apscheduler>=3.10.0",

&nbsp;   "httpx>=0.24.0",

&nbsp;   "openpyxl>=3.1.0",

&nbsp;   "email-validator>=2.0.0",

&nbsp;   "psycopg2-binary>=2.9.0",

]



\[project.optional-dependencies]

dev = \[

&nbsp;   "pytest>=7.4.0",

&nbsp;   "pytest-asyncio>=0.21.0",

&nbsp;   "httpx>=0.24.0",

&nbsp;   "aiosqlite>=0.19.0",

&nbsp;   "ruff>=0.1.0",

]



\[tool.ruff]

target-version = "py311"

line-length = 120



\[tool.pytest.ini\_options]

asyncio\_mode = "auto"

```



---



\## Frontend Scaffold



\### frontend/package.json



```json

{

&nbsp; "name": "loan-engine-frontend",

&nbsp; "version": "1.0.0",

&nbsp; "type": "module",

&nbsp; "scripts": {

&nbsp;   "dev": "vite",

&nbsp;   "build": "vite build",

&nbsp;   "preview": "vite preview"

&nbsp; },

&nbsp; "dependencies": {

&nbsp;   "react": "^18.2.0",

&nbsp;   "react-dom": "^18.2.0",

&nbsp;   "react-router-dom": "^6.20.0",

&nbsp;   "axios": "^1.6.0"

&nbsp; },

&nbsp; "devDependencies": {

&nbsp;   "@vitejs/plugin-react": "^4.2.0",

&nbsp;   "vite": "^5.0.0",

&nbsp;   "@types/react": "^18.2.0"

&nbsp; }

}

```



\### frontend/vite.config.js



```javascript

import { defineConfig } from 'vite';

import react from '@vitejs/plugin-react';



export default defineConfig({

&nbsp; plugins: \[react()],

&nbsp; server: {

&nbsp;   port: 5173,

&nbsp;   proxy: {

&nbsp;     '/api': {

&nbsp;       target: 'http://localhost:8000',

&nbsp;       changeOrigin: true,

&nbsp;     },

&nbsp;   },

&nbsp; },

});

```



Generate complete working code for all frontend files listed in the directory structure:

\- `index.html`: Standard Vite entry point mounting `#root`

\- `src/main.jsx`: React root render with BrowserRouter and AuthProvider

\- `src/App.jsx`: Route definitions with auth-protected layout

\- `src/api/client.js`: Axios instance, base URL `/api`, JWT interceptor from localStorage

\- `src/context/AuthContext.jsx`: AuthProvider with login/logout/user state, token in localStorage

\- `src/hooks/useAuth.js`: `useAuth()` hook consuming AuthContext

\- `src/components/Layout.jsx`: Sidebar navigation + content area, shows user role, logout button

\- All 6 page components: LoginPage (form with username/password), DashboardPage (placeholder table),

&nbsp; RunDetailPage (placeholder), ExceptionsPage (placeholder), FilesPage (placeholder),

&nbsp; UsersPage (placeholder with admin-only note)



Each page must be a functional React component that renders properly.

Placeholder pages should show the page title, a brief description, and a

"This page will be implemented in Phase X" note.



---



\## Validation Criteria



After generation, the scaffold MUST pass ALL of these checks:



```

&nbsp;1. pip install -e ".\[dev]"                              → installs without errors

&nbsp;2. cp .env.example .env                                 → config file ready

&nbsp;3. docker-compose -f deploy/docker-compose.yml up db    → PostgreSQL starts

&nbsp;4. python scripts/init-db.ps1                           → migrations + admin + seed

&nbsp;5. uvicorn backend.api.main:app --reload                → starts on port 8000

&nbsp;6. GET /health                                          → 200 {"status": "ok"}

&nbsp;7. GET /health/ready                                    → 200 {"database": "connected"}

&nbsp;8. GET /docs                                            → Swagger UI loads with 26 endpoints

&nbsp;9. All 26 stub endpoints return correct status codes and schema shapes

10\. pytest backend/tests/test\_health.py                  → all tests pass

11\. cd frontend \&\& npm install \&\& npm run dev             → Vite starts on 5173

12\. docker build -f deploy/Dockerfile .                   → image builds successfully

13\. terraform -chdir=terraform init                       → Terraform initializes

14\. ruff check backend/                                   → no lint errors

15\. alembic revision --autogenerate -m "verify"           → produces EMPTY migration

&nbsp;    (proving models.py and 001\_initial\_schema.py are in sync)



