Task: Implement Production Hardening \& Observability for the Loan Engine



You are extending the Loan Engine application (Phases 0-6 complete) with

production-grade hardening. After this phase, the application has structured

logging with request tracing, health monitoring with dependency checks,

rate limiting, global error handling, performance optimization, database

connection management, graceful shutdown, and operational scripts. The system

is ready for production traffic.





Context: What Already Exists



Application State (Phases 0-6 complete)





Backend:    FastAPI + SQLAlchemy async + PostgreSQL

Frontend:   React 18 (built, served via FastAPI static mount)

Auth:       JWT (python-jose) + bcrypt + OAuth2PasswordBearer

Pipeline:   7-phase loan processing engine

Storage:    Local filesystem + S3 (dual backend)

Tests:      300+ tests covering all layers

Infra:      Terraform, Docker, GitHub Actions CI/CD



Current Gaps (what this phase addresses)



| Gap | Risk | Solution |

|-----|------|----------|

| No structured logging | Cannot search/filter logs in CloudWatch | JSON structured logging with correlation IDs |

| No request tracing | Cannot trace requests across log entries | Request ID middleware, propagated to all log entries |

| Basic error handling | Unhandled exceptions leak stack traces | Global exception middleware with safe error responses |

| No rate limiting | API vulnerable to abuse | Sliding window rate limiter on auth and pipeline endpoints |

| Basic health check | /health/ready only checks DB | Extended health with storage, memory, disk checks |

| No performance monitoring | Cannot identify slow endpoints | Request timing middleware with slow query logging |

| No graceful shutdown | In-flight requests dropped on deploy | Signal handling with drain period |

| No DB connection tuning | Default pool settings | Tuned pool size, overflow, recycle for production |

| No request validation limits | Large payloads accepted | Request size limits and timeout enforcement |

| No operational tooling | Manual debugging only | Admin CLI commands and diagnostic endpoints |



Files That Exist (DO NOT MODIFY unless listed)





backend/api/main.py              # FastAPI app, lifespan, routers, health endpoints

backend/api/routes.py            # Pipeline/run endpoints

backend/api/files.py             # File management endpoints

backend/api/dependencies.py      # get\_db, get\_storage, get\_current\_user

backend/auth/routes.py           # Auth endpoints

backend/auth/security.py         # JWT, password hashing

backend/config.py                # Settings (BaseSettings)

backend/database.py              # Engine, session factory, Base

backend/models.py                # ORM models

backend/pipeline/engine.py       # Pipeline orchestrator

backend/pipeline/phases.py       # Pipeline phases

backend/pipeline/eligibility.py  # Eligibility rules

backend/storage/local.py         # Local storage backend

backend/storage/s3.py            # S3 storage backend

backend/utils/path\_utils.py      # Path security utilities

backend/tests/conftest.py        # Test fixtures

deploy/Dockerfile                # Production Docker build

deploy/entrypoint.sh             # Container startup script





Files to Create



| File | Purpose |

|------|---------|

| backend/middleware/\_\_init\_\_.py | Middleware package |

| backend/middleware/request\_id.py | Request ID generation and propagation |

| backend/middleware/logging\_middleware.py | Structured request/response logging |

| backend/middleware/error\_handler.py | Global exception handling |

| backend/middleware/rate\_limiter.py | Sliding window rate limiting |

| backend/middleware/timing.py | Request timing and slow request detection |

| backend/middleware/security\_headers.py | Security response headers |

| backend/observability/\_\_init\_\_.py | Observability package |

| backend/observability/logging\_config.py | Structured JSON logging configuration |

| backend/observability/health.py | Extended health check system |

| backend/observability/metrics.py | Application metrics collection |

| backend/admin/\_\_init\_\_.py | Admin package |

| backend/admin/cli.py | Admin CLI commands |

| backend/admin/diagnostics.py | Diagnostic endpoints |

| backend/tests/test\_middleware.py | Middleware tests |

| backend/tests/test\_observability.py | Health and metrics tests |

| backend/tests/test\_hardening.py | Production hardening tests |



Files to Modify



| File | Changes |

|------|---------|

| backend/api/main.py | Add middleware stack, update lifespan, add diagnostic routes |

| backend/config.py | Add production config variables |

| backend/database.py | Add connection pool tuning, slow query logging |

| deploy/entrypoint.sh | Add graceful shutdown handling |



DO NOT MODIFY

• backend/api/routes.py, backend/api/files.py (business logic stable)

• backend/auth/\* (auth layer stable)

• backend/pipeline/\* (pipeline stable)

• backend/storage/\* (storage stable)

• backend/models.py (schema stable)

• backend/tests/test\_auth\_routes.py, test\_pipeline\_routes.py, test\_file\_routes.py,

&nbsp; test\_storage\_.py, test\_integration\_.py, test\_security.py, test\_data\_integrity.py,

&nbsp; test\_edge\_cases.py, test\_eligibility\_rules.py, test\_pipeline\_phases.py,

&nbsp; test\_path\_utils.py, test\_pagination.py, test\_concurrent.py (existing tests stable)

• All frontend/ files

• All terraform/ files





Configuration Extensions (backend/config.py)



Add these fields to the existing Settings class. Do NOT remove or change

any existing fields.



python

─── Add to existing Settings class ─────────────────────



&nbsp;   # Logging

&nbsp;   LOG\_LEVEL: str = "INFO"

&nbsp;   LOG\_FORMAT: str = "json"            # "json" | "text"

&nbsp;   LOG\_INCLUDE\_TIMESTAMP: bool = True



&nbsp;   # Rate Limiting

&nbsp;   RATE\_LIMIT\_ENABLED: bool = True

&nbsp;   RATE\_LIMIT\_LOGIN: str = "10/minute"          # max 10 login attempts per minute per IP

&nbsp;   RATE\_LIMIT\_REGISTER: str = "5/minute"        # max 5 registrations per minute

&nbsp;   RATE\_LIMIT\_PIPELINE: str = "5/minute"        # max 5 pipeline runs per minute

&nbsp;   RATE\_LIMIT\_API: str = "100/minute"           # general API rate limit per user

&nbsp;   RATE\_LIMIT\_UPLOAD: str = "20/minute"         # file uploads per minute



&nbsp;   # Performance

&nbsp;   REQUEST\_TIMEOUT\_SECONDS: int = 300           # max request duration

&nbsp;   SLOW\_REQUEST\_THRESHOLD\_MS: int = 1000        # log warning for requests slower than this

&nbsp;   MAX\_REQUEST\_SIZE\_MB: int = 100               # max request body size



&nbsp;   # Database Pool

&nbsp;   DB\_POOL\_SIZE: int = 10                       # connection pool size

&nbsp;   DB\_MAX\_OVERFLOW: int = 20                    # max connections beyond pool\_size

&nbsp;   DB\_POOL\_RECYCLE: int = 3600                  # recycle connections after N seconds

&nbsp;   DB\_POOL\_TIMEOUT: int = 30                    # wait timeout for getting connection

&nbsp;   DB\_ECHO\_QUERIES: bool = False                # log all SQL queries

&nbsp;   DB\_SLOW\_QUERY\_MS: int = 500                  # log warning for queries slower than this



&nbsp;   # Health Checks

&nbsp;   HEALTH\_CHECK\_TIMEOUT: int = 5                # timeout for health check probes

&nbsp;   HEALTH\_INCLUDE\_DETAILS: bool = True          # include component details in /health/ready



&nbsp;   # Security Headers

&nbsp;   ENABLE\_SECURITY\_HEADERS: bool = True



&nbsp;   # Admin

&nbsp;   ADMIN\_DIAGNOSTICS\_ENABLED: bool = True       # enable /admin/diagnostics endpoints





Structured Logging (backend/observability/logging\_config.py)



python

"""

Structured JSON logging configuration.

All log entries include: timestamp, level, logger, message, request\_id, extra fields.

In production (LOG\_FORMAT=json), outputs machine-parseable JSON lines.

In development (LOG\_FORMAT=text), outputs human-readable colored text.

"""

import logging

import logging.config

import json

import sys

from datetime import datetime, timezone

from typing import Any

from contextvars import ContextVar



Context variable for request-scoped data

request\_id\_var: ContextVar\[str] = ContextVar("request\_id", default="")

request\_user\_var: ContextVar\[str] = ContextVar("request\_user", default="")



class JSONFormatter(logging.Formatter):

&nbsp;   """

&nbsp;   Formats log records as single-line JSON objects.

&nbsp;   Fields: timestamp, level, logger, message, request\_id, user, extra.

&nbsp;   """



