"""Pipeline run context and parameters."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid
from utils.date_utils import calculate_next_tuesday


@dataclass
class RunContext:
    """Context for a pipeline execution run."""
    run_id: str
    sales_team_id: Optional[int]
    created_by_id: Optional[int]
    pdate: str  # Purchase date in YYYY-MM-DD format
    tday: str   # Base "today" date in YYYY-MM-DD format (for file naming)
    irr_target: float = 8.05
    input_file_path: Optional[str] = None
    output_dir: Optional[str] = None
    
    @classmethod
    def create(
        cls,
        sales_team_id: Optional[int] = None,
        created_by_id: Optional[int] = None,
        pdate: Optional[str] = None,
        irr_target: float = 8.05,
        tday: Optional[str] = None,
    ) -> "RunContext":
        """
        Create a new run context.
        
        - Tday defaults to today's date (YYYY-MM-DD) and is used as the base
          for file date calculations (yesterday, last month end, etc.).
        - pdate defaults to the next Tuesday after Tday (matching notebook logic).
        """
        now = datetime.now()
        run_id = f"run_{uuid.uuid4().hex[:12]}_{now.strftime('%Y%m%d_%H%M%S')}"
        
        # Resolve Tday (base date)
        if tday is None:
            base_date = now
            tday_str = now.strftime('%Y-%m-%d')
        else:
            try:
                base_date = datetime.strptime(tday, "%Y-%m-%d")
                tday_str = tday
            except ValueError:
                # Fall back to system date on invalid tday
                base_date = now
                tday_str = now.strftime('%Y-%m-%d')
        
        # Resolve purchase date
        if pdate is None:
            # Default to next Tuesday based on Tday/base_date (not wall-clock)
            pdate = calculate_next_tuesday(base_date=base_date)
        
        return cls(
            run_id=run_id,
            sales_team_id=sales_team_id,
            created_by_id=created_by_id,
            pdate=pdate,
            tday=tday_str,
            irr_target=irr_target,
        )
