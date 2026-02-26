\#specs/context/project-context.md



\#Loan Engine — Shared Project Context

\#═══════════════════════════════════════════════════════════

\#This file is the single source of truth for the Loan Engine project.

\#It is prepended to every phase prompt (or chunk) to ensure the LLM

\#has consistent context about architecture, conventions, schemas,

\#and interfaces — regardless of which phase it is generating.

\#Last updated: 2025-07-11

\#Phase coverage: 0 through 7

\#═══════════════════════════════════════════════════════════



1\. Project Overview



The Loan Engine is a full-stack web application that processes residential

mortgage loan tapes through an automated eligibility, pricing, and disposition

pipeline. Users upload CSV loan tapes, trigger pipeline runs, review results

(exceptions, summaries, output files), and export reports.



Business Flow:



Upload loan tape → Trigger run → Ingest → Validate → Eligibility →

Pricing → Disposition → Output generation → Archive



User Roles:

• admin: Full access — user management, all runs, all data

• analyst: Read/write — trigger runs, view all data, cannot manage users

• sales\_team: Scoped — sees only their team's runs and exceptions

2\. Technology Stack



| Layer | Technology | Version |

|-------|-----------|---------|

| Backend framework | FastAPI | 0.104+ |

| Python | CPython | 3.11+ |

| ORM | SQLAlchemy | 2.0+ (async) |

| Database driver | asyncpg (async) / psycopg2 (sync) | latest |

| Database | PostgreSQL | 15 |

| Migrations | Alembic | 1.12+ |

| Auth | python-jose (JWT) + passlib\[bcrypt] | latest |

| Frontend framework | React | 18.2+ |

| Frontend build | Vite | 5.0+ |

| Frontend routing | React Router | v6.20+ |

| HTTP client (frontend) | Axios | 1.6+ |

| HTTP client (testing) | httpx | 0.25+ |

| Testing | pytest + pytest-asyncio | latest |

| Linting | Ruff | latest |

| Container | Docker (multi-stage) | latest |

| IaC | Terraform | >= 1.5.0 |

| Cloud | AWS (ECS Fargate, RDS, S3, ALB, ECR) | — |

| CI/CD | GitHub Actions | — |

| Monitoring | CloudWatch Logs (structured JSON) | — |

3\. Project Structure





loan-engine/

├── backend/

│   ├── \_\_init\_\_.py

│   ├── config.py                  # Settings (BaseSettings), get\_settings()

│   ├── database.py                # engine, async\_session\_factory, Base, get\_db

│   ├── models.py                  # User, SalesTeam, PipelineRun, LoanException, LoanFact

│   ├── seed\_data.py               # Reference data seeder

│   │

│   ├── api/

│   │   ├── \_\_init\_\_.py

│   │   ├── main.py                # FastAPI app, lifespan, middleware, routers, health

│   │   ├── routes.py              # Pipeline, runs, summary, exceptions, loans endpoints

│   │   ├── files.py               # File management endpoints

│   │   └── dependencies.py        # get\_db, get\_storage, get\_current\_user

│   │

│   ├── auth/

│   │   ├── \_\_init\_\_.py

│   │   ├── routes.py              # Auth endpoints (login, register, me, users)

│   │   ├── security.py            # hash\_password, verify\_password, create\_access\_token, get\_current\_user, admin\_required

│   │   ├── schemas.py             # UserRole, UserCreate, UserUpdate, UserResponse, Token

│   │   ├── validators.py          # require\_roles, active\_user\_required, sales\_team\_scoped, admin\_or\_self

│   │   └── create\_admin.py        # CLI script to seed initial admin user

│   │

│   ├── schemas/

│   │   ├── \_\_init\_\_.py

│   │   └── api.py                 # RunCreate, RunResponse, SummaryResponse, ExceptionResponse

│   │

│   ├── pipeline/

│   │   ├── \_\_init\_\_.py

│   │   ├── engine.py              # execute\_pipeline() orchestrator

│   │   ├── phases.py              # phase\_ingest through phase\_archive (7 phases)

│   │   └── eligibility.py         # ELIGIBILITY\_RULES, run\_eligibility\_checks()

