"""File discovery utilities for dynamic input file resolution."""
from pathlib import Path
from typing import Optional, List
import logging
import re
from datetime import datetime
from utils.date_utils import calculate_last_month_end

logger = logging.getLogger(__name__)


def find_file_by_pattern(
    directory: str,
    pattern: str,
    date_str: Optional[str] = None,
    required: bool = True
) -> Optional[Path]:
    """
    Find a file matching a pattern in the given directory.
    
    Args:
        directory: Base directory to search
        pattern: File pattern (supports {date} placeholder)
        date_str: Optional date string to substitute in pattern
        required: If True, raises error when file not found
    
    Returns:
        Path to found file, or None if not found and not required
    
    Examples:
        find_file_by_pattern("/data", "Tape20Loans_{date}.csv", "10-21-2025")
        find_file_by_pattern("/data", "SFY_*.xlsx")  # Wildcard pattern
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        if required:
            raise FileNotFoundError(f"Directory not found: {directory}")
        return None
    
    # Substitute date if provided
    if date_str and '{date}' in pattern:
        search_pattern = pattern.replace('{date}', date_str)
    else:
        search_pattern = pattern
    
    # Convert glob pattern to regex
    regex_pattern = search_pattern.replace('*', '.*').replace('?', '.')
    
    # Search for matching files
    matches = []
    for file_path in dir_path.iterdir():
        if file_path.is_file() and re.match(regex_pattern, file_path.name):
            matches.append(file_path)
    
    if not matches:
        if required:
            # List available files to help user
            available_files = [f.name for f in dir_path.iterdir() if f.is_file()]
            available_str = "\n  - ".join(available_files[:10])  # Show first 10
            if len(available_files) > 10:
                available_str += f"\n  ... and {len(available_files) - 10} more files"
            
            error_msg = (
                f"No file found matching pattern '{pattern}' in {directory}\n"
                f"Available files in directory:\n  - {available_str if available_files else '(directory is empty)'}"
            )
            raise FileNotFoundError(error_msg)
        logger.warning(f"No file found matching pattern '{pattern}' in {directory}")
        return None
    
    if len(matches) > 1:
        # If multiple matches, prefer most recent
        matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        logger.warning(
            f"Multiple files match pattern '{pattern}'. Using most recent: {matches[0].name}"
        )
    
    return matches[0]


def find_tape_loans_file(directory: str, yesterday: str, required: bool = True) -> Optional[Path]:
    """
    Find Tape20Loans CSV file.
    
    Expected pattern: Tape20Loans_MM-DD-YYYY.csv
    """
    pattern = f"Tape20Loans_{yesterday}.csv"
    return find_file_by_pattern(
        f"{directory}/files_required",
        pattern,
        required=required
    )


def find_sfy_file(directory: str, date_str: Optional[str] = None, required: bool = True) -> Optional[Path]:
    """
    Find SFY Exhibit file.
    
    Expected pattern: SFY_MM-DD-YYYY_ExhibitAtoFormofSaleNotice - Pre-Funding.xlsx
    If date_str not provided, searches for most recent matching file.
    """
    if date_str:
        pattern = f"SFY_{date_str}_ExhibitAtoFormofSaleNotice - Pre-Funding.xlsx"
        return find_file_by_pattern(
            f"{directory}/files_required",
            pattern,
            required=required
        )
    else:
        # Search for any SFY file matching pattern
        return find_file_by_pattern(
            f"{directory}/files_required",
            "SFY_*_ExhibitAtoFormofSaleNotice - Pre-Funding.xlsx",
            required=required
        )


def find_prime_file(directory: str, date_str: Optional[str] = None, required: bool = True) -> Optional[Path]:
    """
    Find PRIME Exhibit file.
    
    Expected pattern: PRIME_MM-DD-YYYY_ExhibitAtoFormofSaleNotice - Pre-Funding.xlsx
    If date_str not provided, searches for most recent matching file.
    """
    if date_str:
        pattern = f"PRIME_{date_str}_ExhibitAtoFormofSaleNotice - Pre-Funding.xlsx"
        return find_file_by_pattern(
            f"{directory}/files_required",
            pattern,
            required=required
        )
    else:
        # Search for any PRIME file matching pattern
        return find_file_by_pattern(
            f"{directory}/files_required",
            "PRIME_*_ExhibitAtoFormofSaleNotice - Pre-Funding.xlsx",
            required=required
        )


def find_fx_file(directory: str, last_end: str, fx_number: int = 3, required: bool = False) -> Optional[Path]:
    """
    Find FX servicing file.
    
    Expected pattern: FX{number}_{last_end}.xlsx
    """
    pattern = f"FX{fx_number}_{last_end}.xlsx"
    return find_file_by_pattern(
        f"{directory}/files_required",
        pattern,
        required=required
    )


def discover_input_files(
    directory: str,
    yesterday: str,
    sfy_date: Optional[str] = None,
    prime_date: Optional[str] = None
) -> dict:
    """
    Discover all input files needed for pipeline execution.
    
    Returns:
        Dictionary with file paths:
        {
            'loans': Path,
            'sfy_file': Path,
            'prime_file': Path,
            'fx3_file': Optional[Path],
            'fx4_file': Optional[Path]
        }
    """
    files = {}
    
    # Required files
    files['loans'] = find_tape_loans_file(directory, yesterday, required=True)
    files['sfy_file'] = find_sfy_file(directory, sfy_date, required=True)
    files['prime_file'] = find_prime_file(directory, prime_date, required=True)
    
    # Optional FX files
    last_end = calculate_last_month_end()
    files['fx3_file'] = find_fx_file(directory, last_end, fx_number=3, required=False)
    files['fx4_file'] = find_fx_file(directory, last_end, fx_number=4, required=False)
    
    logger.info(f"Discovered input files: {[str(f) if f else None for f in files.values()]}")
    
    return files
