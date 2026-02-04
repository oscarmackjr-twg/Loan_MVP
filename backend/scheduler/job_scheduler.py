"""Automated pipeline job scheduler."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
from typing import Optional
from pathlib import Path

from config.settings import settings
from orchestration.run_context import RunContext
from orchestration.pipeline import PipelineExecutor
from db.connection import SessionLocal
from db.models import SalesTeam, PipelineRun, RunStatus
from utils.path_utils import get_sales_team_input_path, get_sales_team_output_path, get_sales_team_share_path
from scheduler.notifications import notify_run_started, notify_run_completed, notify_run_failed

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def run_daily_pipeline(sales_team_id: Optional[int] = None):
    """
    Execute daily pipeline run for a sales team.
    
    Args:
        sales_team_id: Optional sales team ID. If None, runs for general (non-team) data.
    
    Returns:
        Pipeline execution result
    """
    db = SessionLocal()
    context = None
    try:
        logger.info(f"Starting scheduled pipeline run for sales_team_id={sales_team_id}")
        
        # Create run context with dynamic date calculation (next Tuesday)
        context = RunContext.create(
            sales_team_id=sales_team_id,
            created_by_id=None,  # System-initiated
            pdate=None,  # Will use default (next Tuesday)
            irr_target=settings.IRR_TARGET
        )
        
        # Notify run started
        notify_run_started(sales_team_id, context.run_id)
        
        # Use sales team-specific paths for isolation
        base_input_path = get_sales_team_input_path(settings.INPUT_DIR, sales_team_id)
        base_output_path = get_sales_team_output_path(settings.OUTPUT_DIR, sales_team_id)
        
        context.input_file_path = base_input_path
        context.output_dir = base_output_path
        
        # Ensure directories exist
        Path(base_input_path).mkdir(parents=True, exist_ok=True)
        Path(base_output_path).mkdir(parents=True, exist_ok=True)
        Path(get_sales_team_share_path(settings.OUTPUT_DIR, sales_team_id)).mkdir(parents=True, exist_ok=True)
        
        # Execute pipeline
        with PipelineExecutor(context) as executor:
            result = executor.execute(base_input_path)
        
        logger.info(
            f"Scheduled pipeline run completed: {context.run_id} "
            f"(sales_team_id={sales_team_id}, loans={result.get('total_loans', 0)})"
        )
        
        # Notify run completed
        notify_run_completed(sales_team_id, context.run_id, result)
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        logger.error(
            f"Scheduled pipeline run failed for sales_team_id={sales_team_id}: {error_msg}",
            exc_info=True
        )
        
        # Notify run failed
        run_id = context.run_id if context else None
        notify_run_failed(sales_team_id, run_id, error_msg)
        
        # Update run status to failed if run was created
        try:
            if context and context.run_id:
                run = db.query(PipelineRun).filter(PipelineRun.run_id == context.run_id).first()
                if run:
                    run.status = RunStatus.FAILED
                    run.errors = [error_msg]
                    db.commit()
        except Exception as update_error:
            logger.error(f"Failed to update run status: {update_error}")
        
        # Re-raise to allow scheduler to handle retry logic if configured
        raise
        
    finally:
        db.close()


def schedule_daily_runs():
    """
    Schedule daily pipeline runs for all active sales teams.
    
    This function should be called after the application starts to ensure
    the database is available and settings are loaded.
    """
    if not settings.ENABLE_SCHEDULER:
        logger.info("Scheduler is disabled")
        return
    
    # Parse run time
    try:
        hour, minute = map(int, settings.DAILY_RUN_TIME.split(':'))
    except ValueError:
        logger.error(f"Invalid DAILY_RUN_TIME format: {settings.DAILY_RUN_TIME}. Expected HH:MM")
        return
    
    # Get all active sales teams
    db = SessionLocal()
    try:
        sales_teams = db.query(SalesTeam).filter(SalesTeam.is_active == True).all()
        
        # Schedule a run for each sales team
        for team in sales_teams:
            job_id = f"daily_pipeline_{team.id}"
            scheduler.add_job(
                run_daily_pipeline,
                trigger=CronTrigger(hour=hour, minute=minute),
                args=[team.id],
                id=job_id,
                replace_existing=True,
                max_instances=1,
                misfire_grace_time=3600  # Allow 1 hour grace period for missed runs
            )
            logger.info(
                f"Scheduled daily pipeline for sales team: {team.name} (ID: {team.id}) "
                f"at {settings.DAILY_RUN_TIME}"
            )
        
        # Also schedule a general run (no sales team) if needed
        # Comment out if you don't want general runs
        scheduler.add_job(
            run_daily_pipeline,
            trigger=CronTrigger(hour=hour, minute=minute),
            args=[None],
            id="daily_pipeline_general",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=3600
        )
        logger.info(f"Scheduled general daily pipeline run at {settings.DAILY_RUN_TIME}")
        
        logger.info(f"Total scheduled jobs: {len(scheduler.get_jobs())}")
        
    except Exception as e:
        logger.error(f"Failed to schedule daily runs: {e}", exc_info=True)
    finally:
        db.close()


def reschedule_daily_runs():
    """
    Reschedule daily runs (useful when sales teams are added/removed).
    Call this after creating or updating sales teams.
    """
    # Remove existing jobs
    scheduler.remove_all_jobs()
    logger.info("Removed all scheduled jobs")
    
    # Reschedule
    schedule_daily_runs()


# Note: Don't initialize scheduler on import - wait for application startup
# The scheduler will be started in the FastAPI lifespan handler
