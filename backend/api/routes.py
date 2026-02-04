"""API routes for loan engine."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from db.connection import get_db
from db.models import PipelineRun, RunStatus, LoanException, LoanFact, User, SalesTeam
from auth.security import get_current_user, require_role, require_sales_team_access, UserRole
from auth.validators import get_user_sales_team_id, validate_sales_team_access
from auth.audit import log_data_access, log_authorization_failure
from orchestration.run_context import RunContext
from orchestration.pipeline import PipelineExecutor
from config.settings import settings

router = APIRouter(prefix="/api", tags=["api"])


class RunCreate(BaseModel):
    """Pipeline run creation model."""
    pdate: Optional[str] = None
    irr_target: float = 8.05
    folder: str = "C:/Users/omack/Intrepid/pythonFramework/loan_engine/legacy"


class RunResponse(BaseModel):
    """Pipeline run response model."""
    id: int
    run_id: str
    status: str
    sales_team_id: Optional[int]
    total_loans: int
    total_balance: float
    exceptions_count: int
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


def filter_by_sales_team(query, user: User):
    """Filter query by sales team if user is sales team member."""
    if user.role == UserRole.SALES_TEAM and user.sales_team_id:
        return query.filter(PipelineRun.sales_team_id == user.sales_team_id)
    elif user.role == UserRole.ADMIN:
        return query  # Admins see all
    else:
        return query  # Analysts see all for now


@router.post("/pipeline/run", response_model=RunResponse)
async def create_pipeline_run(
    run_data: RunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_sales_team_access())
):
    """Create and execute a new pipeline run."""
    # Get sales team ID (enforced for SALES_TEAM users)
    sales_team_id = get_user_sales_team_id(current_user) if current_user.role == UserRole.SALES_TEAM else None
    
    # Create run context
    context = RunContext.create(
        sales_team_id=sales_team_id,
        created_by_id=current_user.id,
        pdate=run_data.pdate,
        irr_target=run_data.irr_target
    )
    
    # Add sales team ID to file paths for isolation
    if sales_team_id:
        context.input_file_path = f"{run_data.folder}/sales_team_{sales_team_id}"
        context.output_dir = f"{run_data.folder}/sales_team_{sales_team_id}/output"
    else:
        context.input_file_path = run_data.folder
        context.output_dir = f"{run_data.folder}/output"
    
    # Execute pipeline
    try:
        with PipelineExecutor(context) as executor:
            result = executor.execute(run_data.folder)
        
        # Get updated run record
        run_record = db.query(PipelineRun).filter(PipelineRun.run_id == context.run_id).first()
        return run_record
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")


@router.get("/runs", response_model=List[RunResponse])
async def list_runs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List pipeline runs with pagination."""
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


@router.get("/exceptions", response_model=List[ExceptionResponse])
async def get_exceptions(
    run_id: Optional[str] = None,
    exception_type: Optional[str] = None,
    severity: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get loan exceptions with filtering."""
    query = db.query(LoanException).join(PipelineRun)
    
    # Apply sales team filter
    query = filter_by_sales_team(query, current_user)
    
    if run_id:
        query = query.filter(PipelineRun.run_id == run_id)
    
    if exception_type:
        query = query.filter(LoanException.exception_type == exception_type)
    
    if severity:
        query = query.filter(LoanException.severity == severity)
    
    query = query.order_by(LoanException.created_at.desc())
    exceptions = query.offset(skip).limit(limit).all()
    
    return exceptions


@router.get("/loans", response_model=List[dict])
async def get_loans(
    run_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get loan facts for a run."""
    # Verify run access
    run_query = db.query(PipelineRun).filter(PipelineRun.run_id == run_id)
    run_query = filter_by_sales_team(run_query, current_user)
    run = run_query.first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Get loan facts with sales team filtering
    query = db.query(LoanFact).join(PipelineRun).filter(LoanFact.run_id == run.id)
    query = filter_by_sales_team(query, current_user)
    query = query.order_by(LoanFact.created_at.desc())
    facts = query.offset(skip).limit(limit).all()
    
    # Convert to dicts
    return [fact.loan_data for fact in facts]


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