│   │

│   ├── storage/

│   │   ├── \_\_init\_\_.py

│   │   ├── base.py                # StorageBackend (ABC)

│   │   ├── local.py               # LocalStorage (filesystem)

│   │   └── s3.py                  # S3Storage (AWS)

│   │

│   ├── utils/

│   │   ├── \_\_init\_\_.py

│   │   └── path\_utils.py          # safe\_join, sanitize\_filename, validate\_\*

│   │

│   ├── middleware/                 # Phase 7

│   │   ├── \_\_init\_\_.py

│   │   ├── request\_id.py          # X-Request-ID generation/propagation

│   │   ├── logging\_middleware.py   # Structured request/response logging

│   │   ├── error\_handler.py       # Global exception handling

│   │   ├── rate\_limiter.py        # Sliding window rate limiting

│   │   ├── timing.py              # Server-Timing header, slow request detection

│   │   └── security\_headers.py    # OWASP security headers

│   │

│   ├── observability/             # Phase 7

│   │   ├── \_\_init\_\_.py

│   │   ├── logging\_config.py      # JSON/text structured logging

│   │   ├── health.py              # Extended health checks (DB, storage, system)

│   │   └── metrics.py             # In-memory request/pipeline metrics

│   │

│   ├── admin/                     # Phase 7

│   │   ├── \_\_init\_\_.py

│   │   ├── cli.py                 # Admin CLI commands

│   │   └── diagnostics.py         # Admin diagnostic endpoints

│   │

│   └── tests/

│       ├── \_\_init\_\_.py

│       ├── conftest.py            # Shared fixtures: engine, db, client, users, tokens

│       ├── pytest.ini

│       ├── test\_health.py

│       ├── test\_auth\_routes.py

│       ├── test\_pipeline\_routes.py

│       ├── test\_file\_routes.py

│       ├── test\_storage\_local.py

│       ├── test\_storage\_s3.py

│       ├── test\_integration\_auth\_pipeline.py    # Phase 6

│       ├── test\_integration\_pipeline\_files.py   # Phase 6

│       ├── test\_integration\_full\_workflow.py     # Phase 6

│       ├── test\_security.py                     # Phase 6

│       ├── test\_data\_integrity.py               # Phase 6

│       ├── test\_edge\_cases.py                   # Phase 6

│       ├── test\_eligibility\_rules.py            # Phase 6

│       ├── test\_pipeline\_phases.py              # Phase 6

│       ├── test\_path\_utils.py                   # Phase 6

│       ├── test\_pagination.py                   # Phase 6

│       ├── test\_concurrent.py                   # Phase 6

│       ├── test\_middleware.py                    # Phase 7

│       ├── test\_observability.py                # Phase 7

│       └── test\_hardening.py                    # Phase 7

│

├── frontend/

│   ├── package.json

│   ├── vite.config.js             # Proxy /api → localhost:8000

│   ├── index.html

│   └── src/

│       ├── main.jsx

│       ├── App.jsx

│       ├── api/                   # client.js, auth.js, runs.js, exceptions.js, loans.js, files.js

│       ├── context/               # AuthContext.jsx

│       ├── hooks/                 # useAuth.js, useApi.js, usePagination.js

│       ├── components/            # Layout, ProtectedRoute, StatusBadge, DataTable, Modal, etc.

│       ├── pages/                 # LoginPage, DashboardPage, RunDetailPage, ExceptionsPage, FilesPage, UsersPage

│       ├── styles/                # global.css

│       └── utils/                 # format.js

│

├── deploy/

│   ├── Dockerfile                 # Multi-stage: Node build → Python runtime

│   ├── .dockerignore

│   ├── docker-compose.yml         # Local dev (app + postgres)

│   └── entrypoint.sh             # Migration retry + seed + uvicorn

│

├── terraform/

│   ├── main.tf                   # Root module, provider, state backend

│   ├── variables.tf              # All input variables

│   ├── terraform.tfvars          # Test environment defaults

│   ├── outputs.tf                # Key outputs (ALB DNS, ECR URL, etc.)

│   └── modules/

