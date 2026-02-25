Task: Implement the Authentication Layer for the Loan Engine API



You are extending the Loan Engine scaffold (Phase 0) with a fully functional

authentication system. Replace all auth stub routes with real implementations.

After this phase, users can log in, receive JWT tokens, and all protected

endpoints enforce authentication and role-based access control.





Context: What Already Exists (from Phase 0)



These files exist and contain working code. Do NOT regenerate them from scratch.

Modify only the files listed in the "Files to Modify" section.

Import from these existing modules freely.





backend/config.py          → Settings with SECRET\_KEY, JWT\_ALGORITHM, ACCESS\_TOKEN\_EXPIRE\_MINUTES

backend/database.py        → async engine, async\_session\_factory, get\_db dependency, Base

backend/models.py          → User, SalesTeam, PipelineRun, LoanException, LoanFact ORM models



backend/auth/schemas.py    → UserRole enum, UserCreate, UserUpdate, UserResponse, Token

backend/schemas/api.py     → RunCreate, RunResponse, SummaryResponse, ExceptionResponse



backend/auth/security.py   → hash\_password, verify\_password, create\_access\_token,

&nbsp;                             get\_current\_user dependency, admin\_required dependency,

&nbsp;                             OAuth2PasswordBearer(tokenUrl="/api/auth/login")



backend/api/main.py        → FastAPI app with CORS, lifespan, router includes,

&nbsp;                             health endpoints, static file mounting



backend/api/dependencies.py → get\_db (re-exported from database.py)



backend/tests/conftest.py  → test\_engine (SQLite in-memory), test\_db fixture,

&nbsp;                             async\_client fixture, admin\_user, analyst\_user,

&nbsp;                             admin\_token, analyst\_token fixtures



Existing User Model (backend/models.py)



python

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

&nbsp;   sales\_team: Mapped\[Optional\["SalesTeam"]] = relationship(back\_populates="users", lazy="selectin")



Existing Schemas (backend/auth/schemas.py)



python

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



Existing Security Module (backend/auth/security.py)



python

pwd\_context = CryptContext(schemes=\["bcrypt"], deprecated="auto")

oauth2\_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")



def hash\_password(password: str) -> str

def verify\_password(plain\_password: str, hashed\_password: str) -> bool

def create\_access\_token(data: dict, expires\_delta: Optional\[timedelta] = None) -> str

async def get\_current\_user(token: str = Depends(oauth2\_scheme), db: AsyncSession = Depends(get\_db)) -> User

async def admin\_required(current\_user = Depends(get\_current\_user)) -> User





Files to Modify



Replace the stub implementations in these files with complete, production-ready code:

1\. backend/auth/routes.py — FULL REWRITE



Replace the entire file. Implement all 5 auth endpoints with real database operations.

2\. backend/auth/validators.py — FULL REWRITE



Replace with complete role-based validation utilities.

3\. backend/tests/test\_auth\_routes.py — NEW FILE



Create comprehensive auth tests.

4\. backend/auth/security.py — VERIFY AND EXTEND IF NEEDED



The Phase 0 version should be mostly complete. Review and add any missing

functionality (e.g., token refresh, password strength validation).





Endpoint Specifications



POST /api/auth/login



OpenAPI operationId: login\_api\_auth\_login\_post



Request: application/x-www-form-urlencoded (OAuth2 password flow)





Fields:

• username: string (required)

• password: string (required)

• grant\_type: "password" | null (optional)

• scope: string (optional, default "")

• client\_id: string | null (optional)

• client\_secret: string | null (optional)



Logic:

1\. Query User by username (case-insensitive)

2\. If user not found → 401 "Incorrect username or password"

3\. If user.is\_active is False → 401 "Account is disabled"

4\. If verify\_password fails → 401 "Incorrect username or password"

5\. Create JWT with payload: {"sub": user.username, "role": user.role, "user\_id": user.id}

6\. Return Token:

json

{

&nbsp; "access\_token": "<jwt>",

&nbsp; "token\_type": "bearer",

&nbsp; "user": {

&nbsp;   "id": 1,

&nbsp;   "username": "admin",

&nbsp;   "email": "admin@loanengine.local",

&nbsp;   "full\_name": "System Administrator",

&nbsp;   "role": "admin",

&nbsp;   "sales\_team\_id": null,

&nbsp;   "is\_active": true

&nbsp; }

}



Security notes:

• Use OAuth2PasswordRequestForm from fastapi.security

• Do NOT reveal whether username or password was wrong (same error for both)

• Log failed login attempts (use Python logging, not print)

• Username lookup must be case-insensitive: func.lower(User.username) == username.lower()





GET /api/auth/me



OpenAPI operationId: get\_current\_user\_info\_api\_auth\_me\_get



Auth: Required (OAuth2PasswordBearer)



Logic:

1\. Extract user from JWT via get\_current\_user dependency

2\. Return UserResponse for the authenticated user



Response: UserResponse





POST /api/auth/register



OpenAPI operationId: register\_api\_auth\_register\_post



Auth: Required (admin\_required)



Request body: UserCreate (JSON)



Logic:

1\. Verify requesting user is admin (via admin\_required dependency)

2\. Check email uniqueness → 409 "Email already registered"

3\. Check username uniqueness → 409 "Username already taken"

4\. If sales\_team\_id provided, verify SalesTeam exists → 404 "Sales team not found"

5\. Hash password

6\. Create User record

7\. Return UserResponse (201 status)



Validation rules:

• Username: 3-50 characters, alphanumeric + underscore only

• Password: minimum 8 characters

• Email: valid email format (handled by Pydantic EmailStr)



Error responses:

• 409: Duplicate email or username

• 404: Invalid sales\_team\_id

• 422: Pydantic validation error (automatic)





