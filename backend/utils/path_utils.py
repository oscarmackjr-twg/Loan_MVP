"""Path utilities for sales team isolation."""
from pathlib import Path
from typing import Optional


def get_sales_team_input_path(base_path: str, sales_team_id: Optional[int]) -> str:
    """
    Get input path for sales team (with isolation if sales_team_id provided).
    
    Args:
        base_path: Base input directory
        sales_team_id: Optional sales team ID
    
    Returns:
        Input path string
    """
    if sales_team_id:
        return str(Path(base_path) / f"sales_team_{sales_team_id}")
    return base_path


def get_sales_team_output_path(base_path: str, sales_team_id: Optional[int]) -> str:
    """
    Get output path for sales team (with isolation if sales_team_id provided).
    
    Args:
        base_path: Base output directory
        sales_team_id: Optional sales team ID
    
    Returns:
        Output path string
    """
    if sales_team_id:
        return str(Path(base_path) / f"sales_team_{sales_team_id}" / "output")
    return str(Path(base_path) / "output")


def get_sales_team_share_path(base_path: str, sales_team_id: Optional[int]) -> str:
    """
    Get output_share path for sales team (with isolation if sales_team_id provided).
    
    Args:
        base_path: Base output directory
        sales_team_id: Optional sales team ID
    
    Returns:
        Output share path string
    """
    if sales_team_id:
        return str(Path(base_path) / f"sales_team_{sales_team_id}" / "output_share")
    return str(Path(base_path) / "output_share")
