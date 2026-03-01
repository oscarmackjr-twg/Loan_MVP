"""API routes for loan engine."""
import io
import logging
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
from pydantic import BaseModel

from db.connection import get_db
from db.models import PipelineRun, RunStatus, LoanException, LoanFact, User, SalesTeam, Holiday
from orchestration.pipeline import RunCancelledException
from auth.security import get_current_user, require_role, require_sales_team_access, UserRole
from auth.validators import get_user_sales_team_id, validate_sales_team_access
from auth.audit import log_data_access, log_authorization_failure
from orchestration.run_context import RunContext
from orchestration.pipeline import PipelineExecutor
from orchestration.s3_input_sync import sync_s3_input_to_temp, remove_temp_input_dir
from orchestration.archive_run import archive_previous_run
from config.settings import settings
from storage import get_storage_backend
from utils.holiday_calendar import (
    get_supported_countries,
    get_holidays_list,
    is_business_day,
    PDATE_COUNTRY,
)
from utils.date_utils import calculate_next_tuesday, calculate_pipeline_dates
from orchestration.tagging_runner import execute_tagging
from orchestration.final_funding_runner import execute_final_funding_sg, execute_final_funding_cibc

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["api"])

# All notebook-style outputs (mirror February_Baseline + eligibility). Keys must match report keys from pipeline.
NOTEBOOK_OUTPUT_DEFS = [
    {"key": "flagged_loans", "filename": "flagged_loans.xlsx", "label": "Flagged loans"},
    {"key": "purchase_price_mismatch", "filename": "purchase_price_mismatch.xlsx", "label": "Purchase price mismatch"},
    {"key": "comap_not_passed", "filename": "comap_not_passed.xlsx", "label": "CoMAP not passed"},
    {"key": "notes_flagged_loans", "filename": "notes_flagged_loans.xlsx", "label": "Notes flagged loans"},
    {"key": "special_asset_prime", "filename": "special_asset_prime.xlsx", "label": "Special asset (Prime)"},
    {"key": "special_asset_sfy", "filename": "special_asset_sfy.xlsx", "label": "Special asset (SFY)"},
    {"key": "eligibility_checks_json", "filename": "eligibility_checks.json", "label": "Eligibility checks (JSON)"},
    {"key": "eligibility_checks_summary", "filename": "eligibility_checks_summary.xlsx", "label": "Eligibility checks summary"},
]


class ProgramRunCreate(BaseModel):
    """Program run request (Pre-Funding, Tagging, Final Funding SG, Final Funding CIBC)."""
    phase: str  # "pre_funding" | "tagging" | "final_funding_sg" | "final_funding_cibc"
    folder: Optional[str] = None  # optional input folder (local path or S3 prefix); default uses INPUT_DIR / "input"


class ProgramRunResponse(BaseModel):
    """Program run response."""
    phase: str
    message: str
    output_prefix: Optional[str] = None  # e.g. "tagging" for file manager


class RunCreate(BaseModel):
    """Pipeline run creation model."""
    # Purchase date (YYYY-MM-DD). If omitted, defaults to next Tuesday (US business day; if that Tuesday is a US holiday, the following business day).
    pdate: Optional[str] = None
    # Base "today" date (YYYY-MM-DD) used for file naming (yesterday, last month end).
    # Defaults to the current system date when omitted.
    tday: Optional[str] = None
    irr_target: float = 8.05
    # Local: filesystem path to input folder. S3 (AWS): key prefix under inputs area (e.g. "legacy", "sales_team_1").
    folder: str = "C:/Users/omack/Intrepid/pythonFramework/loan_engine/legacy"