&nbsp;   def format(self, record: logging.LogRecord) -> str:

&nbsp;       log\_entry: dict\[str, Any] = {

&nbsp;           "timestamp": datetime.fromtimestamp(

&nbsp;               record.created, tz=timezone.utc

&nbsp;           ).isoformat(),

&nbsp;           "level": record.levelname,

&nbsp;           "logger": record.name,

&nbsp;           "message": record.getMessage(),

&nbsp;       }



&nbsp;       # Add request context from ContextVars

&nbsp;       req\_id = request\_id\_var.get("")

&nbsp;       if req\_id:

&nbsp;           log\_entry\["request\_id"] = req\_id



&nbsp;       user = request\_user\_var.get("")

&nbsp;       if user:

&nbsp;           log\_entry\["user"] = user



&nbsp;       # Add extra fields from the log record

&nbsp;       extra\_keys = set(record.\_\_dict\_\_.keys()) - {

&nbsp;           "name", "msg", "args", "created", "relativeCreated",

&nbsp;           "exc\_info", "exc\_text", "stack\_info", "lineno", "funcName",

&nbsp;           "pathname", "filename", "module", "levelno", "levelname",

&nbsp;           "thread", "threadName", "process", "processName",

&nbsp;           "getMessage", "message", "msecs", "taskName",

&nbsp;       }

&nbsp;       for key in sorted(extra\_keys):

&nbsp;           value = record.\_\_dict\_\_\[key]

&nbsp;           if value is not None:

&nbsp;               log\_entry\[key] = value



&nbsp;       # Add exception info

&nbsp;       if record.exc\_info and record.exc\_info\[1]:

&nbsp;           log\_entry\["exception"] = {

&nbsp;               "type": type(record.exc\_info\[1]).\_\_name\_\_,

&nbsp;               "message": str(record.exc\_info\[1]),

&nbsp;               "traceback": self.formatException(record.exc\_info),

&nbsp;           }



&nbsp;       return json.dumps(log\_entry, default=str)



class TextFormatter(logging.Formatter):

&nbsp;   """

&nbsp;   Human-readable colored formatter for development.

&nbsp;   """



&nbsp;   COLORS = {

&nbsp;       "DEBUG": "\\033\[36m",     # cyan

&nbsp;       "INFO": "\\033\[32m",      # green

&nbsp;       "WARNING": "\\033\[33m",   # yellow

&nbsp;       "ERROR": "\\033\[31m",     # red

&nbsp;       "CRITICAL": "\\033\[35m",  # magenta

&nbsp;   }

&nbsp;   RESET = "\\033\[0m"



&nbsp;   def format(self, record: logging.LogRecord) -> str:

&nbsp;       color = self.COLORS.get(record.levelname, "")

&nbsp;       reset = self.RESET



&nbsp;       req\_id = request\_id\_var.get("")

&nbsp;       req\_prefix = f"\[{req\_id\[:8]}] " if req\_id else ""



&nbsp;       user = request\_user\_var.get("")

&nbsp;       user\_prefix = f"({user}) " if user else ""



&nbsp;       timestamp = datetime.fromtimestamp(

&nbsp;           record.created, tz=timezone.utc

&nbsp;       ).strftime("%H:%M:%S.%f")\[:-3]



&nbsp;       msg = f"{timestamp} {color}{record.levelname:8}{reset} " \\

&nbsp;             f"{req\_prefix}{user\_prefix}" \\

&nbsp;             f"{record.name}: {record.getMessage()}"



&nbsp;       if record.exc\_info and record.exc\_info\[1]:

&nbsp;           msg += f"\\n{self.formatException(record.exc\_info)}"



&nbsp;       return msg



def configure\_logging(log\_level: str = "INFO", log\_format: str = "json"):

&nbsp;   """

&nbsp;   Configure application-wide logging.

&nbsp;   Call once at application startup (in lifespan handler).

&nbsp;   """

&nbsp;   # Determine formatter

&nbsp;   if log\_format == "json":

&nbsp;       formatter\_class = JSONFormatter

&nbsp;       formatter\_args = {}

&nbsp;   else:

&nbsp;       formatter\_class = TextFormatter

&nbsp;       formatter\_args = {}



&nbsp;   config = {

&nbsp;       "version": 1,

&nbsp;       "disable\_existing\_loggers": False,

&nbsp;       "formatters": {

&nbsp;           "default": {

&nbsp;               "()": formatter\_class,

&nbsp;               formatter\_args,

&nbsp;           },

&nbsp;       },

&nbsp;       "handlers": {

&nbsp;           "console": {

&nbsp;               "class": "logging.StreamHandler",

&nbsp;               "formatter": "default",

&nbsp;               "stream": "ext://sys.stdout",

&nbsp;           },

&nbsp;       },

&nbsp;       "root": {

&nbsp;           "level": log\_level,

&nbsp;           "handlers": \["console"],

&nbsp;       },

&nbsp;       "loggers": {

&nbsp;           # Application loggers

&nbsp;           "backend": {"level": log\_level, "propagate": True},

&nbsp;           "uvicorn": {"level": log\_level, "propagate": True},

&nbsp;           "uvicorn.access": {"level": "WARNING", "propagate": True},



&nbsp;           # Quiet noisy libraries

&nbsp;           "sqlalchemy.engine": {

&nbsp;               "level": "WARNING",

&nbsp;               "propagate": True,

&nbsp;           },

&nbsp;           "httpcore": {"level": "WARNING", "propagate": True},

&nbsp;           "httpx": {"level": "WARNING", "propagate": True},

&nbsp;           "botocore": {"level": "WARNING", "propagate": True},

&nbsp;       },

&nbsp;   }



&nbsp;   logging.config.dictConfig(config)





Request ID Middleware (backend/middleware/request\_id.py)



python

"""

Request ID middleware.

Generates a unique ID for each request, propagates it through

logging context vars, and returns it in the X-Request-ID response header.

"""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware

from starlette.requests import Request

from starlette.responses import Response



from backend.observability.logging\_config import request\_id\_var, request\_user\_var



class RequestIDMiddleware(BaseHTTPMiddleware):

&nbsp;   """

&nbsp;   Assigns a unique request ID to each incoming request.

• Reads X-Request-ID from incoming headers (for distributed tracing)

• Generates a new UUID if not present

• Sets ContextVar so all log entries include the request ID

• Adds X-Request-ID to response headers

&nbsp;   """



&nbsp;   async def dispatch(self, request: Request, call\_next) -> Response:

&nbsp;       # Use incoming request ID or generate one

&nbsp;       request\_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))



&nbsp;       # Set context variables for structured logging

&nbsp;       req\_id\_token = request\_id\_var.set(request\_id)



&nbsp;       # Extract username from auth header if present (for logging)

&nbsp;       user\_token = None

&nbsp;       auth\_header = request.headers.get("Authorization", "")

&nbsp;       if auth\_header.startswith("Bearer "):

&nbsp;           try:

&nbsp;               from jose import jwt

&nbsp;               from backend.config import get\_settings

&nbsp;               settings = get\_settings()

&nbsp;               token = auth\_header.split(" ")\[1]

&nbsp;               payload = jwt.decode(

&nbsp;                   token, settings.SECRET\_KEY,

&nbsp;                   algorithms=\[settings.JWT\_ALGORITHM],

&nbsp;                   options={"verify\_exp": False},

&nbsp;               )

&nbsp;               username = payload.get("sub", "")

&nbsp;               if username:

&nbsp;                   user\_token = request\_user\_var.set(username)

&nbsp;           except Exception:

&nbsp;               pass



&nbsp;       # Store request ID on request state for access in route handlers

&nbsp;       request.state.request\_id = request\_id



&nbsp;       response = await call\_next(request)



&nbsp;       # Add request ID to response headers

&nbsp;       response.headers\["X-Request-ID"] = request\_id



&nbsp;       # Reset context variables

&nbsp;       request\_id\_var.reset(req\_id\_token)

&nbsp;       if user\_token:

&nbsp;           request\_user\_var.reset(user\_token)



&nbsp;       return response





Logging Middleware (backend/middleware/logging\_middleware.py)



python

"""

Structured request/response logging middleware.

Logs every request with method, path, status, duration, and user context.

Excludes health check endpoints from verbose logging.

"""

import time

import logging

from starlette.middleware.base import BaseHTTPMiddleware

from starlette.requests import Request

from starlette.responses import Response



logger = logging.getLogger("backend.access")



Paths excluded from access logging (too noisy)

EXCLUDED\_PATHS = {"/health", "/health/ready", "/favicon.ico"}



