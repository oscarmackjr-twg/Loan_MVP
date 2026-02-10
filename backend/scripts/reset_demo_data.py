"""Reset database to a clean state before the demo: delete all rows, keep tables.

Use this to re-initialize data (clear runs, exceptions, loans, and optionally users)
without dropping tables. After a full reset you must run seed_admin.py again to log in.

Database Connection:
Uses the same configuration as the main app (DATABASE_URL from env or .env).

Usage:
    # Clear pipeline data only (runs, exceptions, loan_facts). Keeps users/sales_teams so login still works.
    python backend/scripts/reset_demo_data.py

    # Clear everything including users and sales_teams. Run seed_admin.py afterward to recreate admin.
    python backend/scripts/reset_demo_data.py --all

    # Skip confirmation prompt (e.g. for CI)
    python backend/scripts/reset_demo_data.py --yes
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from db.connection import SessionLocal
from db.models import (
    LoanException,
    LoanFact,
    PipelineRun,
    User,
    SalesTeam,
)
from config.settings import settings


# Deletion order: children first (respect FK constraints).
PIPELINE_TABLES = [
    ("loan_exceptions", LoanException),
    ("loan_facts", LoanFact),
    ("pipeline_runs", PipelineRun),
]
USER_TABLES = [
    ("users", User),
    ("sales_teams", SalesTeam),
]


def delete_all(db: Session, model_class) -> int:
    """Delete all rows for the given model. Returns count deleted."""
    result = db.query(model_class).delete()
    return result


def run_reset(keep_users: bool, dry_run: bool = False) -> None:
    db: Session = SessionLocal()
    try:
        tables_to_clear = list(PIPELINE_TABLES)
        if not keep_users:
            tables_to_clear = tables_to_clear + list(USER_TABLES)

        if dry_run:
            print("Dry run. Would clear (delete all rows from):")
            for name, _ in tables_to_clear:
                print(f"  - {name}")
            return

        total = 0
        for name, model_class in tables_to_clear:
            n = delete_all(db, model_class)
            total += n
            print(f"  {name}: deleted {n} row(s)")

        db.commit()
        print(f"Done. Total rows deleted: {total}")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Delete all rows from demo tables (keeps table structure). Use before demo for a clean slate."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Also delete users and sales_teams. Run seed_admin.py afterward to recreate admin.",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print which tables would be cleared; do not delete.",
    )
    args = parser.parse_args()

    keep_users = not args.all
    db_display = settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL
    print(f"Database: {db_display}")

    if keep_users:
        print("Mode: clear pipeline data only (runs, exceptions, loan_facts). Users and sales_teams are kept.")
    else:
        print("Mode: clear all data including users and sales_teams. You will need to run seed_admin.py after.")

    if args.dry_run:
        run_reset(keep_users=keep_users, dry_run=True)
        return

    if not args.yes:
        confirm = input("Proceed? [y/N]: ").strip().lower()
        if confirm not in ("y", "yes"):
            print("Aborted.")
            sys.exit(0)

    print("Deleting rows...")
    run_reset(keep_users=keep_users, dry_run=False)


if __name__ == "__main__":
    main()
