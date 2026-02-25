\# Task: Implement the Pipeline \& Runs Layer for the Loan Engine API



You are extending the Loan Engine application (Phases 0-1 complete) with a fully

functional pipeline execution system. Replace all pipeline and run stub routes with

real implementations. After this phase, users can trigger loan processing pipelines,

track run status, retrieve results, and download output files.



---



\## Context: What Already Exists (from Phases 0-1)



These files exist with working code. Do NOT regenerate them.

Import from these modules freely.



\### backend/config.py — Settings



```python

class Settings(BaseSettings):

&nbsp;   APP\_NAME: str = "loan-engine"

&nbsp;   ENVIRONMENT: str = "development"

&nbsp;   DEBUG: bool = True

&nbsp;   DATABASE\_URL: str = "postgresql+asyncpg://..."

&nbsp;   DATABASE\_URL\_SYNC: str = "postgresql://..."

&nbsp;   SECRET\_KEY: str

&nbsp;   JWT\_ALGORITHM: str = "HS256"

&nbsp;   ACCESS\_TOKEN\_EXPIRE\_MINUTES: int = 480

&nbsp;   STORAGE\_TYPE: str = "local"          # "local" | "s3"

&nbsp;   LOCAL\_STORAGE\_PATH: str = "./storage"

&nbsp;   S3\_BUCKET\_NAME: str = ""

&nbsp;   S3\_REGION: str = "us-east-1"

&nbsp;   AWS\_ACCESS\_KEY\_ID: str = ""

&nbsp;   AWS\_SECRET\_ACCESS\_KEY: str = ""

&nbsp;   CORS\_ORIGINS: list\[str]

```



\### backend/database.py



```python

engine                  # async SQLAlchemy engine

async\_session\_factory   # async\_sessionmaker

Base                    # DeclarativeBase

async def get\_db() -> AsyncGenerator\[AsyncSession, None]

async def check\_db\_connection() -> bool

```



\### backend/models.py — All ORM Models



```python

class SalesTeam(Base):

&nbsp;   \_\_tablename\_\_ = "sales\_teams"

&nbsp;   id: Mapped\[int]                    # PK

&nbsp;   name: Mapped\[str]                  # unique

&nbsp;   created\_at: Mapped\[datetime]



class User(Base):

&nbsp;   \_\_tablename\_\_ = "users"

&nbsp;   id: Mapped\[int]                    # PK

&nbsp;   email: Mapped\[str]                 # unique, indexed

&nbsp;   username: Mapped\[str]              # unique, indexed

&nbsp;   hashed\_password: Mapped\[str]

&nbsp;   full\_name: Mapped\[str|None]

&nbsp;   role: Mapped\[str]                  # "admin"|"analyst"|"sales\_team"

&nbsp;   sales\_team\_id: Mapped\[int|None]    # FK → sales\_teams.id

&nbsp;   is\_active: Mapped\[bool]

&nbsp;   created\_at: Mapped\[datetime]



class PipelineRun(Base):

&nbsp;   \_\_tablename\_\_ = "pipeline\_runs"

&nbsp;   id: Mapped\[int]                    # PK

&nbsp;   run\_id: Mapped\[str]                # UUID string, unique, indexed

&nbsp;   status: Mapped\[str]                # "pending"|"running"|"completed"|"failed"

&nbsp;   sales\_team\_id: Mapped\[int|None]    # FK → sales\_teams.id

&nbsp;   total\_loans: Mapped\[int]           # default 0

&nbsp;   total\_balance: Mapped\[float]       # default 0.0

&nbsp;   exceptions\_count: Mapped\[int]      # default 0

&nbsp;   run\_weekday: Mapped\[int|None]      # 0=Mon..6=Sun

&nbsp;   run\_weekday\_name: Mapped\[str|None] # "Monday".."Sunday"

&nbsp;   pdate: Mapped\[str|None]            # purchase date string

&nbsp;   last\_phase: Mapped\[str|None]       # last completed pipeline phase

&nbsp;   output\_dir: Mapped\[str|None]       # per-run output directory path

&nbsp;   started\_at: Mapped\[datetime|None]

&nbsp;   completed\_at: Mapped\[datetime|None]

&nbsp;   created\_at: Mapped\[datetime]

&nbsp;   exceptions: Mapped\[list\["LoanException"]]  # relationship

&nbsp;   loan\_facts: Mapped\[list\["LoanFact"]]       # relationship



class LoanException(Base):

&nbsp;   \_\_tablename\_\_ = "loan\_exceptions"

&nbsp;   id: Mapped\[int]                    # PK

&nbsp;   run\_id: Mapped\[str]                # FK → pipeline\_runs.run\_id, indexed

&nbsp;   seller\_loan\_number: Mapped\[str]    # indexed

&nbsp;   exception\_type: Mapped\[str]

&nbsp;   exception\_category: Mapped\[str]

&nbsp;   severity: Mapped\[str]

&nbsp;   message: Mapped\[str|None]

&nbsp;   rejection\_criteria: Mapped\[str|None]

&nbsp;   created\_at: Mapped\[datetime]



class LoanFact(Base):

&nbsp;   \_\_tablename\_\_ = "loan\_facts"

&nbsp;   id: Mapped\[int]                    # PK

&nbsp;   run\_id: Mapped\[str]                # FK → pipeline\_runs.run\_id, indexed

&nbsp;   seller\_loan\_number: Mapped\[str]    # indexed

&nbsp;   disposition: Mapped\[str|None]      # "to\_purchase"|"projected"|"rejected"

&nbsp;   loan\_data: Mapped\[dict|None]       # JSON column

&nbsp;   created\_at: Mapped\[datetime]

```



\### backend/schemas/api.py — Existing Pydantic Models



```python

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



\### backend/auth/security.py — Auth Dependencies



```python

async def get\_current\_user(token, db) -> User      # requires valid JWT

async def admin\_required(current\_user) -> User      # requires admin role

```



\### backend/auth/validators.py — Role Validators



```python

async def sales\_team\_scoped(current\_user) -> User   # scopes by sales team

def require\_roles(\*roles: UserRole) -> dependency    # factory for role checks

```



\### backend/storage/base.py — Storage Abstraction



```python

class StorageBackend(ABC):

&nbsp;   async def list\_files(self, path: str, recursive: bool = False, area: str = "inputs") -> list\[dict]

&nbsp;   async def upload\_file(self, file, destination: str, area: str = "inputs") -> dict

&nbsp;   async def download\_file(self, path: str, area: str = "inputs") -> StreamingResponse

&nbsp;   async def delete\_file(self, path: str, area: str = "inputs") -> dict

&nbsp;   async def create\_directory(self, path: str, area: str = "inputs") -> dict

&nbsp;   async def get\_presigned\_url(self, path: str, expires\_in: int = 3600, area: str = "inputs") -> str

```



\### backend/api/dependencies.py — Shared Dependencies



```python

from backend.database import get\_db

from backend.auth.security import get\_current\_user

\# Add new dependencies here as needed

```



---



\## Files to Create or Modify



\### NEW FILES



| File | Purpose |

|------|---------|

| `backend/pipeline/\_\_init\_\_.py` | Pipeline package init |

| `backend/pipeline/engine.py` | Core pipeline execution engine |

| `backend/pipeline/phases.py` | Individual pipeline phase implementations |

| `backend/pipeline/eligibility.py` | Loan eligibility checking logic |

| `backend/pipeline/notebook\_outputs.py` | Notebook-replacement output generation |

| `backend/tests/test\_pipeline\_routes.py` | Pipeline \& runs test suite |



\### MODIFY



| File | Changes |

|------|---------|

| `backend/api/routes.py` | Replace ALL stub routes with real implementations |

| `backend/api/dependencies.py` | Add get\_storage dependency |

| `backend/schemas/api.py` | Add any new schemas needed |



\### DO NOT MODIFY



\- backend/auth/\* (Phase 1 complete)

\- backend/api/main.py (router wiring already done)

\- backend/api/files.py (Phase 3)

\- backend/models.py (schema stable)

\- backend/database.py (stable)

\- backend/config.py (stable)



---



\## Pipeline Architecture



The Loan Engine pipeline processes loan tapes through a series of phases.

Each run ingests input files, applies eligibility rules, categorizes loans,

generates exceptions, and produces output files.



\### Pipeline Phases (executed in order)



```

