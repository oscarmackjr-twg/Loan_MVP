"""List and fix pipeline runs stuck in "running" state.

When the backend process is killed or crashes during a run, the run record may never
get updated to 'completed' or 'failed'. This script lets you list such runs and mark
them as 'failed' or 'cancelled'.

Database connection: same as the app (DATABASE_URL from env or .env).

Usage:
    # List all runs currently in 'running' state (with duration)
    python backend/scripts/fix_stuck_runs.py --list

    # Mark a specific run as failed (run_id is the UUID string, e.g. from API or UI)
    python backend/scripts/fix_stuck_runs.py --run-id <RUN_ID> --mark failed

    # Mark as cancelled
    python backend/scripts/fix_stuck_runs.py --run-id <RUN_ID> --mark cancelled

    # Add a reason (stored in run.errors for 'failed')
    python backend/scripts/fix_stuck_runs.py --run-id <RUN_ID> --mark failed --reason "Server restarted"

    # Mark all runs that have been 'running' longer than N minutes
    python backend/scripts/fix_stuck_runs.py --mark failed --older-than-minutes 60
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from db.connection import SessionLocal
from db.models import PipelineRun, RunStatus
from config.settings import settings


def list_stuck_runs(db: Session, older_than_minutes: Optional[int] = None):
    """Return list of runs with status=running, optionally filtered by started_at age."""
    q = db.query(PipelineRun).filter(PipelineRun.status == RunStatus.RUNNING)
    runs = q.order_by(PipelineRun.started_at.desc()).all()
    if older_than_minutes is not None and older_than_minutes > 0:
        cutoff = datetime.utcnow() - timedelta(minutes=older_than_minutes)
        runs = [r for r in runs if r.started_at and r.started_at < cutoff]
    return runs


def format_duration(started_at):
    if not started_at:
        return "?"
    now_utc = datetime.now(timezone.utc)
    st = started_at if started_at.tzinfo else started_at.replace(tzinfo=timezone.utc)
    delta = now_utc - st
    total_mins = int(delta.total_seconds() / 60)
    if total_mins < 60:
        return f"{total_mins} min"
    hours, mins = divmod(total_mins, 60)
    return f"{hours}h {mins}m"


def run_list(db: Session, older_than_minutes: Optional[int] = None) -> None:
    runs = list_stuck_runs(db, older_than_minutes)
    if not runs:
        print("No runs in 'running' state.")
        return
    print(f"Found {len(runs)} run(s) in 'running' state:\n")
    for r in runs:
        duration = format_duration(r.started_at)
        last_phase = getattr(r, "last_phase", None)
        print(f"  run_id: {r.run_id}")
        print(f"    started_at: {r.started_at}  (running for {duration})")
        if last_phase:
            print(f"    last_phase: {last_phase}  <- execution stopped here (see TROUBLESHOOTING_STUCK_RUNS.md for data vs code)")
        if r.input_file_path:
            print(f"    input_file_path: {r.input_file_path}")
        print()
    print("To mark as failed:  python backend/scripts/fix_stuck_runs.py --run-id <RUN_ID> --mark failed")
    print("To mark as cancelled: python backend/scripts/fix_stuck_runs.py --run-id <RUN_ID> --mark cancelled")


def run_mark(
    db: Session,
    run_id: Optional[str],
    mark: str,
    reason: Optional[str],
    older_than_minutes: Optional[int],
    yes: bool,
) -> None:
    if mark not in ("failed", "cancelled"):
        print(f"Invalid --mark: {mark}. Use 'failed' or 'cancelled'.", file=sys.stderr)
        sys.exit(1)

    if run_id:
        runs = db.query(PipelineRun).filter(PipelineRun.run_id == run_id, PipelineRun.status == RunStatus.RUNNING).all()
        if not runs:
            print(f"No run in 'running' state with run_id={run_id}. It may already be completed/failed/cancelled or the run_id is wrong.", file=sys.stderr)
            sys.exit(1)
    else:
        runs = list_stuck_runs(db, older_than_minutes)
        if not runs:
            print("No runs in 'running' state matching the criteria.")
            return
        if not yes:
            print(f"About to mark {len(runs)} run(s) as '{mark}'.")
            confirm = input("Proceed? [y/N]: ").strip().lower()
            if confirm not in ("y", "yes"):
                print("Aborted.")
                sys.exit(0)

    new_status = RunStatus.FAILED if mark == "failed" else RunStatus.CANCELLED
    reason_msg = reason or f"Marked as {mark} by fix_stuck_runs.py"

    for r in runs:
        r.status = new_status
        r.completed_at = datetime.utcnow()
        if mark == "failed":
            err_list = list(r.errors) if r.errors else []
            err_list.append(reason_msg)
            r.errors = err_list
        print(f"  {r.run_id} -> {new_status.value}")
    db.commit()
    print(f"Done. Updated {len(runs)} run(s) to '{mark}'.")


def main():
    parser = argparse.ArgumentParser(
        description="List or fix pipeline runs stuck in 'running' state.",
    )
    parser.add_argument("--list", action="store_true", help="List runs in 'running' state.")
    parser.add_argument("--run-id", type=str, help="Run ID (UUID string) to operate on.")
    parser.add_argument("--mark", type=str, choices=["failed", "cancelled"], help="Mark run(s) as failed or cancelled.")
    parser.add_argument("--reason", type=str, help="Reason (e.g. 'Server restarted'). Stored in errors when marking as failed.")
    parser.add_argument("--older-than-minutes", type=int, metavar="N", help="Only consider runs that have been running longer than N minutes (use with --mark without --run-id).")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation when marking multiple runs.")
    args = parser.parse_args()

    if args.list:
        db = SessionLocal()
        try:
            run_list(db, args.older_than_minutes)
        finally:
            db.close()
        return

    if args.mark:
        if not args.run_id and not args.older_than_minutes:
            print("Use either --run-id <id> or --older-than-minutes N with --mark.", file=sys.stderr)
            sys.exit(1)
        db = SessionLocal()
        try:
            run_mark(
                db,
                run_id=args.run_id,
                mark=args.mark,
                reason=args.reason,
                older_than_minutes=args.older_than_minutes,
                yes=args.yes,
            )
        finally:
            db.close()
        return

    # Default: list
    db = SessionLocal()
    try:
        run_list(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