│       ├── networking/           # VPC, subnets, NAT, IGW, security groups

│       ├── ecs/                  # Cluster, service, task def, ECR, logs

│       ├── rds/                  # PostgreSQL instance, subnet group

│       ├── alb/                  # Load balancer, target group, listener

│       ├── iam/                  # Execution role, task role, policies

│       ├── secrets/              # Secrets Manager (DATABASE\_URL, SECRET\_KEY)

│       └── s3/                   # Data bucket with versioning

│

├── alembic/

│   ├── env.py

│   ├── script.py.mako

│   └── versions/

│

├── scripts/

│   ├── init-db.ps1

│   ├── terraform-init.ps1

│   └── deploy-manual.ps1

│

├── .github/workflows/

│   └── deploy.yml                # Lint → Test → Build → Push → Deploy

│

├── specs/                        # Dark Factory orchestration (not deployed)

│   ├── context/

│   │   └── project-context.md    # THIS FILE

│   ├── prompts/

│   │   ├── phase0-scaffold-prompt.md

│   │   ├── phase1-auth-prompt.md

│   │   ├── phase2-pipeline-prompt.md

│   │   ├── phase3-files-prompt.md

│   │   ├── phase4-frontend-prompt.md

│   │   ├── phase5-infrastructure-prompt.md

│   │   ├── phase6-tests-prompt.md

│   │   └── phase7-hardening-prompt.md

│   ├── reports/

│   ├── backups/

│   ├── orchestrate.py

│   └── validate\_scaffold.py

│

├── pyproject.toml

├── requirements.txt

├── alembic.ini

├── .env.example

├── .gitignore

└── README.md

4\. Database Schema



ORM Models (backend/models.py)



python

class User(Base):

&nbsp;   \_\_tablename\_\_ = "users"



&nbsp;   id: Mapped\[int] = mapped\_column(primary\_key=True)

&nbsp;   email: Mapped\[str] = mapped\_column(String(255), unique=True, index=True)

&nbsp;   username: Mapped\[str] = mapped\_column(String(100), unique=True, index=True)

&nbsp;   hashed\_password: Mapped\[str] = mapped\_column(String(255))

&nbsp;   full\_name: Mapped\[str | None] = mapped\_column(String(255))

&nbsp;   role: Mapped\[str] = mapped\_column(String(50), default="analyst")     # admin | analyst | sales\_team

&nbsp;   sales\_team\_id: Mapped\[int | None] = mapped\_column(ForeignKey("sales\_teams.id"))

&nbsp;   is\_active: Mapped\[bool] = mapped\_column(default=True)

&nbsp;   created\_at: Mapped\[datetime] = mapped\_column(default=func.now())

&nbsp;   updated\_at: Mapped\[datetime | None] = mapped\_column(onupdate=func.now())



class SalesTeam(Base):

&nbsp;   \_\_tablename\_\_ = "sales\_teams"



&nbsp;   id: Mapped\[int] = mapped\_column(primary\_key=True)

&nbsp;   name: Mapped\[str] = mapped\_column(String(200), unique=True)

&nbsp;   created\_at: Mapped\[datetime] = mapped\_column(default=func.now())



class PipelineRun(Base):

&nbsp;   \_\_tablename\_\_ = "pipeline\_runs"



&nbsp;   id: Mapped\[int] = mapped\_column(primary\_key=True)

&nbsp;   run\_id: Mapped\[str] = mapped\_column(String(100), unique=True, index=True)  # UUID

&nbsp;   status: Mapped\[str] = mapped\_column(String(50), default="pending")          # pending | running | completed | failed

&nbsp;   sales\_team\_id: Mapped\[int | None] = mapped\_column(ForeignKey("sales\_teams.id"))

&nbsp;   total\_loans: Mapped\[int] = mapped\_column(default=0)

&nbsp;   total\_balance: Mapped\[float] = mapped\_column(default=0.0)

&nbsp;   exceptions\_count: Mapped\[int] = mapped\_column(default=0)

&nbsp;   run\_weekday: Mapped\[int | None]                      # 0=Monday ... 6=Sunday

&nbsp;   run\_weekday\_name: Mapped\[str | None] = mapped\_column(String(20))