PUT /api/auth/users/{user\_id}



OpenAPI operationId: update\_user\_api\_auth\_users\_\_user\_id\_\_put



Auth: Required (admin\_required)



Path params: user\_id: int



Request body: UserUpdate (JSON)



Logic:

1\. Verify requesting user is admin

2\. Look up target user by id → 404 "User not found"

3\. If email changed, check uniqueness → 409 "Email already registered"

4\. If username changed, check uniqueness → 409 "Username already taken"

5\. If sales\_team\_id changed and not null, verify SalesTeam exists → 404 "Sales team not found"

6\. If password provided, hash it before storing

7\. Apply only non-None fields from UserUpdate (partial update)

8\. Save and return updated UserResponse



Prevent self-demotion:

• Admin cannot change their own role from admin to a lower role

• Admin cannot set their own is\_active to False





GET /api/auth/users



OpenAPI operationId: list\_users\_api\_auth\_users\_get



Auth: Required (admin\_required)



Query params:



&nbsp; skip: int = 0

&nbsp; limit: int = 100

&nbsp; role: UserRole | None = None         # Filter by role

&nbsp; sales\_team\_id: int | None = None     # Filter by sales team



Logic:

1\. Verify requesting user is admin

2\. Build query with optional filters

3\. Apply skip/limit pagination

4\. Return List\[UserResponse]



Query must be ordered by User.id for deterministic pagination.





backend/auth/routes.py — Complete Implementation



python

"""

Authentication routes for the Loan Engine API.

Handles login, registration, user management, and current user info.

"""

import logging

import re

from fastapi import APIRouter, Depends, HTTPException, status

from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy import select, func

from sqlalchemy.ext.asyncio import AsyncSession



from backend.database import get\_db

from backend.models import User, SalesTeam

from backend.auth.schemas import UserCreate, UserUpdate, UserResponse, UserRole, Token

from backend.auth.security import (

&nbsp;   hash\_password,

&nbsp;   verify\_password,

&nbsp;   create\_access\_token,

&nbsp;   get\_current\_user,

&nbsp;   admin\_required,

)



logger = logging.getLogger(\_\_name\_\_)

router = APIRouter()



─── Validation helpers ─────────────────────────────────────────────────



USERNAME\_PATTERN = re.compile(r"^\[a-zA-Z0-9\_]{3,50}$")

MIN\_PASSWORD\_LENGTH = 8



def validate\_username(username: str) -> None:

&nbsp;   """Validate username format: 3-50 chars, alphanumeric + underscore."""

&nbsp;   if not USERNAME\_PATTERN.match(username):

&nbsp;       raise HTTPException(

&nbsp;           status\_code=status.HTTP\_422\_UNPROCESSABLE\_ENTITY,

&nbsp;           detail="Username must be 3-50 characters, alphanumeric and underscores only.",

&nbsp;       )



def validate\_password(password: str) -> None:

&nbsp;   """Validate password meets minimum strength requirements."""

&nbsp;   if len(password) < MIN\_PASSWORD\_LENGTH:

&nbsp;       raise HTTPException(

&nbsp;           status\_code=status.HTTP\_422\_UNPROCESSABLE\_ENTITY,

&nbsp;           detail=f"Password must be at least {MIN\_PASSWORD\_LENGTH} characters.",

&nbsp;       )



async def check\_email\_unique(db: AsyncSession, email: str, exclude\_user\_id: int | None = None) -> None:

&nbsp;   """Raise 409 if email is already registered by another user."""

&nbsp;   query = select(User).where(func.lower(User.email) == email.lower())

&nbsp;   if exclude\_user\_id is not None:

&nbsp;       query = query.where(User.id != exclude\_user\_id)

&nbsp;   result = await db.execute(query)

&nbsp;   if result.scalar\_one\_or\_none():

&nbsp;       raise HTTPException(

&nbsp;           status\_code=status.HTTP\_409\_CONFLICT,

&nbsp;           detail="Email already registered.",

&nbsp;       )



async def check\_username\_unique(db: AsyncSession, username: str, exclude\_user\_id: int | None = None) -> None:

&nbsp;   """Raise 409 if username is already taken by another user."""

&nbsp;   query = select(User).where(func.lower(User.username) == username.lower())

&nbsp;   if exclude\_user\_id is not None:

&nbsp;       query = query.where(User.id != exclude\_user\_id)

&nbsp;   result = await db.execute(query)

&nbsp;   if result.scalar\_one\_or\_none():

&nbsp;       raise HTTPException(

&nbsp;           status\_code=status.HTTP\_409\_CONFLICT,

&nbsp;           detail="Username already taken.",

&nbsp;       )



async def verify\_sales\_team\_exists(db: AsyncSession, sales\_team\_id: int) -> None:

&nbsp;   """Raise 404 if sales team does not exist."""

&nbsp;   result = await db.execute(select(SalesTeam).where(SalesTeam.id == sales\_team\_id))

&nbsp;   if not result.scalar\_one\_or\_none():

&nbsp;       raise HTTPException(

&nbsp;           status\_code=status.HTTP\_404\_NOT\_FOUND,

&nbsp;           detail="Sales team not found.",

&nbsp;       )



def user\_to\_dict(user: User) -> dict:

&nbsp;   """Convert User model to dict for Token response."""

&nbsp;   return {

&nbsp;       "id": user.id,

&nbsp;       "username": user.username,

&nbsp;       "email": user.email,

&nbsp;       "full\_name": user.full\_name,

&nbsp;       "role": user.role,

&nbsp;       "sales\_team\_id": user.sales\_team\_id,

&nbsp;       "is\_active": user.is\_active,

&nbsp;   }



─── Routes ─────────────────────────────────────────────────────────────