class LoggingMiddleware(BaseHTTPMiddleware):



&nbsp;   async def dispatch(self, request: Request, call\_next) -> Response:

&nbsp;       if request.url.path in EXCLUDED\_PATHS:

&nbsp;           return await call\_next(request)



&nbsp;       start\_time = time.perf\_counter()



&nbsp;       # Log request start

&nbsp;       logger.info(

&nbsp;           "Request started",

&nbsp;           extra={

&nbsp;               "method": request.method,

&nbsp;               "path": request.url.path,

&nbsp;               "query": str(request.query\_params) if request.query\_params else None,

&nbsp;               "client\_ip": request.client.host if request.client else None,

&nbsp;               "content\_length": request.headers.get("content-length"),

&nbsp;           },

&nbsp;       )



&nbsp;       response = await call\_next(request)



&nbsp;       duration\_ms = (time.perf\_counter() - start\_time) \* 1000



&nbsp;       # Determine log level based on status code

&nbsp;       if response.status\_code >= 500:

&nbsp;           log\_fn = logger.error

&nbsp;       elif response.status\_code >= 400:

&nbsp;           log\_fn = logger.warning

&nbsp;       else:

&nbsp;           log\_fn = logger.info



&nbsp;       log\_fn(

&nbsp;           "Request completed",

&nbsp;           extra={

&nbsp;               "method": request.method,

&nbsp;               "path": request.url.path,

&nbsp;               "status\_code": response.status\_code,

&nbsp;               "duration\_ms": round(duration\_ms, 2),

&nbsp;               "client\_ip": request.client.host if request.client else None,

&nbsp;           },

&nbsp;       )



&nbsp;       return response





Request Timing Middleware (backend/middleware/timing.py)



python

"""

Request timing middleware.

Adds Server-Timing header and logs warnings for slow requests.

"""

import time

import logging

from starlette.middleware.base import BaseHTTPMiddleware

from starlette.requests import Request

from starlette.responses import Response



from backend.config import get\_settings



logger = logging.getLogger("backend.performance")



class TimingMiddleware(BaseHTTPMiddleware):



&nbsp;   async def dispatch(self, request: Request, call\_next) -> Response:

&nbsp;       settings = get\_settings()

&nbsp;       start = time.perf\_counter()



&nbsp;       response = await call\_next(request)



&nbsp;       duration\_ms = (time.perf\_counter() - start) \* 1000



&nbsp;       # Add Server-Timing header

&nbsp;       response.headers\["Server-Timing"] = f"total;dur={duration\_ms:.1f}"



&nbsp;       # Log slow requests

&nbsp;       if duration\_ms > settings.SLOW\_REQUEST\_THRESHOLD\_MS:

&nbsp;           logger.warning(

&nbsp;               "Slow request detected",

&nbsp;               extra={

&nbsp;                   "method": request.method,

&nbsp;                   "path": request.url.path,

&nbsp;                   "duration\_ms": round(duration\_ms, 2),

&nbsp;                   "threshold\_ms": settings.SLOW\_REQUEST\_THRESHOLD\_MS,

&nbsp;               },

&nbsp;           )



&nbsp;       return response





Global Error Handler (backend/middleware/error\_handler.py)



python

"""

Global exception handling middleware.

Catches unhandled exceptions and returns safe, structured error responses.

Never exposes stack traces, internal paths, or sensitive data to clients.

"""

import logging

import traceback

from fastapi import Request, status

from fastapi.responses import JSONResponse

from fastapi.exceptions import RequestValidationError

from starlette.exceptions import HTTPException as StarletteHTTPException

from sqlalchemy.exc import IntegrityError, OperationalError



logger = logging.getLogger("backend.errors")



async def http\_exception\_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:

&nbsp;   """Handle FastAPI/Starlette HTTP exceptions."""

&nbsp;   request\_id = getattr(request.state, "request\_id", None)



&nbsp;   if exc.status\_code >= 500:

&nbsp;       logger.error(

&nbsp;           "HTTP error",

&nbsp;           extra={

&nbsp;               "status\_code": exc.status\_code,

&nbsp;               "detail": str(exc.detail),

&nbsp;               "path": request.url.path,

&nbsp;           },

&nbsp;       )

&nbsp;   elif exc.status\_code >= 400:

&nbsp;       logger.info(

&nbsp;           "Client error",

&nbsp;           extra={

&nbsp;               "status\_code": exc.status\_code,

&nbsp;               "detail": str(exc.detail),

&nbsp;               "path": request.url.path,

&nbsp;           },

&nbsp;       )



&nbsp;   return JSONResponse(

&nbsp;       status\_code=exc.status\_code,

&nbsp;       content={

&nbsp;           "error": exc.detail,

&nbsp;           "status\_code": exc.status\_code,

&nbsp;           "request\_id": request\_id,

&nbsp;       },

&nbsp;       headers=exc.headers if hasattr(exc, "headers") and exc.headers else None,

&nbsp;   )



async def validation\_exception\_handler(request: Request, exc: RequestValidationError) -> JSONResponse:

&nbsp;   """Handle Pydantic validation errors with safe formatting."""

&nbsp;   request\_id = getattr(request.state, "request\_id", None)



&nbsp;   # Sanitize validation errors (remove raw input values for security)

&nbsp;   safe\_errors = \[]

&nbsp;   for error in exc.errors():

&nbsp;       safe\_error = {

&nbsp;           "field": " → ".join(str(loc) for loc in error.get("loc", \[])),

&nbsp;           "message": error.get("msg", "Validation error"),

&nbsp;           "type": error.get("type", "unknown"),

&nbsp;       }

&nbsp;       safe\_errors.append(safe\_error)



&nbsp;   logger.info(

&nbsp;       "Validation error",

&nbsp;       extra={

&nbsp;           "path": request.url.path,

&nbsp;           "error\_count": len(safe\_errors),

&nbsp;       },

&nbsp;   )



&nbsp;   return JSONResponse(

&nbsp;       status\_code=status.HTTP\_422\_UNPROCESSABLE\_ENTITY,

&nbsp;       content={

&nbsp;           "error": "Validation error",

&nbsp;           "details": safe\_errors,

&nbsp;           "status\_code": 422,

&nbsp;           "request\_id": request\_id,

&nbsp;       },

&nbsp;   )



async def database\_exception\_handler(request: Request, exc: Exception) -> JSONResponse:

&nbsp;   """Handle database-specific exceptions."""

&nbsp;   request\_id = getattr(request.state, "request\_id", None)



&nbsp;   if isinstance(exc, IntegrityError):

&nbsp;       logger.warning(

&nbsp;           "Database integrity error",

&nbsp;           extra={"path": request.url.path, "error": str(exc.orig)\[:200]},

&nbsp;       )

&nbsp;       return JSONResponse(

&nbsp;           status\_code=status.HTTP\_409\_CONFLICT,

&nbsp;           content={

&nbsp;               "error": "Data conflict. The record may already exist.",

&nbsp;               "status\_code": 409,

&nbsp;               "request\_id": request\_id,

&nbsp;           },

&nbsp;       )



&nbsp;   if isinstance(exc, OperationalError):

&nbsp;       logger.error(

&nbsp;           "Database operational error",

&nbsp;           extra={"path": request.url.path},

&nbsp;           exc\_info=True,

&nbsp;       )

&nbsp;       return JSONResponse(

&nbsp;           status\_code=status.HTTP\_503\_SERVICE\_UNAVAILABLE,

&nbsp;           content={

&nbsp;               "error": "Database temporarily unavailable. Please try again.",

&nbsp;               "status\_code": 503,

&nbsp;               "request\_id": request\_id,

&nbsp;           },

&nbsp;       )



&nbsp;   return None  # Let the generic handler catch it



async def generic\_exception\_handler(request: Request, exc: Exception) -> JSONResponse:

&nbsp;   """

&nbsp;   Catch-all for unhandled exceptions.

&nbsp;   NEVER expose internal details to the client.

&nbsp;   """

&nbsp;   request\_id = getattr(request.state, "request\_id", None)



&nbsp;   # Log the full exception internally

&nbsp;   logger.error(

&nbsp;       "Unhandled exception",

&nbsp;       extra={

&nbsp;           "path": request.url.path,

&nbsp;           "method": request.method,

&nbsp;           "exception\_type": type(exc).\_\_name\_\_,

&nbsp;       },

&nbsp;       exc\_info=True,

&nbsp;   )



&nbsp;   # Return safe generic error to client