&nbsp;   pdate: Mapped\[str | None] = mapped\_column(String(20))  # Purchase date

&nbsp;   last\_phase: Mapped\[str | None] = mapped\_column(String(50))

&nbsp;   output\_dir: Mapped\[str | None] = mapped\_column(String(500))

&nbsp;   input\_dir: Mapped\[str | None] = mapped\_column(String(500))

&nbsp;   config\_json: Mapped\[dict | None] = mapped\_column(JSON)

&nbsp;   started\_at: Mapped\[datetime | None]

&nbsp;   completed\_at: Mapped\[datetime | None]

&nbsp;   created\_at: Mapped\[datetime] = mapped\_column(default=func.now())



class LoanException(Base):

&nbsp;   \_\_tablename\_\_ = "loan\_exceptions"



&nbsp;   id: Mapped\[int] = mapped\_column(primary\_key=True)

&nbsp;   run\_id: Mapped\[str] = mapped\_column(String(100), ForeignKey("pipeline\_runs.run\_id"), index=True)

&nbsp;   seller\_loan\_number: Mapped\[str] = mapped\_column(String(100), index=True)

&nbsp;   exception\_type: Mapped\[str] = mapped\_column(String(100))       # e.g., "ltv\_ratio", "credit\_score"

&nbsp;   exception\_category: Mapped\[str] = mapped\_column(String(100))   # e.g., "credit", "data\_quality"

&nbsp;   severity: Mapped\[str] = mapped\_column(String(20))              # "hard" | "soft"

&nbsp;   message: Mapped\[str | None] = mapped\_column(Text)

&nbsp;   rejection\_criteria: Mapped\[str | None] = mapped\_column(String(200))

&nbsp;   created\_at: Mapped\[datetime] = mapped\_column(default=func.now())



class LoanFact(Base):

&nbsp;   \_\_tablename\_\_ = "loan\_facts"



&nbsp;   id: Mapped\[int] = mapped\_column(primary\_key=True)

&nbsp;   run\_id: Mapped\[str] = mapped\_column(String(100), ForeignKey("pipeline\_runs.run\_id"), index=True)

&nbsp;   seller\_loan\_number: Mapped\[str] = mapped\_column(String(100), index=True)

&nbsp;   disposition: Mapped\[str] = mapped\_column(String(50))           # "to\_purchase" | "rejected" | "projected"

&nbsp;   loan\_data: Mapped\[dict] = mapped\_column(JSON)                  # Full loan record as JSON

&nbsp;   created\_at: Mapped\[datetime] = mapped\_column(default=func.now())



Entity Relationships





SalesTeam 1──N User

SalesTeam 1──N PipelineRun

PipelineRun 1──N LoanException (via run\_id)

PipelineRun 1──N LoanFact (via run\_id)

5\. API Specification (26 endpoints)



Authentication (5 endpoints)





POST /api/auth/login

&nbsp; Body: OAuth2PasswordRequestForm (username, password)

&nbsp; Response: Token {access\_token, token\_type, user: UserResponse}



GET /api/auth/me

&nbsp; Auth: Bearer token

&nbsp; Response: UserResponse



POST /api/auth/register

&nbsp; Auth: admin required

&nbsp; Body: UserCreate {email, username, password, full\_name?, role?, sales\_team\_id?}

&nbsp; Response: UserResponse (201)



PUT /api/auth/users/{user\_id}

&nbsp; Auth: admin required

&nbsp; Body: UserUpdate {email?, full\_name?, role?, sales\_team\_id?, is\_active?, password?}

&nbsp; Response: UserResponse



GET /api/auth/users

&nbsp; Auth: admin required

&nbsp; Query: ?skip=0 \&limit=100 \&role= \&sales\_team\_id=

&nbsp; Response: List\[UserResponse]



Pipeline \& Runs (7 endpoints)





POST /api/pipeline/run

&nbsp; Auth: required

&nbsp; Body: RunCreate {pdate?, irr\_target?: 8.05, folder?}

&nbsp; Response: RunResponse



GET /api/runs

&nbsp; Auth: required (sales\_team scoped)

