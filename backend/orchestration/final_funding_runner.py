"""Run Final Funding SG and CIBC workbooks using app standard inputs and outputs.

Expects workbook scripts to read FOLDER from environment (Path(os.environ.get("FOLDER"))).
We prepare a temp directory with the same structure as the pipeline (files_required/ under FOLDER),
run the script, then copy FOLDER/output and FOLDER/output_share into storage outputs area
under final_funding_sg/ or final_funding_cibc/ so results appear in the Program Runs file manager.
"""
import os
import shutil
import subprocess
import logging
import tempfile
from pathlib import Path
from typing import Optional

from config.settings import settings
from storage import get_storage_backend

logger = logging.getLogger(__name__)

FINAL_FUNDING_SG_PREFIX = "final_funding_sg"
FINAL_FUNDING_CIBC_PREFIX = "final_funding_cibc"


def _prepare_temp_input_from_local(input_base: str) -> str:
    """Copy local input_base (must contain files_required/) to a temp dir. Returns path to work dir that has files_required/."""
    base = Path(input_base).resolve()
    if not base.exists():
        raise FileNotFoundError(f"Input directory does not exist: {base}")
    files_required = base / "files_required"
    if not files_required.is_dir():
        raise FileNotFoundError(f"Input directory must contain files_required/: {base}")
    parent = Path(tempfile.mkdtemp(prefix="loan_engine_final_funding_"))
    work_dir = parent / "work"
    work_dir.mkdir()
    try:
        shutil.copytree(base, work_dir, dirs_exist_ok=True)
        return str(work_dir.resolve())
    except Exception:
        shutil.rmtree(parent, ignore_errors=True)
        raise


def _prepare_temp_input_from_s3(prefix: str) -> str:
    """Sync S3 inputs prefix to temp dir. Returns path to temp dir (with files_required under it if prefix is like 'input')."""
    from orchestration.s3_input_sync import sync_s3_input_to_temp
    input_storage = get_storage_backend(area="inputs")
    return sync_s3_input_to_temp(input_storage, prefix)


def _run_workbook_script(script_path: str, folder: str) -> None:
    """Run the workbook Python script with FOLDER env set."""
    env = os.environ.copy()
    env["FOLDER"] = folder
    result = subprocess.run(
        [os.environ.get("PYTHON", "python"), script_path],
        env=env,
        cwd=str(Path(script_path).parent),
        capture_output=True,
        text=True,
        timeout=3600,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Script failed: {result.stderr or result.stdout or 'unknown error'}")


def _upload_local_output_to_storage(local_folder: str, output_prefix: str) -> None:
    """Copy local_folder/output and local_folder/output_share into storage outputs under output_prefix."""
    folder_path = Path(local_folder)
    output_storage = get_storage_backend(area="outputs")
    for subdir in ("output", "output_share"):
        src = folder_path / subdir
        if not src.is_dir():
            continue
        for f in src.rglob("*"):
            if f.is_file():
                rel = f.relative_to(src)
                key = f"{output_prefix}/{subdir}/{rel.as_posix()}"
                content = f.read_bytes()
                output_storage.write_file(key, content)
                logger.debug("Uploaded %s -> %s", f, key)


def execute_final_funding_sg(folder: Optional[str] = None) -> str:
    """
    Run Final Funding SG workbook. Uses app inputs (folder or INPUT_DIR) and writes to outputs/final_funding_sg/.
    Returns output prefix for file manager.
    """
    script_path = getattr(settings, "FINAL_FUNDING_SG_SCRIPT_PATH", None) or os.environ.get("FINAL_FUNDING_SG_SCRIPT_PATH")
    if not script_path or not Path(script_path).exists():
        raise FileNotFoundError(
            "FINAL_FUNDING_SG_SCRIPT_PATH not set or file not found. "
            "Set it to the path of final_funding_sg.py (e.g. .../loan_engine/inputs/93rd_buy/bin/final_funding_sg.py). "
            "Script must use folder = Path(os.environ.get('FOLDER')) at the top."
        )
    return _execute_final_funding(script_path, FINAL_FUNDING_SG_PREFIX, folder)


def execute_final_funding_cibc(folder: Optional[str] = None) -> str:
    """
    Run Final Funding CIBC workbook. Uses app inputs and writes to outputs/final_funding_cibc/.
    Returns output prefix for file manager.
    """
    script_path = getattr(settings, "FINAL_FUNDING_CIBC_SCRIPT_PATH", None) or os.environ.get("FINAL_FUNDING_CIBC_SCRIPT_PATH")
    if not script_path or not Path(script_path).exists():
        raise FileNotFoundError(
            "FINAL_FUNDING_CIBC_SCRIPT_PATH not set or file not found. "
            "Set it to the path of final_funding_cibc.py. "
            "Script must use folder = Path(os.environ.get('FOLDER')) at the top."
        )
    return _execute_final_funding(script_path, FINAL_FUNDING_CIBC_PREFIX, folder)


def _execute_final_funding(script_path: str, output_prefix: str, folder: Optional[str]) -> str:
    storage_type = getattr(settings, "STORAGE_TYPE", "local")
    temp_dir = None
    try:
        if storage_type == "s3":
            from orchestration.s3_input_sync import remove_temp_input_dir
            s3_prefix = (folder or "input").strip("/")
            temp_dir = _prepare_temp_input_from_s3(s3_prefix)
            try:
                _run_workbook_script(script_path, temp_dir)
                _upload_local_output_to_storage(temp_dir, output_prefix)
            finally:
                remove_temp_input_dir(temp_dir)
        else:
            input_base = folder or getattr(settings, "INPUT_DIR", "./data/inputs")
            # If folder is a path segment under INPUT_DIR (e.g. "legacy"), resolve it
            if folder and not Path(folder).is_absolute():
                input_base = str(Path(settings.INPUT_DIR) / folder)
            else:
                input_base = folder or str(Path(settings.INPUT_DIR).resolve())
            temp_dir = _prepare_temp_input_from_local(input_base)
            try:
                _run_workbook_script(script_path, temp_dir)
                output_storage = get_storage_backend(area="outputs")
                for subdir in ("output", "output_share"):
                    src = Path(temp_dir) / subdir
                    if not src.is_dir():
                        continue
                    for f in src.rglob("*"):
                        if f.is_file():
                            rel = f.relative_to(src)
                            key = f"{output_prefix}/{subdir}/{rel.as_posix()}"
                            content = f.read_bytes()
                            output_storage.write_file(key, content)
            finally:
                try:
                    shutil.rmtree(Path(temp_dir).parent, ignore_errors=True)
                except Exception:
                    pass
        return output_prefix
    except Exception as e:
        logger.exception("Final funding run failed: %s", e)
        raise