Phase 1: INGEST        → Read loan tape files from storage inputs/ directory

Phase 2: VALIDATE      → Validate required fields, data types, formats

Phase 3: ELIGIBILITY   → Apply eligibility rules, flag exceptions

Phase 4: PRICING       → Apply IRR target pricing to eligible loans

Phase 5: DISPOSITION   → Categorize: to\_purchase | projected | rejected

Phase 6: OUTPUT        → Generate 4 notebook-replacement output files

Phase 7: ARCHIVE       → Archive inputs and outputs to archive/{run\_id}/

```



\### Pipeline Execution Flow



```

RunCreate request

&nbsp;   │

&nbsp;   ▼

Create PipelineRun record (status="pending")

&nbsp;   │

&nbsp;   ▼

Set status="running", started\_at=now()

&nbsp;   │

&nbsp;   ├──▶ Phase 1: INGEST

&nbsp;   │    Read loan files from folder or storage inputs/

&nbsp;   │    Parse CSV/Excel → list of loan dicts

&nbsp;   │    Update: total\_loans, total\_balance

&nbsp;   │

&nbsp;   ├──▶ Phase 2: VALIDATE

&nbsp;   │    Check required fields per loan

&nbsp;   │    Create LoanException for validation failures

&nbsp;   │    Update: last\_phase="validate"

&nbsp;   │

&nbsp;   ├──▶ Phase 3: ELIGIBILITY

&nbsp;   │    Apply eligibility rules (see Eligibility section)

&nbsp;   │    Create LoanException for each failed rule

&nbsp;   │    Update: last\_phase="eligibility", exceptions\_count

&nbsp;   │

&nbsp;   ├──▶ Phase 4: PRICING

&nbsp;   │    Calculate pricing based on irr\_target

&nbsp;   │    Update loan\_data with pricing fields

&nbsp;   │    Update: last\_phase="pricing"

&nbsp;   │

&nbsp;   ├──▶ Phase 5: DISPOSITION

&nbsp;   │    Categorize each loan:

&nbsp;   │      - to\_purchase: passes all eligibility, priced

&nbsp;   │      - projected: passes eligibility, not yet priced

&nbsp;   │      - rejected: failed eligibility

&nbsp;   │    Create LoanFact records with disposition

&nbsp;   │    Update: last\_phase="disposition"

&nbsp;   │

&nbsp;   ├──▶ Phase 6: OUTPUT

&nbsp;   │    Generate 4 notebook output files (see Outputs section)

&nbsp;   │    Store in outputs/{run\_id}/

&nbsp;   │    Update: last\_phase="output", output\_dir

&nbsp;   │

&nbsp;   ├──▶ Phase 7: ARCHIVE

&nbsp;   │    Copy inputs → archive/{run\_id}/input/

&nbsp;   │    Copy outputs → archive/{run\_id}/output/

&nbsp;   │    Update: last\_phase="archive"

&nbsp;   │

&nbsp;   ▼

Set status="completed", completed\_at=now()

(On any error: status="failed", record error in last\_phase)

```



---



\## Eligibility Rules (backend/pipeline/eligibility.py)



Each rule takes a loan dict and returns (passed: bool, exception\_data: dict | None).



```python

ELIGIBILITY\_RULES = \[

&nbsp;   {

&nbsp;       "name": "loan\_amount\_range",

&nbsp;       "category": "credit",

&nbsp;       "severity": "hard",

&nbsp;       "rejection\_criteria": "notebook.loan\_amount\_out\_of\_range",

&nbsp;       "check": lambda loan: 50\_000 <= loan.get("loan\_amount", 0) <= 5\_000\_000,

&nbsp;       "message": "Loan amount must be between $50,000 and $5,000,000",

&nbsp;   },

&nbsp;   {

&nbsp;       "name": "ltv\_ratio",

&nbsp;       "category": "credit",

&nbsp;       "severity": "hard",

&nbsp;       "rejection\_criteria": "notebook.ltv\_exceeds\_maximum",

&nbsp;       "check": lambda loan: loan.get("ltv\_ratio", 100) <= 97.0,

&nbsp;       "message": "LTV ratio exceeds maximum of 97%",

&nbsp;   },

&nbsp;   {

&nbsp;       "name": "dti\_ratio",

&nbsp;       "category": "credit",

&nbsp;       "severity": "hard",

&nbsp;       "rejection\_criteria": "notebook.dti\_exceeds\_maximum",

&nbsp;       "check": lambda loan: loan.get("dti\_ratio", 100) <= 50.0,

&nbsp;       "message": "DTI ratio exceeds maximum of 50%",

&nbsp;   },

&nbsp;   {

&nbsp;       "name": "credit\_score",

&nbsp;       "category": "credit",

&nbsp;       "severity": "hard",

&nbsp;       "rejection\_criteria": "notebook.credit\_score\_below\_minimum",

&nbsp;       "check": lambda loan: loan.get("credit\_score", 0) >= 620,

&nbsp;       "message": "Credit score below minimum of 620",

&nbsp;   },

&nbsp;   {

&nbsp;       "name": "property\_type",

&nbsp;       "category": "collateral",

&nbsp;       "severity": "hard",

&nbsp;       "rejection\_criteria": "notebook.ineligible\_property\_type",

&nbsp;       "check": lambda loan: loan.get("property\_type", "").lower() in

&nbsp;           \["sfr", "condo", "townhouse", "pud", "2-4 unit"],

&nbsp;       "message": "Ineligible property type",

&nbsp;   },

&nbsp;   {

&nbsp;       "name": "occupancy\_status",

&nbsp;       "category": "collateral",

&nbsp;       "severity": "hard",

&nbsp;       "rejection\_criteria": "notebook.ineligible\_occupancy",

&nbsp;       "check": lambda loan: loan.get("occupancy\_status", "").lower() in

&nbsp;           \["primary", "second home", "investment"],

&nbsp;       "message": "Ineligible occupancy status",

&nbsp;   },

&nbsp;   {

&nbsp;       "name": "loan\_purpose",

&nbsp;       "category": "compliance",

&nbsp;       "severity": "hard",

&nbsp;       "rejection\_criteria": "notebook.ineligible\_loan\_purpose",

&nbsp;       "check": lambda loan: loan.get("loan\_purpose", "").lower() in

&nbsp;           \["purchase", "rate\_term\_refinance", "cash\_out\_refinance"],

&nbsp;       "message": "Ineligible loan purpose",

&nbsp;   },

&nbsp;   {

&nbsp;       "name": "missing\_purchase\_price",

&nbsp;       "category": "data\_quality",

&nbsp;       "severity": "soft",

&nbsp;       "rejection\_criteria": "notebook.purchase\_price\_mismatch",

&nbsp;       "check": lambda loan: loan.get("purchase\_price") is not None and loan.get("purchase\_price", 0) > 0,

&nbsp;       "message": "Purchase price is missing or zero",

&nbsp;   },

&nbsp;   {

&nbsp;       "name": "missing\_appraisal",

&nbsp;       "category": "data\_quality",

&nbsp;       "severity": "soft",

&nbsp;       "rejection\_criteria": "notebook.appraisal\_missing",

&nbsp;       "check": lambda loan: loan.get("appraisal\_value") is not None and loan.get("appraisal\_value", 0) > 0,

&nbsp;       "message": "Appraisal value is missing or zero",

&nbsp;   },

&nbsp;   {

&nbsp;       "name": "note\_rate\_range",

&nbsp;       "category": "pricing",

&nbsp;       "severity": "soft",

&nbsp;       "rejection\_criteria": "notebook.note\_rate\_out\_of\_range",

&nbsp;       "check": lambda loan: 1.0 <= loan.get("note\_rate", 0) <= 15.0,

&nbsp;       "message": "Note rate outside acceptable range (1%-15%)",

&nbsp;   },

]

```



Implementation requirements:

\- Function `run\_eligibility\_checks(loan: dict) -> tuple\[bool, list\[dict]]`

&nbsp; Returns (all\_passed, list\_of\_exception\_dicts)

\- Hard severity failures → loan is rejected

\- Soft severity failures → loan gets exception but is NOT rejected

\- Each exception dict has: exception\_type, exception\_category, severity,

&nbsp; message, rejection\_criteria, seller\_loan\_number



---



\## Notebook-Replacement Outputs (backend/pipeline/notebook\_outputs.py)



The pipeline generates 4 output files that replace the legacy Excel notebooks.

Store them in the outputs storage area under `{run\_id}/`.



```python