&nbsp; Query: ?skip=0 \&limit=25 \&status= \&run\_weekday=

&nbsp; Response: List\[RunResponse]



GET /api/runs/{run\_id}

&nbsp; Auth: required (sales\_team scoped)

&nbsp; Response: RunResponse



GET /api/runs/{run\_id}/notebook-outputs

&nbsp; Auth: required

&nbsp; Response: List\[{name, path, type, size}]



GET /api/runs/{run\_id}/notebook-outputs/{output\_key}/download

&nbsp; Auth: required

&nbsp; Response: File download (StreamingResponse)



GET /api/runs/{run\_id}/archive

&nbsp; Auth: required

&nbsp; Response: {input: List\[FileInfo], output: List\[FileInfo]}



GET /api/runs/{run\_id}/archive/download

&nbsp; Auth: required

&nbsp; Query: ?path=input/filename.csv

&nbsp; Response: File download (StreamingResponse)



Data \& Reporting (6 endpoints)





GET /api/summary/{run\_id}

&nbsp; Auth: required

&nbsp; Response: SummaryResponse {run\_id, total\_loans, total\_balance, exceptions\_count,

&nbsp;   eligibility\_checks: {total\_loans, eligible, rejected, projected,

&nbsp;     exceptions\_by\_type: {}, exceptions\_by\_severity: {}}}



GET /api/exceptions

&nbsp; Auth: required (sales\_team scoped)

&nbsp; Query: ?run\_id= \&exception\_type= \&severity= \&rejection\_criteria= \&skip=0 \&limit=25

&nbsp; Response: List\[ExceptionResponse]



GET /api/exceptions/export

&nbsp; Auth: required

&nbsp; Query: ?format=csv|xlsx \&run\_id= \&exception\_type= \&severity=

&nbsp; Response: File download (CSV or XLSX)



GET /api/loans

&nbsp; Auth: required

&nbsp; Query: ?run\_id= \&disposition= \&skip=0 \&limit=25

&nbsp; Response: List\[dict]



GET /api/sales-teams

&nbsp; Auth: required

&nbsp; Response: List\[{id, name}]



GET /api/config

&nbsp; Auth: required

&nbsp; Response: {storage\_type, environment}



File Management (6 endpoints)





GET /api/files/list

&nbsp; Auth: required

&nbsp; Query: ?path= \&recursive=false \&area=inputs

&nbsp; Response: {path, area, recursive, count, files: List\[FileInfo]}



POST /api/files/upload

&nbsp; Auth: required

&nbsp; Body: multipart/form-data (file)

&nbsp; Query: ?path= \&area=inputs

&nbsp; Response: {filename, path, area, size, status}



GET /api/files/download/{file\_path:path}

&nbsp; Auth: required

&nbsp; Query: ?area=inputs

&nbsp; Response: File download (StreamingResponse)



GET /api/files/url/{file\_path:path}

&nbsp; Auth: required

&nbsp; Query: ?area=inputs \&expires\_in=3600

&nbsp; Response: {path, area, url, expires\_in}



DELETE /api/files/{file\_path:path}

&nbsp; Auth: required

&nbsp; Query: ?area=inputs

&nbsp; Response: {path, area, type, status}



POST /api/files/mkdir

&nbsp; Auth: required

&nbsp; Query: ?path= \&area=inputs

&nbsp; Response: {path, area, status}



Infrastructure (3 endpoints)





GET /

&nbsp; Response: {message, version, docs\_url}



GET /health

&nbsp; Response: {status: "ok", timestamp}



GET /health/ready

&nbsp; Response: {status, timestamp, uptime\_seconds, version, environment, components: \[...]}

&nbsp; Status: 200 if healthy/degraded, 503 if unhealthy



Admin (4 endpoints, Phase 7)





GET /admin/health/detailed    (admin only)

GET /admin/metrics            (admin only)

GET /admin/config             (admin only, secrets redacted)

GET /admin/info               (admin only)

POST /admin/metrics/reset     (admin only)

6\. Storage Architecture





storage\_root/

├── inputs/              # Uploaded loan tape files

│   ├── daily/

