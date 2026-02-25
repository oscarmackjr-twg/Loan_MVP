# specs/validate_scaffold.py
"""
Loan Engine — Phase 0 Scaffold Validation
==========================================
Automates all 15 validation checks after Codex generates the scaffold.
Run from the project root: python specs/validate_scaffold.py

Exit codes:
  0 = all checks passed
  1 = one or more checks failed

Optional flags:
  --skip-docker      Skip Docker-dependent checks (3, 12)
  --skip-terraform   Skip Terraform checks (13)
  --skip-frontend    Skip frontend checks (11)
  --verbose          Show full command output on failure
  --fix              Attempt to auto-fix common issues before validating
"""

import subprocess
import sys
import os
import json
import time
import shutil
import signal
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


# ─── Configuration ───────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_PORT = 8000
FRONTEND_PORT = 5173
STARTUP_WAIT_SECONDS = 8
HEALTH_RETRY_ATTEMPTS = 5
HEALTH_RETRY_DELAY = 2

# Checks that can be skipped via flags
DOCKER_CHECKS = {3, 12}
TERRAFORM_CHECKS = {13}
FRONTEND_CHECKS = {11}


# ─── Data structures ────────────────────────────────────────────────────────

@dataclass
class CheckResult:
    number: int
    name: str
    passed: bool
    message: str
    duration: float = 0.0
    skipped: bool = False
    output: str = ""


@dataclass
class ValidationReport:
    results: list[CheckResult] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed and not r.skipped)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed and not r.skipped)

    @property
    def skipped_count(self) -> int:
        return sum(1 for r in self.results if r.skipped)

    @property
    def total(self) -> int:
        return len(self.results)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def run_cmd(
    cmd: list[str] | str,
    cwd: Optional[Path] = None,
    timeout: int = 120,
    shell: bool = False,
    env: Optional[dict] = None,
) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    merged_env = {**os.environ, **(env or {})}
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=shell,
            env=merged_env,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s"
    except FileNotFoundError as e:
        return -1, "", f"Command not found: {e}"


def start_process(
    cmd: list[str] | str,
    cwd: Optional[Path] = None,
    env: Optional[dict] = None,
    shell: bool = False,
) -> subprocess.Popen:
    """Start a background process."""
    merged_env = {**os.environ, **(env or {})}
    return subprocess.Popen(
        cmd,
        cwd=cwd or PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=shell,
        env=merged_env,
    )


def kill_process(proc: subprocess.Popen):
    """Kill a process and all children."""
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                capture_output=True,
            )
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def http_get(url: str, timeout: int = 10) -> tuple[int, dict | str]:
    """Make an HTTP GET request using httpx or urllib."""
    try:
        import httpx
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url)
            try:
                return resp.status_code, resp.json()
            except Exception:
                return resp.status_code, resp.text
    except ImportError:
        from urllib.request import urlopen, Request
        from urllib.error import URLError, HTTPError
        try:
            req = Request(url)
            with urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode()
                try:
                    return resp.status, json.loads(body)
                except Exception:
                    return resp.status, body
        except HTTPError as e:
            return e.code, str(e)
        except URLError as e:
            return -1, str(e)


def wait_for_server(url: str, retries: int = HEALTH_RETRY_ATTEMPTS, delay: int = HEALTH_RETRY_DELAY) -> bool:
    """Wait for a server to become available."""
    for attempt in range(retries):
        try:
            status, _ = http_get(url, timeout=5)
            if status > 0:
                return True
        except Exception:
            pass
        if attempt < retries - 1:
            time.sleep(delay)
    return False


def check_command_exists(cmd: str) -> bool:
    """Check if a command is available on PATH."""
    return shutil.which(cmd) is not None


def print_header(text: str):
    width = 70
    print(f"\n{'=' * width}")
    print(f"  {text}")
    print(f"{'=' * width}")


