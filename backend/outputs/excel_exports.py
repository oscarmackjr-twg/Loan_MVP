"""Excel export functionality."""
import io
import pandas as pd
from pathlib import Path
from typing import Optional

from storage.base import StorageBackend


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


def export_to_excel_bytes(
    df: pd.DataFrame,
    sheet_name: str = "Sheet1",
    max_cols: Optional[int] = None,
) -> bytes:
    """Export dataframe to an Excel workbook (bytes)."""
    export_df = df.copy()
    if max_cols:
        export_df = export_df.iloc[:, :max_cols]

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        export_df.to_excel(writer, sheet_name=sheet_name, index=False)
    buffer.seek(0)
    return buffer.read()


def export_exception_reports(
    purchase_mismatch: pd.DataFrame,
    flagged_loans: pd.DataFrame,
    notes_flagged: pd.DataFrame,
    comap_failed: pd.DataFrame,
    output_prefix: str,
    output_share_prefix: str,
    *,
    storage: StorageBackend,
    share_storage: StorageBackend,
    special_asset_prime: Optional[pd.DataFrame] = None,
    special_asset_sfy: Optional[pd.DataFrame] = None,
) -> dict:
    """
    Export notebook-replacement exception reports and special-asset outputs.

    Writes:
    - flagged_loans.xlsx, purchase_price_mismatch.xlsx, comap_not_passed.xlsx, notes_flagged_loans.xlsx
    - to both internal outputs and share (share = first 30 columns).
    - special_asset_prime.xlsx, special_asset_sfy.xlsx to internal outputs only (when non-empty).
    """
    reports = {}
    
    # Internal reports (full data)
    if not purchase_mismatch.empty:
        purchase_path = f"{output_prefix}/purchase_price_mismatch.xlsx"
        storage.write_file(purchase_path, export_to_excel_bytes(purchase_mismatch))
        reports["purchase_price_mismatch"] = purchase_path
    
    if not flagged_loans.empty:
        flagged_path = f"{output_prefix}/flagged_loans.xlsx"
        storage.write_file(flagged_path, export_to_excel_bytes(flagged_loans))
        reports["flagged_loans"] = flagged_path
    
    if not notes_flagged.empty:
        notes_path = f"{output_prefix}/notes_flagged_loans.xlsx"
        storage.write_file(notes_path, export_to_excel_bytes(notes_flagged))
        reports["notes_flagged_loans"] = notes_path
    
    if not comap_failed.empty:
        comap_path = f"{output_prefix}/comap_not_passed.xlsx"
        storage.write_file(comap_path, export_to_excel_bytes(comap_failed))
        reports["comap_not_passed"] = comap_path
    
    # Shared reports (limited columns)
    if not purchase_mismatch.empty:
        purchase_share_path = f"{output_share_prefix}/purchase_price_mismatch.xlsx"
        share_storage.write_file(purchase_share_path, export_to_excel_bytes(purchase_mismatch, max_cols=30))
        reports["purchase_price_mismatch_share"] = purchase_share_path
    
    if not flagged_loans.empty:
        flagged_share_path = f"{output_share_prefix}/flagged_loans.xlsx"
        share_storage.write_file(flagged_share_path, export_to_excel_bytes(flagged_loans, max_cols=30))
        reports["flagged_loans_share"] = flagged_share_path
    
    if not notes_flagged.empty:
        notes_share_path = f"{output_share_prefix}/notes_flagged_loans.xlsx"
        share_storage.write_file(notes_share_path, export_to_excel_bytes(notes_flagged, max_cols=30))
        reports["notes_flagged_loans_share"] = notes_share_path
    
    if not comap_failed.empty:
        comap_share_path = f"{output_share_prefix}/comap_not_passed.xlsx"
        share_storage.write_file(comap_share_path, export_to_excel_bytes(comap_failed, max_cols=30))
        reports["comap_not_passed_share"] = comap_share_path
    
    # Special asset outputs (notebook: special_asset_prime.xlsx; mirror for SFY)
    if special_asset_prime is not None and not special_asset_prime.empty:
        path = f"{output_prefix}/special_asset_prime.xlsx"
        storage.write_file(path, export_to_excel_bytes(special_asset_prime))
        reports["special_asset_prime"] = path
    if special_asset_sfy is not None and not special_asset_sfy.empty:
        path = f"{output_prefix}/special_asset_sfy.xlsx"
        storage.write_file(path, export_to_excel_bytes(special_asset_sfy))
        reports["special_asset_sfy"] = path
    
    return reports