@router.post("/login", response\_model=Token)

async def login(

&nbsp;   form\_data: OAuth2PasswordRequestForm = Depends(),

&nbsp;   db: AsyncSession = Depends(get\_db),

):

&nbsp;   """Authenticate user and return access token."""



&nbsp;   # Case-insensitive username lookup

&nbsp;   result = await db.execute(

&nbsp;       select(User).where(func.lower(User.username) == form\_data.username.lower())

&nbsp;   )

&nbsp;   user = result.scalar\_one\_or\_none()



&nbsp;   # Uniform error for both bad username and bad password

&nbsp;   credentials\_error = HTTPException(

&nbsp;       status\_code=status.HTTP\_401\_UNAUTHORIZED,

&nbsp;       detail="Incorrect username or password",

&nbsp;       headers={"WWW-Authenticate": "Bearer"},

&nbsp;   )



&nbsp;   if not user:

&nbsp;       logger.warning("Login failed: unknown username '%s'", form\_data.username)

&nbsp;       raise credentials\_error



&nbsp;   if not user.is\_active:

&nbsp;       logger.warning("Login failed: disabled account '%s'", form\_data.username)

&nbsp;       raise HTTPException(

&nbsp;           status\_code=status.HTTP\_401\_UNAUTHORIZED,

&nbsp;           detail="Account is disabled",

&nbsp;           headers={"WWW-Authenticate": "Bearer"},

&nbsp;       )



&nbsp;   if not verify\_password(form\_data.password, user.hashed\_password):

&nbsp;       logger.warning("Login failed: bad password for '%s'", form\_data.username)

&nbsp;       raise credentials\_error



&nbsp;   access\_token = create\_access\_token(

&nbsp;       data={"sub": user.username, "role": user.role, "user\_id": user.id}

&nbsp;   )



&nbsp;   logger.info("Login successful: '%s' (role=%s)", user.username, user.role)



&nbsp;   return Token(

&nbsp;       access\_token=access\_token,

&nbsp;       token\_type="bearer",

&nbsp;       user=user\_to\_dict(user),

&nbsp;   )



@router.get("/me", response\_model=UserResponse)

async def get\_current\_user\_info(

&nbsp;   current\_user: User = Depends(get\_current\_user),

):

&nbsp;   """Get current user information."""

&nbsp;   return current\_user



@router.post("/register", response\_model=UserResponse, status\_code=status.HTTP\_201\_CREATED)

async def register(

&nbsp;   user\_data: UserCreate,

&nbsp;   db: AsyncSession = Depends(get\_db),

&nbsp;   current\_user: User = Depends(admin\_required),

):

&nbsp;   """Register a new user (admin only)."""



&nbsp;   # Validate inputs

&nbsp;   validate\_username(user\_data.username)

&nbsp;   validate\_password(user\_data.password)



&nbsp;   # Check uniqueness

&nbsp;   await check\_email\_unique(db, user\_data.email)

&nbsp;   await check\_username\_unique(db, user\_data.username)



&nbsp;   # Verify sales team if provided

&nbsp;   if user\_data.sales\_team\_id is not None:

&nbsp;       await verify\_sales\_team\_exists(db, user\_data.sales\_team\_id)



&nbsp;   # Create user

&nbsp;   new\_user = User(

&nbsp;       email=user\_data.email,

&nbsp;       username=user\_data.username,

&nbsp;       hashed\_password=hash\_password(user\_data.password),

&nbsp;       full\_name=user\_data.full\_name,

&nbsp;       role=user\_data.role.value,

&nbsp;       sales\_team\_id=user\_data.sales\_team\_id,

&nbsp;       is\_active=True,

&nbsp;   )

&nbsp;   db.add(new\_user)

&nbsp;   await db.commit()

&nbsp;   await db.refresh(new\_user)



&nbsp;   logger.info(

&nbsp;       "User registered: '%s' (role=%s) by admin '%s'",

&nbsp;       new\_user.username, new\_user.role, current\_user.username,

&nbsp;   )



&nbsp;   return new\_user



@router.put("/users/{user\_id}", response\_model=UserResponse)

async def update\_user(

&nbsp;   user\_id: int,

&nbsp;   user\_data: UserUpdate,

&nbsp;   db: AsyncSession = Depends(get\_db),

&nbsp;   current\_user: User = Depends(admin\_required),

):

&nbsp;   """Update a user (admin only)."""



&nbsp;   # Find target user

&nbsp;   result = await db.execute(select(User).where(User.id == user\_id))

&nbsp;   target\_user = result.scalar\_one\_or\_none()



&nbsp;   if not target\_user:

&nbsp;       raise HTTPException(

&nbsp;           status\_code=status.HTTP\_404\_NOT\_FOUND,

&nbsp;           detail="User not found.",

&nbsp;       )



&nbsp;   # Prevent self-demotion

&nbsp;   if target\_user.id == current\_user.id:

&nbsp;       if user\_data.role is not None and user\_data.role != UserRole.admin:

&nbsp;           raise HTTPException(

&nbsp;               status\_code=status.HTTP\_400\_BAD\_REQUEST,

&nbsp;               detail="Cannot demote your own admin role.",

&nbsp;           )

&nbsp;       if user\_data.is\_active is not None and user\_data.is\_active is False:

&nbsp;           raise HTTPException(

&nbsp;               status\_code=status.HTTP\_400\_BAD\_REQUEST,

&nbsp;               detail="Cannot deactivate your own account.",

&nbsp;           )



&nbsp;   # Validate and apply updates (only non-None fields)

&nbsp;   if user\_data.email is not None:

&nbsp;       await check\_email\_unique(db, user\_data.email, exclude\_user\_id=user\_id)

&nbsp;       target\_user.email = user\_data.email



