"""Sync S3 input prefix to a local temp directory for pipeline execution."""
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from storage.base import StorageBackend

logger = logging.getLogger(__name__)


def sync_s3_input_to_temp(input_storage: StorageBackend, s3_prefix: str) -> str:
    """
    Download all files under the given S3 prefix (inputs area) to a temp directory.
    The prefix is relative to the inputs area (e.g. "legacy" or "sales_team_1").
    Returns the path to the temp directory; the caller must remove it when done.

    The temp dir layout mirrors the prefix content so that folder=temp_dir can be
    passed to the pipeline (e.g. temp_dir/files_required/MASTER_SHEET.xlsx).
    """
    prefix = s3_prefix.strip("/")
    if not prefix:
        prefix = ""
    list_prefix = f"{prefix}/" if prefix else ""
    try:
        all_files = input_storage.list_files(list_prefix, recursive=True)
    except Exception as e:
        logger.error("Failed to list S3 input prefix %s: %s", list_prefix, e)
        raise

    file_keys = [f.path for f in all_files if not f.is_directory and not f.path.endswith("/")]
    if not file_keys:
        location = f"prefix '{list_prefix}'" if list_prefix else "root of input directory (no subfolder)"
        raise FileNotFoundError(f"No files found in inputs area at {location}")

    temp_dir = tempfile.mkdtemp(prefix="loan_engine_input_")
    try:
        for key in file_keys:
            # key is e.g. "legacy/files_required/MASTER_SHEET.xlsx"; we want temp_dir/files_required/...
            if prefix and key.startswith(prefix + "/"):
                rel = key[len(prefix) + 1:]
            elif prefix and key == prefix:
                rel = Path(key).name
            else:
                rel = key
            local_path = Path(temp_dir) / rel
            local_path.parent.mkdir(parents=True, exist_ok=True)
            content = input_storage.read_file(key)
            local_path.write_bytes(content)
            logger.debug("Synced S3 %s -> %s", key, local_path)
        logger.info("Synced %d files from S3 %s to %s", len(file_keys), list_prefix, temp_dir)
        return temp_dir
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def remove_temp_input_dir(temp_dir: Optional[str]) -> None:
    """Safely remove a temp directory created by sync_s3_input_to_temp."""
    if not temp_dir:
        return
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.debug("Removed temp input dir %s", temp_dir)
    except Exception as e:
        logger.warning("Failed to remove temp dir %s: %s", temp_dir, e)