class RunResponse(BaseModel):
    """Pipeline run response model."""
    id: int
    run_id: str
    status: str
    sales_team_id: Optional[int]
    created_by_id: Optional[int] = None
    created_by_username: Optional[str] = None
    total_loans: int
    total_balance: float
    exceptions_count: int
    run_weekday: Optional[int] = None
    run_weekday_name: Optional[str] = None
    pdate: Optional[str] = None
    last_phase: Optional[str] = None
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ExceptionResponse(BaseModel):
    """Exception response model."""
    id: int
    seller_loan_number: str
    exception_type: str
    exception_category: str
    severity: str
    message: Optional[str]
    rejection_criteria: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class LoanFactResponse(BaseModel):
    """Loan fact response (for to_purchase / projected / rejected)."""
    id: int
    run_id: int
    seller_loan_number: str
    platform: Optional[str]
    loan_program: Optional[str]
    disposition: Optional[str] = None
    rejection_criteria: Optional[str] = None
    purchase_price_check: Optional[bool] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class SummaryResponse(BaseModel):
    """Summary response model."""
    run_id: str
    total_loans: int
    total_balance: float
    exceptions_count: int
    eligibility_checks: dict


class HolidayBase(BaseModel):
    """Base holiday fields for admin maintenance."""
    date: date
    country: str
    name: Optional[str] = None


class HolidayCreate(HolidayBase):
    """Create holiday payload."""
    pass


class HolidayResponse(HolidayBase):
    """Holiday response model."""
    id: int

    class Config:
        from_attributes = True


def filter_by_sales_team(query, user: User):
    """Filter query by sales team if user is sales team member."""
    if user.role == UserRole.SALES_TEAM and user.sales_team_id:
        return query.filter(PipelineRun.sales_team_id == user.sales_team_id)
    elif user.role == UserRole.ADMIN:
        return query  # Admins see all
    else:
        return query  # Analysts see all for now