&nbsp;   if user\_data.username is not None:

&nbsp;       validate\_username(user\_data.username)

&nbsp;       await check\_username\_unique(db, user\_data.username, exclude\_user\_id=user\_id)

&nbsp;       target\_user.username = user\_data.username



&nbsp;   if user\_data.full\_name is not None:

&nbsp;       target\_user.full\_name = user\_data.full\_name



&nbsp;   if user\_data.role is not None:

&nbsp;       target\_user.role = user\_data.role.value



&nbsp;   if user\_data.sales\_team\_id is not None:

&nbsp;       await verify\_sales\_team\_exists(db, user\_data.sales\_team\_id)

&nbsp;       target\_user.sales\_team\_id = user\_data.sales\_team\_id



&nbsp;   if user\_data.is\_active is not None:

&nbsp;       target\_user.is\_active = user\_data.is\_active



&nbsp;   if user\_data.password is not None:

&nbsp;       validate\_password(user\_data.password)

&nbsp;       target\_user.hashed\_password = hash\_password(user\_data.password)



&nbsp;   await db.commit()

&nbsp;   await db.refresh(target\_user)



&nbsp;   logger.info(

&nbsp;       "User updated: '%s' (id=%d) by admin '%s'",

&nbsp;       target\_user.username, target\_user.id, current\_user.username,

&nbsp;   )



&nbsp;   return target\_user



@router.get("/users", response\_model=list\[UserResponse])

async def list\_users(

&nbsp;   skip: int = 0,

&nbsp;   limit: int = 100,

&nbsp;   role: UserRole | None = None,

&nbsp;   sales\_team\_id: int | None = None,

&nbsp;   db: AsyncSession = Depends(get\_db),

&nbsp;   current\_user: User = Depends(admin\_required),

):

&nbsp;   """List all users (admin only)."""



&nbsp;   query = select(User).order\_by(User.id)



&nbsp;   if role is not None:

&nbsp;       query = query.where(User.role == role.value)



&nbsp;   if sales\_team\_id is not None:

&nbsp;       query = query.where(User.sales\_team\_id == sales\_team\_id)



&nbsp;   query = query.offset(skip).limit(limit)



&nbsp;   result = await db.execute(query)

&nbsp;   users = result.scalars().all()



&nbsp;   return users





backend/auth/validators.py — Complete Implementation



python

"""

Role-based access control validators and utilities.

Provides reusable dependencies for route-level authorization.

"""

from functools import wraps

from fastapi import Depends, HTTPException, status

from backend.models import User

from backend.auth.security import get\_current\_user

from backend.auth.schemas import UserRole



async def admin\_or\_self(

&nbsp;   user\_id: int,

&nbsp;   current\_user: User = Depends(get\_current\_user),

) -> User:

&nbsp;   """Allow access if current user is admin OR is accessing their own resource."""

&nbsp;   if current\_user.role != UserRole.admin.value and current\_user.id != user\_id:

&nbsp;       raise HTTPException(

&nbsp;           status\_code=status.HTTP\_403\_FORBIDDEN,

&nbsp;           detail="Access denied. Admin role or resource ownership required.",

&nbsp;       )

&nbsp;   return current\_user



async def active\_user\_required(

&nbsp;   current\_user: User = Depends(get\_current\_user),

) -> User:

&nbsp;   """Verify the authenticated user account is still active."""

&nbsp;   if not current\_user.is\_active:

&nbsp;       raise HTTPException(

&nbsp;           status\_code=status.HTTP\_403\_FORBIDDEN,

&nbsp;           detail="Account is disabled. Contact an administrator.",

&nbsp;       )

&nbsp;   return current\_user



def require\_roles(\*allowed\_roles: UserRole):

&nbsp;   """

&nbsp;   Factory that creates a dependency requiring specific roles.



&nbsp;   Usage:

&nbsp;       @router.get("/admin-stuff", dependencies=\[Depends(require\_roles(UserRole.admin))])

&nbsp;       async def admin\_only\_route():

&nbsp;           ...



&nbsp;       @router.get("/team-view", dependencies=\[Depends(require\_roles(UserRole.admin, UserRole.sales\_team))])

&nbsp;       async def admin\_or\_sales():

&nbsp;           ...

&nbsp;   """

&nbsp;   allowed\_values = {r.value for r in allowed\_roles}



&nbsp;   async def role\_checker(current\_user: User = Depends(get\_current\_user)) -> User:

&nbsp;       if current\_user.role not in allowed\_values:

&nbsp;           raise HTTPException(

&nbsp;               status\_code=status.HTTP\_403\_FORBIDDEN,

&nbsp;               detail=f"Access denied. Required role(s): {', '.join(allowed\_values)}.",

&nbsp;           )

&nbsp;       return current\_user



&nbsp;   return role\_checker



async def sales\_team\_scoped(

&nbsp;   current\_user: User = Depends(get\_current\_user),

) -> User:

&nbsp;   """

&nbsp;   Dependency for sales\_team role users.

&nbsp;   Ensures non-admin users can only see data for their own sales team.

&nbsp;   Admins and analysts bypass this restriction.



&nbsp;   Usage in routes:

&nbsp;       @router.get("/runs")

&nbsp;       async def list\_runs(current\_user: User = Depends(sales\_team\_scoped)):

&nbsp;           if current\_user.role == "sales\_team":

&nbsp;               # Filter by current\_user.sales\_team\_id

&nbsp;               ...

&nbsp;           else:

&nbsp;               # Return all

&nbsp;               ...

&nbsp;   """

&nbsp;   if current\_user.role == UserRole.sales\_team.value and current\_user.sales\_team\_id is None:

&nbsp;       raise HTTPException(

&nbsp;           status\_code=status.HTTP\_403\_FORBIDDEN,

&nbsp;           detail="Sales team user has no team assignment. Contact an administrator.",

&nbsp;       )

&nbsp;   return current\_user





backend/tests/test\_auth\_routes.py — Complete Test Suite



python

"""

Comprehensive tests for the authentication endpoints.

Tests cover: login, registration, user management, access control, edge cases.

"""

import pytest

from httpx import AsyncClient



from backend.auth.security import hash\_password, create\_access\_token

from backend.models import User, SalesTeam



─── Helpers ─────────────────────────────────────────────────────────────



def auth\_header(token: str) -> dict:

&nbsp;   return {"Authorization": f"Bearer {token}"}



─── POST /api/auth/login ────────────────────────────────────────────────



class TestLogin:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_login\_success(self, async\_client: AsyncClient, admin\_user):

&nbsp;       """Valid credentials return a JWT token and user info."""

&nbsp;       response = await async\_client.post(

&nbsp;           "/api/auth/login",

&nbsp;           data={"username": "admin", "password": "adminpass"},

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       body = response.json()

&nbsp;       assert "access\_token" in body

&nbsp;       assert body\["token\_type"] == "bearer"

&nbsp;       assert body\["user"]\["username"] == "admin"

&nbsp;       assert body\["user"]\["role"] == "admin"

&nbsp;       assert "hashed\_password" not in str(body)



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_login\_wrong\_password(self, async\_client: AsyncClient, admin\_user):

&nbsp;       """Wrong password returns 401 without revealing which field was wrong."""

&nbsp;       response = await async\_client.post(

&nbsp;           "/api/auth/login",

&nbsp;           data={"username": "admin", "password": "wrongpassword"},

&nbsp;       )

&nbsp;       assert response.status\_code == 401

&nbsp;       assert "Incorrect username or password" in response.json()\["detail"]



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_login\_unknown\_user(self, async\_client: AsyncClient):

&nbsp;       """Non-existent username returns 401."""

&nbsp;       response = await async\_client.post(

&nbsp;           "/api/auth/login",

&nbsp;           data={"username": "nonexistent", "password": "anypassword"},

&nbsp;       )

&nbsp;       assert response.status\_code == 401



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_login\_case\_insensitive\_username(self, async\_client: AsyncClient, admin\_user):

&nbsp;       """Username lookup is case-insensitive."""

&nbsp;       response = await async\_client.post(

&nbsp;           "/api/auth/login",

&nbsp;           data={"username": "ADMIN", "password": "adminpass"},

&nbsp;       )

&nbsp;       assert response.status\_code == 200



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_login\_disabled\_account(self, async\_client: AsyncClient, test\_db):

&nbsp;       """Disabled account returns 401."""

&nbsp;       disabled\_user = User(

&nbsp;           email="disabled@test.com",

&nbsp;           username="disabled",

&nbsp;           hashed\_password=hash\_password("password123"),

&nbsp;           full\_name="Disabled User",

&nbsp;           role="analyst",

&nbsp;           is\_active=False,

&nbsp;       )

&nbsp;       test\_db.add(disabled\_user)

&nbsp;       await test\_db.commit()



&nbsp;       response = await async\_client.post(

&nbsp;           "/api/auth/login",

&nbsp;           data={"username": "disabled", "password": "password123"},

&nbsp;       )

&nbsp;       assert response.status\_code == 401

&nbsp;       assert "disabled" in response.json()\["detail"].lower()



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_login\_missing\_fields(self, async\_client: AsyncClient):

&nbsp;       """Missing required fields return 422."""

&nbsp;       response = await async\_client.post(

&nbsp;           "/api/auth/login",

&nbsp;           data={"username": "admin"},

&nbsp;       )

&nbsp;       assert response.status\_code == 422



─── GET /api/auth/me ────────────────────────────────────────────────────



class TestGetMe:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_me\_authenticated(self, async\_client: AsyncClient, admin\_user, admin\_token):

&nbsp;       """Authenticated user can retrieve their own info."""

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/auth/me",

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       body = response.json()

&nbsp;       assert body\["username"] == "admin"

&nbsp;       assert body\["role"] == "admin"

&nbsp;       assert body\["is\_active"] is True

&nbsp;       assert "hashed\_password" not in body



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_me\_unauthenticated(self, async\_client: AsyncClient):

&nbsp;       """Unauthenticated request returns 401."""

&nbsp;       response = await async\_client.get("/api/auth/me")

&nbsp;       assert response.status\_code == 401



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_me\_invalid\_token(self, async\_client: AsyncClient):

&nbsp;       """Invalid token returns 401."""

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/auth/me",

&nbsp;           headers=auth\_header("invalid-token-value"),

&nbsp;       )

&nbsp;       assert response.status\_code == 401



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_me\_expired\_token(self, async\_client: AsyncClient, admin\_user):

&nbsp;       """Expired token returns 401."""

&nbsp;       from datetime import timedelta

&nbsp;       expired\_token = create\_access\_token(

&nbsp;           data={"sub": "admin"},

&nbsp;           expires\_delta=timedelta(seconds=-1),

&nbsp;       )

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/auth/me",

