"""Excel export functionality."""
import pandas as pd
from pathlib import Path
from typing import Optional


def export_to_excel(
    df: pd.DataFrame,
    file_path: str,
    sheet_name: str = "Sheet1",
    max_cols: Optional[int] = None
) -> None:
    """Export dataframe to Excel file."""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    
    export_df = df.copy()
    if max_cols:
        export_df = export_df.iloc[:, :max_cols]
    
    export_df.to_excel(file_path, sheet_name=sheet_name, index=False)


def export_exception_reports(
    purchase_mismatch: pd.DataFrame,
    flagged_loans: pd.DataFrame,
    notes_flagged: pd.DataFrame,
    comap_failed: pd.DataFrame,
    output_dir: str,
    output_share_dir: str
) -> dict:
    """Export all exception reports to Excel."""
    reports = {}
    
    # Internal reports (full data)
    if not purchase_mismatch.empty:
        purchase_path = f"{output_dir}/purchase_price_mismatch.xlsx"
        export_to_excel(purchase_mismatch, purchase_path)
        reports['purchase_price_mismatch'] = purchase_path
    
    if not flagged_loans.empty:
        flagged_path = f"{output_dir}/flagged_loans_first.xlsx"
        export_to_excel(flagged_loans, flagged_path)
        reports['flagged_loans'] = flagged_path
    
    if not notes_flagged.empty:
        notes_path = f"{output_dir}/NOTES_flagged_loans_first.xlsx"
        export_to_excel(notes_flagged, notes_path)
        reports['notes_flagged'] = notes_path
    
    if not comap_failed.empty:
        comap_path = f"{output_dir}/comap_not_passed.xlsx"
        export_to_excel(comap_failed, comap_path)
        reports['comap_failed'] = comap_path
    
    # Shared reports (limited columns)
    if not purchase_mismatch.empty:
        purchase_share_path = f"{output_share_dir}/purchase_price_mismatch.xlsx"
        export_to_excel(purchase_mismatch.iloc[:, :30], purchase_share_path)
        reports['purchase_price_mismatch_share'] = purchase_share_path
    
    if not flagged_loans.empty:
        flagged_share_path = f"{output_share_dir}/flagged_loans_first.xlsx"
        export_to_excel(flagged_loans.iloc[:, :30], flagged_share_path)
        reports['flagged_loans_share'] = flagged_share_path
    
    if not notes_flagged.empty:
        notes_share_path = f"{output_share_dir}/NOTES_flagged_loans_first.xlsx"
        export_to_excel(notes_flagged.iloc[:, :30], notes_share_path)
        reports['notes_flagged_share'] = notes_share_path
    
    if not comap_failed.empty:
        comap_share_path = f"{output_share_dir}/comap_not_passed.xlsx"
        export_to_excel(comap_failed.iloc[:, :30], comap_share_path)
        reports['comap_failed_share'] = comap_share_path
    
    return reports
