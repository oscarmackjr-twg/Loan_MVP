"""Run the Tagging phase: reads from the inputs directory (not files_required), writes to outputs/tagging/."""
import os
import subprocess
import logging
from pathlib import Path
from typing import Optional

from config.settings import settings
from storage import get_storage_backend

logger = logging.getLogger(__name__)

TAGGING_OUTPUT_PREFIX = "tagging"


def run_tagging(input_dir: str, output_dir: str, script_path: Optional[str] = None) -> None:
    """
    Run the tagging script with INPUT_DIR and OUTPUT_DIR set.
    script_path: if set, run this Python script; else run a stub that writes a placeholder.
    """
    env = os.environ.copy()
    env["INPUT_DIR"] = input_dir
    env["OUTPUT_DIR"] = output_dir

    if script_path and Path(script_path).exists():
        logger.info("Running tagging script at %s with INPUT_DIR=%s OUTPUT_DIR=%s", script_path, input_dir, output_dir)
        result = subprocess.run(
            [os.environ.get("PYTHON", "python"), script_path],
            env=env,
            cwd=str(Path(script_path).parent),
            capture_output=True,
            text=True,
            timeout=3600,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Tagging script failed: {result.stderr or result.stdout or 'unknown error'}")
        return

    # Stub: list inputs and write a placeholder output under output_dir
    logger.info("No tagging script at %s; running stub (list inputs, write placeholder)", script_path or "TAGGING_SCRIPT_PATH")
    stub_run(input_dir, output_dir)


def stub_run(input_dir: str, output_dir: str) -> None:
    """Stub implementation: list files in input_dir and write a placeholder file to output_dir."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    try:
        names = list(Path(input_dir).iterdir()) if Path(input_dir).exists() else []
        listing = "\n".join(p.name for p in names) or "(empty)"
    except Exception as e:
        listing = f"(error listing: {e})"
    placeholder = out_path / "tagging_placeholder.txt"
    placeholder.write_text(f"Tagging stub run.\nInput directory: {input_dir}\nFiles listed:\n{listing}\n", encoding="utf-8")
    logger.info("Stub wrote %s", placeholder)


def execute_tagging() -> str:
    """
    Execute the Tagging program run: read from storage inputs (root), write to outputs/tagging/.
    Returns the output prefix path (e.g. 'tagging') for the file manager.
    """
    storage_type = getattr(settings, "STORAGE_TYPE", "local")
    script_path = getattr(settings, "TAGGING_SCRIPT_PATH", None) or os.environ.get("TAGGING_SCRIPT_PATH")

    if storage_type == "s3":
        from orchestration.s3_input_sync import sync_s3_input_to_temp, remove_temp_input_dir
        input_storage = get_storage_backend(area="inputs")
        # Use prefix "" to sync root of inputs (the "inputs directory")
        temp_dir = sync_s3_input_to_temp(input_storage, "")
        try:
            output_storage = get_storage_backend(area="outputs")
            out_prefix = TAGGING_OUTPUT_PREFIX
            # Materialize a local temp dir for script output, then upload to outputs/tagging/
            import tempfile
            with tempfile.TemporaryDirectory() as out_temp:
                run_tagging(temp_dir, out_temp, script_path)
                for f in Path(out_temp).rglob("*"):
                    if f.is_file():
                        rel = f.relative_to(out_temp)
                        key = f"{out_prefix}/{rel.as_posix()}"
                        content = f.read_bytes()
                        output_storage.write_file(key, content)
        finally:
            remove_temp_input_dir(temp_dir)
        return out_prefix

    # Local storage
    input_dir = str(Path(settings.INPUT_DIR).resolve())
    output_base = Path(settings.OUTPUT_DIR) / TAGGING_OUTPUT_PREFIX
    output_dir = str(output_base.resolve())
    run_tagging(input_dir, output_dir, script_path)
    return TAGGING_OUTPUT_PREFIX
