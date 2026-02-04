"""Date calculation utilities for file naming and pipeline execution."""
from datetime import datetime, timedelta
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


def calculate_next_tuesday() -> str:
    """
    Calculate next Tuesday date in YYYY-MM-DD format.
    If today is Tuesday, returns next Tuesday (7 days away).
    """
    today = datetime.today()
    days_until_tuesday = (1 - today.weekday() + 7) % 7  # 1 is Tuesday
    days_until_tuesday = 7 if days_until_tuesday == 0 else days_until_tuesday
    next_tuesday = today + timedelta(days=days_until_tuesday)
    return next_tuesday.strftime('%Y-%m-%d')


def calculate_yesterday() -> str:
    """Calculate yesterday's date in MM-DD-YYYY format."""
    yesterday = datetime.today() - timedelta(days=1)
    return yesterday.strftime('%m-%d-%Y')


def calculate_last_month_end() -> str:
    """
    Calculate last day of previous month in YYYY_MMM_DD format.
    Example: 2025_010_31 for January 31, 2025
    """
    today = datetime.today()
    first_day_of_current_month = datetime(today.year, today.month, 1)
    last_day_previous_month = first_day_of_current_month - timedelta(days=1)
    return f"{last_day_previous_month.year}_{last_day_previous_month.month:03}_{last_day_previous_month.day:02}"


def calculate_pipeline_dates(pdate: str = None) -> Tuple[str, str, str]:
    """
    Calculate all dates needed for pipeline execution.
    
    Args:
        pdate: Optional purchase date override (YYYY-MM-DD). If None, calculates next Tuesday.
    
    Returns:
        Tuple of (pdate, yesterday, last_end)
        - pdate: Purchase date in YYYY-MM-DD format
        - yesterday: Yesterday in MM-DD-YYYY format (for Tape20Loans files)
        - last_end: Last month end in YYYY_MMM_DD format (for FX files)
    """
    if pdate is None:
        pdate = calculate_next_tuesday()
    
    yesterday = calculate_yesterday()
    last_end = calculate_last_month_end()
    
    logger.info(f"Calculated dates - pdate: {pdate}, yesterday: {yesterday}, last_end: {last_end}")
    
    return pdate, yesterday, last_end