&nbsp;   return JSONResponse(

&nbsp;       status\_code=status.HTTP\_500\_INTERNAL\_SERVER\_ERROR,

&nbsp;       content={

&nbsp;           "error": "An internal error occurred. Please try again later.",

&nbsp;           "status\_code": 500,

&nbsp;           "request\_id": request\_id,

&nbsp;       },

&nbsp;   )





Rate Limiter (backend/middleware/rate\_limiter.py)



python

"""

In-memory sliding window rate limiter.

Limits requests per IP (for auth endpoints) and per user (for API endpoints).

Uses an in-memory store — suitable for single-instance deployments.

For multi-instance deployments, swap to Redis-backed storage.

"""

import time

import logging

from collections import defaultdict

from dataclasses import dataclass, field

from starlette.middleware.base import BaseHTTPMiddleware

from starlette.requests import Request

from starlette.responses import Response

from fastapi.responses import JSONResponse



from backend.config import get\_settings



logger = logging.getLogger("backend.ratelimit")



@dataclass

class RateLimitRule:

&nbsp;   max\_requests: int

&nbsp;   window\_seconds: int

&nbsp;   key\_func: str = "ip"  # "ip" | "user" | "ip\_and\_path"



def parse\_rate\_limit(limit\_str: str) -> tuple\[int, int]:

&nbsp;   """Parse '10/minute' → (10, 60)."""

&nbsp;   parts = limit\_str.split("/")

&nbsp;   count = int(parts\[0])

&nbsp;   unit = parts\[1].lower()

&nbsp;   multipliers = {

&nbsp;       "second": 1, "minute": 60, "hour": 3600, "day": 86400,

&nbsp;   }

&nbsp;   return count, multipliers.get(unit, 60)



class SlidingWindowCounter:

&nbsp;   """Simple in-memory sliding window rate limiter."""



&nbsp;   def \_\_init\_\_(self):

&nbsp;       self.\_requests: dict\[str, list\[float]] = defaultdict(list)



&nbsp;   def is\_allowed(self, key: str, max\_requests: int, window\_seconds: int) -> tuple\[bool, int]:

&nbsp;       """

&nbsp;       Check if a request is allowed.

&nbsp;       Returns (allowed, remaining\_requests).

&nbsp;       """

&nbsp;       now = time.time()

&nbsp;       window\_start = now - window\_seconds



&nbsp;       # Clean old entries

&nbsp;       self.\_requests\[key] = \[

&nbsp;           ts for ts in self.\_requests\[key] if ts > window\_start

&nbsp;       ]



&nbsp;       current\_count = len(self.\_requests\[key])



&nbsp;       if current\_count >= max\_requests:

&nbsp;           return False, 0



&nbsp;       self.\_requests\[key].append(now)

&nbsp;       return True, max\_requests - current\_count - 1



&nbsp;   def cleanup(self, max\_age: int = 3600):

&nbsp;       """Remove entries older than max\_age seconds."""

&nbsp;       cutoff = time.time() - max\_age

&nbsp;       empty\_keys = \[]

&nbsp;       for key, timestamps in self.\_requests.items():

&nbsp;           self.\_requests\[key] = \[ts for ts in timestamps if ts > cutoff]

&nbsp;           if not self.\_requests\[key]:

&nbsp;               empty\_keys.append(key)

&nbsp;       for key in empty\_keys:

&nbsp;           del self.\_requests\[key]



Global rate limiter instance

\_limiter = SlidingWindowCounter()



Route-specific rate limit rules

RATE\_LIMIT\_ROUTES: dict\[str, str] = {}



def configure\_rate\_limits(settings):

&nbsp;   """Configure rate limit rules from settings."""

&nbsp;   global RATE\_LIMIT\_ROUTES

&nbsp;   RATE\_LIMIT\_ROUTES = {

&nbsp;       "/api/auth/login": settings.RATE\_LIMIT\_LOGIN,

&nbsp;       "/api/auth/register": settings.RATE\_LIMIT\_REGISTER,

&nbsp;       "/api/pipeline/run": settings.RATE\_LIMIT\_PIPELINE,

&nbsp;       "/api/files/upload": settings.RATE\_LIMIT\_UPLOAD,

&nbsp;   }



class RateLimitMiddleware(BaseHTTPMiddleware):



&nbsp;   async def dispatch(self, request: Request, call\_next) -> Response:

&nbsp;       settings = get\_settings()



&nbsp;       if not settings.RATE\_LIMIT\_ENABLED:

&nbsp;           return await call\_next(request)



&nbsp;       path = request.url.path

&nbsp;       client\_ip = request.client.host if request.client else "unknown"



&nbsp;       # Check route-specific limits first

&nbsp;       limit\_str = RATE\_LIMIT\_ROUTES.get(path)



&nbsp;       if not limit\_str:

&nbsp;           # Apply general API limit for /api/ paths

&nbsp;           if path.startswith("/api/"):

&nbsp;               limit\_str = settings.RATE\_LIMIT\_API

&nbsp;           else:

&nbsp;               return await call\_next(request)



&nbsp;       max\_requests, window\_seconds = parse\_rate\_limit(limit\_str)



&nbsp;       # Build rate limit key

&nbsp;       # For auth endpoints: use IP

&nbsp;       # For other endpoints: use IP + authenticated user if available

&nbsp;       if "/auth/login" in path:

&nbsp;           key = f"ip:{client\_ip}:{path}"

&nbsp;       else:

&nbsp;           key = f"ip:{client\_ip}:api"



&nbsp;       allowed, remaining = \_limiter.is\_allowed(key, max\_requests, window\_seconds)



&nbsp;       if not allowed:

&nbsp;           logger.warning(

&nbsp;               "Rate limit exceeded",

&nbsp;               extra={

&nbsp;                   "path": path,

&nbsp;                   "client\_ip": client\_ip,

&nbsp;                   "limit": limit\_str,

&nbsp;               },

&nbsp;           )

&nbsp;           return JSONResponse(

&nbsp;               status\_code=429,

&nbsp;               content={

&nbsp;                   "error": "Rate limit exceeded. Please try again later.",

&nbsp;                   "status\_code": 429,

&nbsp;                   "retry\_after": window\_seconds,

&nbsp;               },

&nbsp;               headers={

&nbsp;                   "Retry-After": str(window\_seconds),

&nbsp;                   "X-RateLimit-Limit": str(max\_requests),

&nbsp;                   "X-RateLimit-Remaining": "0",

&nbsp;               },

&nbsp;           )



&nbsp;       response = await call\_next(request)



&nbsp;       # Add rate limit headers

&nbsp;       response.headers\["X-RateLimit-Limit"] = str(max\_requests)

&nbsp;       response.headers\["X-RateLimit-Remaining"] = str(remaining)



&nbsp;       return response





Security Headers Middleware (backend/middleware/security\_headers.py)



python

"""

Security response headers middleware.

Adds OWASP-recommended security headers to all responses.

"""

from starlette.middleware.base import BaseHTTPMiddleware

from starlette.requests import Request

from starlette.responses import Response



class SecurityHeadersMiddleware(BaseHTTPMiddleware):



&nbsp;   async def dispatch(self, request: Request, call\_next) -> Response:

&nbsp;       response = await call\_next(request)



&nbsp;       response.headers\["X-Content-Type-Options"] = "nosniff"

&nbsp;       response.headers\["X-Frame-Options"] = "DENY"

&nbsp;       response.headers\["X-XSS-Protection"] = "1; mode=block"

&nbsp;       response.headers\["Referrer-Policy"] = "strict-origin-when-cross-origin"