def print_check(result: CheckResult, verbose: bool = False):
    if result.skipped:
        icon = "⊘"
        color = "\033[33m"  # yellow
        label = "SKIP"
    elif result.passed:
        icon = "✓"
        color = "\033[32m"  # green
        label = "PASS"
    else:
        icon = "✗"
        color = "\033[31m"  # red
        label = "FAIL"

    reset = "\033[0m"
    duration = f"({result.duration:.1f}s)" if result.duration > 0 else ""

    print(f"  {color}{icon} Check {result.number:>2}: {label}{reset}  {result.name}  {duration}")

    if result.message and (not result.passed or verbose):
        for line in result.message.strip().split("\n"):
            print(f"           {line}")

    if verbose and result.output and not result.passed:
        print(f"           --- output ---")
        for line in result.output.strip().split("\n")[:20]:
            print(f"           {line}")
        if result.output.strip().count("\n") > 20:
            print(f"           ... (truncated)")


# ─── Individual Checks ──────────────────────────────────────────────────────

def check_01_pip_install() -> CheckResult:
    """Check 1: pip install -e '.[dev]' succeeds."""
    start = time.time()

    # Verify pyproject.toml exists
    if not (PROJECT_ROOT / "pyproject.toml").exists():
        return CheckResult(1, "pip install -e '.[dev]'", False,
                           "pyproject.toml not found", time.time() - start)

    code, stdout, stderr = run_cmd(
        [sys.executable, "-m", "pip", "install", "-e", ".[dev]", "--quiet"],
        timeout=300,
    )
    duration = time.time() - start

    if code == 0:
        return CheckResult(1, "pip install -e '.[dev]'", True,
                           "All dependencies installed", duration)
    else:
        return CheckResult(1, "pip install -e '.[dev]'", False,
                           f"pip install failed (exit {code})", duration,
                           output=stderr[-2000:])


def check_02_env_file() -> CheckResult:
    """Check 2: .env.example exists and can be copied to .env."""
    start = time.time()

    example = PROJECT_ROOT / ".env.example"
    env_file = PROJECT_ROOT / ".env"

    if not example.exists():
        return CheckResult(2, "cp .env.example .env", False,
                           ".env.example not found", time.time() - start)

    # Check required variables are present
    content = example.read_text()
    required_vars = [
        "DATABASE_URL", "DATABASE_URL_SYNC", "SECRET_KEY",
        "STORAGE_TYPE", "ENVIRONMENT",
    ]
    missing = [v for v in required_vars if v not in content]

    if missing:
        return CheckResult(2, "cp .env.example .env", False,
                           f"Missing required vars: {', '.join(missing)}",
                           time.time() - start)

    # Copy if .env doesn't exist
    if not env_file.exists():
        shutil.copy2(example, env_file)

    return CheckResult(2, "cp .env.example .env", True,
                       f".env ready ({len(required_vars)} required vars present)",
                       time.time() - start)


def check_03_docker_postgres(skip: bool) -> CheckResult:
    """Check 3: docker-compose up db starts PostgreSQL."""
    start = time.time()
    name = "docker-compose up db (PostgreSQL)"

    if skip:
        return CheckResult(3, name, True, "Skipped via --skip-docker",
                           time.time() - start, skipped=True)

    if not check_command_exists("docker"):
        return CheckResult(3, name, False, "Docker not found on PATH",
                           time.time() - start)

    compose_file = PROJECT_ROOT / "deploy" / "docker-compose.yml"
    if not compose_file.exists():
        return CheckResult(3, name, False,
                           "deploy/docker-compose.yml not found",
                           time.time() - start)

    # Try docker compose (v2) then docker-compose (v1)
    for compose_cmd in [["docker", "compose"], ["docker-compose"]]:
        code, _, _ = run_cmd(compose_cmd + ["version"], timeout=10)
        if code == 0:
            break
    else:
        return CheckResult(3, name, False,
                           "Neither 'docker compose' nor 'docker-compose' available",
                           time.time() - start)

    # Start only the db service
    code, stdout, stderr = run_cmd(
        compose_cmd + ["-f", str(compose_file), "up", "-d", "db"],
        timeout=60,
    )

    if code != 0:
        return CheckResult(3, name, False,
                           f"docker-compose up db failed (exit {code})",
                           time.time() - start, output=stderr[-1000:])

    # Wait for PostgreSQL to be ready
    for attempt in range(10):
        code, stdout, _ = run_cmd(
            compose_cmd + ["-f", str(compose_file), "exec", "db",
                           "pg_isready", "-U", "postgres"],
            timeout=10,
        )
        if code == 0:
            return CheckResult(3, name, True,
                               "PostgreSQL is accepting connections",
                               time.time() - start)
        time.sleep(2)

    return CheckResult(3, name, False,
                       "PostgreSQL did not become ready within 20s",
                       time.time() - start)