@router.post("/program-run", response_model=ProgramRunResponse)
async def create_program_run(
    body: ProgramRunCreate,
    current_user: User = Depends(get_current_user),
):
    """Run a program phase: Pre-Funding (use pipeline/run), Tagging, Final Funding SG, or Final Funding CIBC."""
    if body.phase == "pre_funding":
        raise HTTPException(
            status_code=400,
            detail="Use POST /api/pipeline/run for Pre-Funding. The Program Runs UI calls that when you click Pre-Funding.",
        )
    if body.phase == "tagging":
        try:
            output_prefix = execute_tagging()
            return ProgramRunResponse(
                phase="tagging",
                message="Tagging completed. Outputs are in the output directory under tagging/.",
                output_prefix=output_prefix,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Tagging failed: {str(e)}") from e
    if body.phase == "final_funding_sg":
        try:
            output_prefix = execute_final_funding_sg(folder=body.folder)
            return ProgramRunResponse(
                phase="final_funding_sg",
                message="Final Funding SG completed. Outputs are in the output directory under final_funding_sg/.",
                output_prefix=output_prefix,
            )
        except FileNotFoundError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Final Funding SG failed: {str(e)}") from e
    if body.phase == "final_funding_cibc":
        try:
            output_prefix = execute_final_funding_cibc(folder=body.folder)
            return ProgramRunResponse(
                phase="final_funding_cibc",
                message="Final Funding CIBC completed. Outputs are in the output directory under final_funding_cibc/.",
                output_prefix=output_prefix,
            )
        except FileNotFoundError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Final Funding CIBC failed: {str(e)}") from e
    raise HTTPException(status_code=400, detail=f"Unknown phase: {body.phase}")


@router.get("/config")
async def get_config(current_user: User = Depends(get_current_user)):
    """Return app config for the UI (e.g. storage type, S3 bucket when using S3)."""
    out = {"storage_type": settings.STORAGE_TYPE}
    if settings.STORAGE_TYPE == "s3" and settings.S3_BUCKET_NAME:
        out["s3_bucket_name"] = settings.S3_BUCKET_NAME
        out["s3_region"] = settings.S3_REGION or "us-east-1"
    return out


# ---------- Business holiday calendar (US, India, England, Singapore); used for pdate ----------
@router.get("/calendar/countries")
async def list_calendar_countries(current_user: User = Depends(get_current_user)):
    """List supported holiday calendar countries (US, IN, GB, SG) for the next 10 years."""
    return get_supported_countries()


@router.get("/calendar/holidays")
async def list_holidays(
    country: str = Query(..., description="Country code: US, IN, GB, SG"),
    year: Optional[int] = Query(None, description="Year (default: current through +10)"),
    year_end: Optional[int] = Query(None, description="End year for range (use with year)"),
    current_user: User = Depends(get_current_user),
):
    """List holidays for a country. Covers current year through current + 10 years."""
    supported = get_supported_countries()
    if country not in supported:
        raise HTTPException(status_code=400, detail=f"Unsupported country. Use one of: {list(supported.keys())}")
    return get_holidays_list(country, year=year, year_end=year_end)


@router.get("/calendar/next-posting-date")
async def get_next_posting_date(
    tday: Optional[str] = Query(None, description="Base date YYYY-MM-DD (default: today)"),
    current_user: User = Depends(get_current_user),
):
    """
    Return the next posting date (pdate). Next Tuesday that is a US business day,
    or the following business day if that Tuesday is a US holiday.
    """
    base = None
    if tday:
        try:
            base = datetime.strptime(tday, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="tday must be YYYY-MM-DD")
    pdate = calculate_next_tuesday(base_date=base)
    pdate_dt = datetime.strptime(pdate, "%Y-%m-%d").date()
    return {
        "pdate": pdate,
        "is_us_business_day": is_business_day(pdate_dt, country=PDATE_COUNTRY),
        "country_used": PDATE_COUNTRY,
    }


# ---------- Admin-maintained holiday records (CRUD, admin-only) ----------
@router.get("/admin/holidays", response_model=List[HolidayResponse])
async def list_admin_holidays(
    country: Optional[str] = Query(None, description="Filter by country code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
):
    """List maintained holiday records (admin only), optionally filtered by country."""
    query = db.query(Holiday)
    if country:
        query = query.filter(Holiday.country == country)
    holidays = query.order_by(Holiday.country.asc(), Holiday.date.asc()).all()
    return holidays


@router.post("/admin/holidays", response_model=HolidayResponse)
async def create_admin_holiday(
    holiday_in: HolidayCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
):
    """Create a new maintained holiday (admin only)."""
    holiday = Holiday(
        country=holiday_in.country,
        date=holiday_in.date,
        name=holiday_in.name,
    )
    db.add(holiday)
    db.commit()
    db.refresh(holiday)
    return holiday


@router.delete("/admin/holidays/{holiday_id}", status_code=204)
async def delete_admin_holiday(
    holiday_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
):
    """Delete a maintained holiday (admin only)."""
    holiday = db.query(Holiday).filter(Holiday.id == holiday_id).first()
    if not holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")
    db.delete(holiday)
    db.commit()
    return Response(status_code=204)


@router.post("/pipeline/run", response_model=RunResponse)
async def create_pipeline_run(
    run_data: RunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_sales_team_access())
):
    """Create and execute a new pipeline run. Blocks if another run is already RUNNING (jobs run sequentially)."""
    # Block if any run is already in RUNNING state (sequential jobs only)
    running_query = db.query(PipelineRun).filter(PipelineRun.status == RunStatus.RUNNING)
    running_query = filter_by_sales_team(running_query, current_user)
    existing_running = running_query.first()
    if existing_running:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Another run is already in progress ({existing_running.run_id}). "
                "Jobs must run in sequence. Wait for it to finish or cancel it before starting a new run."
            ),
        )

    # Get sales team ID (enforced for SALES_TEAM users)
    sales_team_id = get_user_sales_team_id(current_user) if current_user.role == UserRole.SALES_TEAM else None

    # Create run context
    context = RunContext.create(
        sales_team_id=sales_team_id,
        created_by_id=current_user.id,
        pdate=run_data.pdate,
        irr_target=run_data.irr_target,
        tday=run_data.tday,
    )
    logger.info("Pipeline run starting run_id=%s user_id=%s pdate=%s", context.run_id, current_user.id, context.pdate)

    # Add sales team ID to file paths for isolation.
    # Inputs go to input directory; outputs go to output directory.
    # At the start of a run, the previous run is archived; at the end, the current run is archived.
    if sales_team_id:
        context.input_file_path = f"{run_data.folder}/sales_team_{sales_team_id}"
        context.output_dir = f"sales_team_{sales_team_id}/runs/{context.run_id}"
    else:
        context.input_file_path = run_data.folder
        context.output_dir = f"runs/{context.run_id}"
    
    # At the start of this run, archive the previous run (outputs and, when S3, inputs from storage).
    prev_run_query = db.query(PipelineRun).order_by(PipelineRun.created_at.desc()).limit(1)
    prev_run_query = filter_by_sales_team(prev_run_query, current_user)
    prev_run = prev_run_query.first()
    if prev_run and prev_run.run_id != context.run_id:
        archive_previous_run(
            prev_run_id=prev_run.run_id,
            output_prefix=prev_run.output_dir or f"runs/{prev_run.run_id}",
            input_prefix=prev_run.input_file_path,
        )
    
    # When using S3, run reads from the inputs area root: bucket/input/files_required/ (prefix "" = root of inputs).
    temp_dir = None
    if settings.STORAGE_TYPE == "s3":
        s3_prefix = ""  # root of inputs area -> bucket/input/files_required/
        try:
            logger.info("Pipeline run run_id=%s syncing S3 inputs (prefix=%s)", context.run_id, s3_prefix or "(root)")
            input_storage = get_storage_backend(area="inputs")
            temp_dir = sync_s3_input_to_temp(input_storage, s3_prefix)
            folder_for_run = temp_dir
            logger.info("Pipeline run run_id=%s S3 sync complete, starting execution", context.run_id)
        except FileNotFoundError as e:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No files found in inputs area (files_required/). "
                    "Upload files in File Manager to path 'files_required/' (default). Then start the run again."
                ),
            ) from e
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to load inputs from S3 input directory: {str(e)}",
            ) from e
    else:
        folder_for_run = run_data.folder
    
    try:
        with PipelineExecutor(context) as executor:
            result = executor.execute(folder_for_run)

        # Get updated run record
        run_record = db.query(PipelineRun).filter(PipelineRun.run_id == context.run_id).first()
        logger.info("Pipeline run run_id=%s completed successfully", context.run_id)
        return run_record

    except RunCancelledException:
        run_record = db.query(PipelineRun).filter(PipelineRun.run_id == context.run_id).first()
        if run_record:
            return run_record
        raise HTTPException(status_code=500, detail="Run was cancelled but run record not found")
    except Exception as e:
        logger.exception("Pipeline run run_id=%s failed: %s", context.run_id, e)
        detail = (
            f"Pipeline execution failed: {str(e)}. run_id={context.run_id}. "
            "Check application logs (e.g. AWS CloudWatch log group for this environment, e.g. /ecs/loan-engine-qa) for details."
        )
        raise HTTPException(status_code=500, detail=detail) from e
    finally:
        if temp_dir:
            remove_temp_input_dir(temp_dir)