│   │   └── loans\_2026-02-20.csv

│   └── weekly/

│       └── batch\_tape.xlsx

├── outputs/             # Pipeline-generated files (one dir per run)

│   └── {run\_id}/

│       ├── purchase\_tape.csv

│       ├── projected\_tape.csv

│       ├── rejection\_report.csv

│       └── exception\_summary.csv

└── output\_share/        # Shared exports

&nbsp;   └── exports/



Valid areas: inputs, outputs, output\_share

Allowed upload extensions: .csv, .xlsx, .xls, .json, .txt, .pdf, .zip

Max upload size: 100 MB



Security: All operations enforce path traversal prevention via safe\_join().

Cross-area access is blocked (inputs files cannot be accessed via outputs area).

7\. Pipeline Phases





Phase 1: Ingest      Read CSV from storage, parse into loan records

Phase 2: Validate    Check required fields, flag data quality issues

Phase 3: Eligibility Run ELIGIBILITY\_RULES, create LoanException records

Phase 4: Pricing     Calculate pricing spreads using IRR target

Phase 5: Disposition Assign to\_purchase | rejected | projected, create LoanFact records

Phase 6: Output      Generate 4 CSV files (purchase, projected, rejection, exception summary)

Phase 7: Archive     Store input + output files, update run record



Eligibility Rules



| Rule | Field | Condition | Severity |

|------|-------|-----------|----------|

| Loan Amount Min | loan\_amount | ≥ $50,000 | hard |

| Loan Amount Max | loan\_amount | ≤ $5,000,000 | hard |

| LTV Maximum | ltv\_ratio | ≤ 97.0% | hard |

| DTI Maximum | dti\_ratio | ≤ 50.0% | hard |

| Credit Score Min | credit\_score | ≥ 620 | hard |

| Property Type | property\_type | in \[sfr, condo, townhouse, pud, 2-4\_unit] | hard |

| Occupancy | occupancy\_status | in \[primary, second\_home, investment] | hard |

| Loan Purpose | loan\_purpose | in \[purchase, rate\_term\_refi, cash\_out\_refi] | hard |

| Purchase Price | purchase\_price | present and > 0 | soft |

| Appraisal Value | appraisal\_value | present and > 0 | soft |

| Note Rate Range | note\_rate | between 2.0% and 12.0% | soft |



Hard failures → loan rejected.

Soft failures → exception recorded but loan continues through pipeline.

8\. Test Infrastructure



Test Configuration



python

Tests use SQLite in-memory (async via aiosqlite)

No external services required

All storage tests use LocalStorage in tmp\_path

S3 tests mock boto3

Every test rolls back DB changes automatically



Core Fixtures (conftest.py)



python

test\_engine         # SQLite async engine, tables auto-created

test\_db             # AsyncSession per test, auto-rollback

async\_client        # httpx AsyncClient with app + DB override

admin\_user          # User(username="admin", role="admin", password="adminpass")

analyst\_user        # User(username="analyst", role="analyst", password="analystpass")

admin\_token         # Valid JWT for admin\_user

analyst\_token       # Valid JWT for analyst\_user

sales\_team\_user     # User(role="sales\_team", team assigned)

sales\_team\_token    # Valid JWT for sales\_team\_user

sample\_sales\_team   # SalesTeam record

sample\_run\_completed # PipelineRun(status=completed, with stats)

sample\_run\_failed   # PipelineRun(status=failed)

sample\_run\_pending  # PipelineRun(status=pending)

populated\_run       # Run with 100 loan facts + 12 exceptions

multiple\_runs       # 10 runs with varied statuses

sample\_loan\_tape\_csv # Valid CSV bytes for pipeline testing

temp\_storage        # LocalStorage in tmp\_path

override\_storage    # App dependency override for temp\_storage

9\. Key Design Decisions

1\. Async everywhere: All database operations use async/await. No sync SQLAlchemy calls.

2\. Dependency injection: FastAPI Depends() for DB sessions, storage, and auth.

3\. No circular imports: Models import nothing from api/auth/pipeline. Config is imported by everything.

4\. Storage abstraction: StorageBackend ABC allows swapping local ↔ S3 via config.