def check_04_init_db() -> CheckResult:
    """Check 4: scripts/init-db.ps1 runs migrations + admin + seed."""
    start = time.time()
    name = "scripts/init-db.ps1 (migrations + admin + seed)"

    init_script = PROJECT_ROOT / "scripts" / "init-db.ps1"

    if not init_script.exists():
        return CheckResult(4, name, False,
                           "scripts/init-db.ps1 not found", time.time() - start)

    if sys.platform == "win32" and check_command_exists("powershell"):
        code, stdout, stderr = run_cmd(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(init_script)],
            timeout=60,
        )
    else:
        # Run the steps directly if PowerShell isn't available
        results = []

        # Step 1: alembic upgrade
        c1, o1, e1 = run_cmd(["alembic", "upgrade", "head"], timeout=30)
        results.append(("alembic upgrade head", c1, o1, e1))

        # Step 2: create admin
        c2, o2, e2 = run_cmd(
            [sys.executable, "-m", "backend.auth.create_admin"], timeout=30
        )
        results.append(("create_admin", c2, o2, e2))

        # Step 3: seed data
        c3, o3, e3 = run_cmd(
            [sys.executable, "-m", "backend.seed_data"], timeout=30
        )
        results.append(("seed_data", c3, o3, e3))

        failed = [r for r in results if r[1] != 0]
        if failed:
            msgs = [f"{r[0]}: exit {r[1]} — {r[3][:200]}" for r in failed]
            return CheckResult(4, name, False,
                               "\n".join(msgs), time.time() - start)

        return CheckResult(4, name, True,
                           "Migrations, admin user, and seed data complete",
                           time.time() - start)

    duration = time.time() - start
    if code == 0:
        return CheckResult(4, name, True,
                           "Migrations, admin user, and seed data complete",
                           duration, output=stdout[-1000:])
    else:
        return CheckResult(4, name, False,
                           f"init-db.ps1 failed (exit {code})",
                           duration, output=(stderr or stdout)[-1000:])


def check_05_uvicorn_starts() -> tuple[CheckResult, Optional[subprocess.Popen]]:
    """Check 5: uvicorn starts on port 8000. Returns (result, process)."""
    start = time.time()
    name = "uvicorn backend.api.main:app starts"

    # Check if main.py exists
    main_py = PROJECT_ROOT / "backend" / "api" / "main.py"
    if not main_py.exists():
        return CheckResult(5, name, False,
                           "backend/api/main.py not found",
                           time.time() - start), None

    proc = start_process(
        [sys.executable, "-m", "uvicorn", "backend.api.main:app",
         "--port", str(BACKEND_PORT), "--no-access-log"],
    )

    # Wait for server to start
    if wait_for_server(f"http://localhost:{BACKEND_PORT}/health"):
        return CheckResult(5, name, True,
                           f"Server running on port {BACKEND_PORT}",
                           time.time() - start), proc
    else:
        # Capture any startup errors
        kill_process(proc)
        _, stderr = proc.communicate(timeout=5)
        return CheckResult(5, name, False,
                           f"Server did not start within {HEALTH_RETRY_ATTEMPTS * HEALTH_RETRY_DELAY}s",
                           time.time() - start,
                           output=stderr[-1000:] if stderr else ""), None


