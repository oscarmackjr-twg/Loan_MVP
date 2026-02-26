Task: Implement Comprehensive Integration \& End-to-End Tests for the Loan Engine



You are extending the Loan Engine application (Phases 0-5 complete) with a

comprehensive test suite that validates cross-module integration, end-to-end

workflows, security boundaries, data integrity, and edge cases. After this

phase, the test suite serves as an executable specification — if all tests

pass, the system is production-ready.





Context: What Already Exists



Existing Test Files (from Phases 0-3)





backend/tests/

├── \_\_init\_\_.py

├── conftest.py                  # Core fixtures: test\_engine, test\_db, async\_client,

│                                #   admin\_user, analyst\_user, admin\_token, analyst\_token

├── pytest.ini                   # asyncio\_mode = auto

├── test\_health.py               # 3 tests: /, /health, /health/ready

├── test\_auth\_routes.py          # 30+ tests: login, register, me, update, list users

├── test\_pipeline\_routes.py      # 25+ tests: runs, summary, exceptions, loans, config

├── test\_file\_routes.py          # 25+ tests: list, upload, download, delete, mkdir

├── test\_storage\_local.py        # 15+ tests: LocalStorage unit tests

└── test\_storage\_s3.py           # 10+ tests: S3Storage unit tests (mocked boto3)



Existing conftest.py Fixtures



python

Engine \& Session

test\_engine          # SQLite in-memory async engine, tables auto-created

test\_db              # AsyncSession per test, auto-rollback



HTTP Client

async\_client         # httpx AsyncClient with app, get\_db overridden



Users (created in test\_db)

admin\_user           # User(username="admin", password="adminpass", role="admin")

analyst\_user         # User(username="analyst", password="analystpass", role="analyst")



Tokens

admin\_token          # Valid JWT for admin\_user

analyst\_token        # Valid JWT for analyst\_user



Backend Modules Available



python

Models

from backend.models import User, SalesTeam, PipelineRun, LoanException, LoanFact



Auth

from backend.auth.security import hash\_password, create\_access\_token, verify\_password

from backend.auth.schemas import UserRole, UserCreate, UserUpdate



Pipeline

from backend.pipeline.engine import execute\_pipeline

from backend.pipeline.eligibility import run\_eligibility\_checks, ELIGIBILITY\_RULES

from backend.pipeline.phases import (

&nbsp;   phase\_ingest, phase\_validate, phase\_eligibility,

&nbsp;   phase\_pricing, phase\_disposition, phase\_output, phase\_archive,

)



Storage

from backend.storage.local import LocalStorage

from backend.storage.s3 import S3Storage

from backend.storage.base import StorageBackend



Config

from backend.config import get\_settings



Utils

from backend.utils.path\_utils import (

&nbsp;   safe\_join, sanitize\_filename, validate\_file\_extension,

&nbsp;   validate\_file\_size, validate\_area, normalize\_storage\_path,

)



API

from backend.api.main import app

from backend.api.dependencies import get\_storage



API Endpoints (all 26)





Auth (5)

POST /api/auth/login

GET  /api/auth/me

POST /api/auth/register

PUT  /api/auth/users/{user\_id}

GET  /api/auth/users



Pipeline (7)

POST /api/pipeline/run

GET  /api/runs

GET  /api/runs/{run\_id}

GET  /api/runs/{run\_id}/notebook-outputs

GET  /api/runs/{run\_id}/notebook-outputs/{output\_key}/download

GET  /api/runs/{run\_id}/archive

GET  /api/runs/{run\_id}/archive/download



Data (6)

GET  /api/summary/{run\_id}

GET  /api/exceptions

GET  /api/exceptions/export

GET  /api/loans

GET  /api/sales-teams

GET  /api/config



Files (6)

GET  /api/files/list

POST /api/files/upload

GET  /api/files/download/{file\_path}

GET  /api/files/url/{file\_path}

DELETE /api/files/{file\_path}

POST /api/files/mkdir



Infrastructure (3)

GET  /

GET  /health

GET  /health/ready





Files to Create



| File | Purpose |

|------|---------|

| backend/tests/conftest.py | EXTEND with new shared fixtures |

| backend/tests/test\_integration\_auth\_pipeline.py | Auth → Pipeline cross-module tests |

| backend/tests/test\_integration\_pipeline\_files.py | Pipeline → File output integration |

| backend/tests/test\_integration\_full\_workflow.py | Complete end-to-end workflow tests |

| backend/tests/test\_security.py | Security boundary and attack vector tests |

| backend/tests/test\_data\_integrity.py | Data consistency and constraint tests |

| backend/tests/test\_edge\_cases.py | Boundary conditions and error handling |

| backend/tests/test\_eligibility\_rules.py | Eligibility rule unit tests |

| backend/tests/test\_pipeline\_phases.py | Pipeline phase unit tests |

| backend/tests/test\_path\_utils.py | Path security utility tests |

| backend/tests/test\_concurrent.py | Concurrency and race condition tests |

| backend/tests/test\_pagination.py | Pagination behavior across all list endpoints |



DO NOT MODIFY

• Any file in backend/api/, backend/auth/, backend/pipeline/, backend/storage/

• backend/models.py, backend/config.py, backend/database.py

• Any frontend/ files

• Any deploy/ or terraform/ files



EXTEND ONLY

• backend/tests/conftest.py — add new fixtures, do NOT modify existing ones





Test Architecture



Fixture Hierarchy





conftest.py (session-scoped)

├── test\_engine          # SQLite in-memory engine

│

├── (per-test fixtures)

│   ├── test\_db          # Fresh session, auto-rollback

│   ├── async\_client     # httpx client with DB override

│   ├── admin\_user       # Admin user in test\_db

│   ├── analyst\_user     # Analyst user in test\_db

│   ├── admin\_token      # JWT for admin

│   └── analyst\_token    # JWT for analyst

│

├── (new fixtures — add these)

│   ├── sales\_team\_user  # User with role=sales\_team + team assignment

│   ├── sales\_team\_token # JWT for sales\_team\_user

│   ├── sample\_sales\_team # SalesTeam record

│   ├── temp\_storage     # LocalStorage in tmp\_path

│   ├── override\_storage # Overrides get\_storage dependency

│   ├── sample\_run\_completed    # PipelineRun(status=completed)

│   ├── sample\_run\_failed       # PipelineRun(status=failed)