5\. JWT stateless auth: No server-side session store. Tokens are self-contained.

6\. Sales team scoping: Implemented at query level, not middleware. Routes that need scoping explicitly filter by sales\_team\_id.

7\. Pipeline is synchronous within a request: POST /api/pipeline/run runs the full pipeline and returns the result. No background task queue (intentional for V1).

8\. Frontend served by FastAPI: StaticFiles mount for frontend/dist/. Single container deployment.

9\. Tests are self-contained: No external database, no network calls, no file system pollution beyond tmp\_path.

10\. Infrastructure as code: Terraform modules are environment-parameterized. Same code for test/staging/prod.

10\. Coding Conventions



Python (Backend)

• Formatting: Ruff with default settings

• Imports: stdlib → third-party → local (isort compatible)

• Type hints: Use Mapped\[] for SQLAlchemy, standard hints elsewhere

• Async: All DB operations use async def + await

• Naming: snake\_case for functions/variables, PascalCase for classes

• Docstrings: Module-level docstrings required, function docstrings for public APIs

• Error handling: Raise HTTPException with specific status codes, never bare except:

• No global mutable state except get\_settings() cache and metrics singleton



JavaScript (Frontend)

• Components: Functional only, no class components

• State: Hooks (useState, useEffect, useCallback, useMemo)

• Files: PascalCase for components, camelCase for hooks/utils

• No TypeScript: Plain JSX with JSDoc for complex props

• No additional UI libraries: Plain HTML + CSS custom properties

• API calls: Always in dedicated api/\*.js modules, never inline in components

• Error handling: Every API call wrapped in try/catch with user-visible feedback



Terraform

• Naming: {app\_name}-{environment}-{resource} pattern

• Modules: Each resource group in its own module with main.tf, variables.tf, outputs.tf

• Variables: All configurable values exposed as variables with sensible defaults

• Tags: All resources tagged with Project, Environment, ManagedBy

11\. Environment Variables



env

--- Core ---

APP\_NAME=loan-engine

ENVIRONMENT=development          # development | test | staging | production

DEBUG=true

SECRET\_KEY=<random-64-chars>

JWT\_ALGORITHM=HS256

JWT\_EXPIRE\_MINUTES=1440



--- Database ---

DATABASE\_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/loan\_engine

DATABASE\_URL\_SYNC=postgresql://postgres:postgres@localhost:5432/loan\_engine



--- Storage ---

STORAGE\_TYPE=local               # local | s3

LOCAL\_STORAGE\_PATH=./storage

S3\_BUCKET\_NAME=

S3\_REGION=us-east-1

AWS\_ACCESS\_KEY\_ID=

AWS\_SECRET\_ACCESS\_KEY=



--- CORS ---

CORS\_ORIGINS=\["http://localhost:5173","http://localhost:8000"]



--- Logging (Phase 7) ---

LOG\_LEVEL=INFO

LOG\_FORMAT=json                  # json | text



--- Rate Limiting (Phase 7) ---

RATE\_LIMIT\_ENABLED=true

RATE\_LIMIT\_LOGIN=10/minute

RATE\_LIMIT\_API=100/minute



--- Database Pool (Phase 7) ---

DB\_POOL\_SIZE=10

DB\_MAX\_OVERFLOW=20

DB\_POOL\_RECYCLE=3600

12\. Phase Dependency Chain





Phase 0: Scaffold

&nbsp; └─→ Phase 1: Auth (depends on: models, config, database)

&nbsp;      └─→ Phase 2: Pipeline (depends on: auth, models, storage stubs)

&nbsp;           └─→ Phase 3: Files (depends on: auth, storage base)

&nbsp;                └─→ Phase 4: Frontend (depends on: all API endpoints)

&nbsp;                     └─→ Phase 5: Infrastructure (depends on: full app)

&nbsp;                          └─→ Phase 6: Integration Tests (depends on: all code)

&nbsp;                               └─→ Phase 7: Hardening (depends on: all code + tests)



Each phase can only import from its own modules and previously completed phases.

Never import forward (e.g., Phase 1 cannot import from Phase 2 modules).



