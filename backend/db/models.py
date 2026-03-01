"""Database models for the loan engine."""
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    Text,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from db.connection import Base


class UserRole(str, enum.Enum):
    """User roles for authorization."""
    ADMIN = "admin"
    ANALYST = "analyst"
    SALES_TEAM = "sales_team"


class RunStatus(str, enum.Enum):
    """Pipeline run status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(
        SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x]),
        default=UserRole.ANALYST,
        nullable=False,
    )
    sales_team_id = Column(Integer, ForeignKey("sales_teams.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    sales_team = relationship("SalesTeam", back_populates="users")
    runs = relationship("PipelineRun", back_populates="created_by_user")


class SalesTeam(Base):
    """Sales team model for multi-tenancy."""
    __tablename__ = "sales_teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="sales_team")
    runs = relationship("PipelineRun", back_populates="sales_team")


class PipelineRun(Base):
    """Pipeline execution run tracking."""
    __tablename__ = "pipeline_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(100), unique=True, index=True, nullable=False)
    status = Column(
        SQLEnum(RunStatus, values_callable=lambda x: [e.value for e in x]),
        default=RunStatus.PENDING,
        nullable=False,
    )
    sales_team_id = Column(Integer, ForeignKey("sales_teams.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Run parameters
    pdate = Column(String(20))  # Purchase date (YYYY-MM-DD)
    irr_target = Column(Float, default=8.05)
    input_file_path = Column(String(500))
    output_dir = Column(String(500))
    
    # Day-of-week segregation (0=Monday .. 6=Sunday; derived from pdate)
    run_weekday = Column(Integer, nullable=True)  # 0-6
    run_weekday_name = Column(String(20), nullable=True)  # Monday, Tuesday, ...
    
    # Results summary
    total_loans = Column(Integer, default=0)
    total_balance = Column(Float, default=0.0)
    exceptions_count = Column(Integer, default=0)
    errors = Column(JSON, default=list)
    
    # Last pipeline phase reached (for stuck runs: shows where execution stopped)
    last_phase = Column(String(80), nullable=True)
    
    # Timestamps
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    sales_team = relationship("SalesTeam", back_populates="runs")
    created_by_user = relationship("User", back_populates="runs")
    exceptions = relationship("LoanException", back_populates="run")

    @property
    def created_by_username(self) -> str | None:
        """Convenience property for API responses: username of user who started the run."""
        return self.created_by_user.username if self.created_by_user else None


class LoanException(Base):
    """Loan-level exceptions and validations."""
    __tablename__ = "loan_exceptions"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("pipeline_runs.id"), nullable=False)
    seller_loan_number = Column(String(100), index=True, nullable=False)
    
    # Exception details
    exception_type = Column(String(100), nullable=False)  # purchase_price, underwriting, comap, eligibility
    exception_category = Column(String(100))  # flagged, mismatch, etc.
    severity = Column(String(20), default="warning")  # error, warning, info
    message = Column(Text)
    # Canonical rejection criteria key mapping to notebook (see NOTEBOOK_REJECTION_MAPPING.md)
    rejection_criteria = Column(String(120), nullable=True)
    loan_data = Column(JSON)  # Snapshot of loan data
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    run = relationship("PipelineRun", back_populates="exceptions")


class LoanFact(Base):
    """Processed loan facts for analytics."""
    __tablename__ = "loan_facts"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("pipeline_runs.id"), nullable=False)
    seller_loan_number = Column(String(100), index=True, nullable=False)
    
    # Loan attributes
    platform = Column(String(50))
    loan_program = Column(String(255))
    application_type = Column(String(100))
    orig_balance = Column(Float)
    purchase_price = Column(Float)
    lender_price_pct = Column(Float)
    fico_borrower = Column(Integer)
    dti = Column(Float)
    pti = Column(Float)
    term = Column(Integer)
    apr = Column(Float)
    property_state = Column(String(10))
    
    # Validation flags
    purchase_price_check = Column(Boolean, default=False)
    underwriting_pass = Column(Boolean, default=False)
    comap_pass = Column(Boolean, default=False)
    eligibility_pass = Column(Boolean, default=False)
    
    # Disposition: to_purchase (passed all checks), projected (included in run), rejected (failed one+ checks)
    disposition = Column(String(30), default="projected")  # to_purchase | projected | rejected
    # Canonical rejection reason mapping to notebook (set when disposition=rejected)
    rejection_criteria = Column(String(120), nullable=True)
    
    # Additional data
    loan_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    run = relationship("PipelineRun")


class Holiday(Base):
    """Maintained holiday calendar entries (admin-managed)."""

    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, index=True)
    country = Column(String(4), nullable=False, index=True)  # ISO country code (US, IN, GB, SG, etc.)
    date = Column(Date, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Ensure country/date pairs are logically unique at the application level; DB uniqueness can be added via migrations.