│   ├── sample\_run\_pending      # PipelineRun(status=pending)

│   ├── populated\_run   # Run with exceptions + loan facts

│   ├── sample\_loan\_tape\_csv    # CSV content bytes for a valid loan tape

│   └── multiple\_runs    # 10 runs with varied statuses and dates





conftest.py Extensions



Add these fixtures to the existing conftest.py. DO NOT remove or modify

the existing fixtures (test\_engine, test\_db, async\_client, admin\_user,

analyst\_user, admin\_token, analyst\_token).



python

─── New fixtures to ADD to conftest.py ──────────────────



import csv

import io

from datetime import datetime, timezone, timedelta



from backend.models import User, SalesTeam, PipelineRun, LoanException, LoanFact

from backend.auth.security import hash\_password, create\_access\_token

from backend.storage.local import LocalStorage

from backend.api.dependencies import get\_storage

from backend.api.main import app



@pytest\_asyncio.fixture

async def sample\_sales\_team(test\_db) -> SalesTeam:

&nbsp;   team = SalesTeam(name="Integration Test Team")

&nbsp;   test\_db.add(team)

&nbsp;   await test\_db.commit()

&nbsp;   await test\_db.refresh(team)

&nbsp;   return team



@pytest\_asyncio.fixture

async def sales\_team\_user(test\_db, sample\_sales\_team) -> User:

&nbsp;   user = User(

&nbsp;       email="salesteam@test.com",

&nbsp;       username="salesteamuser",

&nbsp;       hashed\_password=hash\_password("salespass"),

&nbsp;       full\_name="Sales Team User",

&nbsp;       role="sales\_team",

&nbsp;       sales\_team\_id=sample\_sales\_team.id,

&nbsp;       is\_active=True,

&nbsp;   )

&nbsp;   test\_db.add(user)

&nbsp;   await test\_db.commit()

&nbsp;   await test\_db.refresh(user)

&nbsp;   return user



@pytest\_asyncio.fixture

def sales\_team\_token(sales\_team\_user) -> str:

&nbsp;   return create\_access\_token(data={"sub": sales\_team\_user.username})



@pytest\_asyncio.fixture

async def sample\_run\_completed(test\_db) -> PipelineRun:

&nbsp;   run = PipelineRun(

&nbsp;       run\_id="completed-run-001",

&nbsp;       status="completed",

&nbsp;       total\_loans=100,

&nbsp;       total\_balance=15\_000\_000.0,

&nbsp;       exceptions\_count=12,

&nbsp;       run\_weekday=2,

&nbsp;       run\_weekday\_name="Wednesday",

&nbsp;       pdate="2026-02-20",

&nbsp;       last\_phase="archive",

&nbsp;       output\_dir="outputs/completed-run-001",

&nbsp;       started\_at=datetime.now(timezone.utc) - timedelta(minutes=5),

&nbsp;       completed\_at=datetime.now(timezone.utc),

&nbsp;       created\_at=datetime.now(timezone.utc),

&nbsp;   )

&nbsp;   test\_db.add(run)

&nbsp;   await test\_db.commit()

&nbsp;   await test\_db.refresh(run)

&nbsp;   return run



@pytest\_asyncio.fixture

async def sample\_run\_failed(test\_db) -> PipelineRun:

&nbsp;   run = PipelineRun(

&nbsp;       run\_id="failed-run-001",

&nbsp;       status="failed",

&nbsp;       total\_loans=50,

&nbsp;       total\_balance=7\_500\_000.0,

&nbsp;       exceptions\_count=0,

&nbsp;       last\_phase="eligibility",

&nbsp;       started\_at=datetime.now(timezone.utc) - timedelta(minutes=2),

&nbsp;       completed\_at=datetime.now(timezone.utc),

&nbsp;       created\_at=datetime.now(timezone.utc),

&nbsp;   )

&nbsp;   test\_db.add(run)

&nbsp;   await test\_db.commit()

&nbsp;   await test\_db.refresh(run)

&nbsp;   return run



@pytest\_asyncio.fixture

async def sample\_run\_pending(test\_db) -> PipelineRun:

&nbsp;   run = PipelineRun(

&nbsp;       run\_id="pending-run-001",

&nbsp;       status="pending",

&nbsp;       total\_loans=0,

&nbsp;       total\_balance=0.0,

&nbsp;       exceptions\_count=0,

&nbsp;       created\_at=datetime.now(timezone.utc),

&nbsp;   )

&nbsp;   test\_db.add(run)

&nbsp;   await test\_db.commit()

&nbsp;   await test\_db.refresh(run)

&nbsp;   return run



@pytest\_asyncio.fixture

async def populated\_run(test\_db, sample\_run\_completed) -> dict:

&nbsp;   """A completed run with exceptions and loan facts populated."""

&nbsp;   run = sample\_run\_completed



&nbsp;   # Create exceptions

&nbsp;   exceptions = \[]

&nbsp;   for i in range(12):

&nbsp;       exc = LoanException(

&nbsp;           run\_id=run.run\_id,

&nbsp;           seller\_loan\_number=f"LOAN-{i:04d}",

&nbsp;           exception\_type="ltv\_ratio" if i % 3 == 0 else ("credit\_score" if i % 3 == 1 else "missing\_field"),

&nbsp;           exception\_category="credit" if i % 2 == 0 else "data\_quality",

&nbsp;           severity="hard" if i % 4 == 0 else "soft",

&nbsp;           message=f"Test exception message {i}",

&nbsp;           rejection\_criteria=f"notebook.rule\_{i}",

&nbsp;           created\_at=datetime.now(timezone.utc),

&nbsp;       )

&nbsp;       exceptions.append(exc)

&nbsp;   test\_db.add\_all(exceptions)



&nbsp;   # Create loan facts

&nbsp;   facts = \[]

&nbsp;   dispositions = \["to\_purchase"]  70 + \["rejected"]  20 + \["projected"] \* 10

&nbsp;   for i, disp in enumerate(dispositions):