@router.get("/runs", response_model=List[RunResponse])
async def list_runs(
    response: Response,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    run_weekday: Optional[int] = Query(None, ge=0, le=6, description="Filter by day of week (0=Monday .. 6=Sunday)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List pipeline runs with pagination. Filter by run_weekday for day-of-week segregation."""
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    query = db.query(PipelineRun)
    
    # Apply sales team filter
    query = filter_by_sales_team(query, current_user)
    
    # Log data access
    log_data_access(current_user, 'pipeline_runs', sales_team_id=current_user.sales_team_id)
    
    # Filter by status if provided
    if status:
        try:
            status_enum = RunStatus(status)
            query = query.filter(PipelineRun.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    # Filter by day of week (activity segregation)
    if run_weekday is not None:
        query = query.filter(PipelineRun.run_weekday == run_weekday)
    
    # Order by created_at descending
    query = query.order_by(PipelineRun.created_at.desc())
    
    # Paginate
    runs = query.offset(skip).limit(limit).all()
    return runs


@router.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific pipeline run."""
    query = db.query(PipelineRun).filter(PipelineRun.run_id == run_id)
    query = filter_by_sales_team(query, current_user)
    
    run = query.first()
    if not run:
        log_authorization_failure(current_user, 'get_run', 'run_not_found', run_id)
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Log data access
    log_data_access(current_user, 'pipeline_run', run_id, sales_team_id=run.sales_team_id)
    
    return run


@router.post("/runs/{run_id}/cancel", response_model=RunResponse)
async def cancel_run(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a running pipeline run. Jobs run sequentially; cancelling frees the slot for a new run."""
    query = db.query(PipelineRun).filter(PipelineRun.run_id == run_id)
    query = filter_by_sales_team(query, current_user)
    run = query.first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status != RunStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail=f"Run is not running (status={run.status}). Only runs in 'running' state can be cancelled.",
        )
    run.status = RunStatus.CANCELLED
    run.completed_at = datetime.utcnow()
    err_list = list(run.errors) if run.errors else []
    err_list.append("Cancelled by user")
    run.errors = err_list
    db.commit()
    db.refresh(run)
    logger.info("Pipeline run run_id=%s cancelled by user_id=%s", run_id, current_user.id)
    return run


@router.get("/runs/{run_id}/notebook-outputs")
async def list_notebook_outputs(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List the 4 notebook-replacement output files for a run.

    Files are stored under the per-run prefix `PipelineRun.output_dir` in the **outputs** storage area
    (local disk in development, S3 in test/production).
    """
    query = db.query(PipelineRun).filter(PipelineRun.run_id == run_id)
    query = filter_by_sales_team(query, current_user)
    run = query.first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    prefix = (run.output_dir or f"runs/{run_id}").strip("/")
    # Back-compat: older runs stored absolute local paths in output_dir. Those aren't usable
    # with the storage abstraction (which expects a relative key within the outputs area).
    if ":" in prefix or prefix.startswith(("/", "\\")):
        prefix = f"runs/{run_id}"
    storage = get_storage_backend(area="outputs")

    outputs = []
    for d in NOTEBOOK_OUTPUT_DEFS:
        path = f"{prefix}/{d['filename']}"
        outputs.append(
            {
                "key": d["key"],
                "label": d["label"],
                "path": path,
                "exists": storage.file_exists(path),
            }
        )
    return {"run_id": run_id, "prefix": prefix, "outputs": outputs}


def _media_type_for_filename(filename: str) -> str:
    """Return media type for notebook output download."""
    if filename.endswith(".json"):
        return "application/json"
    if filename.endswith(".xlsx"):
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return "application/octet-stream"


@router.get("/runs/{run_id}/notebook-outputs/{output_key}/download")
async def download_notebook_output(
    run_id: str,
    output_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download one of the notebook-replacement output files for a run (Excel or JSON)."""
    query = db.query(PipelineRun).filter(PipelineRun.run_id == run_id)
    query = filter_by_sales_team(query, current_user)
    run = query.first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    match = next((d for d in NOTEBOOK_OUTPUT_DEFS if d["key"] == output_key), None)
    if not match:
        raise HTTPException(status_code=404, detail="Unknown output key")

    prefix = (run.output_dir or f"runs/{run_id}").strip("/")
    if ":" in prefix or prefix.startswith(("/", "\\")):
        prefix = f"runs/{run_id}"
    path = f"{prefix}/{match['filename']}"
    storage = get_storage_backend(area="outputs")
    if not storage.file_exists(path):
        raise HTTPException(status_code=404, detail="File not found")

    content = storage.read_file(path)
    return StreamingResponse(
        io.BytesIO(content),
        media_type=_media_type_for_filename(match["filename"]),
        headers={"Content-Disposition": f'attachment; filename="{match["filename"]}"'},
    )


@router.get("/runs/{run_id}/archive")
async def list_run_archive(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List archived input and output files for a run (archive/{run_id}/input and archive/{run_id}/output).
    """
    query = db.query(PipelineRun).filter(PipelineRun.run_id == run_id)
    query = filter_by_sales_team(query, current_user)
    run = query.first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    try:
        storage = get_storage_backend(area="archive")
    except Exception:
        return {"run_id": run_id, "input": [], "output": [], "error": "Archive storage not configured"}

    def list_dir(prefix: str, download_prefix: str):
        try:
            files = storage.list_files(prefix, recursive=False)
            return [
                {
                    "path": f.path,
                    "size": f.size,
                    "last_modified": f.last_modified,
                    "name": f.path.split("/")[-1] if "/" in f.path else f.path,
                    "download_path": f"{download_prefix}/{f.path.split('/')[-1]}" if "/" in f.path else f"{download_prefix}/{f.path}",
                }
                for f in files if not f.is_directory
            ]
        except Exception:
            return []

    input_prefix = f"{run_id}/input"
    output_prefix = f"{run_id}/output"
    input_files = list_dir(input_prefix, "input")
    output_files = list_dir(output_prefix, "output")
    return {"run_id": run_id, "input": input_files, "output": output_files}


@router.get("/runs/{run_id}/archive/download")
async def download_run_archive_file(
    run_id: str,
    path: str = Query(..., description="Path relative to run archive: input/filename or output/filename"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download a file from the run archive (input or output)."""
    if ".." in path or path.strip("/").startswith(".."):
        raise HTTPException(status_code=400, detail="Invalid path")
    if not (path.startswith("input/") or path.startswith("output/")):
        raise HTTPException(status_code=400, detail="Path must be input/... or output/...")
    query = db.query(PipelineRun).filter(PipelineRun.run_id == run_id)
    query = filter_by_sales_team(query, current_user)
    run = query.first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    full_key = f"{run_id}/{path}"
    try:
        storage = get_storage_backend(area="archive")
    except Exception as e:
        raise HTTPException(status_code=503, detail="Archive storage not available") from e
    if not storage.file_exists(full_key):
        raise HTTPException(status_code=404, detail="File not found")

    content = storage.read_file(full_key)
    filename = path.split("/")[-1]
    media_type = "application/octet-stream"
    if filename.endswith(".xlsx"):
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif filename.endswith(".csv"):
        media_type = "text/csv"
    elif filename.endswith(".json"):
        media_type = "application/json"
    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/summary/{run_id}", response_model=SummaryResponse)
async def get_run_summary(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get summary metrics for a pipeline run."""
    query = db.query(PipelineRun).filter(PipelineRun.run_id == run_id)
    query = filter_by_sales_team(query, current_user)
    
    run = query.first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Get eligibility checks from run errors (stored as JSON)
    eligibility_checks = {}
    if run.errors:
        eligibility_checks = run.errors
    
    return {
        "run_id": run.run_id,
        "total_loans": run.total_loans,
        "total_balance": run.total_balance,
        "exceptions_count": run.exceptions_count,
        "eligibility_checks": eligibility_checks
    }


def _exceptions_query(
    db: Session,
    current_user: User,
    run_id: Optional[str] = None,
    exception_type: Optional[str] = None,
    severity: Optional[str] = None,
    rejection_criteria: Optional[str] = None,
):
    """Base filtered query for exceptions (list and export)."""
    query = db.query(LoanException).join(PipelineRun)
    query = filter_by_sales_team(query, current_user)
    if run_id:
        query = query.filter(PipelineRun.run_id == run_id)
    if exception_type:
        query = query.filter(LoanException.exception_type == exception_type)
    if severity:
        query = query.filter(LoanException.severity == severity)
    if rejection_criteria:
        query = query.filter(LoanException.rejection_criteria == rejection_criteria)
    return query.order_by(LoanException.created_at.desc())


@router.get("/exceptions", response_model=List[ExceptionResponse])
async def get_exceptions(
    run_id: Optional[str] = None,
    exception_type: Optional[str] = None,
    severity: Optional[str] = None,
    rejection_criteria: Optional[str] = Query(None, description="Filter by notebook rejection key (e.g. notebook.purchase_price_mismatch)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get loan exceptions with filtering (including rejection_criteria for notebook mapping)."""
    query = _exceptions_query(db, current_user, run_id, exception_type, severity, rejection_criteria)
    exceptions = query.offset(skip).limit(limit).all()
    return exceptions


@router.get("/exceptions/export")
async def export_exceptions(
    format: str = Query("csv", description="Export format: csv or xlsx"),
    run_id: Optional[str] = None,
    exception_type: Optional[str] = None,
    severity: Optional[str] = None,
    rejection_criteria: Optional[str] = None,
    limit: int = Query(10000, ge=1, le=50000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export loan exceptions to CSV or Excel. Uses same filters as GET /api/exceptions."""
    log_data_access(current_user, "exceptions_export", details={"format": format})
    query = _exceptions_query(db, current_user, run_id, exception_type, severity, rejection_criteria)
    rows = query.limit(limit).all()
    if not rows:
        raise HTTPException(status_code=404, detail="No exceptions match the filters.")
    # Build export rows (no loan_data to keep file simple)
    data = [
        {
            "seller_loan_number": e.seller_loan_number,
            "exception_type": e.exception_type,
            "exception_category": e.exception_category or "",
            "severity": e.severity or "",
            "message": e.message or "",
            "rejection_criteria": e.rejection_criteria or "",
            "created_at": e.created_at.isoformat() if e.created_at else "",
        }
        for e in rows
    ]
    df = pd.DataFrame(data)
    if format.lower() == "csv":
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        csv_bytes = buf.getvalue().encode("utf-8")
        filename = f"loan_exceptions_{datetime.utcnow().strftime('%Y-%m-%d_%H%M')}.csv"
        return Response(
            content=csv_bytes,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    if format.lower() in ("xlsx", "excel"):
        buf = io.BytesIO()
        df.to_excel(buf, index=False, engine="openpyxl")
        buf.seek(0)
        filename = f"loan_exceptions_{datetime.utcnow().strftime('%Y-%m-%d_%H%M')}.xlsx"
        return Response(
            content=buf.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    raise HTTPException(status_code=400, detail="format must be csv or xlsx")


@router.get("/loans", response_model=List[dict])
async def get_loans(
    run_id: str,
    disposition: Optional[str] = Query(
        None,
        description="Filter by disposition: to_purchase (eligible), projected, rejected",
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get loan facts for a run. Filter by disposition for to_purchase vs projected vs rejected."""
    # Verify run access
    run_query = db.query(PipelineRun).filter(PipelineRun.run_id == run_id)
    run_query = filter_by_sales_team(run_query, current_user)
    run = run_query.first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Get loan facts with sales team filtering
    query = db.query(LoanFact).join(PipelineRun).filter(LoanFact.run_id == run.id)
    query = filter_by_sales_team(query, current_user)
    
    if disposition:
        query = query.filter(LoanFact.disposition == disposition)
    
    query = query.order_by(LoanFact.created_at.desc())
    facts = query.offset(skip).limit(limit).all()
    
    # Return dicts with loan_data plus disposition and rejection_criteria
    out = []
    for fact in facts:
        item = {
            "seller_loan_number": fact.seller_loan_number,
            "disposition": getattr(fact, "disposition", None),
            "rejection_criteria": getattr(fact, "rejection_criteria", None),
        }
        if fact.loan_data:
            item["loan_data"] = fact.loan_data
        out.append(item)
    return out


@router.get("/sales-teams", response_model=List[dict])
async def list_sales_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """List all sales teams (admin only)."""
    teams = db.query(SalesTeam).filter(SalesTeam.is_active == True).all()
    return [
        {
            "id": team.id,
            "name": team.name,
            "description": team.description,
            "user_count": len(team.users)
        }
        for team in teams
    ]