&nbsp;           headers=auth\_header(expired\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 401



─── POST /api/auth/register ─────────────────────────────────────────────



class TestRegister:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_register\_by\_admin(self, async\_client: AsyncClient, admin\_user, admin\_token):

&nbsp;       """Admin can register a new user."""

&nbsp;       response = await async\_client.post(

&nbsp;           "/api/auth/register",

&nbsp;           json={

&nbsp;               "email": "newuser@test.com",

&nbsp;               "username": "newuser",

&nbsp;               "password": "securepassword123",

&nbsp;               "full\_name": "New User",

&nbsp;               "role": "analyst",

&nbsp;           },

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 201

&nbsp;       body = response.json()

&nbsp;       assert body\["username"] == "newuser"

&nbsp;       assert body\["email"] == "newuser@test.com"

&nbsp;       assert body\["role"] == "analyst"

&nbsp;       assert body\["is\_active"] is True

&nbsp;       assert "password" not in body

&nbsp;       assert "hashed\_password" not in body



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_register\_by\_analyst\_forbidden(self, async\_client: AsyncClient, analyst\_user, analyst\_token):

&nbsp;       """Non-admin cannot register users."""

&nbsp;       response = await async\_client.post(

&nbsp;           "/api/auth/register",

&nbsp;           json={

&nbsp;               "email": "another@test.com",

&nbsp;               "username": "another",

&nbsp;               "password": "securepassword123",

&nbsp;               "full\_name": "Another User",

&nbsp;           },

&nbsp;           headers=auth\_header(analyst\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 403



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_register\_unauthenticated(self, async\_client: AsyncClient):

&nbsp;       """Unauthenticated request cannot register users."""

&nbsp;       response = await async\_client.post(

&nbsp;           "/api/auth/register",

&nbsp;           json={

&nbsp;               "email": "anon@test.com",

&nbsp;               "username": "anon",

&nbsp;               "password": "securepassword123",

&nbsp;               "full\_name": "Anonymous",

&nbsp;           },

&nbsp;       )

&nbsp;       assert response.status\_code == 401



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_register\_duplicate\_email(self, async\_client: AsyncClient, admin\_user, admin\_token):

&nbsp;       """Duplicate email returns 409."""

&nbsp;       response = await async\_client.post(

&nbsp;           "/api/auth/register",

&nbsp;           json={

&nbsp;               "email": "admin@test.com",  # already used by admin\_user fixture

&nbsp;               "username": "uniqueuser",

&nbsp;               "password": "securepassword123",

&nbsp;               "full\_name": "Duplicate Email",

&nbsp;           },

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 409

&nbsp;       assert "email" in response.json()\["detail"].lower()



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_register\_duplicate\_username(self, async\_client: AsyncClient, admin\_user, admin\_token):

&nbsp;       """Duplicate username returns 409."""

&nbsp;       response = await async\_client.post(

&nbsp;           "/api/auth/register",

&nbsp;           json={

&nbsp;               "email": "unique@test.com",

&nbsp;               "username": "admin",  # already used by admin\_user fixture

&nbsp;               "password": "securepassword123",

&nbsp;               "full\_name": "Duplicate Username",

&nbsp;           },

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 409

&nbsp;       assert "username" in response.json()\["detail"].lower()



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_register\_weak\_password(self, async\_client: AsyncClient, admin\_user, admin\_token):

&nbsp;       """Password shorter than 8 chars returns 422."""

&nbsp;       response = await async\_client.post(

&nbsp;           "/api/auth/register",

&nbsp;           json={

&nbsp;               "email": "weak@test.com",

&nbsp;               "username": "weakuser",

&nbsp;               "password": "short",

&nbsp;               "full\_name": "Weak Password",

&nbsp;           },

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 422



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_register\_invalid\_username(self, async\_client: AsyncClient, admin\_user, admin\_token):

&nbsp;       """Username with invalid characters returns 422."""

&nbsp;       response = await async\_client.post(

&nbsp;           "/api/auth/register",

&nbsp;           json={

&nbsp;               "email": "invalid@test.com",

&nbsp;               "username": "invalid user!",

&nbsp;               "password": "securepassword123",

&nbsp;               "full\_name": "Invalid Username",

&nbsp;           },

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 422



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_register\_with\_sales\_team(self, async\_client: AsyncClient, admin\_user, admin\_token, test\_db):

&nbsp;       """Register user with valid sales\_team\_id succeeds."""

&nbsp;       team = SalesTeam(name="Test Team Register")

&nbsp;       test\_db.add(team)

&nbsp;       await test\_db.commit()

&nbsp;       await test\_db.refresh(team)



&nbsp;       response = await async\_client.post(

&nbsp;           "/api/auth/register",

&nbsp;           json={

&nbsp;               "email": "teamuser@test.com",

&nbsp;               "username": "teamuser",

&nbsp;               "password": "securepassword123",

&nbsp;               "full\_name": "Team User",

&nbsp;               "role": "sales\_team",

&nbsp;               "sales\_team\_id": team.id,

&nbsp;           },

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 201

&nbsp;       assert response.json()\["sales\_team\_id"] == team.id



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_register\_invalid\_sales\_team(self, async\_client: AsyncClient, admin\_user, admin\_token):

&nbsp;       """Register with non-existent sales\_team\_id returns 404."""

&nbsp;       response = await async\_client.post(

&nbsp;           "/api/auth/register",

&nbsp;           json={

&nbsp;               "email": "badteam@test.com",

&nbsp;               "username": "badteam",

&nbsp;               "password": "securepassword123",

&nbsp;               "full\_name": "Bad Team",

&nbsp;               "sales\_team\_id": 99999,

&nbsp;           },

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 404



─── PUT /api/auth/users/{user\_id} ──────────────────────────────────────



class TestUpdateUser:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_update\_user\_full\_name(self, async\_client: AsyncClient, admin\_user, analyst\_user, admin\_token):

&nbsp;       """Admin can update another user's full name."""

&nbsp;       response = await async\_client.put(

&nbsp;           f"/api/auth/users/{analyst\_user.id}",

&nbsp;           json={"full\_name": "Updated Name"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       assert response.json()\["full\_name"] == "Updated Name"



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_update\_user\_role(self, async\_client: AsyncClient, admin\_user, analyst\_user, admin\_token):

&nbsp;       """Admin can change another user's role."""

&nbsp;       response = await async\_client.put(

&nbsp;           f"/api/auth/users/{analyst\_user.id}",

&nbsp;           json={"role": "sales\_team"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       assert response.json()\["role"] == "sales\_team"



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_update\_user\_password(self, async\_client: AsyncClient, admin\_user, analyst\_user, admin\_token):

&nbsp;       """Admin can reset another user's password."""

&nbsp;       response = await async\_client.put(

&nbsp;           f"/api/auth/users/{analyst\_user.id}",

&nbsp;           json={"password": "newpassword123"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200



&nbsp;       # Verify new password works

&nbsp;       login\_response = await async\_client.post(

&nbsp;           "/api/auth/login",

&nbsp;           data={"username": "analyst", "password": "newpassword123"},

&nbsp;       )

&nbsp;       assert login\_response.status\_code == 200



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_update\_nonexistent\_user(self, async\_client: AsyncClient, admin\_user, admin\_token):

&nbsp;       """Updating non-existent user returns 404."""

&nbsp;       response = await async\_client.put(

&nbsp;           "/api/auth/users/99999",

&nbsp;           json={"full\_name": "Ghost"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 404



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_update\_by\_analyst\_forbidden(self, async\_client: AsyncClient, admin\_user, analyst\_user, analyst\_token):

&nbsp;       """Non-admin cannot update users."""

&nbsp;       response = await async\_client.put(

&nbsp;           f"/api/auth/users/{admin\_user.id}",

&nbsp;           json={"full\_name": "Hacked"},

&nbsp;           headers=auth\_header(analyst\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 403



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_admin\_cannot\_self\_demote(self, async\_client: AsyncClient, admin\_user, admin\_token):

&nbsp;       """Admin cannot change their own role away from admin."""

&nbsp;       response = await async\_client.put(

&nbsp;           f"/api/auth/users/{admin\_user.id}",

&nbsp;           json={"role": "analyst"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 400

&nbsp;       assert "demote" in response.json()\["detail"].lower()



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_admin\_cannot\_self\_deactivate(self, async\_client: AsyncClient, admin\_user, admin\_token):

&nbsp;       """Admin cannot deactivate their own account."""

&nbsp;       response = await async\_client.put(

&nbsp;           f"/api/auth/users/{admin\_user.id}",

&nbsp;           json={"is\_active": False},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 400

&nbsp;       assert "deactivate" in response.json()\["detail"].lower()



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_update\_duplicate\_email(self, async\_client: AsyncClient, admin\_user, analyst\_user, admin\_token):

&nbsp;       """Updating to an already-used email returns 409."""

&nbsp;       response = await async\_client.put(

&nbsp;           f"/api/auth/users/{analyst\_user.id}",

&nbsp;           json={"email": "admin@test.com"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 409



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_partial\_update(self, async\_client: AsyncClient, admin\_user, analyst\_user, admin\_token):

&nbsp;       """Partial update only changes specified fields."""

&nbsp;       original\_email = analyst\_user.email

&nbsp;       response = await async\_client.put(

&nbsp;           f"/api/auth/users/{analyst\_user.id}",

&nbsp;           json={"full\_name": "Only Name Changed"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       body = response.json()

&nbsp;       assert body\["full\_name"] == "Only Name Changed"

&nbsp;       assert body\["email"] == original\_email  # unchanged



─── GET /api/auth/users ─────────────────────────────────────────────────



class TestListUsers:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_users\_admin(self, async\_client: AsyncClient, admin\_user, analyst\_user, admin\_token):

&nbsp;       """Admin can list all users."""

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/auth/users",

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       users = response.json()

&nbsp;       assert isinstance(users, list)

&nbsp;       assert len(users) >= 2  # at least admin + analyst

&nbsp;       # Verify no password hashes leak

&nbsp;       for user in users:

&nbsp;           assert "hashed\_password" not in user

&nbsp;           assert "password" not in user



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_users\_analyst\_forbidden(self, async\_client: AsyncClient, analyst\_user, analyst\_token):

&nbsp;       """Non-admin cannot list users."""

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/auth/users",

&nbsp;           headers=auth\_header(analyst\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 403



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_users\_filter\_by\_role(self, async\_client: AsyncClient, admin\_user, analyst\_user, admin\_token):

&nbsp;       """Filter users by role."""

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/auth/users",

&nbsp;           params={"role": "admin"},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       users = response.json()

&nbsp;       assert all(u\["role"] == "admin" for u in users)



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_users\_pagination(self, async\_client: AsyncClient, admin\_user, analyst\_user, admin\_token):

&nbsp;       """Pagination with skip and limit works."""

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/auth/users",

&nbsp;           params={"skip": 0, "limit": 1},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       users = response.json()

&nbsp;       assert len(users) == 1



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_users\_filter\_by\_sales\_team(

&nbsp;       self, async\_client: AsyncClient, admin\_user, admin\_token, test\_db,

&nbsp;   ):

&nbsp;       """Filter users by sales\_team\_id."""

&nbsp;       team = SalesTeam(name="Test Team Filter")

&nbsp;       test\_db.add(team)

&nbsp;       await test\_db.commit()

&nbsp;       await test\_db.refresh(team)



&nbsp;       team\_user = User(

&nbsp;           email="teamfilter@test.com",

&nbsp;           username="teamfilter",

&nbsp;           hashed\_password=hash\_password("password123"),

&nbsp;           full\_name="Team Filter User",

&nbsp;           role="sales\_team",

&nbsp;           sales\_team\_id=team.id,

&nbsp;           is\_active=True,

&nbsp;       )

&nbsp;       test\_db.add(team\_user)

&nbsp;       await test\_db.commit()



&nbsp;       response = await async\_client.get(

&nbsp;           "/api/auth/users",

&nbsp;           params={"sales\_team\_id": team.id},

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       users = response.json()

&nbsp;       assert all(u\["sales\_team\_id"] == team.id for u in users)

&nbsp;       assert len(users) >= 1



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_list\_users\_deterministic\_order(self, async\_client: AsyncClient, admin\_user, analyst\_user, admin\_token):

&nbsp;       """Users are returned in deterministic order (by id)."""

&nbsp;       response = await async\_client.get(

&nbsp;           "/api/auth/users",

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert response.status\_code == 200

&nbsp;       users = response.json()

&nbsp;       ids = \[u\["id"] for u in users]

&nbsp;       assert ids == sorted(ids)



─── Integration: Login → Use Token ──────────────────────────────────────



class TestAuthIntegration:



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_login\_then\_access\_me(self, async\_client: AsyncClient, admin\_user):

&nbsp;       """Full flow: login → get token → use token to access /me."""

&nbsp;       # Login

&nbsp;       login\_response = await async\_client.post(

&nbsp;           "/api/auth/login",

&nbsp;           data={"username": "admin", "password": "adminpass"},

&nbsp;       )

&nbsp;       assert login\_response.status\_code == 200

&nbsp;       token = login\_response.json()\["access\_token"]



&nbsp;       # Use token

&nbsp;       me\_response = await async\_client.get(

&nbsp;           "/api/auth/me",

&nbsp;           headers=auth\_header(token),

&nbsp;       )

&nbsp;       assert me\_response.status\_code == 200

&nbsp;       assert me\_response.json()\["username"] == "admin"



&nbsp;   @pytest.mark.asyncio

&nbsp;   async def test\_register\_then\_login\_as\_new\_user(self, async\_client: AsyncClient, admin\_user, admin\_token):

&nbsp;       """Full flow: admin registers user → new user logs in → accesses /me."""

&nbsp;       # Admin registers new user

&nbsp;       reg\_response = await async\_client.post(

&nbsp;           "/api/auth/register",

&nbsp;           json={

&nbsp;               "email": "newflow@test.com",

&nbsp;               "username": "newflow",

&nbsp;               "password": "flowpassword123",

&nbsp;               "full\_name": "Flow Test User",

&nbsp;           },

&nbsp;           headers=auth\_header(admin\_token),

&nbsp;       )

&nbsp;       assert reg\_response.status\_code == 201



&nbsp;       # New user logs in

&nbsp;       login\_response = await async\_client.post(

&nbsp;           "/api/auth/login",

&nbsp;           data={"username": "newflow", "password": "flowpassword123"},

&nbsp;       )

&nbsp;       assert login\_response.status\_code == 200

&nbsp;       new\_token = login\_response.json()\["access\_token"]



&nbsp;       # New user accesses /me

&nbsp;       me\_response = await async\_client.get(

&nbsp;           "/api/auth/me",

&nbsp;           headers=auth\_header(new\_token),

&nbsp;       )

&nbsp;       assert me\_response.status\_code == 200

&nbsp;       assert me\_response.json()\["username"] == "newflow"

&nbsp;       assert me\_response.json()\["role"] == "analyst"  # default role





Validation Criteria for Phase 1



After implementation, ALL of these must pass:

1\. uvicorn backend.api.main:app --reload starts without errors

2\. POST /api/auth/login with valid credentials returns 200 + JWT

3\. POST /api/auth/login with bad password returns 401

4\. GET /api/auth/me with valid token returns 200 + user info

5\. GET /api/auth/me without token returns 401

6\. POST /api/auth/register with admin token returns 201

7\. POST /api/auth/register with analyst token returns 403

8\. POST /api/auth/register with duplicate email returns 409

9\. PUT /api/auth/users/{id} updates user fields

10\. PUT /api/auth/users/{id} prevents admin self-demotion

11\. GET /api/auth/users with admin token returns user list

12\. GET /api/auth/users with role filter returns filtered results

13\. GET /api/auth/users with analyst token returns 403

14\. pytest backend/tests/test\_auth\_routes.py — all tests pass (30+ tests)

15\. ruff check backend/auth/ — no lint errors

16\. No password hashes appear in any API response



Run the auth tests:



bash

pytest backend/tests/test\_auth\_routes.py -v --tb=short



Expected:





backend/tests/test\_auth\_routes.py::TestLogin::test\_login\_success PASSED

backend/tests/test\_auth\_routes.py::TestLogin::test\_login\_wrong\_password PASSED

backend/tests/test\_auth\_routes.py::TestLogin::test\_login\_unknown\_user PASSED

backend/tests/test\_auth\_routes.py::TestLogin::test\_login\_case\_insensitive\_username PASSED

backend/tests/test\_auth\_routes.py::TestLogin::test\_login\_disabled\_account PASSED

backend/tests/test\_auth\_routes.py::TestLogin::test\_login\_missing\_fields PASSED

backend/tests/test\_auth\_routes.py::TestGetMe::test\_me\_authenticated PASSED

backend/tests/test\_auth\_routes.py::TestGetMe::test\_me\_unauthenticated PASSED

backend/tests/test\_auth\_routes.py::TestGetMe::test\_me\_invalid\_token PASSED

backend/tests/test\_auth\_routes.py::TestGetMe::test\_me\_expired\_token PASSED

backend/tests/test\_auth\_routes.py::TestRegister::test\_register\_by\_admin PASSED

... (30+ tests)



============================== 30 passed ==============================



Do NOT modify any files outside of the auth module unless absolutely necessary

for the auth system to function (e.g., if backend/api/dependencies.py needs

a new re-export). Do NOT change endpoint stubs in routes.py or files.py.



