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
    irr_target: float = 8.05
    input_file_path: Optional[str] = None
    output_dir: Optional[str] = None
    
    @classmethod
    def create(
        cls,
        sales_team_id: Optional[int] = None,
        created_by_id: Optional[int] = None,
        pdate: Optional[str] = None,
        irr_target: float = 8.05
    ) -> "RunContext":
        """Create a new run context."""
        run_id = f"run_{uuid.uuid4().hex[:12]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if pdate is None:
            # Default to next Tuesday (matching notebook logic)
            pdate = calculate_next_tuesday()
        
        return cls(
            run_id=run_id,
            sales_team_id=sales_team_id,
            created_by_id=created_by_id,
            pdate=pdate,
            irr_target=irr_target
        )