OUTPUT\_FILES = {

&nbsp;   "purchase\_tape": {

&nbsp;       "filename": "purchase\_tape.csv",

&nbsp;       "description": "Loans eligible for purchase (disposition=to\_purchase)",

&nbsp;       "filter": lambda facts: \[f for f in facts if f.disposition == "to\_purchase"],

&nbsp;   },

&nbsp;   "projected\_tape": {

&nbsp;       "filename": "projected\_tape.csv",

&nbsp;       "description": "Projected loans not yet priced (disposition=projected)",

&nbsp;       "filter": lambda facts: \[f for f in facts if f.disposition == "projected"],

&nbsp;   },

&nbsp;   "rejection\_report": {

&nbsp;       "filename": "rejection\_report.csv",

&nbsp;       "description": "Rejected loans with exception details (disposition=rejected)",

&nbsp;       "filter": lambda facts: \[f for f in facts if f.disposition == "rejected"],

&nbsp;   },

&nbsp;   "exception\_summary": {

&nbsp;       "filename": "exception\_summary.csv",

&nbsp;       "description": "All exceptions grouped by type and severity",

&nbsp;       "source": "exceptions",  # built from LoanException records, not LoanFact

&nbsp;   },

}

```



Implementation:

\- Generate each file as CSV using Python `csv` module

\- Write to storage via StorageBackend.upload\_file()

\- purchase\_tape.csv columns: seller\_loan\_number, loan\_amount, note\_rate, ltv\_ratio,

&nbsp; dti\_ratio, credit\_score, property\_type, occupancy\_status, loan\_purpose, purchase\_price,

&nbsp; appraisal\_value, disposition, pricing\_spread, final\_price

\- rejection\_report.csv: same loan columns + exception\_type, severity, message,

&nbsp; rejection\_criteria

\- exception\_summary.csv: exception\_type, exception\_category, severity, count,

&nbsp; rejection\_criteria, sample\_message



---



\## Pipeline Engine (backend/pipeline/engine.py)



```python

"""

Core pipeline execution engine.

Orchestrates the 7-phase pipeline from ingest to archive.

Designed to be called from the API route or scheduled jobs.

"""

import logging

import uuid

from datetime import datetime, timezone



from sqlalchemy.ext.asyncio import AsyncSession



from backend.models import PipelineRun, LoanException, LoanFact

from backend.storage.base import StorageBackend

from backend.pipeline.phases import (

&nbsp;   phase\_ingest,

&nbsp;   phase\_validate,

&nbsp;   phase\_eligibility,

&nbsp;   phase\_pricing,

&nbsp;   phase\_disposition,

&nbsp;   phase\_output,

&nbsp;   phase\_archive,

)



logger = logging.getLogger(\_\_name\_\_)



async def execute\_pipeline(

&nbsp;   run\_config: dict,

&nbsp;   db: AsyncSession,

&nbsp;   storage: StorageBackend,

&nbsp;   current\_user\_id: int | None = None,

&nbsp;   sales\_team\_id: int | None = None,

) -> PipelineRun:

&nbsp;   """

&nbsp;   Execute the full loan processing pipeline.



&nbsp;   Args:

&nbsp;       run\_config: Dict with keys: pdate, irr\_target, folder

&nbsp;       db: Async database session

&nbsp;       storage: Storage backend (local or S3)

&nbsp;       current\_user\_id: ID of the user who triggered the run

&nbsp;       sales\_team\_id: Sales team to associate with this run



&nbsp;   Returns:

&nbsp;       PipelineRun: The completed (or failed) run record

&nbsp;   """

&nbsp;   run\_id = str(uuid.uuid4())

&nbsp;   now = datetime.now(timezone.utc)



&nbsp;   # Determine weekday from run time

&nbsp;   weekday = now.weekday()  # 0=Monday

&nbsp;   weekday\_names = \["Monday", "Tuesday", "Wednesday", "Thursday",

&nbsp;                    "Friday", "Saturday", "Sunday"]



&nbsp;   # Create run record

&nbsp;   pipeline\_run = PipelineRun(

&nbsp;       run\_id=run\_id,

&nbsp;       status="pending",

&nbsp;       sales\_team\_id=sales\_team\_id,

&nbsp;       pdate=run\_config.get("pdate"),

&nbsp;       run\_weekday=weekday,

&nbsp;       run\_weekday\_name=weekday\_names\[weekday],

&nbsp;       output\_dir=f"outputs/{run\_id}",

&nbsp;       created\_at=now,

&nbsp;   )

&nbsp;   db.add(pipeline\_run)

&nbsp;   await db.commit()

&nbsp;   await db.refresh(pipeline\_run)



&nbsp;   try:

&nbsp;       # Update to running

&nbsp;       pipeline\_run.status = "running"

&nbsp;       pipeline\_run.started\_at = datetime.now(timezone.utc)

&nbsp;       await db.commit()



&nbsp;       logger.info("Pipeline %s started (pdate=%s, irr\_target=%s)",

&nbsp;                    run\_id, run\_config.get("pdate"), run\_config.get("irr\_target"))



&nbsp;       # ── Phase 1: Ingest ──

&nbsp;       loans = await phase\_ingest(

&nbsp;           run\_id=run\_id,

&nbsp;           folder=run\_config.get("folder", ""),

&nbsp;           storage=storage,

&nbsp;           db=db,

&nbsp;       )

&nbsp;       pipeline\_run.total\_loans = len(loans)

&nbsp;       pipeline\_run.total\_balance = sum(l.get("loan\_amount", 0) for l in loans)

&nbsp;       pipeline\_run.last\_phase = "ingest"

&nbsp;       await db.commit()



&nbsp;       logger.info("Pipeline %s ingest complete: %d loans, $%.2f total",

&nbsp;                    run\_id, len(loans), pipeline\_run.total\_balance)



&nbsp;       # ── Phase 2: Validate ──

&nbsp;       loans, validation\_exceptions = await phase\_validate(

&nbsp;           run\_id=run\_id,

&nbsp;           loans=loans,

&nbsp;           db=db,

&nbsp;       )

&nbsp;       pipeline\_run.last\_phase = "validate"

&nbsp;       await db.commit()



&nbsp;       # ── Phase 3: Eligibility ──

&nbsp;       loans, eligibility\_exceptions = await phase\_eligibility(

&nbsp;           run\_id=run\_id,

&nbsp;           loans=loans,

&nbsp;           db=db,

&nbsp;       )

&nbsp;       total\_exceptions = len(validation\_exceptions) + len(eligibility\_exceptions)

&nbsp;       pipeline\_run.exceptions\_count = total\_exceptions

&nbsp;       pipeline\_run.last\_phase = "eligibility"

&nbsp;       await db.commit()



&nbsp;       # ── Phase 4: Pricing ──

&nbsp;       loans = await phase\_pricing(

&nbsp;           loans=loans,

&nbsp;           irr\_target=run\_config.get("irr\_target", 8.05),

&nbsp;       )

&nbsp;       pipeline\_run.last\_phase = "pricing"

&nbsp;       await db.commit()



&nbsp;       # ── Phase 5: Disposition ──

&nbsp;       loan\_facts = await phase\_disposition(

&nbsp;           run\_id=run\_id,

&nbsp;           loans=loans,

&nbsp;           db=db,

&nbsp;       )

&nbsp;       pipeline\_run.last\_phase = "disposition"

&nbsp;       await db.commit()



&nbsp;       # ── Phase 6: Output ──

&nbsp;       await phase\_output(

&nbsp;           run\_id=run\_id,

&nbsp;           loan\_facts=loan\_facts,

&nbsp;           exceptions=validation\_exceptions + eligibility\_exceptions,

&nbsp;           storage=storage,

&nbsp;           db=db,

&nbsp;       )

&nbsp;       pipeline\_run.last\_phase = "output"

&nbsp;       await db.commit()



&nbsp;       # ── Phase 7: Archive ──

&nbsp;       await phase\_archive(

&nbsp;           run\_id=run\_id,

&nbsp;           folder=run\_config.get("folder", ""),

&nbsp;           storage=storage,

&nbsp;       )

&nbsp;       pipeline\_run.last\_phase = "archive"