&nbsp;       fact = LoanFact(

&nbsp;           run\_id=run.run\_id,

&nbsp;           seller\_loan\_number=f"LOAN-{i:04d}",

&nbsp;           disposition=disp,

&nbsp;           loan\_data={

&nbsp;               "seller\_loan\_number": f"LOAN-{i:04d}",

&nbsp;               "loan\_amount": 150\_000 + (i \* 1000),

&nbsp;               "note\_rate": 6.5 + (i \* 0.01),

&nbsp;               "ltv\_ratio": 75.0 + (i \* 0.1),

&nbsp;               "dti\_ratio": 35.0 + (i \* 0.05),

&nbsp;               "credit\_score": 700 + i,

&nbsp;               "property\_type": "sfr",

&nbsp;               "occupancy\_status": "primary",

&nbsp;               "loan\_purpose": "purchase",

&nbsp;               "purchase\_price": 200\_000 + (i \* 1000),

&nbsp;               "appraisal\_value": 210\_000 + (i \* 1000),

&nbsp;           },

&nbsp;           created\_at=datetime.now(timezone.utc),

&nbsp;       )

&nbsp;       facts.append(fact)

&nbsp;   test\_db.add\_all(facts)

&nbsp;   await test\_db.commit()



&nbsp;   return {"run": run, "exceptions": exceptions, "facts": facts}



@pytest\_asyncio.fixture

async def multiple\_runs(test\_db, sample\_sales\_team) -> list\[PipelineRun]:

&nbsp;   """Create 10 runs with varied statuses, dates, and team assignments."""

&nbsp;   runs = \[]

&nbsp;   statuses = \["completed"]  5 + \["failed"]  2 + \["running"]  1 + \["pending"]  2

&nbsp;   for i, status in enumerate(statuses):

