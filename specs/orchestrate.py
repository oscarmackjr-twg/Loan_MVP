"""
Loan Engine — Dark Factory Master Orchestration
=================================================
Drives Codex through all generation phases sequentially.
Each phase: generate → validate → summarize → proceed or halt.

Usage:
    python specs/orchestrate.py                    # Run all phases
    python specs/orchestrate.py --start-from 2     # Resume from Phase 2
    python specs/orchestrate.py --phase 1          # Run only Phase 1
    python specs/orchestrate.py --dry-run           # Show plan without executing
    python specs/orchestrate.py --codex-cmd "cursor" # Use different LLM tool
    python specs/orchestrate.py --skip-docker --skip-terraform

Exit codes:
    0 = all phases completed successfully
    1 = a phase failed validation
    2 = configuration or setup error
"""

import subprocess
import sys
import os
import json
import time
import shutil
import argparse
import logging
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Callable
from enum import Enum

─── Configuration ───────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPECS_DIR = PROJECT_ROOT / "specs"
CONTEXT_DIR = SPECS_DIR / "context"
PROMPTS_DIR = SPECS_DIR / "prompts"
REPORTS_DIR = SPECS_DIR / "reports"
BACKUPS_DIR = SPECS_DIR / "backups"

Default Codex command — override with --codex-cmd
DEFAULT_CODEX_CMD = "codex"

Maximum retries per phase before giving up
MAX_PHASE_RETRIES = 2

Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("orchestrator")

─── Data Structures ────────────────────────────────────────────────────

class PhaseStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    VALIDATING = "validating"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class ValidationCheck:
    name: str
    command: list[str] | str
    expected_exit_code: int = 0
    timeout: int = 120
    shell: bool = False
    check_fn: Optional[Callable] = None  # Custom validation function
    required: bool = True  # If False, failure is a warning not a blocker

@dataclass
class PhaseResult:
    phase_number: int
    phase_name: str
    status: PhaseStatus
    generation_time: float = 0.0
    validation_time: float = 0.0
    total_time: float = 0.0
    checks_passed: int = 0
    checks_failed: int = 0
    checks_warned: int = 0
    retry_count: int = 0
    error_message: str = ""
    validation_details: list[dict] = field(default_factory=list)

@dataclass
class OrchestratorReport:
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    phases: list[PhaseResult] = field(default_factory=list)
    overall_status: str = "pending"

    def to_dict(self) -> dict:
        return {
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "overall_status": self.overall_status,
            "total_time": (self.completed_at - self.started_at).total_seconds()
                if self.started_at and self.completed_at else 0,
            "phases": [
                {
                    "phase": p.phase_number,
                    "name": p.phase_name,
                    "status": p.status.value,
                    "generation_time": round(p.generation_time, 1),
                    "validation_time": round(p.validation_time, 1),
                    "total_time": round(p.total_time, 1),
                    "checks_passed": p.checks_passed,
                    "checks_failed": p.checks_failed,
                    "checks_warned": p.checks_warned,
                    "retries": p.retry_count,
                    "error": p.error_message,
                }
                for p in self.phases
            ],
        }

─── Helper Functions ────────────────────────────────────────────────────

def run_cmd(
    cmd: list[str] | str,
    cwd: Optional[Path] = None,
    timeout: int = 120,
    shell: bool = False,
    env: Optional[dict] = None,
    capture: bool = True,
) -> tuple[int, str, str]:
    """Run a command and return (exit_code, stdout, stderr)."""
    merged_env = {os.environ, (env or {})}
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or PROJECT_ROOT,
            capture_output=capture,
            text=True,
            timeout=timeout,
            shell=shell,
            env=merged_env,
        )
        return result.returncode, result.stdout or "", result.stderr or ""
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s"
    except FileNotFoundError as e:
        return -1, "", f"Command not found: {e}"