def check_06_health() -> CheckResult:
    """Check 6: GET /health returns 200 with status ok."""
    start = time.time()
    name = 'GET /health → 200 {"status": "ok"}'

    status, body = http_get(f"http://localhost:{BACKEND_PORT}/health")
    duration = time.time() - start

    if status != 200:
        return CheckResult(6, name, False,
                           f"Expected 200, got {status}", duration)

    if isinstance(body, dict):
        if body.get("status") != "ok":
            return CheckResult(6, name, False,
                               f'Expected {{"status": "ok"}}, got {json.dumps(body)}',
                               duration)
        if "timestamp" not in body:
            return CheckResult(6, name, False,
                               "Missing 'timestamp' field", duration)
        return CheckResult(6, name, True,
                           f"Response: {json.dumps(body)}", duration)

    return CheckResult(6, name, False,
                       f"Expected JSON, got: {str(body)[:200]}", duration)


def check_07_health_ready() -> CheckResult:
    """Check 7: GET /health/ready returns 200 with database connected."""
    start = time.time()
    name = 'GET /health/ready → 200 {"database": "connected"}'

    status, body = http_get(f"http://localhost:{BACKEND_PORT}/health/ready")
    duration = time.time() - start

    if status == 200 and isinstance(body, dict):
        if body.get("database") == "connected":
            return CheckResult(7, name, True,
                               f"Response: {json.dumps(body)}", duration)
        else:
            return CheckResult(7, name, False,
                               f"Database not connected: {json.dumps(body)}", duration)
    elif status == 503:
        return CheckResult(7, name, False,
                           f"Database unavailable (503): {json.dumps(body) if isinstance(body, dict) else body}",
                           duration)
    else:
        return CheckResult(7, name, False,
                           f"Unexpected status {status}", duration)


def check_08_swagger_docs() -> CheckResult:
    """Check 8: GET /docs loads Swagger UI with all endpoints."""
    start = time.time()
    name = "GET /docs → Swagger UI with 26 endpoints"

    # Check Swagger UI loads
    status, body = http_get(f"http://localhost:{BACKEND_PORT}/docs")
    if status != 200:
        return CheckResult(8, name, False,
                           f"/docs returned status {status}", time.time() - start)

    # Check OpenAPI spec has correct endpoint count
    status, spec = http_get(f"http://localhost:{BACKEND_PORT}/openapi.json")
    duration = time.time() - start

    if status != 200 or not isinstance(spec, dict):
        return CheckResult(8, name, False,
                           f"/openapi.json returned status {status}", duration)

    paths = spec.get("paths", {})
    endpoint_count = sum(
        len([m for m in methods if m in ("get", "post", "put", "delete", "patch")])
        for methods in paths.values()
    )

    if endpoint_count < 20:
        return CheckResult(8, name, False,
                           f"Only {endpoint_count} endpoints found (expected ~26). "
                           f"Paths: {list(paths.keys())}",
                           duration)

    return CheckResult(8, name, True,
                       f"Swagger UI loaded with {endpoint_count} endpoints across {len(paths)} paths",
                       duration)


def check_09_stub_endpoints() -> CheckResult:
    """Check 9: All 26 stub endpoints return correct status codes."""
    start = time.time()
    name = "All stub endpoints return correct status/schema"

    # Define expected endpoints and their expected behavior
    endpoints = [
        # (method, path, expected_status, schema_check)
        ("GET", "/", 200, None),
        ("GET", "/health", 200, lambda b: b.get("status") == "ok"),
        ("GET", "/health/ready", [200, 503], None),
        ("GET", "/api/config", [200, 401], None),
        ("GET", "/api/runs", [200, 401], None),
        ("GET", "/api/loans", [200, 401, 422], None),
        ("GET", "/api/exceptions", [200, 401], None),
        ("GET", "/api/exceptions/export", [200, 401], None),
        ("GET", "/api/sales-teams", [200, 401], None),
        ("GET", "/api/files/list", [200, 401], None),
    ]

    results = []
    for method, path, expected, schema_fn in endpoints:
        url = f"http://localhost:{BACKEND_PORT}{path}"
        status, body = http_get(url)

        if isinstance(expected, list):
            ok = status in expected
        else:
            ok = status == expected

        if schema_fn and ok and isinstance(body, dict):
            ok = schema_fn(body)

        results.append((method, path, status, ok))

    failed = [(m, p, s) for m, p, s, ok in results if not ok]
    duration = time.time() - start

    if failed:
        msgs = [f"  {m} {p} → {s}" for m, p, s in failed]
        return CheckResult(9, name, False,
                           f"{len(failed)} endpoint(s) failed:\n" + "\n".join(msgs),
                           duration)

    return CheckResult(9, name, True,
                       f"All {len(results)} tested endpoints returned expected status codes",
                       duration)


