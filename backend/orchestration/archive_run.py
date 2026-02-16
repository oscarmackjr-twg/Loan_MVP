"""Archive input and output files for each pipeline run under archive root: {run_id}/input and {run_id}/output.

- Input files are read from the input directory; outputs are written to the output directory.
- At the start of a new run, the previous run is archived (its output dir and, when available, input prefix).
- At the end of a run, the current run is also archived (inputs from run folder, outputs from storage).
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from storage import get_storage_backend
from storage.base import StorageBackend
from utils.date_utils import calculate_pipeline_dates, calculate_last_month_end
from utils.file_discovery import discover_input_files

logger = logging.getLogger(__name__)

# Reference files always loaded by the pipeline (under folder/files_required/)
REFERENCE_FILENAMES = [
    "MASTER_SHEET.xlsx",
    "MASTER_SHEET - Notes.xlsx",
    "current_assets.csv",
    "Underwriting_Grids_COMAP.xlsx",
]


def _collect_input_paths(folder: str, pdate: Optional[str]) -> List[Path]:
    """Collect all input file paths used for this run (reference + discovered)."""
    folder_path = Path(folder)
    paths = []

    # Reference files
    files_required = folder_path / "files_required"
    for name in REFERENCE_FILENAMES:
        p = files_required / name
        if p.exists():
            paths.append(p)

    # Discovered input files (loans, sfy, prime, optional fx3/fx4)
    try:
        pdate_val, yesterday, _ = calculate_pipeline_dates(pdate)
        file_paths = discover_input_files(
            directory=folder,
            yesterday=yesterday,
            sfy_date=None,
            prime_date=None,
        )
        for key in ("loans", "sfy_file", "prime_file", "fx3_file", "fx4_file"):
            fp = file_paths.get(key)
            if fp is not None:
                path = Path(fp) if not isinstance(fp, Path) else fp
                if path.exists() and path not in paths:
                    paths.append(path)
    except Exception as e:
        logger.warning("Could not discover input files for archive: %s", e)

    return paths


def _copy_inputs_to_archive(
    run_id: str,
    folder: str,
    pdate: Optional[str],
    archive_storage: StorageBackend,
) -> int:
    """Copy input files used for this run to archive/{run_id}/input/. Returns count copied."""
    input_paths = _collect_input_paths(folder, pdate)
    prefix = f"{run_id}/input"
    archive_storage.create_directory(prefix)
    count = 0
    for src in input_paths:
        try:
            content = src.read_bytes()
            key = f"{prefix}/{src.name}"
            archive_storage.write_file(key, content)
            count += 1
            logger.debug("Archived input %s -> %s", src.name, key)
        except Exception as e:
            logger.warning("Failed to archive input %s: %s", src, e)
    if count:
        logger.info("Archived %d input file(s) to %s", count, prefix)
    return count


def _copy_outputs_to_archive(
    run_id: str,
    output_prefix: str,
    reports: Dict[str, Any],
    output_storage: StorageBackend,
    archive_storage: StorageBackend,
    eligibility_report_local_path: Optional[str] = None,
) -> int:
    """Copy output files produced for this run to archive/{run_id}/output/. Returns count copied."""
    prefix = f"{run_id}/output"
    archive_storage.create_directory(prefix)
    count = 0

    # Exception reports and share reports (stored in output_storage at output_prefix)
    report_keys = [
        "purchase_price_mismatch",
        "flagged_loans",
        "notes_flagged_loans",
        "comap_not_passed",
    ]
    for key in report_keys:
        path = reports.get(key)
        if not path:
            continue
        try:
            content = output_storage.read_file(path)
            # path is like "runs/run_xxx/flagged_loans.xlsx"
            name = Path(path).name
            archive_storage.write_file(f"{prefix}/{name}", content)
            count += 1
        except Exception as e:
            logger.warning("Failed to archive report %s: %s", path, e)

    # Eligibility report may be on local disk (export_eligibility_report writes to local path)
    if eligibility_report_local_path:
        for suffix in ("eligibility_checks.json", "eligibility_checks_summary.xlsx"):
            local_path = Path(eligibility_report_local_path).parent / suffix
            if local_path.exists():
                try:
                    content = local_path.read_bytes()
                    archive_storage.write_file(f"{prefix}/{local_path.name}", content)
                    count += 1
                except Exception as e:
                    logger.warning("Failed to archive eligibility %s: %s", local_path, e)

    if count:
        logger.info("Archived %d output file(s) to %s", count, prefix)
    return count


def archive_run(
    run_id: str,
    folder: str,
    pdate: Optional[str],
    output_prefix: str,
    reports: Dict[str, Any],
    output_storage: StorageBackend,
    eligibility_report_local_path: Optional[str] = None,
) -> None:
    """
    Archive input and output files for a completed run to archive root: {run_id}/input and {run_id}/output.
    Safe to call on failure (logs and returns); best called after successful run.
    """
    try:
        archive_storage = get_storage_backend(area="archive")
    except Exception as e:
        logger.warning("Archive storage not available, skipping run archive: %s", e)
        return

    try:
        in_count = _copy_inputs_to_archive(run_id, folder, pdate, archive_storage)
        out_count = _copy_outputs_to_archive(
            run_id,
            output_prefix,
            reports,
            output_storage,
            archive_storage,
            eligibility_report_local_path=eligibility_report_local_path,
        )
        logger.info(
            "Run archive complete: %s (inputs=%d, outputs=%d)",
            run_id,
            in_count,
            out_count,
        )
    except Exception as e:
        logger.exception("Run archive failed for %s: %s", run_id, e)


def _is_s3_style_prefix(path: Optional[str]) -> bool:
    """True if path looks like an S3 prefix (no drive letter or absolute path)."""
    if not path or not path.strip():
        return False
    p = path.strip().replace("\\", "/")
    if ":" in p or p.startswith("/"):
        return False
    return True


def archive_previous_run(prev_run_id: str, output_prefix: str, input_prefix: Optional[str] = None) -> None:
    """
    Archive the previous run at the start of a new run.
    Copies all files under output_prefix to archive/{prev_run_id}/output.
    If input_prefix is set and looks like an S3/key prefix (not a local path), copies from input storage to archive/{prev_run_id}/input.
    Safe to call if archive or storage is unavailable (logs and returns).
    """
    try:
        archive_storage = get_storage_backend(area="archive")
        output_storage = get_storage_backend(area="outputs")
    except Exception as e:
        logger.warning("Storage not available for previous-run archive: %s", e)
        return

    out_count = 0
    try:
        # Archive previous run's output directory (list all files under output_prefix, copy to archive)
        out_prefix = (output_prefix or "").strip("/")
        if out_prefix:
            files = output_storage.list_files(out_prefix, recursive=True)
            archive_out_prefix = f"{prev_run_id}/output"
            archive_storage.create_directory(archive_out_prefix)
            for f in files:
                if f.is_directory or f.path.endswith("/"):
                    continue
                try:
                    content = output_storage.read_file(f.path)
                    name = Path(f.path).name
                    archive_storage.write_file(f"{archive_out_prefix}/{name}", content)
                    out_count += 1
                except Exception as e:
                    logger.warning("Failed to archive previous output %s: %s", f.path, e)
            if out_count:
                logger.info("Archived previous run %s: %d output file(s) -> %s", prev_run_id, out_count, archive_out_prefix)
    except Exception as e:
        logger.warning("Failed to archive previous run outputs: %s", e)

    # Optionally archive previous run's inputs from input storage (when it's an S3-style prefix)
    if input_prefix and _is_s3_style_prefix(input_prefix):
        try:
            input_storage = get_storage_backend(area="inputs")
            list_prefix = f"{input_prefix.strip('/')}/"
            files = input_storage.list_files(list_prefix, recursive=True)
            archive_in_prefix = f"{prev_run_id}/input"
            archive_storage.create_directory(archive_in_prefix)
            in_count = 0
            for f in files:
                if f.is_directory or f.path.endswith("/"):
                    continue
                try:
                    content = input_storage.read_file(f.path)
                    name = Path(f.path).name
                    archive_storage.write_file(f"{archive_in_prefix}/{name}", content)
                    in_count += 1
                except Exception as e:
                    logger.warning("Failed to archive previous input %s: %s", f.path, e)
            if in_count:
                logger.info("Archived previous run %s: %d input file(s) -> %s", prev_run_id, in_count, archive_in_prefix)
        except Exception as e:
            logger.debug("Could not archive previous run inputs from storage: %s", e)