&nbsp;       response.headers\["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

&nbsp;       response.headers\["Cache-Control"] = "no-store, no-cache, must-revalidate"

&nbsp;       response.headers\["Pragma"] = "no-cache"



&nbsp;       # Content-Security-Policy for HTML responses

&nbsp;       if "text/html" in response.headers.get("content-type", ""):

&nbsp;           response.headers\["Content-Security-Policy"] = (

&nbsp;               "default-src 'self'; "

&nbsp;               "script-src 'self'; "

&nbsp;               "style-src 'self' 'unsafe-inline'; "

&nbsp;               "img-src 'self' data:; "

&nbsp;               "font-src 'self'; "

&nbsp;               "connect-src 'self'; "

&nbsp;               "frame-ancestors 'none'"

&nbsp;           )



&nbsp;       return response





Extended Health Checks (backend/observability/health.py)



python

"""

Extended health check system.

Provides detailed health status for all application dependencies.

Used by ALB health checks and operational monitoring.

"""

import time

import psutil

import logging

from datetime import datetime, timezone

from dataclasses import dataclass



from sqlalchemy import text

from sqlalchemy.ext.asyncio import AsyncSession



from backend.database import engine

from backend.storage.base import StorageBackend

from backend.config import get\_settings



logger = logging.getLogger("backend.health")



Track application start time

\_app\_start\_time: datetime | None = None



def set\_app\_start\_time():

&nbsp;   global \_app\_start\_time

&nbsp;   \_app\_start\_time = datetime.now(timezone.utc)



@dataclass

class ComponentHealth:

&nbsp;   name: str

&nbsp;   status: str        # "healthy" | "degraded" | "unhealthy"

&nbsp;   latency\_ms: float

&nbsp;   details: dict | None = None

&nbsp;   error: str | None = None



async def check\_database\_health() -> ComponentHealth:

&nbsp;   """Check database connectivity and response time."""

&nbsp;   start = time.perf\_counter()

&nbsp;   try:

&nbsp;       async with engine.connect() as conn:

&nbsp;           result = await conn.execute(text("SELECT 1"))

&nbsp;           result.scalar()

&nbsp;       latency = (time.perf\_counter() - start) \* 1000



&nbsp;       status = "healthy" if latency < 100 else "degraded"

&nbsp;       return ComponentHealth(

&nbsp;           name="database",

&nbsp;           status=status,

&nbsp;           latency\_ms=round(latency, 2),

&nbsp;           details={"pool\_size": engine.pool.size(), "checked\_out": engine.pool.checkedout()},

&nbsp;       )

&nbsp;   except Exception as e:

&nbsp;       latency = (time.perf\_counter() - start) \* 1000

&nbsp;       logger.error("Database health check failed: %s", str(e))

&nbsp;       return ComponentHealth(

&nbsp;           name="database",

&nbsp;           status="unhealthy",

&nbsp;           latency\_ms=round(latency, 2),

&nbsp;           error=str(e)\[:200],

&nbsp;       )



async def check\_storage\_health(storage: StorageBackend) -> ComponentHealth:

&nbsp;   """Check storage backend connectivity."""

&nbsp;   start = time.perf\_counter()

&nbsp;   try:

&nbsp;       await storage.list\_files("", area="inputs")

&nbsp;       latency = (time.perf\_counter() - start) \* 1000

&nbsp;       return ComponentHealth(

&nbsp;           name="storage",

&nbsp;           status="healthy",

&nbsp;           latency\_ms=round(latency, 2),

&nbsp;           details={"backend": type(storage).\_\_name\_\_},

&nbsp;       )

&nbsp;   except Exception as e:

&nbsp;       latency = (time.perf\_counter() - start) \* 1000

&nbsp;       logger.error("Storage health check failed: %s", str(e))

&nbsp;       return ComponentHealth(

&nbsp;           name="storage",

&nbsp;           status="unhealthy",

&nbsp;           latency\_ms=round(latency, 2),

&nbsp;           error=str(e)\[:200],

&nbsp;       )



def check\_system\_health() -> ComponentHealth:

&nbsp;   """Check system resource usage."""

&nbsp;   try:

&nbsp;       memory = psutil.virtual\_memory()

&nbsp;       disk = psutil.disk\_usage("/")

&nbsp;       cpu\_percent = psutil.cpu\_percent(interval=0.1)



&nbsp;       status = "healthy"

&nbsp;       if memory.percent > 90 or disk.percent > 90:

&nbsp;           status = "degraded"

&nbsp;       if memory.percent > 95 or disk.percent > 95:

&nbsp;           status = "unhealthy"



&nbsp;       return ComponentHealth(

&nbsp;           name="system",

&nbsp;           status=status,

&nbsp;           latency\_ms=0,

&nbsp;           details={

&nbsp;               "cpu\_percent": cpu\_percent,

&nbsp;               "memory\_percent": round(memory.percent, 1),

&nbsp;               "memory\_available\_mb": round(memory.available / (1024 \* 1024), 0),

&nbsp;               "disk\_percent": round(disk.percent, 1),

&nbsp;               "disk\_free\_gb": round(disk.free / (1024  1024  1024), 1),

&nbsp;           },

&nbsp;       )

&nbsp;   except Exception as e:

&nbsp;       return ComponentHealth(

&nbsp;           name="system",

&nbsp;           status="degraded",

&nbsp;           latency\_ms=0,

&nbsp;           error=str(e)\[:200],

&nbsp;       )



async def get\_full\_health(storage: StorageBackend) -> dict:

&nbsp;   """Run all health checks and return aggregated status."""

&nbsp;   settings = get\_settings()

&nbsp;   components = \[]



&nbsp;   # Database

&nbsp;   db\_health = await check\_database\_health()

&nbsp;   components.append(db\_health)



&nbsp;   # Storage

&nbsp;   storage\_health = await check\_storage\_health(storage)

&nbsp;   components.append(storage\_health)



&nbsp;   # System

&nbsp;   system\_health = check\_system\_health()

&nbsp;   components.append(system\_health)



&nbsp;   # Aggregate status

&nbsp;   statuses = \[c.status for c in components]

&nbsp;   if "unhealthy" in statuses:

&nbsp;       overall = "unhealthy"

&nbsp;   elif "degraded" in statuses:

&nbsp;       overall = "degraded"

&nbsp;   else:

&nbsp;       overall = "healthy"



&nbsp;   result = {

&nbsp;       "status": overall,

&nbsp;       "timestamp": datetime.now(timezone.utc).isoformat(),

&nbsp;       "uptime\_seconds": (datetime.now(timezone.utc) - \_app\_start\_time).total\_seconds()

&nbsp;           if \_app\_start\_time else 0,

&nbsp;       "version": "1.0.0",

&nbsp;       "environment": settings.ENVIRONMENT,

&nbsp;   }



&nbsp;   if settings.HEALTH\_INCLUDE\_DETAILS:

&nbsp;       result\["components"] = \[

&nbsp;           {

&nbsp;               "name": c.name,

&nbsp;               "status": c.status,

&nbsp;               "latency\_ms": c.latency\_ms,

&nbsp;               ({"details": c.details} if c.details else {}),

&nbsp;               ({"error": c.error} if c.error else {}),

&nbsp;           }

&nbsp;           for c in components

&nbsp;       ]



&nbsp;   return result





Application Metrics (backend/observability/metrics.py)



python

"""

Application metrics collection.

Tracks request counts, error rates, latency percentiles, and business metrics.

Stored in-memory; suitable for single-instance or scraping via /admin/metrics.

"""

import time

import threading

from collections import defaultdict

from dataclasses import dataclass, field

from datetime import datetime, timezone



@dataclass

class MetricsBucket:

&nbsp;   """Holds metrics for a time window."""

&nbsp;   request\_count: int = 0

&nbsp;   error\_count: int = 0

&nbsp;   latencies: list\[float] = field(default\_factory=list)

&nbsp;   status\_codes: dict\[int, int] = field(default\_factory=lambda: defaultdict(int))

&nbsp;   endpoints: dict\[str, int] = field(default\_factory=lambda: defaultdict(int))



class MetricsCollector:

&nbsp;   """Thread-safe in-memory metrics collector."""



&nbsp;   def \_\_init\_\_(self):

&nbsp;       self.\_lock = threading.Lock()

&nbsp;       self.\_current = MetricsBucket()

&nbsp;       self.\_total\_requests: int = 0

&nbsp;       self.\_total\_errors: int = 0

&nbsp;       self.\_start\_time = datetime.now(timezone.utc)



&nbsp;       # Pipeline metrics

&nbsp;       self.\_pipeline\_runs: int = 0

&nbsp;       self.\_pipeline\_successes: int = 0

&nbsp;       self.\_pipeline\_failures: int = 0

&nbsp;       self.\_total\_loans\_processed: int = 0



&nbsp;   def record\_request(self, method: str, path: str, status\_code: int, duration\_ms: float):

&nbsp;       with self.\_lock:

&nbsp;           self.\_current.request\_count += 1

&nbsp;           self.\_current.latencies.append(duration\_ms)

&nbsp;           self.\_current.status\_codes\[status\_code] += 1

&nbsp;           self.\_current.endpoints\[f"{method} {path}"] += 1

&nbsp;           self.\_total\_requests += 1

&nbsp;           if status\_code >= 500:

&nbsp;               self.\_current.error\_count += 1

&nbsp;               self.\_total\_errors += 1



&nbsp;   def record\_pipeline\_run(self, success: bool, loans\_count: int = 0):

&nbsp;       with self.\_lock:

&nbsp;           self.\_pipeline\_runs += 1

&nbsp;           if success:

&nbsp;               self.\_pipeline\_successes += 1

&nbsp;           else:

&nbsp;               self.\_pipeline\_failures += 1

&nbsp;           self.\_total\_loans\_processed += loans\_count



&nbsp;   def get\_metrics(self) -> dict:

&nbsp;       with self.\_lock:

&nbsp;           latencies = sorted(self.\_current.latencies)

&nbsp;           p50 = latencies\[len(latencies) // 2] if latencies else 0

&nbsp;           p95 = latencies\[int(len(latencies) \* 0.95)] if latencies else 0

&nbsp;           p99 = latencies\[int(len(latencies) \* 0.99)] if latencies else 0



&nbsp;           uptime = (datetime.now(timezone.utc) - self.\_start\_time).total\_seconds()



&nbsp;           return {

&nbsp;               "uptime\_seconds": round(uptime, 0),

&nbsp;               "requests": {

&nbsp;                   "total": self.\_total\_requests,

&nbsp;                   "current\_window": self.\_current.request\_count,

&nbsp;                   "errors\_total": self.\_total\_errors,

&nbsp;                   "error\_rate": round(

&nbsp;                       self.\_total\_errors / max(self.\_total\_requests, 1) \* 100, 2

&nbsp;                   ),

&nbsp;               },

&nbsp;               "latency\_ms": {

&nbsp;                   "p50": round(p50, 2),

&nbsp;                   "p95": round(p95, 2),

&nbsp;                   "p99": round(p99, 2),

&nbsp;               },

&nbsp;               "status\_codes": dict(self.\_current.status\_codes),

&nbsp;               "top\_endpoints": dict(

&nbsp;                   sorted(

&nbsp;                       self.\_current.endpoints.items(),

&nbsp;                       key=lambda x: -x\[1],

&nbsp;                   )\[:10]

&nbsp;               ),

&nbsp;               "pipeline": {

&nbsp;                   "total\_runs": self.\_pipeline\_runs,

&nbsp;                   "successes": self.\_pipeline\_successes,

&nbsp;                   "failures": self.\_pipeline\_failures,

&nbsp;                   "total\_loans\_processed": self.\_total\_loans\_processed,

&nbsp;               },

&nbsp;           }



&nbsp;   def reset\_window(self):

&nbsp;       """Reset current window metrics (call periodically)."""

&nbsp;       with self.\_lock:

&nbsp;           self.\_current = MetricsBucket()



Global singleton

metrics = MetricsCollector()





Admin Diagnostics (backend/admin/diagnostics.py)



python

"""

Admin diagnostic endpoints.

Provides runtime information for debugging and monitoring.

Protected by admin authentication.

"""

import sys

import platform

from datetime import datetime, timezone

from fastapi import APIRouter, Depends



from backend.auth.security import admin\_required

from backend.api.dependencies import get\_storage

from backend.database import engine

from backend.config import get\_settings

from backend.observability.health import get\_full\_health

from backend.observability.metrics import metrics

from backend.models import User



router = APIRouter(prefix="/admin", tags=\["admin"])



@router.get("/health/detailed")

async def detailed\_health(

&nbsp;   current\_user=Depends(admin\_required),

&nbsp;   storage=Depends(get\_storage),

):

&nbsp;   """Extended health check with component details (admin only)."""

&nbsp;   return await get\_full\_health(storage)



@router.get("/metrics")

async def get\_metrics(current\_user=Depends(admin\_required)):

&nbsp;   """Application metrics (admin only)."""

&nbsp;   return metrics.get\_metrics()



@router.get("/config")

async def get\_runtime\_config(current\_user=Depends(admin\_required)):

&nbsp;   """Current runtime configuration (admin only, secrets redacted)."""

&nbsp;   settings = get\_settings()

&nbsp;   return {

&nbsp;       "app\_name": settings.APP\_NAME,

&nbsp;       "environment": settings.ENVIRONMENT,

&nbsp;       "debug": settings.DEBUG,

&nbsp;       "storage\_type": settings.STORAGE\_TYPE,

&nbsp;       "log\_level": settings.LOG\_LEVEL,

&nbsp;       "log\_format": settings.LOG\_FORMAT,

&nbsp;       "rate\_limit\_enabled": settings.RATE\_LIMIT\_ENABLED,

&nbsp;       "db\_pool\_size": settings.DB\_POOL\_SIZE,

&nbsp;       "db\_max\_overflow": settings.DB\_MAX\_OVERFLOW,

&nbsp;       "slow\_request\_threshold\_ms": settings.SLOW\_REQUEST\_THRESHOLD\_MS,

&nbsp;       "request\_timeout\_seconds": settings.REQUEST\_TIMEOUT\_SECONDS,

&nbsp;   }



@router.get("/info")

async def system\_info(current\_user=Depends(admin\_required)):

&nbsp;   """System and runtime information (admin only)."""

&nbsp;   return {

&nbsp;       "python\_version": sys.version,

&nbsp;       "platform": platform.platform(),

&nbsp;       "architecture": platform.machine(),

&nbsp;       "timestamp": datetime.now(timezone.utc).isoformat(),

&nbsp;       "database": {

&nbsp;           "pool\_size": engine.pool.size(),

&nbsp;           "checked\_out": engine.pool.checkedout(),

&nbsp;           "overflow": engine.pool.overflow(),

&nbsp;           "checked\_in": engine.pool.checkedin(),

&nbsp;       },

&nbsp;   }



@router.post("/metrics/reset")

async def reset\_metrics(current\_user=Depends(admin\_required)):

&nbsp;   """Reset current window metrics (admin only)."""

&nbsp;   metrics.reset\_window()

&nbsp;   return {"status": "metrics reset"}





Admin CLI (backend/admin/cli.py)



python

"""

Admin CLI commands for operational tasks.

Run as: python -m backend.admin.cli <command>

"""

import asyncio

import argparse

import sys

from datetime import datetime, timezone



from sqlalchemy import select, func



from backend.database import async\_session\_factory, engine, Base

from backend.models import User, PipelineRun, LoanException, LoanFact, SalesTeam

from backend.auth.security import hash\_password



async def cmd\_list\_users():

&nbsp;   """List all users."""

&nbsp;   async with async\_session\_factory() as session:

&nbsp;       result = await session.execute(select(User).order\_by(User.id))

&nbsp;       users = result.scalars().all()

&nbsp;       print(f"\\n{'ID':>4}  {'Username':<20} {'Email':<30} {'Role':<12} {'Active':<8} {'Team'}")

&nbsp;       print("-" \* 90)

&nbsp;       for u in users:

&nbsp;           print(f"{u.id:>4}  {u.username:<20} {u.email:<30} {u.role:<12} "

&nbsp;                 f"{'Yes' if u.is\_active else 'No':<8} {u.sales\_team\_id or '-'}")

&nbsp;       print(f"\\nTotal: {len(users)} users")



async def cmd\_reset\_password(username: str, new\_password: str):

&nbsp;   """Reset a user's password."""

&nbsp;   async with async\_session\_factory() as session:

&nbsp;       result = await session.execute(select(User).where(User.username == username))

&nbsp;       user = result.scalar\_one\_or\_none()

&nbsp;       if not user:

&nbsp;           print(f"User '{username}' not found.")

&nbsp;           return

&nbsp;       user.hashed\_password = hash\_password(new\_password)

&nbsp;       await session.commit()

&nbsp;       print(f"Password reset for '{username}'.")



async def cmd\_run\_stats():

&nbsp;   """Show pipeline run statistics."""

&nbsp;   async with async\_session\_factory() as session:

&nbsp;       total = await session.execute(select(func.count(PipelineRun.id)))

&nbsp;       completed = await session.execute(

&nbsp;           select(func.count(PipelineRun.id)).where(PipelineRun.status == "completed")

&nbsp;       )

&nbsp;       failed = await session.execute(

&nbsp;           select(func.count(PipelineRun.id)).where(PipelineRun.status == "failed")

&nbsp;       )

&nbsp;       total\_loans = await session.execute(select(func.sum(PipelineRun.total\_loans)))

&nbsp;       total\_exceptions = await session.execute(select(func.count(LoanException.id)))



&nbsp;       print(f"\\n=== Pipeline Run Statistics ===")

&nbsp;       print(f"Total runs:       {total.scalar() or 0}")

&nbsp;       print(f"Completed:        {completed.scalar() or 0}")

&nbsp;       print(f"Failed:           {failed.scalar() or 0}")

&nbsp;       print(f"Total loans:      {total\_loans.scalar() or 0}")

&nbsp;       print(f"Total exceptions: {total\_exceptions.scalar() or 0}")



async def cmd\_db\_status():

&nbsp;   """Show database connection status."""

&nbsp;   print(f"\\n=== Database Status ===")

&nbsp;   print(f"Pool size:       {engine.pool.size()}")

&nbsp;   print(f"Checked out:     {engine.pool.checkedout()}")

&nbsp;   print(f"Overflow:        {engine.pool.overflow()}")

&nbsp;   print(f"Checked in:      {engine.pool.checkedin()}")



&nbsp;   try:

&nbsp;       from sqlalchemy import text

&nbsp;       async with engine.connect() as conn:

&nbsp;           result = await conn.execute(text("SELECT version()"))

&nbsp;           version = result.scalar()

&nbsp;           print(f"Server version:  {version}")

&nbsp;           print(f"Connection:      OK")

&nbsp;   except Exception as e:

&nbsp;       print(f"Connection:      FAILED — {e}")



def main():

&nbsp;   parser = argparse.ArgumentParser(description="Loan Engine Admin CLI")

&nbsp;   subparsers = parser.add\_subparsers(dest="command")



&nbsp;   subparsers.add\_parser("list-users", help="List all users")



&nbsp;   reset\_pw = subparsers.add\_parser("reset-password", help="Reset user password")

&nbsp;   reset\_pw.add\_argument("username", help="Username")

&nbsp;   reset\_pw.add\_argument("password", help="New password")



&nbsp;   subparsers.add\_parser("run-stats", help="Pipeline run statistics")

&nbsp;   subparsers.add\_parser("db-status", help="Database connection status")



&nbsp;   args = parser.parse\_args()



&nbsp;   if not args.command:

&nbsp;       parser.print\_help()

&nbsp;       return



&nbsp;   commands = {

&nbsp;       "list-users": lambda: cmd\_list\_users(),

&nbsp;       "reset-password": lambda: cmd\_reset\_password(args.username, args.password),

&nbsp;       "run-stats": lambda: cmd\_run\_stats(),

&nbsp;       "db-status": lambda: cmd\_db\_status(),

&nbsp;   }



&nbsp;   asyncio.run(commands\[args.command]())



if \_\_name\_\_ == "\_\_main\_\_":

&nbsp;   main()





Updated main.py (backend/api/main.py)



Modify the existing main.py to wire in all middleware and observability.

Keep all existing functionality (routers, health endpoints, static mount).



Add these changes:



python

─── Additions to main.py ───────────────────────────────

1\. In the lifespan handler, BEFORE yield:

from backend.observability.logging\_config import configure\_logging

from backend.observability.health import set\_app\_start\_time

from backend.middleware.rate\_limiter import configure\_rate\_limits



Inside lifespan():

configure\_logging(settings.LOG\_LEVEL, settings.LOG\_FORMAT)

set\_app\_start\_time()

configure\_rate\_limits(settings)

logger.info("Application started", extra={

&nbsp;   "environment": settings.ENVIRONMENT,

&nbsp;   "storage\_type": settings.STORAGE\_TYPE,

})

2\. After app creation, ADD middleware (order matters — first added = outermost):

from backend.middleware.security\_headers import SecurityHeadersMiddleware

from backend.middleware.request\_id import RequestIDMiddleware

from backend.middleware.timing import TimingMiddleware

from backend.middleware.logging\_middleware import LoggingMiddleware

from backend.middleware.rate\_limiter import RateLimitMiddleware



Middleware stack (outermost to innermost):

if settings.ENABLE\_SECURITY\_HEADERS:

&nbsp;   app.add\_middleware(SecurityHeadersMiddleware)

app.add\_middleware(RequestIDMiddleware)

app.add\_middleware(TimingMiddleware)

app.add\_middleware(LoggingMiddleware)

if settings.RATE\_LIMIT\_ENABLED:

&nbsp;   app.add\_middleware(RateLimitMiddleware)

3\. Register exception handlers:

from backend.middleware.error\_handler import (

&nbsp;   http\_exception\_handler,

&nbsp;   validation\_exception\_handler,

&nbsp;   generic\_exception\_handler,

)

from starlette.exceptions import HTTPException as StarletteHTTPException

from fastapi.exceptions import RequestValidationError



app.add\_exception\_handler(StarletteHTTPException, http\_exception\_handler)

app.add\_exception\_handler(RequestValidationError, validation\_exception\_handler)

app.add\_exception\_handler(Exception, generic\_exception\_handler)

4\. Add admin router:

from backend.admin.diagnostics import router as admin\_router

if settings.ADMIN\_DIAGNOSTICS\_ENABLED:

&nbsp;   app.include\_router(admin\_router)

5\. Replace existing /health/ready with extended version:

from backend.observability.health import get\_full\_health



@app.get("/health/ready")

async def health\_ready(storage: StorageBackend = Depends(get\_storage)):

&nbsp;   health = await get\_full\_health(storage)

&nbsp;   status\_code = 200 if health\["status"] != "unhealthy" else 503

&nbsp;   from fastapi.responses import JSONResponse

&nbsp;   return JSONResponse(status\_code=status\_code, content=health)





Updated database.py (backend/database.py)



Add connection pool tuning. Keep all existing functionality.



python

─── Replace engine creation with tuned version ─────────



from backend.config import get\_settings



settings = get\_settings()



engine = create\_async\_engine(

&nbsp;   settings.DATABASE\_URL,

&nbsp;   echo=settings.DB\_ECHO\_QUERIES,

&nbsp;   pool\_pre\_ping=True,

&nbsp;   pool\_size=settings.DB\_POOL\_SIZE,

&nbsp;   max\_overflow=settings.DB\_MAX\_OVERFLOW,

&nbsp;   pool\_recycle=settings.DB\_POOL\_RECYCLE,

&nbsp;   pool\_timeout=settings.DB\_POOL\_TIMEOUT,

)





Updated entrypoint.sh



Add graceful shutdown signal handling. Keep all existing functionality

(migration retry, admin seed, data seed).



bash

─── Add at the TOP of entrypoint.sh ────────────────────



Graceful shutdown handler

shutdown() {

&nbsp;   echo ""

&nbsp;   echo "Received shutdown signal. Draining connections..."

&nbsp;   # Send SIGTERM to uvicorn to trigger graceful shutdown

&nbsp;   kill -TERM "$APP\_PID" 2>/dev/null

&nbsp;   # Wait for process to exit (with timeout)

&nbsp;   wait "$APP\_PID"

&nbsp;   echo "Application stopped."

&nbsp;   exit 0

}



trap shutdown SIGTERM SIGINT SIGQUIT



─── Modify the uvicorn exec at the BOTTOM ──────────────



Start in background so we can trap signals

uvicorn backend.api.main:app \\

&nbsp;   --host 0.0.0.0 \\

&nbsp;   --port 8000 \\

&nbsp;   --workers "${WEB\_CONCURRENCY:-1}" \\

&nbsp;   --log-level info \\

&nbsp;   --access-log \\

&nbsp;   --proxy-headers \\

&nbsp;   --forwarded-allow-ips='\*' \\

&nbsp;   --timeout-graceful-shutdown 30 \&



APP\_PID=$!

wait "$APP\_PID"





Test Suite



backend/tests/test\_middleware.py



python

"""

Middleware tests.

Validates request ID, logging, timing, rate limiting, security headers, error handling.

"""



class TestRequestIDMiddleware:

&nbsp;   async def test\_response\_has\_request\_id\_header(self, ...): ...

&nbsp;   async def test\_custom\_request\_id\_preserved(self, ...): ...

&nbsp;   async def test\_request\_id\_is\_valid\_uuid(self, ...): ...

&nbsp;   async def test\_each\_request\_gets\_unique\_id(self, ...): ...



class TestTimingMiddleware:

&nbsp;   async def test\_server\_timing\_header\_present(self, ...): ...

&nbsp;   async def test\_timing\_is\_positive\_number(self, ...): ...



class TestSecurityHeaders:

&nbsp;   async def test\_x\_content\_type\_options(self, ...): ...

&nbsp;   async def test\_x\_frame\_options(self, ...): ...

&nbsp;   async def test\_referrer\_policy(self, ...): ...

&nbsp;   async def test\_permissions\_policy(self, ...): ...

&nbsp;   async def test\_cache\_control(self, ...): ...



class TestRateLimiting:

&nbsp;   async def test\_under\_limit\_allowed(self, ...): ...

&nbsp;   async def test\_over\_limit\_returns\_429(self, ...): ...

&nbsp;   async def test\_rate\_limit\_headers\_present(self, ...): ...

&nbsp;   async def test\_retry\_after\_header\_on\_429(self, ...): ...

&nbsp;   async def test\_different\_ips\_have\_separate\_limits(self, ...): ...

&nbsp;   async def test\_health\_endpoints\_not\_rate\_limited(self, ...): ...



class TestErrorHandler:

&nbsp;   async def test\_404\_returns\_structured\_error(self, ...): ...

&nbsp;   async def test\_422\_returns\_safe\_validation\_error(self, ...): ...

&nbsp;   async def test\_500\_does\_not\_expose\_stack\_trace(self, ...): ...

&nbsp;   async def test\_error\_response\_includes\_request\_id(self, ...): ...



backend/tests/test\_observability.py



python

"""

Observability tests.

Validates health checks, metrics, logging configuration, and admin endpoints.

"""



class TestHealthChecks:

&nbsp;   async def test\_health\_returns\_200(self, ...): ...

&nbsp;   async def test\_health\_ready\_includes\_components(self, ...): ...

&nbsp;   async def test\_health\_ready\_includes\_uptime(self, ...): ...

&nbsp;   async def test\_health\_ready\_includes\_version(self, ...): ...

&nbsp;   async def test\_health\_ready\_503\_when\_db\_down(self, ...): ...



class TestMetrics:

&nbsp;   def test\_record\_request(self, ...): ...

&nbsp;   def test\_error\_rate\_calculation(self, ...): ...

&nbsp;   def test\_latency\_percentiles(self, ...): ...

&nbsp;   def test\_pipeline\_metrics(self, ...): ...

&nbsp;   def test\_reset\_window(self, ...): ...



class TestAdminEndpoints:

&nbsp;   async def test\_admin\_metrics\_requires\_auth(self, ...): ...

&nbsp;   async def test\_admin\_metrics\_requires\_admin\_role(self, ...): ...

&nbsp;   async def test\_admin\_health\_detailed(self, ...): ...

&nbsp;   async def test\_admin\_config\_redacts\_secrets(self, ...): ...

&nbsp;   async def test\_admin\_system\_info(self, ...): ...



class TestLoggingConfig:

&nbsp;   def test\_json\_formatter\_output(self, ...): ...

&nbsp;   def test\_json\_formatter\_includes\_request\_id(self, ...): ...

&nbsp;   def test\_text\_formatter\_output(self, ...): ...

&nbsp;   def test\_configure\_logging\_sets\_levels(self, ...): ...



backend/tests/test\_hardening.py



python

"""

Production hardening tests.

Validates the application is ready for production traffic.

"""



class TestDatabasePooling:

&nbsp;   async def test\_pool\_settings\_applied(self, ...): ...

&nbsp;   async def test\_connection\_recycling(self, ...): ...



class TestGracefulBehavior:

&nbsp;   async def test\_concurrent\_requests\_handled(self, ...): ...

&nbsp;   async def test\_large\_response\_streamed(self, ...): ...



class TestRequestValidation:

&nbsp;   async def test\_invalid\_json\_returns\_422(self, ...): ...

&nbsp;   async def test\_missing\_required\_fields\_returns\_422(self, ...): ...

&nbsp;   async def test\_wrong\_field\_types\_returns\_422(self, ...): ...



class TestPathUtils:

&nbsp;   def test\_safe\_join\_with\_production\_paths(self, ...): ...

&nbsp;   def test\_sanitize\_filename\_edge\_cases(self, ...): ...



class TestAdminCLI:

&nbsp;   async def test\_list\_users\_command(self, ...): ...

&nbsp;   async def test\_run\_stats\_command(self, ...): ...

&nbsp;   async def test\_db\_status\_command(self, ...): ...





Updated .env.example



Add new configuration variables to the existing .env.example:



env

─── Append to existing .env.example ────────────────────



--- Logging ---

LOG\_LEVEL=INFO                        # DEBUG | INFO | WARNING | ERROR

LOG\_FORMAT=json                       # json | text



--- Rate Limiting ---

RATE\_LIMIT\_ENABLED=true

RATE\_LIMIT\_LOGIN=10/minute

RATE\_LIMIT\_REGISTER=5/minute

RATE\_LIMIT\_PIPELINE=5/minute

RATE\_LIMIT\_API=100/minute

RATE\_LIMIT\_UPLOAD=20/minute



--- Performance ---

REQUEST\_TIMEOUT\_SECONDS=300

SLOW\_REQUEST\_THRESHOLD\_MS=1000

MAX\_REQUEST\_SIZE\_MB=100



--- Database Pool ---

DB\_POOL\_SIZE=10

DB\_MAX\_OVERFLOW=20

DB\_POOL\_RECYCLE=3600

DB\_POOL\_TIMEOUT=30

DB\_ECHO\_QUERIES=false

DB\_SLOW\_QUERY\_MS=500



--- Health Checks ---

HEALTH\_CHECK\_TIMEOUT=5

HEALTH\_INCLUDE\_DETAILS=true



--- Security ---

ENABLE\_SECURITY\_HEADERS=true



--- Admin ---

ADMIN\_DIAGNOSTICS\_ENABLED=true





Updated requirements.txt / pyproject.toml



Add new dependency:





psutil>=5.9.0



Add to pyproject.toml under dependencies:



toml

&nbsp;   "psutil>=5.9.0",





Validation Criteria for Phase 7



After implementation, ALL must pass:

1\. uvicorn starts without errors with all middleware active

2\. Every response includes X-Request-ID header

3\. Every response includes Server-Timing header

4\. Every response includes security headers (X-Content-Type-Options, X-Frame-Options, etc.)

5\. GET /health returns 200 with status "ok"

6\. GET /health/ready returns component-level health (database, storage, system)

7\. GET /health/ready returns 503 when database is unreachable

8\. Health response includes uptime\_seconds and version

9\. Login endpoint rate limits after 10 requests/minute (returns 429)

10\. 429 responses include Retry-After header

11\. Rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining) present on API responses

12\. Unhandled exceptions return generic 500 without stack traces

13\. Validation errors return structured 422 without raw input values

14\. Error responses include request\_id

15\. JSON logging produces valid JSON lines with all expected fields

16\. Slow request warnings logged for requests exceeding threshold

17\. GET /admin/metrics returns request counts and latency percentiles (admin only)

18\. GET /admin/health/detailed returns full component health (admin only)

19\. GET /admin/config returns config with secrets redacted (admin only)

20\. Non-admin users get 403 on /admin/\* endpoints

21\. python -m backend.admin.cli list-users runs without errors

22\. python -m backend.admin.cli db-status shows connection info

23\. All existing tests (300+) still pass (no regressions)

24\. pytest backend/tests/test\_middleware.py — all pass

25\. pytest backend/tests/test\_observability.py — all pass

26\. pytest backend/tests/test\_hardening.py — all pass

27\. ruff check backend/ — no lint errors

28\. deploy/entrypoint.sh handles SIGTERM gracefully



Run validation:



bash

All new tests

pytest backend/tests/test\_middleware.py backend/tests/test\_observability.py backend/tests/test\_hardening.py -v --tb=short



Full regression (all 300+ existing tests still pass)

pytest backend/tests/ -v --tb=short --timeout=30



Lint

ruff check backend/



CLI commands

python -m backend.admin.cli list-users

python -m backend.admin.cli db-status



Middleware verification (start server, check headers)

In one terminal:

uvicorn backend.api.main:app --port 8000

In another:

curl -v http://localhost:8000/health 2>\&1 | grep -E "X-Request-ID|Server-Timing|X-Content-Type"





Chunking Guide (if prompt exceeds context limits)



| Chunk | File(s) | Focus |

|-------|---------|-------|

| 7a | backend/observability/logging\_config.py | JSON/text formatters, context vars, configure\_logging() |

| 7b | backend/middleware/request\_id.py, backend/middleware/timing.py, backend/middleware/security\_headers.py | Lightweight middleware |

| 7c | backend/middleware/logging\_middleware.py, backend/middleware/error\_handler.py | Request logging + exception handling |

| 7d | backend/middleware/rate\_limiter.py | Rate limiting with sliding window |

| 7e | backend/observability/health.py, backend/observability/metrics.py | Health checks + metrics |

| 7f | backend/admin/diagnostics.py, backend/admin/cli.py | Admin endpoints + CLI |

| 7g | backend/api/main.py modifications, backend/database.py modifications, backend/config.py additions | Wiring everything together |

| 7h | All test files | test\_middleware, test\_observability, test\_hardening |



Prepend specs/context/project-context.md + specs/context/phase6-output-summary.md.