&nbsp;       # Mark complete

&nbsp;       pipeline\_run.status = "completed"

&nbsp;       pipeline\_run.completed\_at = datetime.now(timezone.utc)

&nbsp;       await db.commit()

&nbsp;       await db.refresh(pipeline\_run)



&nbsp;       logger.info("Pipeline %s completed: %d loans, %d exceptions",

&nbsp;                    run\_id, pipeline\_run.total\_loans, pipeline\_run.exceptions\_count)



&nbsp;   except Exception as e:

&nbsp;       logger.error("Pipeline %s failed at phase '%s': %s",

&nbsp;                    run\_id, pipeline\_run.last\_phase, str(e), exc\_info=True)

&nbsp;       pipeline\_run.status = "failed"

&nbsp;       pipeline\_run.completed\_at = datetime.now(timezone.utc)

&nbsp;       await db.commit()

&nbsp;       raise



&nbsp;   return pipeline\_run

```



---



\## Pipeline Phases (backend/pipeline/phases.py)



Implement each phase as an async function. Each phase:

\- Takes the data from the previous phase

\- Performs its processing

\- Returns data for the next phase

\- Creates database records where specified



```python

"""

Individual pipeline phase implementations.

Each phase is an isolated async function with clear inputs and outputs.

"""

import csv

import io

import logging

from datetime import datetime, timezone



from sqlalchemy.ext.asyncio import AsyncSession



from backend.models import LoanException, LoanFact

from backend.storage.base import StorageBackend

from backend.pipeline.eligibility import run\_eligibility\_checks



logger = logging.getLogger(\_\_name\_\_)



REQUIRED\_LOAN\_FIELDS = \[

&nbsp;   "seller\_loan\_number", "loan\_amount", "note\_rate",

&nbsp;   "ltv\_ratio", "credit\_score", "property\_type",

]



async def phase\_ingest(

&nbsp;   run\_id: str,

&nbsp;   folder: str,

&nbsp;   storage: StorageBackend,

&nbsp;   db: AsyncSession,

) -> list\[dict]:

&nbsp;   """

&nbsp;   Phase 1: Read loan tape files from storage.

&nbsp;   Reads CSV files from the inputs area (or specified folder).

&nbsp;   Returns list of loan dicts.

&nbsp;   """

&nbsp;   # List input files

&nbsp;   # ... read CSV/Excel files from storage inputs/ area

&nbsp;   # ... parse into list of dicts

&nbsp;   # ... return loans

&nbsp;   pass  # IMPLEMENT: Read from storage, parse CSV, return list\[dict]



async def phase\_validate(

&nbsp;   run\_id: str,

&nbsp;   loans: list\[dict],

&nbsp;   db: AsyncSession,

) -> tuple\[list\[dict], list\[LoanException]]:

&nbsp;   """

&nbsp;   Phase 2: Validate required fields and data types.

&nbsp;   Creates LoanException for each validation failure.

&nbsp;   Returns (loans\_with\_validation\_flags, list\_of\_exception\_records).

&nbsp;   """

&nbsp;   exceptions = \[]



&nbsp;   for loan in loans:

&nbsp;       missing\_fields = \[f for f in REQUIRED\_LOAN\_FIELDS if not loan.get(f)]

&nbsp;       if missing\_fields:

&nbsp;           exc = LoanException(

&nbsp;               run\_id=run\_id,

&nbsp;               seller\_loan\_number=loan.get("seller\_loan\_number", "UNKNOWN"),

&nbsp;               exception\_type="missing\_field",

&nbsp;               exception\_category="data\_quality",

&nbsp;               severity="hard",

&nbsp;               message=f"Missing required fields: {', '.join(missing\_fields)}",

&nbsp;               rejection\_criteria="notebook.missing\_required\_fields",

&nbsp;               created\_at=datetime.now(timezone.utc),

&nbsp;           )

&nbsp;           db.add(exc)

&nbsp;           exceptions.append(exc)

&nbsp;           loan\["\_validation\_failed"] = True

&nbsp;       else:

&nbsp;           loan\["\_validation\_failed"] = False



&nbsp;   if exceptions:

&nbsp;       await db.commit()



&nbsp;   logger.info("Validate phase: %d exceptions from %d loans", len(exceptions), len(loans))

&nbsp;   return loans, exceptions



async def phase\_eligibility(

&nbsp;   run\_id: str,

&nbsp;   loans: list\[dict],

&nbsp;   db: AsyncSession,

) -> tuple\[list\[dict], list\[LoanException]]:

&nbsp;   """

&nbsp;   Phase 3: Apply eligibility rules.

&nbsp;   Loans that already failed validation are skipped.

&nbsp;   Creates LoanException for each rule failure.

&nbsp;   Returns (loans\_with\_eligibility\_flags, list\_of\_exception\_records).

&nbsp;   """

&nbsp;   exceptions = \[]



&nbsp;   for loan in loans:

&nbsp;       if loan.get("\_validation\_failed"):

&nbsp;           loan\["\_eligible"] = False

&nbsp;           continue



&nbsp;       all\_passed, rule\_exceptions = run\_eligibility\_checks(loan)

&nbsp;       loan\["\_eligible"] = all\_passed



&nbsp;       for exc\_data in rule\_exceptions:

&nbsp;           exc = LoanException(

&nbsp;               run\_id=run\_id,

&nbsp;               seller\_loan\_number=loan.get("seller\_loan\_number", "UNKNOWN"),

&nbsp;               exception\_type=exc\_data\["exception\_type"],

&nbsp;               exception\_category=exc\_data\["exception\_category"],

&nbsp;               severity=exc\_data\["severity"],

&nbsp;               message=exc\_data\["message"],

&nbsp;               rejection\_criteria=exc\_data.get("rejection\_criteria"),

&nbsp;               created\_at=datetime.now(timezone.utc),

&nbsp;           )

&nbsp;           db.add(exc)

&nbsp;           exceptions.append(exc)



&nbsp;           # Hard failures mark loan as ineligible

&nbsp;           if exc\_data\["severity"] == "hard":

&nbsp;               loan\["\_eligible"] = False



&nbsp;   if exceptions:

&nbsp;       await db.commit()



&nbsp;   eligible = sum(1 for l in loans if l.get("\_eligible"))

&nbsp;   logger.info("Eligibility phase: %d/%d eligible, %d exceptions",

&nbsp;               eligible, len(loans), len(exceptions))

&nbsp;   return loans, exceptions



async def phase\_pricing(

&nbsp;   loans: list\[dict],

&nbsp;   irr\_target: float = 8.05,

) -> list\[dict]:

&nbsp;   """

&nbsp;   Phase 4: Apply pricing to eligible loans.

&nbsp;   Calculates pricing\_spread and final\_price based on IRR target.

&nbsp;   Non-eligible loans are skipped.

&nbsp;   """

&nbsp;   for loan in loans:

&nbsp;       if not loan.get("\_eligible"):

&nbsp;           loan\["pricing\_spread"] = None

&nbsp;           loan\["final\_price"] = None

&nbsp;           continue



&nbsp;       note\_rate = loan.get("note\_rate", 0)

&nbsp;       loan\_amount = loan.get("loan\_amount", 0)



&nbsp;       # Simplified pricing model:

&nbsp;       # spread = note\_rate - irr\_target (in percentage points)

&nbsp;       # price = par (100) + spread adjustment

&nbsp;       spread = note\_rate - irr\_target

&nbsp;       base\_price = 100.0

&nbsp;       price\_adjustment = spread \* 2.5  # 2.5 points per 1% spread

&nbsp;       final\_price = round(base\_price + price\_adjustment, 4)



&nbsp;       loan\["pricing\_spread"] = round(spread, 4)

&nbsp;       loan\["final\_price"] = final\_price



&nbsp;   priced = sum(1 for l in loans if l.get("final\_price") is not None)

&nbsp;   logger.info("Pricing phase: %d/%d loans priced (IRR target: %.2f%%)",

&nbsp;               priced, len(loans), irr\_target)

&nbsp;   return loans



async def phase\_disposition(

&nbsp;   run\_id: str,

&nbsp;   loans: list\[dict],

&nbsp;   db: AsyncSession,

) -> list\[LoanFact]:

&nbsp;   """

&nbsp;   Phase 5: Assign disposition and create LoanFact records.

&nbsp;   - to\_purchase: eligible + priced

&nbsp;   - projected: eligible + not priced (edge case)

&nbsp;   - rejected: failed validation or eligibility

&nbsp;   """

&nbsp;   facts = \[]



&nbsp;   for loan in loans:

&nbsp;       if loan.get("\_validation\_failed") or not loan.get("\_eligible"):

&nbsp;           disposition = "rejected"

&nbsp;       elif loan.get("final\_price") is not None:

&nbsp;           disposition = "to\_purchase"

&nbsp;       else:

&nbsp;           disposition = "projected"



&nbsp;       # Clean internal flags before storing

&nbsp;       loan\_data = {k: v for k, v in loan.items() if not k.startswith("\_")}



&nbsp;       fact = LoanFact(

&nbsp;           run\_id=run\_id,

&nbsp;           seller\_loan\_number=loan.get("seller\_loan\_number", "UNKNOWN"),

&nbsp;           disposition=disposition,

&nbsp;           loan\_data=loan\_data,

&nbsp;           created\_at=datetime.now(timezone.utc),

&nbsp;       )

&nbsp;       db.add(fact)

&nbsp;       facts.append(fact)



&nbsp;   await db.commit()



&nbsp;   counts = {}

&nbsp;   for f in facts:

&nbsp;       counts\[f.disposition] = counts.get(f.disposition, 0) + 1

&nbsp;   logger.info("Disposition phase: %s", counts)

&nbsp;   return facts



async def phase\_output(

&nbsp;   run\_id: str,

&nbsp;   loan\_facts: list\[LoanFact],

&nbsp;   exceptions: list\[LoanException],

&nbsp;   storage: StorageBackend,

&nbsp;   db: AsyncSession,

) -> dict:

&nbsp;   """

&nbsp;   Phase 6: Generate 4 notebook-replacement output CSV files.

&nbsp;   Stores files in outputs/{run\_id}/ via storage backend.

&nbsp;   """

&nbsp;   output\_dir = f"{run\_id}"

&nbsp;   results = {}



&nbsp;   # ── purchase\_tape.csv ──

&nbsp;   purchase\_loans = \[f for f in loan\_facts if f.disposition == "to\_purchase"]

&nbsp;   results\["purchase\_tape"] = await \_write\_loan\_csv(

&nbsp;       storage, output\_dir, "purchase\_tape.csv", purchase\_loans,

&nbsp;   )



&nbsp;   # ── projected\_tape.csv ──

&nbsp;   projected\_loans = \[f for f in loan\_facts if f.disposition == "projected"]

&nbsp;   results\["projected\_tape"] = await \_write\_loan\_csv(

&nbsp;       storage, output\_dir, "projected\_tape.csv", projected\_loans,

&nbsp;   )



&nbsp;   # ── rejection\_report.csv ──

&nbsp;   rejected\_loans = \[f for f in loan\_facts if f.disposition == "rejected"]

&nbsp;   results\["rejection\_report"] = await \_write\_rejection\_csv(

&nbsp;       storage, output\_dir, "rejection\_report.csv", rejected\_loans, exceptions,

&nbsp;   )



&nbsp;   # ── exception\_summary.csv ──

&nbsp;   results\["exception\_summary"] = await \_write\_exception\_summary\_csv(

&nbsp;       storage, output\_dir, "exception\_summary.csv", exceptions,

&nbsp;   )



&nbsp;   logger.info("Output phase: generated %d files for run %s", len(results), run\_id)

&nbsp;   return results



async def phase\_archive(

&nbsp;   run\_id: str,

&nbsp;   folder: str,

&nbsp;   storage: StorageBackend,

) -> None:

&nbsp;   """

&nbsp;   Phase 7: Archive inputs and outputs for the run.

&nbsp;   Copies inputs → archive/{run\_id}/input/

&nbsp;   Copies outputs → archive/{run\_id}/output/

&nbsp;   """

&nbsp;   # IMPLEMENT: Copy files from inputs/ and outputs/{run\_id}/ to archive/{run\_id}/

&nbsp;   logger.info("Archive phase: archived run %s", run\_id)



\# ─── CSV Writing Helpers ─────────────────────────────────────────────────



LOAN\_CSV\_COLUMNS = \[

&nbsp;   "seller\_loan\_number", "loan\_amount", "note\_rate", "ltv\_ratio",

&nbsp;   "dti\_ratio", "credit\_score", "property\_type", "occupancy\_status",

&nbsp;   "loan\_purpose", "purchase\_price", "appraisal\_value",

&nbsp;   "disposition", "pricing\_spread", "final\_price",

]



async def \_write\_loan\_csv(

&nbsp;   storage: StorageBackend,

&nbsp;   output\_dir: str,

&nbsp;   filename: str,

&nbsp;   loan\_facts: list\[LoanFact],

) -> dict:

&nbsp;   """Write a CSV file of loan facts to storage."""

&nbsp;   buffer = io.StringIO()

&nbsp;   writer = csv.DictWriter(buffer, fieldnames=LOAN\_CSV\_COLUMNS, extrasaction="ignore")

&nbsp;   writer.writeheader()



&nbsp;   for fact in loan\_facts:

&nbsp;       row = fact.loan\_data or {}

&nbsp;       row\["disposition"] = fact.disposition

&nbsp;       row\["seller\_loan\_number"] = fact.seller\_loan\_number

&nbsp;       writer.writerow(row)



&nbsp;   csv\_bytes = buffer.getvalue().encode("utf-8")



&nbsp;   # Upload to storage

&nbsp;   from io import BytesIO

&nbsp;   from fastapi import UploadFile

&nbsp;   upload = UploadFile(filename=filename, file=BytesIO(csv\_bytes))

&nbsp;   result = await storage.upload\_file(upload, f"{output\_dir}/{filename}", area="outputs")



&nbsp;   return {"filename": filename, "rows": len(loan\_facts), \*\*result}



async def \_write\_rejection\_csv(

&nbsp;   storage: StorageBackend,

&nbsp;   output\_dir: str,

&nbsp;   filename: str,

&nbsp;   rejected\_facts: list\[LoanFact],

&nbsp;   exceptions: list\[LoanException],

) -> dict:

&nbsp;   """Write rejection report with loan data + exception details."""

&nbsp;   # Build exception lookup by seller\_loan\_number

&nbsp;   exc\_lookup: dict\[str, list\[LoanException]] = {}

&nbsp;   for exc in exceptions:

&nbsp;       exc\_lookup.setdefault(exc.seller\_loan\_number, \[]).append(exc)



&nbsp;   columns = LOAN\_CSV\_COLUMNS + \["exception\_type", "severity", "message", "rejection\_criteria"]

&nbsp;   buffer = io.StringIO()

&nbsp;   writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction="ignore")

&nbsp;   writer.writeheader()



&nbsp;   for fact in rejected\_facts:

&nbsp;       row = fact.loan\_data or {}

&nbsp;       row\["disposition"] = fact.disposition

&nbsp;       row\["seller\_loan\_number"] = fact.seller\_loan\_number



&nbsp;       loan\_exceptions = exc\_lookup.get(fact.seller\_loan\_number, \[])

&nbsp;       if loan\_exceptions:

&nbsp;           for exc in loan\_exceptions:

&nbsp;               exc\_row = {\*\*row}

&nbsp;               exc\_row\["exception\_type"] = exc.exception\_type

&nbsp;               exc\_row\["severity"] = exc.severity

&nbsp;               exc\_row\["message"] = exc.message

&nbsp;               exc\_row\["rejection\_criteria"] = exc.rejection\_criteria

&nbsp;               writer.writerow(exc\_row)

&nbsp;       else:

&nbsp;           writer.writerow(row)



&nbsp;   csv\_bytes = buffer.getvalue().encode("utf-8")

&nbsp;   from io import BytesIO

&nbsp;   from fastapi import UploadFile

&nbsp;   upload = UploadFile(filename=filename, file=BytesIO(csv\_bytes))

&nbsp;   result = await storage.upload\_file(upload, f"{output\_dir}/{filename}", area="outputs")



&nbsp;   return {"filename": filename, "rows": len(rejected\_facts), \*\*result}



async def \_write\_exception\_summary\_csv(

&nbsp;   storage: StorageBackend,

&nbsp;   output\_dir: str,

&nbsp;   filename: str,

&nbsp;   exceptions: list\[LoanException],

) -> dict:

&nbsp;   """Write aggregated exception summary."""

&nbsp;   # Group exceptions

&nbsp;   groups: dict\[str, dict] = {}

&nbsp;   for exc in exceptions:

&nbsp;       key = f"{exc.exception\_type}|{exc.severity}"

&nbsp;       if key not in groups:

&nbsp;           groups\[key] = {

&nbsp;               "exception\_type": exc.exception\_type,

&nbsp;               "exception\_category": exc.exception\_category,

&nbsp;               "severity": exc.severity,

&nbsp;               "rejection\_criteria": exc.rejection\_criteria or "",

&nbsp;               "count": 0,

&nbsp;               "sample\_message": exc.message or "",

&nbsp;           }

&nbsp;       groups\[key]\["count"] += 1



&nbsp;   columns = \["exception\_type", "exception\_category", "severity",

&nbsp;              "count", "rejection\_criteria", "sample\_message"]

&nbsp;   buffer = io.StringIO()

&nbsp;   writer = csv.DictWriter(buffer, fieldnames=columns)

&nbsp;   writer.writeheader()

&nbsp;   for group in sorted(groups.values(), key=lambda g: -g\["count"]):

&nbsp;       writer.writerow(group)



&nbsp;   csv\_bytes = buffer.getvalue().encode("utf-8")

&nbsp;   from io import BytesIO

&nbsp;   from fastapi import UploadFile

&nbsp;   upload = UploadFile(filename=filename, file=BytesIO(csv\_bytes))

&nbsp;   result = await storage.upload\_file(upload, f"{output\_dir}/{filename}", area="outputs")



&nbsp;   return {"filename": filename, "rows": len(groups), \*\*result}

```



---



\## API Routes (backend/api/routes.py) — Complete Implementation



Replace the entire file. All routes use real database queries and pipeline execution.



\### Endpoint Specifications



\#### POST /pipeline/run — Create \& Execute Pipeline Run



```

Auth: get\_current\_user (any authenticated user)

Body: RunCreate (pdate, irr\_target, folder)

Logic:

&nbsp; 1. Call execute\_pipeline() with run config

&nbsp; 2. Pass current\_user.sales\_team\_id if user role is sales\_team

&nbsp; 3. Return RunResponse (status will be "completed" or "failed")

Response: RunResponse (200)

Errors: 500 if pipeline fails (return RunResponse with status="failed")

```



\#### GET /runs — List Pipeline Runs



```

Auth: get\_current\_user

Query params:

&nbsp; skip: int = 0 (min 0)

&nbsp; limit: int = 100 (min 1, max 1000)

&nbsp; status: str | None = None

&nbsp; run\_weekday: int | None = None (0-6, for day-of-week segregation)

Logic:

&nbsp; 1. Build query on PipelineRun

&nbsp; 2. If user role is "sales\_team", filter by user's sales\_team\_id

&nbsp; 3. Apply optional status filter

&nbsp; 4. Apply optional run\_weekday filter

&nbsp; 5. Order by created\_at DESC

&nbsp; 6. Apply skip/limit

Response: List\[RunResponse]

```



\#### GET /runs/{run\_id} — Get Specific Run



```

Auth: get\_current\_user

Path: run\_id (string)

Logic:

&nbsp; 1. Query PipelineRun by run\_id

&nbsp; 2. If user role is "sales\_team", verify run.sales\_team\_id matches user

&nbsp; 3. 404 if not found or access denied

Response: RunResponse

```



\#### GET /runs/{run\_id}/notebook-outputs — List Notebook Output Files



```

Auth: get\_current\_user

Path: run\_id (string)

Logic:

&nbsp; 1. Verify run exists (404 if not)

&nbsp; 2. Verify access (sales\_team scoping)

&nbsp; 3. List files in outputs/{run\_id}/ via storage backend

&nbsp; 4. Return list with filename, size, last\_modified for each

Response: list of file info dicts

```



\#### GET /runs/{run\_id}/notebook-outputs/{output\_key}/download — Download Output



```

Auth: get\_current\_user

Path: run\_id (string), output\_key (string — one of: purchase\_tape, projected\_tape,

&nbsp;     rejection\_report, exception\_summary)

Logic:

&nbsp; 1. Verify run exists and access

&nbsp; 2. Map output\_key to filename (e.g., "purchase\_tape" → "purchase\_tape.csv")

&nbsp; 3. Return file via storage.download\_file()

Response: StreamingResponse (CSV file)

Errors: 404 if run or file not found, 400 if invalid output\_key

```



\#### GET /runs/{run\_id}/archive — List Run Archive



```

Auth: get\_current\_user

Path: run\_id (string)

Logic:

&nbsp; 1. Verify run exists and access

&nbsp; 2. List files in archive/{run\_id}/input/ and archive/{run\_id}/output/

&nbsp; 3. Return structured dict: {"input": \[...files], "output": \[...files]}

Response: dict with input and output file lists

```



\#### GET /runs/{run\_id}/archive/download — Download Archive File



```

Auth: get\_current\_user

Path: run\_id (string)

Query: path (string, required — e.g., "input/loans.csv" or "output/purchase\_tape.csv")

Logic:

&nbsp; 1. Verify run exists and access

&nbsp; 2. Sanitize path to prevent directory traversal

&nbsp; 3. Download from archive/{run\_id}/{path}

Response: StreamingResponse

Errors: 404 if file not found, 400 if path is invalid

```



\#### GET /summary/{run\_id} — Run Summary Metrics



```

Auth: get\_current\_user

Path: run\_id (string)

Logic:

&nbsp; 1. Query PipelineRun by run\_id (verify access)

&nbsp; 2. Query LoanException counts grouped by exception\_type for this run

&nbsp; 3. Query LoanFact counts grouped by disposition for this run

&nbsp; 4. Build eligibility\_checks dict:

&nbsp;    {

&nbsp;      "total\_loans": N,

&nbsp;      "eligible": N,

&nbsp;      "rejected": N,

&nbsp;      "projected": N,

&nbsp;      "exceptions\_by\_type": {"missing\_field": 5, "ltv\_ratio": 3, ...},

&nbsp;      "exceptions\_by\_severity": {"hard": 8, "soft": 4},

&nbsp;    }

Response: SummaryResponse

```



\#### GET /exceptions — Get Loan Exceptions



```

Auth: get\_current\_user

Query params:

&nbsp; run\_id: str | None

&nbsp; exception\_type: str | None

&nbsp; severity: str | None

&nbsp; rejection\_criteria: str | None

&nbsp; skip: int = 0 (min 0)

&nbsp; limit: int = 100 (min 1, max 1000)

Logic:

&nbsp; 1. Build query on LoanException

&nbsp; 2. Apply all optional filters

&nbsp; 3. If user role is "sales\_team", join to PipelineRun and filter by sales\_team\_id

&nbsp; 4. Order by created\_at DESC

&nbsp; 5. Apply skip/limit

Response: List\[ExceptionResponse]

```



\#### GET /exceptions/export — Export Exceptions



```

Auth: get\_current\_user

Query params:

&nbsp; format: str = "csv" (csv | xlsx)

&nbsp; run\_id: str | None

&nbsp; exception\_type: str | None

&nbsp; severity: str | None

&nbsp; rejection\_criteria: str | None

&nbsp; limit: int = 10000 (max 50000)

Logic:

&nbsp; 1. Query exceptions with same filters as GET /exceptions

&nbsp; 2. If format == "csv": generate CSV, return StreamingResponse with

&nbsp;    Content-Disposition: attachment; filename="exceptions\_export.csv"

&nbsp; 3. If format == "xlsx": generate Excel via openpyxl, return StreamingResponse

&nbsp;    Content-Disposition: attachment; filename="exceptions\_export.xlsx"

Response: StreamingResponse (file download)

```



\#### GET /loans — Get Loan Facts



```

Auth: get\_current\_user

Query params:

&nbsp; run\_id: str (required)

&nbsp; disposition: str | None ("to\_purchase" | "projected" | "rejected")

&nbsp; skip: int = 0 (min 0)

&nbsp; limit: int = 100 (min 1, max 1000)

Logic:

&nbsp; 1. Verify run exists and access (sales\_team scoping)

&nbsp; 2. Query LoanFact by run\_id

&nbsp; 3. Apply optional disposition filter