def ensure_directories():
    """Create all required directories."""
    for d in [SPECS_DIR, CONTEXT_DIR, PROMPTS_DIR, REPORTS_DIR, BACKUPS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def backup_phase(phase_number: int):
    """Backup current state before running a phase."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = BACKUPS_DIR / f"phase{phase_number}_pre_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Backup the files that this phase will modify
    dirs_to_backup = {
        0: ["backend", "frontend", "deploy", "terraform", "alembic", "scripts"],
        1: ["backend/auth", "backend/tests"],
        2: ["backend/api", "backend/pipeline", "backend/tests"],
        3: ["backend/api/files.py", "backend/storage", "backend/tests"],
        4: ["frontend/src"],
        5: ["terraform", "deploy", ".github"],
        6: ["backend/tests"],
    }

    targets = dirs_to_backup.get(phase_number, [])
    for target in targets:
        src = PROJECT_ROOT / target
        if src.exists():
            dst = backup_dir / target
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True,
                                ignore=shutil.ignore_patterns(
                                    'node_modules', '__pycache__', '.venv',
                                    'venv', '*.pyc', '.git'))
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

    logger.info("Backed up phase %d state to %s", phase_number, backup_dir.name)
    return backup_dir

def generate_phase_summary(phase_number: int, phase_name: str):
    """Generate a context summary file after a phase completes."""
    summary_path = CONTEXT_DIR / f"phase{phase_number}-output-summary.md"

    # Collect information about what was generated
    summary_lines = [
        f"# Phase {phase_number}: {phase_name} — Completed",
        f"",
        f"Generated: {datetime.now().isoformat()}",
        f"",
    ]

    # List files that were created or modified
    phase_file_patterns = {
        0: [
            "backend//.py", "frontend/src//.jsx", "frontend/src//*.js",
            "deploy/", "terraform//.tf", "alembic//*.py",
        ],
        1: ["backend/auth//.py", "backend/tests/test_auth.py"],
        2: ["backend/api/routes.py", "backend/pipeline//*.py",
            "backend/tests/test_pipeline*.py"],
        3: ["backend/api/files.py", "backend/storage//*.py",
            "backend/tests/test_file*.py"],
        4: ["frontend/src//.jsx", "frontend/src//.js"],
        5: ["terraform//.tf", "deploy/", ".github//.yml"],
        6: ["backend/tests//*.py"],
    }

    import glob
    patterns = phase_file_patterns.get(phase_number, [])
    files_found = []
    for pattern in patterns:
        files_found.extend(glob.glob(str(PROJECT_ROOT / pattern), recursive=True))

    summary_lines.append("## Files Generated/Modified")
    summary_lines.append("")
    for f in sorted(set(files_found)):
        rel = os.path.relpath(f, PROJECT_ROOT)
        size = os.path.getsize(f)
        summary_lines.append(f"  {rel} ({size:,} bytes)")
    summary_lines.append("")

    # Extract key interfaces for downstream phases
    if phase_number == 0:
        summary_lines.extend([
            "",
            "## Key Interfaces Available",
            "- backend/config.py: Settings (BaseSettings)",
            "- backend/database.py: engine, get_db, Base, check_db_connection",
            "- backend/models.py: User, SalesTeam, PipelineRun, LoanException, LoanFact",
            "- backend/auth/security.py: hash_password, verify_password, create_access_token, get_current_user, admin_required",
            "- backend/auth/schemas.py: UserRole, UserCreate, UserUpdate, UserResponse, Token",
            "- backend/schemas/api.py: RunCreate, RunResponse, SummaryResponse, ExceptionResponse",
            "- backend/storage/base.py: StorageBackend (ABC)",
        ])
    elif phase_number == 1:
        summary_lines.extend([
            "",
            "## Auth Endpoints (fully implemented)",
            "- POST /api/auth/login → Token",
            "- GET /api/auth/me → UserResponse",
            "- POST /api/auth/register → UserResponse (admin only)",
            "- PUT /api/auth/users/{id} → UserResponse (admin only)",
            "- GET /api/auth/users → List[UserResponse] (admin only)",
            "",
            "## Auth Validators Available",
            "- admin_or_self(user_id) → User",
            "- active_user_required → User",
            "- require_roles(*roles) → dependency factory",
            "- sales_team_scoped → User",
        ])
    elif phase_number == 2:
        summary_lines.extend([
            "",
            "## Pipeline Endpoints (fully implemented)",
            "- POST /api/pipeline/run → RunResponse",
            "- GET /api/runs → List[RunResponse]",
            "- GET /api/runs/{run_id} → RunResponse",
            "- GET /api/runs/{run_id}/notebook-outputs → file list",
            "- GET /api/runs/{run_id}/notebook-outputs/{key}/download → file",
            "- GET /api/runs/{run_id}/archive → archive listing",
            "- GET /api/runs/{run_id}/archive/download → file",
            "- GET /api/summary/{run_id} → SummaryResponse",
            "- GET /api/exceptions → List[ExceptionResponse]",
            "- GET /api/exceptions/export → CSV/XLSX download",
            "- GET /api/loans → List[dict]",
            "- GET /api/sales-teams → List[dict]",
            "- GET /api/config → config dict",
            "",
            "## Pipeline Engine Available",
            "- backend/pipeline/engine.py: execute_pipeline()",
            "- backend/pipeline/phases.py: phase_ingest through phase_archive",
            "- backend/pipeline/eligibility.py: run_eligibility_checks()",
        ])

    summary_path.write_text("\n".join(summary_lines))
    logger.info("Phase %d summary saved to %s", phase_number, summary_path.name)

def print_banner(text: str, char: str = "=", width: int = 72):
    print(f"\n{char * width}")
    print(f"  {text}")
    print(f"{char * width}")

def print_phase_result(result: PhaseResult):
    if result.status == PhaseStatus.PASSED:
        icon, color = "✓", "\033[32m"
    elif result.status == PhaseStatus.FAILED:
        icon, color = "✗", "\033[31m"
    elif result.status == PhaseStatus.SKIPPED:
        icon, color = "⊘", "\033[33m"
    else:
        icon, color = "?", "\033[37m"
    reset = "\033[0m"

    print(f"  {color}{icon} Phase {result.phase_number}: {result.phase_name}{reset}")
    print(f"    Status:     {result.status.value}")
    print(f"    Generation: {result.generation_time:.1f}s")
    print(f"    Validation: {result.validation_time:.1f}s")
    print(f"    Checks:     {result.checks_passed} passed, "
          f"{result.checks_failed} failed, {result.checks_warned} warned")
    if result.retry_count > 0:
        print(f"    Retries:    {result.retry_count}")
    if result.error_message:
        print(f"    Error:      {result.error_message}")

─── Phase Definitions ──────────────────────────────────────────────────

def get_phase_definitions(args) -> list[dict]:
    """
    Define all phases with their prompts, validation checks, and dependencies.
    Returns list of phase definition dicts.
    """

    skip_docker = getattr(args, "skip_docker", False)
    skip_terraform = getattr(args, "skip_terraform", False)
    skip_frontend = getattr(args, "skip_frontend", False)

    phases = [

        # ── Phase 0: Project Scaffold ────────────────────────────────
        {
            "number": 0,
            "name": "Project Scaffold",
            "prompt_file": PROMPTS_DIR / "phase0-scaffold-prompt.md",
            "description": "Generate complete project structure, config, models, stubs",
            "pre_checks": [
                ValidationCheck(
                    name="Prompt file exists",
                    command=[sys.executable, "-c",
                             f"import pathlib; assert pathlib.Path('{PROMPTS_DIR}/phase0-scaffold-prompt.md').exists()"],
                ),
            ],
            "validations": [
                ValidationCheck(
                    name="pyproject.toml exists",
                    command=[sys.executable, "-c",
                             "from pathlib import Path; assert (Path('.') / 'pyproject.toml').exists()"],
                ),
                ValidationCheck(
                    name="pip install -e '.[dev]'",
                    command=[sys.executable, "-m", "pip", "install", "-e", ".[dev]", "--quiet"],
                    timeout=300,
                ),
                ValidationCheck(
                    name=".env.example exists with required vars",
                    command=[sys.executable, "-c", """
import pathlib
content = pathlib.Path('.env.example').read_text()
required = ['DATABASE_URL', 'SECRET_KEY', 'STORAGE_TYPE', 'ENVIRONMENT']
missing = [v for v in required if v not in content]
assert not missing, f'Missing: {missing}'
print(f'All {len(required)} required vars present')
"""],
                ),
                ValidationCheck(
                    name="Backend imports cleanly",
                    command=[sys.executable, "-c",
                             "import backend.config; import backend.database; "
                             "import backend.models; import backend.auth.schemas; "
                             "import backend.schemas.api; print('All imports OK')"],
                ),
                ValidationCheck(
                    name="All expected files exist",
                    command=[sys.executable, "-c", """
from pathlib import Path
required = [
    'backend/__init__.py', 'backend/config.py', 'backend/database.py',
    'backend/models.py', 'backend/api/main.py', 'backend/api/routes.py',
    'backend/api/files.py', 'backend/auth/routes.py', 'backend/auth/security.py',
    'backend/auth/schemas.py', 'backend/auth/create_admin.py',
    'backend/schemas/api.py', 'backend/storage/base.py',
    'backend/storage/local.py', 'backend/storage/s3.py',
    'backend/tests/conftest.py', 'backend/tests/test_health.py',
    'frontend/package.json', 'frontend/vite.config.js',
    'deploy/Dockerfile', 'deploy/docker-compose.yml', 'deploy/entrypoint.sh',
    'alembic/env.py', 'scripts/init-db.ps1',
    '.env.example', '.gitignore', 'README.md',
]
missing = [f for f in required if not Path(f).exists()]
assert not missing, f'Missing {len(missing)} files: {missing[:10]}'
print(f'All {len(required)} files present')
"""],
                ),
                ValidationCheck(
                    name="Docker Compose valid",
                    command=["docker", "compose", "-f", "deploy/docker-compose.yml", "config", "--quiet"],
                    required=not skip_docker,
                    timeout=15,
                ),
                ValidationCheck(
                    name="Terraform init",
                    command=["terraform", f"-chdir=terraform", "init", "-backend=false"],
                    required=not skip_terraform,
                    timeout=60,
                ),
                ValidationCheck(
                    name="Frontend package.json valid",
                    command=[sys.executable, "-c",
                             "import json; d = json.load(open('frontend/package.json')); "
                             "assert 'react' in d.get('dependencies', {}); print('Valid')"],
                    required=not skip_frontend,
                ),
                ValidationCheck(
                    name="Ruff lint backend/",
                    command=[sys.executable, "-m", "ruff", "check", "backend/", "--no-fix"],
                ),
                ValidationCheck(
                    name="pytest test_health.py",
                    command=[sys.executable, "-m", "pytest", "backend/tests/test_health.py",
                             "-v", "--tb=short", "-x"],
                    timeout=60,
                ),
            ],
        },

        # ── Phase 1: Authentication ──────────────────────────────────
        {
            "number": 1,
            "name": "Authentication Layer",
            "prompt_file": PROMPTS_DIR / "phase1-auth-prompt.md",
            "description": "Implement auth routes, validators, and tests",
            "validations": [
                ValidationCheck(
                    name="Auth module imports",
                    command=[sys.executable, "-c",
                             "from backend.auth.routes import router; "
                             "from backend.auth.validators import require_roles; "
                             "print('Auth imports OK')"],
                ),
                ValidationCheck(
                    name="Auth routes registered",
                    command=[sys.executable, "-c", """
from backend.api.main import app
auth_routes = [r.path for r in app.routes if hasattr(r, 'path') and '/auth/' in r.path]
assert len(auth_routes) >= 5, f'Only {len(auth_routes)} auth routes found: {auth_routes}'
print(f'{len(auth_routes)} auth routes registered')
"""],
                ),
                ValidationCheck(
                    name="Ruff lint backend/auth/",
                    command=[sys.executable, "-m", "ruff", "check", "backend/auth/", "--no-fix"],
                ),
                ValidationCheck(
                    name="pytest test_auth_routes.py",
                    command=[sys.executable, "-m", "pytest",
                             "backend/tests/test_auth_routes.py",
                             "-v", "--tb=short", "-x"],
                    timeout=120,
                ),
                ValidationCheck(
                    name="No password hashes in responses",
                    command=[sys.executable, "-c", """
import ast, pathlib
content = pathlib.Path('backend/auth/routes.py').read_text()
assert 'hashed_password' not in content.split('return')[0] if 'return' in content else True
print('No password hash leakage detected')
"""],
                    required=False,  # Warning only
                ),
            ],
        },

        # ── Phase 2: Pipeline & Runs ─────────────────────────────────
        {
            "number": 2,
            "name": "Pipeline & Runs",
            "prompt_file": PROMPTS_DIR / "phase2-pipeline-prompt.md",
            "description": "Implement pipeline engine, phases, eligibility, API routes",
            "validations": [
                ValidationCheck(
                    name="Pipeline module imports",
                    command=[sys.executable, "-c",
                             "from backend.pipeline.engine import execute_pipeline; "
                             "from backend.pipeline.phases import phase_ingest; "
                             "from backend.pipeline.eligibility import run_eligibility_checks; "
                             "print('Pipeline imports OK')"],
                ),
                ValidationCheck(
                    name="API routes registered",
                    command=[sys.executable, "-c", """
from backend.api.main import app
api_paths = [r.path for r in app.routes if hasattr(r, 'path') and '/api/' in r.path]
assert len(api_paths) >= 20, f'Only {len(api_paths)} API routes: {api_paths}'
print(f'{len(api_paths)} API routes registered')
"""],
                ),
                ValidationCheck(
                    name="Eligibility rules defined",
                    command=[sys.executable, "-c",
                             "from backend.pipeline.eligibility import ELIGIBILITY_RULES; "
                             f"assert len(ELIGIBILITY_RULES) >= 8, "
                             f"f'Only {{len(ELIGIBILITY_RULES)}} rules'; "
                             "print(f'{len(ELIGIBILITY_RULES)} eligibility rules defined')"],
                ),
                ValidationCheck(
                    name="Storage dependency available",
                    command=[sys.executable, "-c",
                             "from backend.api.dependencies import get_storage; "
                             "storage = get_storage(); "
                             "print(f'Storage backend: {type(storage).__name__}')"],
                ),
                ValidationCheck(
                    name="Ruff lint backend/api/ backend/pipeline/",
                    command=[sys.executable, "-m", "ruff", "check",
                             "backend/api/", "backend/pipeline/", "--no-fix"],
                ),
                ValidationCheck(
                    name="pytest test_pipeline_routes.py",
                    command=[sys.executable, "-m", "pytest",
                             "backend/tests/test_pipeline_routes.py",
                             "-v", "--tb=short", "-x"],
                    timeout=120,
                ),
            ],
        },

        # ── Phase 3: File Management ─────────────────────────────────
        {
            "number": 3,
            "name": "File Management",
            "prompt_file": PROMPTS_DIR / "phase3-files-prompt.md",
            "description": "Implement file upload/download/list routes and storage backends",
            "validations": [
                ValidationCheck(
                    name="Storage backends import",
                    command=[sys.executable, "-c",
                             "from backend.storage.local import LocalStorage; "
                             "from backend.storage.s3 import S3Storage; "
                             "print('Storage backends OK')"],
                ),
                ValidationCheck(
                    name="File routes registered",
                    command=[sys.executable, "-c", """
from backend.api.main import app
file_routes = [r.path for r in app.routes if hasattr(r, 'path') and '/files' in r.path]
assert len(file_routes) >= 6, f'Only {len(file_routes)} file routes: {file_routes}'
print(f'{len(file_routes)} file routes registered')
"""],
                ),
                ValidationCheck(
                    name="Local storage operations",
                    command=[sys.executable, "-c", """
import asyncio
from backend.storage.local import LocalStorage
async def test():
    storage = LocalStorage(base_path='/tmp/loan-engine-test')
    files = await storage.list_files('', area='inputs')
    print(f'LocalStorage working: {type(files)}')
asyncio.run(test())
"""],
                ),
                ValidationCheck(
                    name="Ruff lint backend/storage/ backend/api/files.py",
                    command=[sys.executable, "-m", "ruff", "check",
                             "backend/storage/", "backend/api/files.py", "--no-fix"],
                ),
                ValidationCheck(
                    name="pytest test_file_routes.py",
                    command=[sys.executable, "-m", "pytest",
                             "backend/tests/test_file_routes.py",
                             "-v", "--tb=short", "-x"],
                    timeout=120,
                ),
            ],
        },

        # ── Phase 4: Frontend ────────────────────────────────────────
        {
            "number": 4,
            "name": "Frontend Implementation",
            "prompt_file": PROMPTS_DIR / "phase4-frontend-prompt.md",
            "description": "Implement React pages, API integration, auth flow",
            "validations": [
                ValidationCheck(
                    name="npm install",
                    command=["npm", "install"],
                    timeout=120,
                    required=not skip_frontend,
                ),
                ValidationCheck(
                    name="npm run build",
                    command=["npm", "run", "build"],
                    timeout=120,
                    required=not skip_frontend,
                ),
                ValidationCheck(
                    name="Build output exists",
                    command=[sys.executable, "-c",
                             "from pathlib import Path; "
                             "assert (Path('frontend/dist/index.html')).exists(); "
                             "print('Frontend build OK')"],
                    required=not skip_frontend,
                ),
                ValidationCheck(
                    name="All page components exist",
                    command=[sys.executable, "-c", """
from pathlib import Path
pages = ['LoginPage', 'DashboardPage', 'RunDetailPage',
         'ExceptionsPage', 'FilesPage', 'UsersPage']
missing = [p for p in pages if not (Path('frontend/src/pages') / f'{p}.jsx').exists()]
assert not missing, f'Missing pages: {missing}'
print(f'All {len(pages)} page components present')
"""],
                    required=not skip_frontend,
                ),
            ],
        },

        # ── Phase 5: Infrastructure ──────────────────────────────────
        {
            "number": 5,
            "name": "AWS Infrastructure",
            "prompt_file": PROMPTS_DIR / "phase5-infrastructure-prompt.md",
            "description": "Generate Terraform modules, CI/CD, Dockerfile",
            "validations": [
                ValidationCheck(
                    name="Terraform modules exist",
                    command=[sys.executable, "-c", """
from pathlib import Path
modules = ['networking', 'ecs', 'rds', 'alb', 'iam', 'secrets']
missing = [m for m in modules if not (Path('terraform/modules') / m / 'main.tf').exists()]
assert not missing, f'Missing modules: {missing}'
print(f'All {len(modules)} Terraform modules present')
"""],
                    required=not skip_terraform,
                ),
                ValidationCheck(
                    name="Terraform validate",
                    command=["terraform", f"-chdir=terraform", "validate"],
                    required=not skip_terraform,
                    timeout=30,
                ),
                ValidationCheck(
                    name="Dockerfile builds",
                    command=["docker", "build", "-f", "deploy/Dockerfile",
                             "-t", "loan-engine:validate", "."],
                    required=not skip_docker,
                    timeout=300,
                ),
                ValidationCheck(
                    name="GitHub Actions workflow valid",
                    command=[sys.executable, "-c",
                             "import yaml; d = yaml.safe_load(open('.github/workflows/deploy.yml')); "
                             "assert 'jobs' in d; print(f'Workflow has {len(d[\"jobs\"])} jobs')"],
                    required=False,
                ),
                ValidationCheck(
                    name="entrypoint.sh is executable",
                    command=[sys.executable, "-c",
                             "from pathlib import Path; "
                             "p = Path('deploy/entrypoint.sh'); "
                             "assert p.exists(); "
                             "content = p.read_text(); "
                             "assert 'alembic upgrade head' in content; "
                             "print('entrypoint.sh valid')"],
                ),
            ],
        },

        # ── Phase 6: Integration Tests ───────────────────────────────
        {
            "number": 6,
            "name": "Integration Tests",
            "prompt_file": PROMPTS_DIR / "phase6-tests-prompt.md",
            "description": "Generate comprehensive integration and E2E test suite",
            "validations": [
                ValidationCheck(
                    name="Test files exist",
                    command=[sys.executable, "-c", """
from pathlib import Path
tests = ['test_health', 'test_auth_routes', 'test_pipeline_routes', 'test_file_routes']
missing = [t for t in tests if not (Path('backend/tests') / f'{t}.py').exists()]
assert not missing, f'Missing tests: {missing}'
print(f'All {len(tests)} test files present')
"""],
                ),
                ValidationCheck(
                    name="Full test suite passes",
                    command=[sys.executable, "-m", "pytest", "backend/tests/",
                             "-v", "--tb=short", "-x", "--timeout=30"],
                    timeout=300,
                ),
                ValidationCheck(
                    name="Ruff lint entire backend",
                    command=[sys.executable, "-m", "ruff", "check", "backend/", "--no-fix"],
                ),
                ValidationCheck(
                    name="Alembic schema sync check",
                    command=[sys.executable, "-c", """
import subprocess, pathlib, sys
result = subprocess.run(
    ['alembic', 'revision', '--autogenerate', '-m', 'orchestrator_sync_check'],
    capture_output=True, text=True, timeout=30,
)
if result.returncode == 0:
    versions = pathlib.Path('alembic/versions')
    sync_files = list(versions.glob('orchestrator_sync_check'))
    if sync_files:
        content = sync_files[0].read_text()
        sync_files[0].unlink()  # Clean up
        has_changes = any(op in content for op in
            ['op.create_table', 'op.drop_table', 'op.add_column', 'op.alter_column'])
        if has_changes:
            print('WARNING: Schema drift detected')
            sys.exit(1)
        else:
            print('Schema in sync')
    else:
        print('Could not verify')
else:
    print(f'Alembic error: {result.stderr[:200]}')
    sys.exit(1)
"""],
                    required=False,
                ),
            ],
        },
    ]

    return phases

─── Phase Execution ─────────────────────────────────────────────────────

def execute_codex(prompt_file: Path, codex_cmd: str, dry_run: bool) -> tuple[int, float]:
    """
    Execute Codex with the given prompt file.
    Returns (exit_code, duration_seconds).
    """
    if not prompt_file.exists():
        logger.error("Prompt file not found: %s", prompt_file)
        return 1, 0.0

    if dry_run:
        logger.info("[DRY RUN] Would execute: %s --prompt-file %s", codex_cmd, prompt_file)
        return 0, 0.0

    start = time.time()

    # Build the Codex command
    # Adapt this to your specific Codex CLI syntax
    cmd = f'{codex_cmd} --prompt-file "{prompt_file}"'

    logger.info("Executing Codex: %s", cmd)

    code, stdout, stderr = run_cmd(cmd, shell=True, timeout=600)

    duration = time.time() - start

    if code != 0:
        logger.error("Codex execution failed (exit %d)", code)
        if stderr:
            logger.error("stderr: %s", stderr[:500])
    else:
        logger.info("Codex execution completed in %.1fs", duration)

    return code, duration

def run_validation(checks: list[ValidationCheck], verbose: bool = False) -> tuple[int, int, int, list[dict]]:
    """
    Run a list of validation checks.
    Returns (passed, failed, warned, details).
    """
    passed = failed = warned = 0
    details = []

    for check in checks:
        start = time.time()
        code, stdout, stderr = run_cmd(
            check.command,
            timeout=check.timeout,
            shell=check.shell,
        )
        duration = time.time() - start

        if code == check.expected_exit_code:
            passed += 1
            status = "passed"
            icon = "\033[32m✓\033[0m"
        elif not check.required:
            warned += 1
            status = "warned"
            icon = "\033[33m⚠\033[0m"
        else:
            failed += 1
            status = "failed"
            icon = "\033[31m✗\033[0m"

        print(f"    {icon} {check.name} ({duration:.1f}s)")

        if status in ("failed", "warned") and verbose:
            output = (stderr or stdout)[:300]
            if output:
                for line in output.strip().split("\n"):
                    print(f"        {line}")

        details.append({
            "name": check.name,
            "status": status,
            "duration": round(duration, 2),
            "exit_code": code,
            "output": (stdout + stderr)[:500],
        })

    return passed, failed, warned, details

def execute_phase(
    phase_def: dict,
    codex_cmd: str,
    dry_run: bool,
    verbose: bool,
) -> PhaseResult:
    """Execute a single phase: generate → validate → summarize."""

    phase_num = phase_def["number"]
    phase_name = phase_def["name"]

    result = PhaseResult(
        phase_number=phase_num,
        phase_name=phase_name,
        status=PhaseStatus.RUNNING,
    )

    total_start = time.time()

    print_banner(f"Phase {phase_num}: {phase_name}", char="━")
    print(f"  {phase_def['description']}")

    # ── Pre-checks ──
    pre_checks = phase_def.get("pre_checks", [])
    if pre_checks:
        print(f"\n  Pre-flight checks:")
        p, f, w, _ = run_validation(pre_checks, verbose)
        if f > 0:
            result.status = PhaseStatus.FAILED
            result.error_message = "Pre-flight checks failed"
            result.total_time = time.time() - total_start
            return result

    # ── Backup ──
    backup_dir = backup_phase(phase_num)

    # ── Generate ──
    prompt_file = phase_def["prompt_file"]
    print(f"\n  Generating with Codex...")
    print(f"  Prompt: {prompt_file.name}")

    for attempt in range(MAX_PHASE_RETRIES + 1):
        if attempt > 0:
            print(f"\n  Retry {attempt}/{MAX_PHASE_RETRIES}...")
            result.retry_count = attempt

        gen_code, gen_duration = execute_codex(prompt_file, codex_cmd, dry_run)
        result.generation_time = gen_duration

        if gen_code != 0 and not dry_run:
            if attempt < MAX_PHASE_RETRIES:
                logger.warning("Generation failed, retrying...")
                continue
            else:
                result.status = PhaseStatus.FAILED
                result.error_message = f"Codex generation failed after {MAX_PHASE_RETRIES + 1} attempts"
                result.total_time = time.time() - total_start
                return result

        # ── Validate ──
        print(f"\n  Validation checks:")
        result.status = PhaseStatus.VALIDATING
        val_start = time.time()

        passed, failed, warned, details = run_validation(
            phase_def["validations"], verbose
        )

        result.validation_time = time.time() - val_start
        result.checks_passed = passed
        result.checks_failed = failed
        result.checks_warned = warned
        result.validation_details = details

        if failed == 0:
            # ── Success ──
            result.status = PhaseStatus.PASSED

            # Generate summary for next phase
            if not dry_run:
                generate_phase_summary(phase_num, phase_name)

            break
        else:
            if attempt < MAX_PHASE_RETRIES:
                logger.warning("Validation failed (%d checks), retrying generation...", failed)
                # Restore backup before retrying
                # (In practice, you might want a smarter retry that sends
                #  the error output back to Codex as correction context)
                continue
            else:
                result.status = PhaseStatus.FAILED
                result.error_message = (
                    f"{failed} validation check(s) failed after "
                    f"{MAX_PHASE_RETRIES + 1} attempts"
                )

    result.total_time = time.time() - total_start
    return result

─── Main ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Loan Engine Dark Factory — Master Orchestration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python specs/orchestrate.py                        # Run all phases
  python specs/orchestrate.py --start-from 2         # Resume from Phase 2
  python specs/orchestrate.py --phase 1              # Run only Phase 1
  python specs/orchestrate.py --dry-run              # Preview without executing
  python specs/orchestrate.py --skip-docker --skip-terraform
  python specs/orchestrate.py --codex-cmd "cursor --apply"
        """,
    )
    parser.add_argument("--start-from", type=int, default=0,
                        help="Start from this phase number (skip earlier phases)")
    parser.add_argument("--phase", type=int, default=None,
                        help="Run only this specific phase")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show execution plan without running Codex")
    parser.add_argument("--verbose", action="store_true",
                        help="Show full output on validation failures")
    parser.add_argument("--codex-cmd", default=DEFAULT_CODEX_CMD,
                        help=f"Codex CLI command (default: {DEFAULT_CODEX_CMD})")
    parser.add_argument("--skip-docker", action="store_true",
                        help="Skip Docker-dependent validations")
    parser.add_argument("--skip-terraform", action="store_true",
                        help="Skip Terraform validations")
    parser.add_argument("--skip-frontend", action="store_true",
                        help="Skip frontend validations")
    parser.add_argument("--max-retries", type=int, default=MAX_PHASE_RETRIES,
                        help=f"Max retries per phase (default: {MAX_PHASE_RETRIES})")

    args = parser.parse_args()

    global MAX_PHASE_RETRIES
    MAX_PHASE_RETRIES = args.max_retries

    # Setup
    ensure_directories()
    report = OrchestratorReport(started_at=datetime.now())

    # Get phase definitions
    all_phases = get_phase_definitions(args)

    # Filter phases based on arguments
    if args.phase is not None:
        phases_to_run = [p for p in all_phases if p["number"] == args.phase]
        if not phases_to_run:
            print(f"Error: Phase {args.phase} not found. Available: {[p['number'] for p in all_phases]}")
            sys.exit(2)
    else:
        phases_to_run = [p for p in all_phases if p["number"] >= args.start_from]

    # ── Print Plan ──
    print_banner("Loan Engine — Dark Factory Orchestration")
    print(f"  Project root:  {PROJECT_ROOT}")
    print(f"  Codex command: {args.codex_cmd}")
    print(f"  Dry run:       {args.dry_run}")
    print(f"  Max retries:   {MAX_PHASE_RETRIES}")
    print(f"  Phases:        {len(phases_to_run)} of {len(all_phases)}")

    print(f"\n  Execution plan:")
    for p in all_phases:
        if p["number"] in [x["number"] for x in phases_to_run]:
            icon = "►"
        elif p["number"] < args.start_from:
            icon = "✓"  # assumed already done
        else:
            icon = "·"
        checks = len(p["validations"])
        print(f"    {icon} Phase {p['number']}: {p['name']} ({checks} validation checks)")

    if args.dry_run:
        print(f"\n  [DRY RUN] No code will be generated.\n")

    # ── Check prompt files exist ──
    missing_prompts = []
    for p in phases_to_run:
        if not p["prompt_file"].exists():
            missing_prompts.append(p)

    if missing_prompts and not args.dry_run:
        print(f"\n  ⚠ Missing prompt files:")
        for p in missing_prompts:
            print(f"    - {p['prompt_file']} (Phase {p['number']}: {p['name']})")
        print(f"\n  Save your prompts to specs/prompts/ before running.")
        print(f"  Expected files:")
        for p in all_phases:
            print(f"    specs/prompts/{p['prompt_file'].name}")
        sys.exit(2)

    # ── Execute Phases ──
    for phase_def in phases_to_run:
        result = execute_phase(
            phase_def=phase_def,
            codex_cmd=args.codex_cmd,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )
        report.phases.append(result)

        print_phase_result(result)

        if result.status == PhaseStatus.FAILED:
            print_banner(f"HALTED — Phase {result.phase_number} failed", char="!")
            print(f"  Error: {result.error_message}")
            print(f"\n  To retry this phase:")
            print(f"    python specs/orchestrate.py --phase {result.phase_number} --verbose")
            print(f"\n  To skip and continue:")
            print(f"    python specs/orchestrate.py --start-from {result.phase_number + 1}")
            print(f"\n  Backup available at:")
            print(f"    {BACKUPS_DIR}/phase{result.phase_number}_pre_*/")
            break

    # ── Final Report ──
    report.completed_at = datetime.now()

    all_passed = all(
        p.status in (PhaseStatus.PASSED, PhaseStatus.SKIPPED)
        for p in report.phases
    )
    report.overall_status = "completed" if all_passed else "failed"

    total_time = (report.completed_at - report.started_at).total_seconds()

    print_banner("Orchestration Summary")

    for result in report.phases:
        print_phase_result(result)

    passed_phases = sum(1 for p in report.phases if p.status == PhaseStatus.PASSED)
    failed_phases = sum(1 for p in report.phases if p.status == PhaseStatus.FAILED)

    if all_passed:
        color = "\033[32m"
        status_text = "ALL PHASES COMPLETED SUCCESSFULLY"
    else:
        color = "\033[31m"
        status_text = f"{failed_phases} PHASE(S) FAILED"

    reset = "\033[0m"
    print(f"""
  {color}{status_text}{reset}

  Phases passed: {passed_phases}/{len(report.phases)}
  Total time:    {total_time:.0f}s ({total_time/60:.1f}m)
  Retries used:  {sum(p.retry_count for p in report.phases)}
""")

    # Save report
    report_path = REPORTS_DIR / f"orchestration-{report.started_at.strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2)
    print(f"  Report: {report_path}")

    # Save latest report link
    latest_path = REPORTS_DIR / "latest.json"
    with open(latest_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2)

    # ── Post-completion checks ──
    if all_passed and not args.dry_run:
        print_banner("Post-Completion")
        print("  All phases passed. Next steps:")
        print("")
        print("  1. Run full validation:")
        print("     python specs/validate_scaffold.py")
        print("")
        print("  2. Start the application:")
        print("     docker-compose -f deploy/docker-compose.yml up")
        print("")
        print("  3. Run the full test suite:")
        print("     pytest backend/tests/ -v")
        print("")
        print("  4. Deploy to AWS:")
        print("     cd terraform && terraform plan")
        print("     git push origin main  # triggers GitHub Actions")

    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()