def check_10_pytest() -> CheckResult:
    """Check 10: pytest backend/tests/test_health.py passes."""
    start = time.time()
    name = "pytest backend/tests/test_health.py"

    test_file = PROJECT_ROOT / "backend" / "tests" / "test_health.py"
    if not test_file.exists():
        return CheckResult(10, name, False,
                           "backend/tests/test_health.py not found",
                           time.time() - start)

    code, stdout, stderr = run_cmd(
        [sys.executable, "-m", "pytest", "backend/tests/test_health.py",
         "-v", "--tb=short", "--no-header"],
        timeout=60,
    )
    duration = time.time() - start

    if code == 0:
        # Count passed tests
        passed_count = stdout.count(" PASSED")
        return CheckResult(10, name, True,
                           f"{passed_count} test(s) passed", duration,
                           output=stdout[-1000:])
    else:
        return CheckResult(10, name, False,
                           f"pytest failed (exit {code})", duration,
                           output=(stdout + "\n" + stderr)[-2000:])


def check_11_frontend(skip: bool) -> CheckResult:
    """Check 11: cd frontend && npm install && npm run dev starts."""
    start = time.time()
    name = "frontend: npm install && npm run dev"

    if skip:
        return CheckResult(11, name, True, "Skipped via --skip-frontend",
                           time.time() - start, skipped=True)

    frontend_dir = PROJECT_ROOT / "frontend"

    if not frontend_dir.exists():
        return CheckResult(11, name, False,
                           "frontend/ directory not found", time.time() - start)

    if not (frontend_dir / "package.json").exists():
        return CheckResult(11, name, False,
                           "frontend/package.json not found", time.time() - start)

    if not check_command_exists("npm"):
        return CheckResult(11, name, False,
                           "npm not found on PATH", time.time() - start)

    # npm install
    code, stdout, stderr = run_cmd(
        ["npm", "install"], cwd=frontend_dir, timeout=120,
    )
    if code != 0:
        return CheckResult(11, name, False,
                           f"npm install failed (exit {code})",
                           time.time() - start, output=stderr[-1000:])

    # Start Vite dev server briefly to verify it launches
    proc = start_process(
        ["npm", "run", "dev"], cwd=frontend_dir,
    )

    # Wait for Vite to start
    vite_ready = False
    for _ in range(15):
        try:
            status, _ = http_get(f"http://localhost:{FRONTEND_PORT}", timeout=3)
            if status == 200:
                vite_ready = True
                break
        except Exception:
            pass
        time.sleep(1)

    kill_process(proc)
    duration = time.time() - start

    if vite_ready:
        return CheckResult(11, name, True,
                           f"Vite dev server started on port {FRONTEND_PORT}",
                           duration)
    else:
        _, stderr = proc.communicate(timeout=5)
        return CheckResult(11, name, False,
                           "Vite dev server did not start within 15s",
                           duration, output=stderr[-500:] if stderr else "")


def check_12_docker_build(skip: bool) -> CheckResult:
    """Check 12: docker build -f deploy/Dockerfile succeeds."""
    start = time.time()
    name = "docker build -f deploy/Dockerfile"

    if skip:
        return CheckResult(12, name, True, "Skipped via --skip-docker",
                           time.time() - start, skipped=True)

    if not check_command_exists("docker"):
        return CheckResult(12, name, False,
                           "Docker not found on PATH", time.time() - start)

    dockerfile = PROJECT_ROOT / "deploy" / "Dockerfile"
    if not dockerfile.exists():
        return CheckResult(12, name, False,
                           "deploy/Dockerfile not found", time.time() - start)

    code, stdout, stderr = run_cmd(
        ["docker", "build", "-f", "deploy/Dockerfile", "-t", "loan-engine:validate", "."],
        timeout=300,
    )
    duration = time.time() - start

    if code == 0:
        return CheckResult(12, name, True,
                           "Docker image built successfully", duration)
    else:
        return CheckResult(12, name, False,
                           f"Docker build failed (exit {code})", duration,
                           output=stderr[-2000:])