&nbsp;       run = PipelineRun(

&nbsp;           run\_id=f"multi-run-{i:03d}",

&nbsp;           status=status,

&nbsp;           sales\_team\_id=sample\_sales\_team.id if i % 2 == 0 else None,

&nbsp;           total\_loans=50 + (i \* 10),

&nbsp;           total\_balance=5\_000\_000.0 + (i \* 1\_000\_000),

&nbsp;           exceptions\_count=i \* 2,

&nbsp;           run\_weekday=i % 7,

&nbsp;           run\_weekday\_name=\["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]\[i % 7],

&nbsp;           pdate=f"2026-02-{10+i:02d}",

&nbsp;           last\_phase="archive" if status == "completed" else "eligibility",

&nbsp;           created\_at=datetime.now(timezone.utc) - timedelta(hours=i),

&nbsp;       )

&nbsp;       runs.append(run)

&nbsp;   test\_db.add\_all(runs)

&nbsp;   await test\_db.commit()

&nbsp;   return runs



@pytest.fixture

def sample\_loan\_tape\_csv() -> bytes:

&nbsp;   """Generate a valid CSV loan tape for pipeline testing."""

&nbsp;   buffer = io.StringIO()

&nbsp;   writer = csv.DictWriter(buffer, fieldnames=\[

&nbsp;       "seller\_loan\_number", "loan\_amount", "note\_rate", "ltv\_ratio",

&nbsp;       "dti\_ratio", "credit\_score", "property\_type", "occupancy\_status",

&nbsp;       "loan\_purpose", "purchase\_price", "appraisal\_value",

&nbsp;   ])

&nbsp;   writer.writeheader()

&nbsp;   for i in range(20):

&nbsp;       writer.writerow({

&nbsp;           "seller\_loan\_number": f"TAPE-{i:04d}",

&nbsp;           "loan\_amount": 200\_000 + (i \* 10\_000),

&nbsp;           "note\_rate": 6.0 + (i \* 0.1),

&nbsp;           "ltv\_ratio": 70.0 + (i \* 0.5),

&nbsp;           "dti\_ratio": 30.0 + (i \* 0.3),

&nbsp;           "credit\_score": 680 + (i \* 5),

&nbsp;           "property\_type": "sfr",

&nbsp;           "occupancy\_status": "primary",

&nbsp;           "loan\_purpose": "purchase",

&nbsp;           "purchase\_price": 250\_000 + (i \* 10\_000),

&nbsp;           "appraisal\_value": 260\_000 + (i \* 10\_000),

&nbsp;       })

&nbsp;   return buffer.getvalue().encode("utf-8")



@pytest.fixture

def temp\_storage(tmp\_path) -> LocalStorage:

&nbsp;   return LocalStorage(base\_path=str(tmp\_path))



@pytest.fixture

def override\_storage(temp\_storage):

&nbsp;   app.dependency\_overrides\[get\_storage] = lambda: temp\_storage

&nbsp;   yield temp\_storage

&nbsp;   app.dependency\_overrides.pop(get\_storage, None)





Test File Specifications

1\. backend/tests/test\_integration\_auth\_pipeline.py



Tests that verify auth and pipeline systems work together correctly.



python

"""

Integration tests: Authentication × Pipeline.

Validates that auth rules correctly gate pipeline operations.

"""



class TestAuthPipelineIntegration:



&nbsp;   # ── Role-Based Run Access ────────────────────────────



&nbsp;   async def test\_admin\_sees\_all\_runs(self, async\_client, admin\_token, multiple\_runs):

&nbsp;       """Admin can see runs across all sales teams."""

&nbsp;       response = await async\_client.get("/api/runs", headers=auth(admin\_token))

&nbsp;       assert response.status\_code == 200

&nbsp;       runs = response.json()

&nbsp;       # Admin sees all 10 runs (both team and non-team)

&nbsp;       assert len(runs) == 10



&nbsp;   async def test\_analyst\_sees\_all\_runs(self, async\_client, analyst\_token, multiple\_runs):

&nbsp;       """Analyst can see all runs (not restricted by sales team)."""

&nbsp;       response = await async\_client.get("/api/runs", headers=auth(analyst\_token))

&nbsp;       assert response.status\_code == 200

&nbsp;       assert len(response.json()) == 10



&nbsp;   async def test\_sales\_team\_user\_sees\_only\_own\_team\_runs(

&nbsp;       self, async\_client, sales\_team\_token, multiple\_runs, sample\_sales\_team

&nbsp;   ):

&nbsp;       """Sales team user only sees runs for their team."""

&nbsp;       response = await async\_client.get("/api/runs", headers=auth(sales\_team\_token))

&nbsp;       assert response.status\_code == 200

&nbsp;       runs = response.json()

&nbsp;       # Only even-indexed runs have sales\_team\_id set

&nbsp;       for run in runs:

&nbsp;           assert run\["sales\_team\_id"] == sample\_sales\_team.id



&nbsp;   async def test\_sales\_team\_user\_cannot\_access\_other\_team\_run(

&nbsp;       self, async\_client, sales\_team\_token, test\_db

&nbsp;   ):

&nbsp;       """Sales team user gets 404 for another team's run."""

&nbsp;       other\_team = SalesTeam(name="Other Team")

&nbsp;       test\_db.add(other\_team)

&nbsp;       await test\_db.commit()

&nbsp;       await test\_db.refresh(other\_team)



&nbsp;       other\_run = PipelineRun(

&nbsp;           run\_id="other-team-run",

&nbsp;           status="completed",

&nbsp;           sales\_team\_id=other\_team.id,

&nbsp;           total\_loans=10,

&nbsp;           total\_balance=1\_000\_000.0,

&nbsp;           exceptions\_count=0,

&nbsp;           created\_at=datetime.now(timezone.utc),

&nbsp;       )

&nbsp;       test\_db.add(other\_run)

&nbsp;       await test\_db.commit()



&nbsp;       response = await async\_client.get(

&nbsp;           "/api/runs/other-team-run", headers=auth(sales\_team\_token)

&nbsp;       )

&nbsp;       assert response.status\_code == 404



&nbsp;   # ── Run Detail Access ────────────────────────────────



&nbsp;   async def test\_admin\_accesses\_any\_run\_detail(

&nbsp;       self, async\_client, admin\_token, sample\_run\_completed

&nbsp;   ):

&nbsp;       response = await async\_client.get(

&nbsp;           f"/api/runs/{sample\_run\_completed.run\_id}",

&nbsp;           headers=auth(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200



&nbsp;   async def test\_summary\_requires\_auth(self, async\_client, sample\_run\_completed):

&nbsp;       response = await async\_client.get(f"/api/summary/{sample\_run\_completed.run\_id}")

&nbsp;       assert response.status\_code == 401



&nbsp;   # ── Exceptions Access ────────────────────────────────



&nbsp;   async def test\_sales\_team\_exceptions\_scoped(

&nbsp;       self, async\_client, sales\_team\_token, multiple\_runs, test\_db, sample\_sales\_team

&nbsp;   ):

&nbsp;       """Sales team user only sees exceptions for their team's runs."""

&nbsp;       # Create exceptions for both team and non-team runs

&nbsp;       exc1 = LoanException(

&nbsp;           run\_id="multi-run-000",  # even index = has sales\_team\_id

&nbsp;           seller\_loan\_number="TEAM-001",

&nbsp;           exception\_type="ltv\_ratio",

&nbsp;           exception\_category="credit",

&nbsp;           severity="hard",

&nbsp;           message="Team exception",

&nbsp;           created\_at=datetime.now(timezone.utc),

&nbsp;       )

&nbsp;       exc2 = LoanException(

&nbsp;           run\_id="multi-run-001",  # odd index = no sales\_team\_id

&nbsp;           seller\_loan\_number="OTHER-001",

&nbsp;           exception\_type="credit\_score",

&nbsp;           exception\_category="credit",

&nbsp;           severity="hard",

&nbsp;           message="Non-team exception",

&nbsp;           created\_at=datetime.now(timezone.utc),

&nbsp;       )

&nbsp;       test\_db.add\_all(\[exc1, exc2])

&nbsp;       await test\_db.commit()



&nbsp;       response = await async\_client.get(

&nbsp;           "/api/exceptions", headers=auth(sales\_team\_token)

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       exceptions = response.json()

&nbsp;       # Should only see exceptions from team runs

&nbsp;       for exc in exceptions:

&nbsp;           assert exc\["seller\_loan\_number"] != "OTHER-001"



&nbsp;   # ── Disabled User Cannot Access Pipeline ─────────────



&nbsp;   async def test\_disabled\_user\_cannot\_list\_runs(

&nbsp;       self, async\_client, test\_db

&nbsp;   ):

&nbsp;       """Disabled user's token is rejected."""

&nbsp;       disabled = User(

&nbsp;           email="disabled@test.com",

&nbsp;           username="disabledpipeline",

&nbsp;           hashed\_password=hash\_password("password123"),

&nbsp;           full\_name="Disabled",

&nbsp;           role="analyst",

&nbsp;           is\_active=False,

&nbsp;       )

&nbsp;       test\_db.add(disabled)

&nbsp;       await test\_db.commit()



&nbsp;       token = create\_access\_token(data={"sub": disabled.username})

&nbsp;       response = await async\_client.get("/api/runs", headers=auth(token))

&nbsp;       assert response.status\_code == 401

2\. backend/tests/test\_integration\_pipeline\_files.py



Tests that verify pipeline output files can be accessed through the file system.



python

"""

Integration tests: Pipeline × File Management.

Validates that pipeline outputs are correctly stored and retrievable.

"""



class TestPipelineFileIntegration:



&nbsp;   async def test\_pipeline\_outputs\_appear\_in\_file\_listing(self, ...):

&nbsp;       """After a run completes, output files appear in /api/files/list."""



&nbsp;   async def test\_download\_pipeline\_output\_via\_files\_endpoint(self, ...):

&nbsp;       """Pipeline outputs can be downloaded through the files API."""



&nbsp;   async def test\_notebook\_output\_download\_returns\_valid\_csv(self, ...):

&nbsp;       """Downloaded CSV files have correct headers and data."""



&nbsp;   async def test\_upload\_loan\_tape\_then\_list\_in\_inputs(self, ...):

&nbsp;       """Upload a CSV → appears in /api/files/list?area=inputs."""



&nbsp;   async def test\_archive\_files\_accessible\_after\_run(self, ...):

&nbsp;       """Archive endpoint returns both input and output files."""



&nbsp;   async def test\_exception\_export\_csv\_matches\_api\_data(self, ...):

&nbsp;       """Exported CSV contains same data as API query."""



&nbsp;   async def test\_exception\_export\_xlsx\_is\_valid(self, ...):

&nbsp;       """Exported XLSX file can be opened and contains data."""

3\. backend/tests/test\_integration\_full\_workflow.py



Complete end-to-end workflows that simulate real user sessions.



python

"""

End-to-end workflow tests.

Each test simulates a complete user journey through the application.

"""



class TestFullWorkflow:



&nbsp;   async def test\_complete\_admin\_workflow(self, async\_client, override\_storage, sample\_loan\_tape\_csv):

&nbsp;       """

&nbsp;       Full admin workflow:

1\. Login as admin

2\. Create a sales team user

3\. Upload a loan tape file

4\. Trigger a pipeline run

5\. Check run status

6\. View summary

7\. Browse exceptions

8\. Download output files

9\. Export exceptions as CSV

&nbsp;       """



&nbsp;   async def test\_analyst\_read\_only\_workflow(self, async\_client, admin\_token, analyst\_token, populated\_run):

&nbsp;       """

&nbsp;       Analyst workflow:

1\. Login as analyst

2\. List completed runs

3\. View run detail

4\. Browse exceptions with filters

5\. Download outputs

6\. Cannot create users (403)

&nbsp;       """



&nbsp;   async def test\_sales\_team\_scoped\_workflow(

&nbsp;       self, async\_client, admin\_token, sales\_team\_token, sample\_sales\_team

&nbsp;   ):

&nbsp;       """

&nbsp;       Sales team workflow:

1\. Login as sales team user

2\. See only own team's runs

3\. View summary for own run

4\. Cannot see other team's runs

5\. Cannot access user management

&nbsp;       """



&nbsp;   async def test\_new\_user\_onboarding\_workflow(self, async\_client, admin\_token):

&nbsp;       """

1\. Admin creates new analyst user

2\. New user logs in with provided credentials

3\. New user accesses /me

4\. New user lists runs

5\. Admin updates user role to sales\_team

6\. User now sees scoped data

&nbsp;       """



&nbsp;   async def test\_pipeline\_failure\_recovery(self, async\_client, admin\_token, override\_storage):

&nbsp;       """

1\. Trigger a run that will fail (bad input data)

2\. Verify run status is "failed"

3\. Verify partial data is still queryable

4\. Trigger a new run with valid data

5\. Verify new run succeeds independently

&nbsp;       """

4\. backend/tests/test\_security.py



Security-focused tests that probe attack vectors and access boundaries.



python

"""

Security boundary tests.

Validates authentication, authorization, injection prevention, and data leakage.

"""



class TestAuthenticationSecurity:



&nbsp;   async def test\_expired\_token\_rejected(self, ...): ...

&nbsp;   async def test\_malformed\_token\_rejected(self, ...): ...

&nbsp;   async def test\_token\_with\_invalid\_signature(self, ...): ...

&nbsp;   async def test\_token\_for\_deleted\_user\_rejected(self, ...): ...

&nbsp;   async def test\_token\_for\_deactivated\_user\_rejected(self, ...): ...

&nbsp;   async def test\_empty\_authorization\_header(self, ...): ...

&nbsp;   async def test\_bearer\_prefix\_required(self, ...): ...



class TestAuthorizationSecurity:



&nbsp;   async def test\_analyst\_cannot\_register\_users(self, ...): ...

&nbsp;   async def test\_analyst\_cannot\_update\_users(self, ...): ...

&nbsp;   async def test\_analyst\_cannot\_list\_users(self, ...): ...

&nbsp;   async def test\_sales\_team\_cannot\_see\_other\_team\_data(self, ...): ...

&nbsp;   async def test\_admin\_cannot\_self\_demote(self, ...): ...

&nbsp;   async def test\_admin\_cannot\_self\_deactivate(self, ...): ...

&nbsp;   async def test\_role\_escalation\_prevented(self, ...):

&nbsp;       """Non-admin cannot set their own role to admin."""



class TestPathTraversalSecurity:



&nbsp;   async def test\_dotdot\_in\_file\_list(self, ...): ...

&nbsp;   async def test\_dotdot\_in\_file\_download(self, ...): ...

&nbsp;   async def test\_dotdot\_in\_file\_upload\_path(self, ...): ...

&nbsp;   async def test\_dotdot\_in\_file\_delete(self, ...): ...

&nbsp;   async def test\_dotdot\_in\_mkdir(self, ...): ...

&nbsp;   async def test\_absolute\_path\_rejected(self, ...): ...

&nbsp;   async def test\_tilde\_home\_dir\_rejected(self, ...): ...

&nbsp;   async def test\_null\_byte\_in\_path(self, ...): ...

&nbsp;   async def test\_encoded\_traversal\_rejected(self, ...):

&nbsp;       """URL-encoded ..%2F.. should be blocked."""



class TestDataLeakagePrevention:



&nbsp;   async def test\_no\_password\_hash\_in\_login\_response(self, ...): ...

&nbsp;   async def test\_no\_password\_hash\_in\_me\_response(self, ...): ...

&nbsp;   async def test\_no\_password\_hash\_in\_user\_list(self, ...): ...

&nbsp;   async def test\_no\_password\_hash\_in\_register\_response(self, ...): ...

&nbsp;   async def test\_no\_internal\_ids\_in\_error\_messages(self, ...): ...

&nbsp;   async def test\_login\_error\_doesnt\_reveal\_user\_existence(self, ...):

&nbsp;       """Same error for bad username and bad password."""



class TestInputValidation:



&nbsp;   async def test\_register\_sql\_injection\_in\_username(self, ...): ...

&nbsp;   async def test\_register\_xss\_in\_full\_name(self, ...): ...

&nbsp;   async def test\_extremely\_long\_username\_rejected(self, ...): ...

&nbsp;   async def test\_extremely\_long\_password\_handled(self, ...): ...

&nbsp;   async def test\_unicode\_username\_handling(self, ...): ...

&nbsp;   async def test\_empty\_body\_returns\_422(self, ...): ...

&nbsp;   async def test\_wrong\_content\_type\_handled(self, ...): ...



class TestFileUploadSecurity:



&nbsp;   async def test\_executable\_extension\_blocked(self, ...): ...

&nbsp;   async def test\_double\_extension\_blocked(self, ...):

&nbsp;       """file.csv.exe should be rejected."""

&nbsp;   async def test\_no\_extension\_blocked(self, ...): ...

&nbsp;   async def test\_oversized\_file\_rejected(self, ...): ...

&nbsp;   async def test\_empty\_file\_handled(self, ...): ...

&nbsp;   async def test\_cross\_area\_access\_blocked(self, ...):

&nbsp;       """Cannot access inputs files via outputs area."""

5\. backend/tests/test\_data\_integrity.py



Tests that verify data consistency across database operations.



python

"""

Data integrity tests.

Validates constraints, relationships, cascading behavior, and consistency.

"""



class TestDatabaseConstraints:



&nbsp;   async def test\_unique\_email\_constraint(self, ...): ...

&nbsp;   async def test\_unique\_username\_constraint(self, ...): ...

&nbsp;   async def test\_unique\_run\_id\_constraint(self, ...): ...

&nbsp;   async def test\_foreign\_key\_sales\_team(self, ...): ...

&nbsp;   async def test\_foreign\_key\_exceptions\_to\_run(self, ...): ...

&nbsp;   async def test\_foreign\_key\_loan\_facts\_to\_run(self, ...): ...



class TestDataConsistency:



&nbsp;   async def test\_run\_totals\_match\_loan\_facts(self, ...):

&nbsp;       """total\_loans matches count of LoanFact records."""



&nbsp;   async def test\_exceptions\_count\_matches\_records(self, ...):

&nbsp;       """exceptions\_count matches count of LoanException records."""



&nbsp;   async def test\_disposition\_counts\_sum\_to\_total(self, ...):

&nbsp;       """to\_purchase + rejected + projected = total\_loans."""



&nbsp;   async def test\_summary\_aggregation\_correct(self, ...):

&nbsp;       """GET /summary/{run\_id} returns correct aggregated numbers."""



&nbsp;   async def test\_exceptions\_by\_type\_counts\_correct(self, ...):

&nbsp;       """eligibility\_checks.exceptions\_by\_type matches actual counts."""



&nbsp;   async def test\_exceptions\_by\_severity\_counts\_correct(self, ...):

&nbsp;       """eligibility\_checks.exceptions\_by\_severity matches actual counts."""



class TestRunLifecycle:



&nbsp;   async def test\_run\_status\_transitions(self, ...):

&nbsp;       """Run status progresses: pending → running → completed."""



&nbsp;   async def test\_failed\_run\_has\_completed\_at(self, ...):

&nbsp;       """Failed runs still have completed\_at timestamp."""



&nbsp;   async def test\_completed\_run\_has\_all\_timestamps(self, ...):

&nbsp;       """Completed run has created\_at, started\_at, completed\_at."""



&nbsp;   async def test\_run\_phases\_progress\_correctly(self, ...):

&nbsp;       """last\_phase progresses through expected values."""

6\. backend/tests/test\_edge\_cases.py



Boundary conditions and unusual inputs.



python

"""

Edge case tests.

Validates behavior at boundaries, with empty data, and unusual inputs.

"""



class TestEmptyData:



&nbsp;   async def test\_list\_runs\_when\_none\_exist(self, ...): ...

&nbsp;   async def test\_list\_exceptions\_when\_none\_exist(self, ...): ...

&nbsp;   async def test\_list\_loans\_for\_empty\_run(self, ...): ...

&nbsp;   async def test\_summary\_for\_run\_with\_no\_exceptions(self, ...): ...

&nbsp;   async def test\_list\_files\_empty\_directory(self, ...): ...

&nbsp;   async def test\_export\_exceptions\_when\_none\_exist(self, ...): ...

&nbsp;   async def test\_list\_sales\_teams\_when\_none\_exist(self, ...): ...



class TestBoundaryValues:



&nbsp;   async def test\_pagination\_skip\_zero(self, ...): ...

&nbsp;   async def test\_pagination\_skip\_beyond\_results(self, ...): ...

&nbsp;   async def test\_pagination\_limit\_one(self, ...): ...

&nbsp;   async def test\_pagination\_limit\_max(self, ...): ...

&nbsp;   async def test\_loan\_amount\_at\_minimum(self, ...):

&nbsp;       """Loan amount exactly $50,000 passes eligibility."""

&nbsp;   async def test\_loan\_amount\_below\_minimum(self, ...):

&nbsp;       """Loan amount $49,999 fails eligibility."""

&nbsp;   async def test\_loan\_amount\_at\_maximum(self, ...):

&nbsp;       """Loan amount exactly $5,000,000 passes."""

&nbsp;   async def test\_loan\_amount\_above\_maximum(self, ...):

&nbsp;       """Loan amount $5,000,001 fails."""

&nbsp;   async def test\_ltv\_at\_maximum(self, ...):

&nbsp;       """LTV exactly 97.0% passes."""

&nbsp;   async def test\_ltv\_above\_maximum(self, ...):

&nbsp;       """LTV 97.01% fails."""

&nbsp;   async def test\_credit\_score\_at\_minimum(self, ...):

&nbsp;       """Credit score exactly 620 passes."""

&nbsp;   async def test\_credit\_score\_below\_minimum(self, ...):

&nbsp;       """Credit score 619 fails."""



class TestSpecialCharacters:



&nbsp;   async def test\_filename\_with\_spaces(self, ...): ...

&nbsp;   async def test\_filename\_with\_unicode(self, ...): ...

&nbsp;   async def test\_path\_with\_special\_chars(self, ...): ...

&nbsp;   async def test\_run\_id\_is\_valid\_uuid(self, ...): ...



class TestConcurrentRequests:



&nbsp;   async def test\_multiple\_simultaneous\_run\_listings(self, ...): ...

&nbsp;   async def test\_simultaneous\_file\_uploads(self, ...): ...

7\. backend/tests/test\_eligibility\_rules.py



Unit tests for each eligibility rule in isolation.



python

"""

Eligibility rule unit tests.

Tests each rule independently with valid, invalid, and boundary values.

"""



class TestLoanAmountRule:

&nbsp;   def test\_valid\_amount(self): ...

&nbsp;   def test\_below\_minimum(self): ...

&nbsp;   def test\_above\_maximum(self): ...

&nbsp;   def test\_at\_minimum\_boundary(self): ...

&nbsp;   def test\_at\_maximum\_boundary(self): ...

&nbsp;   def test\_zero\_amount(self): ...

&nbsp;   def test\_negative\_amount(self): ...

&nbsp;   def test\_missing\_amount(self): ...



class TestLTVRatioRule:

&nbsp;   def test\_valid\_ltv(self): ...

&nbsp;   def test\_exceeds\_maximum(self): ...

&nbsp;   def test\_at\_boundary(self): ...

&nbsp;   def test\_zero\_ltv(self): ...

&nbsp;   def test\_missing\_ltv(self): ...



class TestDTIRatioRule:

&nbsp;   def test\_valid\_dti(self): ...

&nbsp;   def test\_exceeds\_maximum(self): ...

&nbsp;   def test\_at\_boundary(self): ...

&nbsp;   def test\_missing\_dti(self): ...



class TestCreditScoreRule:

&nbsp;   def test\_valid\_score(self): ...

&nbsp;   def test\_below\_minimum(self): ...

&nbsp;   def test\_at\_boundary(self): ...

&nbsp;   def test\_missing\_score(self): ...



class TestPropertyTypeRule:

&nbsp;   def test\_sfr(self): ...

&nbsp;   def test\_condo(self): ...

&nbsp;   def test\_townhouse(self): ...

&nbsp;   def test\_pud(self): ...

&nbsp;   def test\_two\_to\_four\_unit(self): ...

&nbsp;   def test\_invalid\_type(self): ...

&nbsp;   def test\_case\_insensitive(self): ...

&nbsp;   def test\_missing\_type(self): ...



class TestOccupancyRule:

&nbsp;   def test\_primary(self): ...

&nbsp;   def test\_second\_home(self): ...

&nbsp;   def test\_investment(self): ...

&nbsp;   def test\_invalid\_occupancy(self): ...

&nbsp;   def test\_case\_insensitive(self): ...



class TestLoanPurposeRule:

&nbsp;   def test\_purchase(self): ...

&nbsp;   def test\_rate\_term\_refinance(self): ...

&nbsp;   def test\_cash\_out\_refinance(self): ...

&nbsp;   def test\_invalid\_purpose(self): ...



class TestSoftRules:

&nbsp;   """Soft severity rules create exceptions but don't reject loans."""

&nbsp;   def test\_missing\_purchase\_price\_is\_soft(self): ...

&nbsp;   def test\_missing\_appraisal\_is\_soft(self): ...

&nbsp;   def test\_note\_rate\_out\_of\_range\_is\_soft(self): ...



class TestCombinedEligibility:

&nbsp;   def test\_all\_rules\_pass(self): ...

&nbsp;   def test\_multiple\_hard\_failures(self): ...

&nbsp;   def test\_soft\_failures\_dont\_reject(self): ...

&nbsp;   def test\_mix\_of\_hard\_and\_soft(self): ...

&nbsp;   def test\_completely\_empty\_loan(self): ...

8\. backend/tests/test\_pipeline\_phases.py



Unit tests for individual pipeline phases.



python

"""

Pipeline phase unit tests.

Tests each phase function independently.

"""



class TestPhaseValidate:

&nbsp;   async def test\_valid\_loans\_pass(self, ...): ...

&nbsp;   async def test\_missing\_required\_fields\_flagged(self, ...): ...

&nbsp;   async def test\_validation\_exceptions\_created(self, ...): ...

&nbsp;   async def test\_partially\_valid\_batch(self, ...): ...



class TestPhaseEligibility:

&nbsp;   async def test\_eligible\_loans\_pass(self, ...): ...

&nbsp;   async def test\_ineligible\_loans\_flagged(self, ...): ...

&nbsp;   async def test\_validation\_failures\_skipped(self, ...): ...

&nbsp;   async def test\_exception\_records\_created(self, ...): ...



class TestPhasePricing:

&nbsp;   async def test\_eligible\_loans\_priced(self, ...): ...

&nbsp;   async def test\_ineligible\_loans\_not\_priced(self, ...): ...

&nbsp;   async def test\_pricing\_spread\_calculation(self, ...): ...

&nbsp;   async def test\_custom\_irr\_target(self, ...): ...



class TestPhaseDisposition:

&nbsp;   async def test\_to\_purchase\_disposition(self, ...): ...

&nbsp;   async def test\_rejected\_disposition(self, ...): ...

&nbsp;   async def test\_projected\_disposition(self, ...): ...

&nbsp;   async def test\_loan\_facts\_created(self, ...): ...

&nbsp;   async def test\_internal\_flags\_cleaned(self, ...):

&nbsp;       """\_eligible and \_validation\_failed not in loan\_data."""



class TestPhaseOutput:

&nbsp;   async def test\_four\_output\_files\_created(self, ...): ...

&nbsp;   async def test\_purchase\_tape\_content(self, ...): ...

&nbsp;   async def test\_rejection\_report\_includes\_exceptions(self, ...): ...

&nbsp;   async def test\_exception\_summary\_aggregation(self, ...): ...

9\. backend/tests/test\_path\_utils.py



Comprehensive tests for path security utilities.



python

"""

Path utility tests.

Validates sanitization, traversal prevention, and validation functions.

"""



class TestSafeJoin:

&nbsp;   def test\_simple\_join(self): ...

&nbsp;   def test\_nested\_join(self): ...

&nbsp;   def test\_dotdot\_raises(self): ...

&nbsp;   def test\_absolute\_path\_raises(self): ...

&nbsp;   def test\_tilde\_raises(self): ...

&nbsp;   def test\_empty\_parts\_ignored(self): ...

&nbsp;   def test\_dot\_parts\_ignored(self): ...

&nbsp;   def test\_backslash\_normalized(self): ...

&nbsp;   def test\_multiple\_slashes\_collapsed(self): ...



class TestSanitizeFilename:

&nbsp;   def test\_normal\_filename(self): ...

&nbsp;   def test\_spaces\_to\_underscores(self): ...

&nbsp;   def test\_special\_chars\_removed(self): ...

&nbsp;   def test\_unicode\_normalized(self): ...

&nbsp;   def test\_leading\_dots\_stripped(self): ...

&nbsp;   def test\_empty\_filename\_raises(self): ...

&nbsp;   def test\_only\_special\_chars\_raises(self): ...



class TestValidateFileExtension:

&nbsp;   def test\_csv\_allowed(self): ...

&nbsp;   def test\_xlsx\_allowed(self): ...

&nbsp;   def test\_exe\_blocked(self): ...

&nbsp;   def test\_no\_extension\_blocked(self): ...

&nbsp;   def test\_case\_insensitive(self): ...



class TestValidateFileSize:

&nbsp;   def test\_under\_limit(self): ...

&nbsp;   def test\_at\_limit(self): ...

&nbsp;   def test\_over\_limit(self): ...



class TestValidateArea:

&nbsp;   def test\_valid\_areas(self): ...

&nbsp;   def test\_invalid\_area\_raises(self): ...



class TestNormalizeStoragePath:

&nbsp;   def test\_normal\_path(self): ...

&nbsp;   def test\_backslashes\_converted(self): ...

&nbsp;   def test\_leading\_trailing\_slashes\_stripped(self): ...

&nbsp;   def test\_multiple\_slashes\_collapsed(self): ...

&nbsp;   def test\_dot\_components\_removed(self): ...

&nbsp;   def test\_empty\_path(self): ...

10\. backend/tests/test\_pagination.py



Pagination behavior across all list endpoints.



python

"""

Pagination tests across all list endpoints.

Validates skip, limit, ordering, and edge cases.

"""



class TestRunsPagination:

&nbsp;   async def test\_default\_pagination(self, ...): ...

&nbsp;   async def test\_custom\_limit(self, ...): ...

&nbsp;   async def test\_skip\_offset(self, ...): ...

&nbsp;   async def test\_ordered\_by\_created\_at\_desc(self, ...): ...

&nbsp;   async def test\_skip\_beyond\_total(self, ...): ...

&nbsp;   async def test\_limit\_one(self, ...): ...



class TestExceptionsPagination:

&nbsp;   async def test\_default\_pagination(self, ...): ...

&nbsp;   async def test\_combined\_filters\_and\_pagination(self, ...): ...

&nbsp;   async def test\_consistent\_across\_pages(self, ...):

&nbsp;       """Page 1 + Page 2 combined equals full unfiltered list."""



class TestLoansPagination:

&nbsp;   async def test\_default\_pagination(self, ...): ...

&nbsp;   async def test\_disposition\_filter\_with\_pagination(self, ...): ...



class TestUsersPagination:

&nbsp;   async def test\_default\_pagination(self, ...): ...

&nbsp;   async def test\_role\_filter\_with\_pagination(self, ...): ...

&nbsp;   async def test\_deterministic\_order(self, ...): ...

11\. backend/tests/test\_concurrent.py



Concurrency and race condition tests.



python

"""

Concurrency tests.

Validates the application handles concurrent requests correctly.

"""

import asyncio



class TestConcurrentAccess:



&nbsp;   async def test\_concurrent\_run\_listings(self, async\_client, admin\_token, multiple\_runs):

&nbsp;       """Multiple simultaneous GET /runs requests return consistent data."""

&nbsp;       tasks = \[

&nbsp;           async\_client.get("/api/runs", headers=auth(admin\_token))

&nbsp;           for \_ in range(10)

&nbsp;       ]

&nbsp;       responses = await asyncio.gather(\*tasks)

&nbsp;       counts = \[len(r.json()) for r in responses]

&nbsp;       assert all(c == counts\[0] for c in counts), "Inconsistent results"



&nbsp;   async def test\_concurrent\_exception\_queries(self, ...):

&nbsp;       """Multiple simultaneous exception queries return consistent data."""



&nbsp;   async def test\_concurrent\_file\_uploads(self, ...):

&nbsp;       """Multiple simultaneous file uploads don't corrupt each other."""



&nbsp;   async def test\_concurrent\_logins(self, ...):

&nbsp;       """Multiple simultaneous logins succeed independently."""





Test Execution Configuration



Run all tests



bash

pytest backend/tests/ -v --tb=short --timeout=30



Run by category



bash

Unit tests only

pytest backend/tests/test\_eligibility\_rules.py backend/tests/test\_path\_utils.py backend/tests/test\_pipeline\_phases.py -v



Integration tests

pytest backend/tests/test\_integration\_\*.py -v



Security tests

pytest backend/tests/test\_security.py -v



All endpoint tests

pytest backend/tests/test\_auth\_routes.py backend/tests/test\_pipeline\_routes.py backend/tests/test\_file\_routes.py -v



Expected test counts



| File | Expected Tests |

|------|---------------|

| test\_health.py | 3 |

| test\_auth\_routes.py | 30+ |

| test\_pipeline\_routes.py | 25+ |

| test\_file\_routes.py | 25+ |

| test\_storage\_local.py | 15+ |

| test\_storage\_s3.py | 10+ |

| test\_integration\_auth\_pipeline.py | 10+ |

| test\_integration\_pipeline\_files.py | 8+ |

| test\_integration\_full\_workflow.py | 5+ |

| test\_security.py | 30+ |

| test\_data\_integrity.py | 15+ |

| test\_edge\_cases.py | 25+ |

| test\_eligibility\_rules.py | 40+ |

| test\_pipeline\_phases.py | 20+ |

| test\_path\_utils.py | 25+ |

| test\_pagination.py | 15+ |

| test\_concurrent.py | 5+ |

| Total | 300+ |





Validation Criteria for Phase 6



After implementation, ALL must pass:

1\. pytest backend/tests/ -v --timeout=30             → all tests pass

2\. Total test count ≥ 300

3\. ruff check backend/tests/                         → no lint errors

4\. No test uses time.sleep() (use async patterns)

5\. No test depends on external services (database is in-memory, S3 is mocked)

6\. No test modifies files outside tmp\_path

7\. Every API endpoint is tested by at least 2 test files

8\. Every eligibility rule has boundary value tests

9\. Every path traversal vector is tested

10\. All test classes use @pytest.mark.asyncio on async methods

11\. No test imports from frontend/ or deploy/

12\. Test fixtures are properly scoped (no session-scoped data mutations)

13\. Tests are deterministic — running twice produces same results

14\. pytest --co backend/tests/ (collect only) shows all tests without errors



Run validation:



bash

Full suite

pytest backend/tests/ -v --tb=short --timeout=30



Verify test count

pytest backend/tests/ --co -q | tail -1



Lint

ruff check backend/tests/



Determinism check (run twice)

pytest backend/tests/ -x --timeout=30 \&\& pytest backend/tests/ -x --timeout=30





Chunking Guide (if prompt exceeds context limits)



| Chunk | File(s) | Focus |

|-------|---------|-------|

| 6a | conftest.py extensions | New shared fixtures |

| 6b | test\_eligibility\_rules.py, test\_path\_utils.py | Pure unit tests (no DB) |

| 6c | test\_pipeline\_phases.py | Phase function unit tests |

| 6d | test\_security.py | Security boundary tests |

| 6e | test\_data\_integrity.py, test\_edge\_cases.py | Data + boundary tests |

| 6f | test\_integration\_auth\_pipeline.py, test\_integration\_pipeline\_files.py | Cross-module integration |

| 6g | test\_integration\_full\_workflow.py | End-to-end workflows |

| 6h | test\_pagination.py, test\_concurrent.py | Pagination + concurrency |



Prepend the conftest fixtures section to all chunks that need database access.