&nbsp; 4. Order by id

&nbsp; 5. Apply skip/limit

&nbsp; 6. Return loan\_data dicts with disposition included

Response: List\[dict] (loan\_data JSON with disposition field added)

```



\#### GET /sales-teams — List Sales Teams



```

Auth: get\_current\_user

Logic:

&nbsp; 1. Query all SalesTeam records

&nbsp; 2. Return list of dicts with id and name

Response: List\[dict]

```



\#### GET /config — App Config



```

Auth: get\_current\_user

Logic:

&nbsp; 1. Return config relevant to the UI

Response: {"storage\_type": str, "s3\_bucket": str | None, "environment": str}

```



---



\## Storage Dependency (backend/api/dependencies.py)



Add the storage backend dependency:



```python

from functools import lru\_cache

from backend.config import get\_settings

from backend.storage.base import StorageBackend

from backend.storage.local import LocalStorage

from backend.storage.s3 import S3Storage

from backend.database import get\_db

from backend.auth.security import get\_current\_user



@lru\_cache

def get\_storage() -> StorageBackend:

&nbsp;   """Return the configured storage backend (local or S3)."""

&nbsp;   settings = get\_settings()

&nbsp;   if settings.STORAGE\_TYPE == "s3":

&nbsp;       return S3Storage(

&nbsp;           bucket\_name=settings.S3\_BUCKET\_NAME,

&nbsp;           region=settings.S3\_REGION,

&nbsp;           aws\_access\_key\_id=settings.AWS\_ACCESS\_KEY\_ID,

&nbsp;           aws\_secret\_access\_key=settings.AWS\_SECRET\_ACCESS\_KEY,

&nbsp;       )

&nbsp;   else:

&nbsp;       return LocalStorage(base\_path=settings.LOCAL\_STORAGE\_PATH)

```



---



\## Test Suite (backend/tests/test\_pipeline\_routes.py)



```python

"""

Comprehensive tests for pipeline and run endpoints.

"""

import pytest

from httpx import AsyncClient

from backend.models import PipelineRun, LoanException, LoanFact, SalesTeam

from datetime import datetime, timezone



def auth\_header(token: str) -> dict:

&nbsp;   return {"Authorization": f"Bearer {token}"}



\# ─── Test Data Fixtures ──────────────────────────────────────────────────



@pytest.fixture

async def sample\_run(test\_db) -> PipelineRun:

&nbsp;   """Create a completed sample pipeline run."""

&nbsp;   run = PipelineRun(

&nbsp;       run\_id="test-run-001",

&nbsp;       status="completed",

&nbsp;       total\_loans=100,

&nbsp;       total\_balance=15\_000\_000.0,

&nbsp;       exceptions\_count=12,

&nbsp;       run\_weekday=3,

&nbsp;       run\_weekday\_name="Thursday",

&nbsp;       pdate="2026-02-20",

&nbsp;       last\_phase="archive",

&nbsp;       output\_dir="outputs/test-run-001",

&nbsp;       started\_at=datetime.now(timezone.utc),

&nbsp;       completed\_at=datetime.now(timezone.utc),

&nbsp;       created\_at=datetime.now(timezone.utc),

&nbsp;   )

&nbsp;   test\_db.add(run)

&nbsp;   await test\_db.commit()

&nbsp;   await test\_db.refresh(run)

&nbsp;   return run



@pytest.fixture

async def sample\_exceptions(test\_db, sample\_run) -> list\[LoanException]:

&nbsp;   """Create sample exceptions for the test run."""

&nbsp;   exceptions = \[

&nbsp;       LoanException(

&nbsp;           run\_id=sample\_run.run\_id,

&nbsp;           seller\_loan\_number=f"LOAN-{i:04d}",

&nbsp;           exception\_type="ltv\_ratio" if i % 2 == 0 else "credit\_score",

&nbsp;           exception\_category="credit",

&nbsp;           severity="hard" if i % 3 == 0 else "soft",

&nbsp;           message=f"Test exception {i}",

&nbsp;           rejection\_criteria="notebook.ltv\_exceeds\_maximum" if i % 2 == 0 else "notebook.credit\_score\_below\_minimum",

&nbsp;           created\_at=datetime.now(timezone.utc),

&nbsp;       )

&nbsp;       for i in range(12)

&nbsp;   ]

&nbsp;   test\_db.add\_all(exceptions)

&nbsp;   await test\_db.commit()

&nbsp;   return exceptions



@pytest.fixture

async def sample\_loan\_facts(test\_db, sample\_run) -> list\[LoanFact]:

&nbsp;   """Create sample loan facts for the test run."""

&nbsp;   facts = \[]

&nbsp;   dispositions = \["to\_purchase"] \* 70 + \["rejected"] \* 20 + \["projected"] \* 10

&nbsp;   for i, disp in enumerate(dispositions):

&nbsp;       fact = LoanFact(

&nbsp;           run\_id=sample\_run.run\_id,

&nbsp;           seller\_loan\_number=f"LOAN-{i:04d}",

&nbsp;           disposition=disp,

&nbsp;           loan\_data={

&nbsp;               "seller\_loan\_number": f"LOAN-{i:04d}",

&nbsp;               "loan\_amount": 150\_000 + (i \* 1000),

&nbsp;               "note\_rate": 6.5 + (i \* 0.01),

&nbsp;               "ltv\_ratio": 80.0,

&nbsp;               "credit\_score": 720,

&nbsp;           },

&nbsp;           created\_at=datetime.now(timezone.utc),

&nbsp;       )

&nbsp;       facts.append(fact)

&nbsp;   test\_db.add\_all(facts)

&nbsp;   await test\_db.commit()

&nbsp;   return facts



@pytest.fixture

async def sales\_team\_run(test\_db) -> tuple\[SalesTeam, PipelineRun]:

&nbsp;   """Create a run associated with a sales team."""

&nbsp;   team = SalesTeam(name="Test Sales Team")

&nbsp;   test\_db.add(team)

&nbsp;   await test\_db.commit()

&nbsp;   await test\_db.refresh(team)



&nbsp;   run = PipelineRun(

&nbsp;       run\_id="team-run-001",

&nbsp;       status="completed",

&nbsp;       sales\_team\_id=team.id,

&nbsp;       total\_loans=50,

&nbsp;       total\_balance=7\_500\_000.0,

&nbsp;       exceptions\_count=3,

&nbsp;       created\_at=datetime.now(timezone.utc),

&nbsp;   )

&nbsp;   test\_db.add(run)

&nbsp;   await test\_db.commit()

&nbsp;   await test\_db.refresh(run)

&nbsp;   return team, run



\# ─── GET /api/runs ────────────────────────────────────────────────────────



class TestListRuns:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_runs(self, async\_client, admin\_token, sample\_run):

&nbsp;       response = await async\_client.get("/api/runs", headers=auth\_header(admin\_token))

&nbsp;       assert response.status\_code == 200

&nbsp;       runs = response.json()

&nbsp;       assert isinstance(runs, list)

&nbsp;       assert len(runs) >= 1

&nbsp;       assert any(r\["run\_id"] == "test-run-001" for r in runs)



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_runs\_unauthenticated(self, async\_client):

&nbsp;       response = await async\_client.get("/api/runs")

&nbsp;       assert response.status\_code == 401



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_runs\_filter\_status(self, async\_client, admin\_token, sample\_run):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/runs", params={"status": "completed"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       assert all(r\["status"] == "completed" for r in response.json())



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_runs\_filter\_weekday(self, async\_client, admin\_token, sample\_run):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/runs", params={"run\_weekday": 3},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       assert all(r\["run\_weekday"] == 3 for r in response.json())



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_runs\_pagination(self, async\_client, admin\_token, sample\_run):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/runs", params={"skip": 0, "limit": 1},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       assert len(response.json()) <= 1



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_runs\_ordered\_by\_created\_desc(self, async\_client, admin\_token, sample\_run):

&nbsp;       response = await async\_client.get("/api/runs", headers=auth\_header(admin\_token))

&nbsp;       runs = response.json()

&nbsp;       if len(runs) > 1:

&nbsp;           dates = \[r\["created\_at"] for r in runs]

&nbsp;           assert dates == sorted(dates, reverse=True)



\# ─── GET /api/runs/{run\_id} ──────────────────────────────────────────────