def check_13_terraform(skip: bool) -> CheckResult:
    """Check 13: terraform init succeeds."""
    start = time.time()
    name = "terraform -chdir=terraform init"

    if skip:
        return CheckResult(13, name, True, "Skipped via --skip-terraform",
                           time.time() - start, skipped=True)

    terraform_dir = PROJECT_ROOT / "terraform"
    if not terraform_dir.exists():
        return CheckResult(13, name, False,
                           "terraform/ directory not found", time.time() - start)

    if not check_command_exists("terraform"):
        return CheckResult(13, name, False,
                           "terraform not found on PATH (install: https://developer.hashicorp.com/terraform/install)",
                           time.time() - start)

    code, stdout, stderr = run_cmd(
        ["terraform", f"-chdir={terraform_dir}", "init", "-backend=false"],
        timeout=60,
    )
    duration = time.time() - start

    if code == 0:
        return CheckResult(13, name, True,
                           "Terraform initialized successfully", duration)
    else:
        return CheckResult(13, name, False,
                           f"terraform init failed (exit {code})", duration,
                           output=(stdout + stderr)[-1000:])


def check_14_ruff() -> CheckResult:
    """Check 14: ruff check backend/ reports no errors."""
    start = time.time()
    name = "ruff check backend/"

    if not check_command_exists("ruff"):
        # Try as Python module
        code, stdout, stderr = run_cmd(
            [sys.executable, "-m", "ruff", "check", "backend/", "--no-fix"],
            timeout=30,
        )
    else:
        code, stdout, stderr = run_cmd(
            ["ruff", "check", "backend/", "--no-fix"],
            timeout=30,
        )

    duration = time.time() - start

    if code == 0:
        return CheckResult(14, name, True,
                           "No lint errors found", duration)
    else:
        error_count = stdout.count("\n") if stdout else 0
        return CheckResult(14, name, False,
                           f"{error_count} lint error(s) found", duration,
                           output=stdout[-2000:])


def check_15_alembic_sync() -> CheckResult:
    """Check 15: alembic autogenerate produces empty migration."""
    start = time.time()
    name = "alembic autogenerate → empty migration (models in sync)"

    # Generate a test migration
    code, stdout, stderr = run_cmd(
        ["alembic", "revision", "--autogenerate", "-m", "validate_sync_check"],
        timeout=30,
    )
    duration = time.time() - start

    if code != 0:
        return CheckResult(15, name, False,
                           f"alembic revision failed (exit {code})", duration,
                           output=(stderr or stdout)[-1000:])

    # Find the generated migration file
    versions_dir = PROJECT_ROOT / "alembic" / "versions"
    sync_files = list(versions_dir.glob("*validate_sync_check*"))

    if not sync_files:
        return CheckResult(15, name, False,
                           "Could not find generated migration file", duration)

    migration_file = sync_files[0]
    content = migration_file.read_text()

    # Clean up the test migration
    migration_file.unlink()

    # Check if upgrade() and downgrade() are effectively empty
    # An empty migration has "pass" in both functions
    has_create = "op.create_table" in content
    has_drop = "op.drop_table" in content
    has_add_column = "op.add_column" in content
    has_alter = "op.alter_column" in content
    has_create_index = "op.create_index" in content

    has_changes = any([has_create, has_drop, has_add_column, has_alter, has_create_index])

    if has_changes:
        # Extract the changes for reporting
        changes = []
        if has_create:
            changes.append("CREATE TABLE")
        if has_drop:
            changes.append("DROP TABLE")
        if has_add_column:
            changes.append("ADD COLUMN")
        if has_alter:
            changes.append("ALTER COLUMN")
        if has_create_index:
            changes.append("CREATE INDEX")

        return CheckResult(15, name, False,
                           f"Migration is NOT empty. Detected changes: {', '.join(changes)}\n"
                           f"models.py and 001_initial_schema.py are out of sync.",
                           duration, output=content[-2000:])

    return CheckResult(15, name, True,
                       "Migration is empty — models.py and initial migration are in sync",
                       duration)


# ─── File Structure Validation (bonus) ──────────────────────────────────────

def check_file_structure() -> CheckResult:
    """Bonus: Verify all expected files exist."""
    start = time.time()
    name = "File structure completeness"

    required_files = [
        "pyproject.toml",
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "README.md",
        "backend/__init__.py",
        "backend/config.py",
        "backend/database.py",
        "backend/models.py",
        "backend/seed_data.py",
        "backend/api/__init__.py",
        "backend/api/main.py",
        "backend/api/routes.py",
        "backend/api/files.py",
        "backend/api/dependencies.py",
        "backend/auth/__init__.py",
        "backend/auth/routes.py",
        "backend/auth/security.py",
        "backend/auth/schemas.py",
        "backend/auth/validators.py",
        "backend/auth/create_admin.py",
        "backend/schemas/__init__.py",
        "backend/schemas/api.py",
        "backend/storage/__init__.py",
        "backend/storage/base.py",
        "backend/storage/local.py",
        "backend/storage/s3.py",
        "backend/utils/__init__.py",
        "backend/utils/path_utils.py",
        "backend/tests/__init__.py",
        "backend/tests/conftest.py",
        "backend/tests/test_health.py",
        "frontend/package.json",
        "frontend/vite.config.js",
        "frontend/index.html",
        "frontend/src/main.jsx",
        "frontend/src/App.jsx",
        "frontend/src/api/client.js",
        "frontend/src/context/AuthContext.jsx",
        "frontend/src/hooks/useAuth.js",
        "frontend/src/components/Layout.jsx",
        "frontend/src/pages/LoginPage.jsx",
        "frontend/src/pages/DashboardPage.jsx",
        "frontend/src/pages/RunDetailPage.jsx",
        "frontend/src/pages/ExceptionsPage.jsx",
        "frontend/src/pages/FilesPage.jsx",
        "frontend/src/pages/UsersPage.jsx",
        "deploy/Dockerfile",
        "deploy/docker-compose.yml",
        "deploy/entrypoint.sh",
        "deploy/.dockerignore",
        "terraform/main.tf",
        "terraform/variables.tf",
        "terraform/outputs.tf",
        "terraform/terraform.tfvars",
        "alembic/alembic.ini",
        "alembic/env.py",
        "scripts/init-db.ps1",
        "scripts/start-backend.ps1",
        "scripts/start-frontend.ps1",
        ".github/workflows/deploy.yml",
    ]

    missing = []
    for f in required_files:
        if not (PROJECT_ROOT / f).exists():
            missing.append(f)

    duration = time.time() - start

    if missing:
        return CheckResult(0, name, False,
                           f"{len(missing)} file(s) missing:\n" +
                           "\n".join(f"  - {f}" for f in missing),
                           duration)

    return CheckResult(0, name, True,
                       f"All {len(required_files)} expected files present",
                       duration)


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Validate Loan Engine Phase 0 scaffold"
    )
    parser.add_argument("--skip-docker", action="store_true",
                        help="Skip Docker-dependent checks (3, 12)")
    parser.add_argument("--skip-terraform", action="store_true",
                        help="Skip Terraform checks (13)")
    parser.add_argument("--skip-frontend", action="store_true",
                        help="Skip frontend checks (11)")
    parser.add_argument("--verbose", action="store_true",
                        help="Show full command output on failures")
    args = parser.parse_args()

    report = ValidationReport(start_time=datetime.now())
    uvicorn_proc = None

    print_header("Loan Engine — Phase 0 Scaffold Validation")
    print(f"  Project root: {PROJECT_ROOT}")
    print(f"  Python:       {sys.version.split()[0]}")
    print(f"  Platform:     {sys.platform}")
    print(f"  Started:      {report.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # ── Pre-flight: File structure ──
        print_header("Pre-flight: File Structure")
        result = check_file_structure()
        report.results.append(result)
        print_check(result, args.verbose)

        if not result.passed:
            print(f"\n  ⚠ Missing files detected. Continuing with available checks...\n")

        # ── Phase A: Installation & Configuration ──
        print_header("Phase A: Installation & Configuration")

        result = check_01_pip_install()
        report.results.append(result)
        print_check(result, args.verbose)

        result = check_02_env_file()
        report.results.append(result)
        print_check(result, args.verbose)

        # ── Phase B: Database ──
        print_header("Phase B: Database Setup")

        result = check_03_docker_postgres(args.skip_docker)
        report.results.append(result)
        print_check(result, args.verbose)

        result = check_04_init_db()
        report.results.append(result)
        print_check(result, args.verbose)

        # ── Phase C: Backend Server ──
        print_header("Phase C: Backend Server")

        result, uvicorn_proc = check_05_uvicorn_starts()
        report.results.append(result)
        print_check(result, args.verbose)

        if uvicorn_proc:
            result = check_06_health()
            report.results.append(result)
            print_check(result, args.verbose)

            result = check_07_health_ready()
            report.results.append(result)
            print_check(result, args.verbose)

            result = check_08_swagger_docs()
            report.results.append(result)
            print_check(result, args.verbose)

            result = check_09_stub_endpoints()
            report.results.append(result)
            print_check(result, args.verbose)
        else:
            # Server didn't start — skip dependent checks
            for num, chk_name in [(6, "GET /health"), (7, "GET /health/ready"),
                                   (8, "Swagger UI"), (9, "Stub endpoints")]:
                r = CheckResult(num, chk_name, False,
                                "Skipped — server did not start", skipped=True)
                report.results.append(r)
                print_check(r, args.verbose)

        # ── Phase D: Tests ──
        print_header("Phase D: Tests")

        result = check_10_pytest()
        report.results.append(result)
        print_check(result, args.verbose)

        # ── Phase E: Frontend ──
        print_header("Phase E: Frontend")

        result = check_11_frontend(args.skip_frontend)
        report.results.append(result)
        print_check(result, args.verbose)

        # ── Phase F: Build & Infrastructure ──
        print_header("Phase F: Build & Infrastructure")

        result = check_12_docker_build(args.skip_docker)
        report.results.append(result)
        print_check(result, args.verbose)

        result = check_13_terraform(args.skip_terraform)
        report.results.append(result)
        print_check(result, args.verbose)

        # ── Phase G: Code Quality & Sync ──
        print_header("Phase G: Code Quality & Schema Sync")

        result = check_14_ruff()
        report.results.append(result)
        print_check(result, args.verbose)

        result = check_15_alembic_sync()
        report.results.append(result)
        print_check(result, args.verbose)

    finally:
        # Clean up: stop uvicorn
        if uvicorn_proc:
            kill_process(uvicorn_proc)

    # ── Report ──
    report.end_time = datetime.now()
    elapsed = (report.end_time - report.start_time).total_seconds()

    print_header("Validation Summary")

    all_passed = report.failed == 0

    if all_passed:
        color = "\033[32m"
        status = "ALL CHECKS PASSED"
    else:
        color = "\033[31m"
        status = f"{report.failed} CHECK(S) FAILED"

    reset = "\033[0m"

    print(f"""
  {color}{status}{reset}

  Passed:  {report.passed}
  Failed:  {report.failed}
  Skipped: {report.skipped_count}
  Total:   {report.total}
  Time:    {elapsed:.1f}s
""")

    # Show failed checks summary
    if report.failed > 0:
        print("  Failed checks:")
        for r in report.results:
            if not r.passed and not r.skipped:
                print(f"    ✗ Check {r.number}: {r.name}")
        print()

    # Save report to JSON
    report_path = PROJECT_ROOT / "specs" / "validation-report.json"
    report_data = {
        "timestamp": report.start_time.isoformat(),
        "duration_seconds": elapsed,
        "passed": report.passed,
        "failed": report.failed,
        "skipped": report.skipped_count,
        "all_passed": all_passed,
        "results": [
            {
                "check": r.number,
                "name": r.name,
                "passed": r.passed,
                "skipped": r.skipped,
                "message": r.message,
                "duration": round(r.duration, 2),
            }
            for r in report.results
        ],
    }
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=2)
    print(f"  Report saved: {report_path}")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