class TestGetRun:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_get\_run(self, async\_client, admin\_token, sample\_run):

&nbsp;       response = await async\_client.get(

&nbsp;           f"/api/runs/{sample\_run.run\_id}", headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       body = response.json()

&nbsp;       assert body\["run\_id"] == "test-run-001"

&nbsp;       assert body\["status"] == "completed"

&nbsp;       assert body\["total\_loans"] == 100



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_get\_run\_not\_found(self, async\_client, admin\_token):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/runs/nonexistent-run", headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 404



\# ─── GET /api/summary/{run\_id} ───────────────────────────────────────────



class TestRunSummary:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_get\_summary(self, async\_client, admin\_token, sample\_run,

&nbsp;                               sample\_exceptions, sample\_loan\_facts):

&nbsp;       response = await async\_client.get(

&nbsp;           f"/api/summary/{sample\_run.run\_id}", headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       body = response.json()

&nbsp;       assert body\["run\_id"] == "test-run-001"

&nbsp;       assert body\["total\_loans"] == 100

&nbsp;       assert body\["total\_balance"] == 15\_000\_000.0

&nbsp;       assert body\["exceptions\_count"] == 12

&nbsp;       assert isinstance(body\["eligibility\_checks"], dict)



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_get\_summary\_not\_found(self, async\_client, admin\_token):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/summary/nonexistent", headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 404



\# ─── GET /api/exceptions ─────────────────────────────────────────────────



class TestExceptions:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_exceptions(self, async\_client, admin\_token,

&nbsp;                                   sample\_run, sample\_exceptions):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/exceptions", params={"run\_id": sample\_run.run\_id},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       exceptions = response.json()

&nbsp;       assert len(exceptions) == 12



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_filter\_by\_exception\_type(self, async\_client, admin\_token,

&nbsp;                                            sample\_run, sample\_exceptions):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/exceptions",

&nbsp;           params={"run\_id": sample\_run.run\_id, "exception\_type": "ltv\_ratio"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       assert all(e\["exception\_type"] == "ltv\_ratio" for e in response.json())



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_filter\_by\_severity(self, async\_client, admin\_token,

&nbsp;                                      sample\_run, sample\_exceptions):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/exceptions",

&nbsp;           params={"run\_id": sample\_run.run\_id, "severity": "hard"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       assert all(e\["severity"] == "hard" for e in response.json())



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_filter\_by\_rejection\_criteria(self, async\_client, admin\_token,

&nbsp;                                                 sample\_run, sample\_exceptions):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/exceptions",

&nbsp;           params={"rejection\_criteria": "notebook.ltv\_exceeds\_maximum"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       assert all(e\["rejection\_criteria"] == "notebook.ltv\_exceeds\_maximum"

&nbsp;                   for e in response.json())



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_exceptions\_pagination(self, async\_client, admin\_token,

&nbsp;                                         sample\_run, sample\_exceptions):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/exceptions",

&nbsp;           params={"run\_id": sample\_run.run\_id, "skip": 0, "limit": 5},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       assert len(response.json()) == 5



\# ─── GET /api/exceptions/export ───────────────────────────────────────────



class TestExceptionsExport:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_export\_csv(self, async\_client, admin\_token,

&nbsp;                              sample\_run, sample\_exceptions):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/exceptions/export",

&nbsp;           params={"run\_id": sample\_run.run\_id, "format": "csv"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       assert "text/csv" in response.headers.get("content-type", "")



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_export\_xlsx(self, async\_client, admin\_token,

&nbsp;                               sample\_run, sample\_exceptions):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/exceptions/export",

&nbsp;           params={"run\_id": sample\_run.run\_id, "format": "xlsx"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       content\_type = response.headers.get("content-type", "")

&nbsp;       assert "spreadsheet" in content\_type or "octet-stream" in content\_type



\# ─── GET /api/loans ───────────────────────────────────────────────────────



class TestLoans:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_get\_loans(self, async\_client, admin\_token,

&nbsp;                             sample\_run, sample\_loan\_facts):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/loans", params={"run\_id": sample\_run.run\_id},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       loans = response.json()

&nbsp;       assert len(loans) == 100



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_filter\_by\_disposition(self, async\_client, admin\_token,

&nbsp;                                         sample\_run, sample\_loan\_facts):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/loans",

&nbsp;           params={"run\_id": sample\_run.run\_id, "disposition": "to\_purchase"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       assert len(response.json()) == 70



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_loans\_requires\_run\_id(self, async\_client, admin\_token):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/loans", headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 422



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_loans\_pagination(self, async\_client, admin\_token,

&nbsp;                                    sample\_run, sample\_loan\_facts):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/loans",

&nbsp;           params={"run\_id": sample\_run.run\_id, "skip": 0, "limit": 10},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       assert len(response.json()) == 10



\# ─── GET /api/sales-teams ────────────────────────────────────────────────



class TestSalesTeams:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_sales\_teams(self, async\_client, admin\_token, test\_db):

&nbsp;       team = SalesTeam(name="Validation Team")

&nbsp;       test\_db.add(team)

&nbsp;       await test\_db.commit()



&nbsp;       response = await async\_client.get(

&nbsp;           "/api/sales-teams", headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       teams = response.json()

&nbsp;       assert isinstance(teams, list)

&nbsp;       assert any(t\["name"] == "Validation Team" for t in teams)



\# ─── GET /api/config ──────────────────────────────────────────────────────



class TestConfig:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_get\_config(self, async\_client, admin\_token):

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/config", headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       body = response.json()

&nbsp;       assert "storage\_type" in body

&nbsp;       assert "environment" in body



\# ─── Sales Team Scoping ──────────────────────────────────────────────────



class TestSalesTeamScoping:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_sales\_team\_user\_sees\_only\_own\_runs(

&nbsp;       self, async\_client, test\_db, sales\_team\_run,

&nbsp;   ):

&nbsp;       """Sales team user can only see runs for their team."""

&nbsp;       from backend.models import User

&nbsp;       from backend.auth.security import hash\_password, create\_access\_token



&nbsp;       team, team\_run = sales\_team\_run



&nbsp;       # Create sales team user

&nbsp;       st\_user = User(

&nbsp;           email="salesuser@test.com",

&nbsp;           username="salesuser",

&nbsp;           hashed\_password=hash\_password("salespass"),

&nbsp;           full\_name="Sales User",

&nbsp;           role="sales\_team",

&nbsp;           sales\_team\_id=team.id,

&nbsp;           is\_active=True,

&nbsp;       )

&nbsp;       test\_db.add(st\_user)

&nbsp;       await test\_db.commit()

&nbsp;       await test\_db.refresh(st\_user)



&nbsp;       token = create\_access\_token(data={"sub": st\_user.username})



&nbsp;       response = await async\_client.get(

&nbsp;           "/api/runs", headers=auth\_header(token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       runs = response.json()

&nbsp;       # Should only see the team's run, not other runs

&nbsp;       for r in runs:

&nbsp;           assert r\["sales\_team\_id"] == team.id

```



---



\## Validation Criteria for Phase 2



After implementation, ALL must pass:



```

&nbsp;1. uvicorn starts without errors

&nbsp;2. POST /api/pipeline/run with auth creates a run record

&nbsp;3. GET /api/runs returns list of runs, ordered by created\_at DESC

&nbsp;4. GET /api/runs?status=completed filters correctly

&nbsp;5. GET /api/runs?run\_weekday=3 filters correctly

&nbsp;6. GET /api/runs/{run\_id} returns specific run

&nbsp;7. GET /api/runs/{run\_id} with bad ID returns 404

&nbsp;8. GET /api/summary/{run\_id} returns summary with eligibility\_checks dict

&nbsp;9. GET /api/exceptions returns filtered exception list

10\. GET /api/exceptions?severity=hard filters correctly

11\. GET /api/exceptions/export?format=csv returns CSV download

12\. GET /api/exceptions/export?format=xlsx returns Excel download

13\. GET /api/loans?run\_id=X returns loan facts

14\. GET /api/loans?disposition=to\_purchase filters correctly

15\. GET /api/sales-teams returns team list

16\. GET /api/config returns storage\_type and environment

17\. Sales team users only see their own team's runs

18\. Unauthenticated requests return 401

19\. pytest backend/tests/test\_pipeline\_routes.py — all tests pass

20\. ruff check backend/ — no lint errors

```



Run validation:





