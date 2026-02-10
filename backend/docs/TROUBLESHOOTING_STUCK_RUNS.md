# Troubleshooting: Pipeline Run Stuck in "Running"

When a pipeline run stays in **running** state, it usually means the process that was executing the run stopped before it could update the database to **completed** or **failed**.

---

## Why runs get stuck

1. **Process killed** – Server restarted, process killed (Ctrl+C, OOM, deploy), or backend crash before the pipeline finished.
2. **Unhandled exception** – In rare cases an error might not be caught by the pipeline’s `try/except`, so `update_run_status(RunStatus.FAILED)` never runs.
3. **Long-running or hung pipeline** – The run is still actually running but taking a long time (e.g. large files, slow disk); the UI shows "running" until it finishes or is killed.

The pipeline sets status to **running** at the start of `execute()` and to **completed** or **failed** only at the end. If the process exits in between, the row stays **running**.

---

## How to troubleshoot

### 1. Confirm which runs are stuck

- **UI**: Dashboard or **Pipeline Runs** – look for runs with status **running** that have been that way for a long time (e.g. hours).
- **API**:  
  `GET /api/runs?status=running`  
  Returns all runs with status `running`.
- **Script**:  
  `python backend/scripts/fix_stuck_runs.py --list`  
  Lists runs in `running` state and how long they’ve been running (based on `started_at`).

### 2. Decide if the run is really stuck

- If the run started only a few minutes ago and the pipeline is heavy, it may still be running. Check backend logs and CPU/memory; wait or inspect the process.
- If the backend was restarted, or you know the run was interrupted, treat it as stuck and mark it **failed** or **cancelled** (see below).

### 3. Fix stuck runs (mark as failed or cancelled)

Use the provided script so you don’t leave runs in **running** forever:

```bash
# From project root (or backend directory)

# List all runs currently in "running" state
python backend/scripts/fix_stuck_runs.py --list

# Mark a specific run as failed (by run_id, the UUID string)
python backend/scripts/fix_stuck_runs.py --run-id <RUN_ID> --mark failed

# Mark as cancelled instead
python backend/scripts/fix_stuck_runs.py --run-id <RUN_ID> --mark cancelled

# Optional: add a reason (stored in errors for "failed")
python backend/scripts/fix_stuck_runs.py --run-id <RUN_ID> --mark failed --reason "Process restarted during run"

# Mark all runs that have been "running" for more than 60 minutes as failed
python backend/scripts/fix_stuck_runs.py --mark failed --older-than-minutes 60
```

After marking, the run will show as **failed** or **cancelled** in the UI/API and will no longer block or confuse reporting.

### 4. Prevent future stuck runs (optional)

- Ensure the backend process is not killed mid-run (e.g. graceful shutdown, or run pipeline in a worker that can be retried).
- For long-running pipelines, consider a background job that periodically marks runs that have been **running** longer than a threshold (e.g. 2 hours) as **failed** with reason "Stuck run cleanup".

---

---

## How to tell if it was a data or code issue

You can’t always tell for certain, but these signals help.

### 1. Use **last_phase** (where execution stopped)

The pipeline records the **last phase** it reached before the process died. For runs stuck in **running**, check:

- **API**: `GET /api/runs?status=running` or `GET /api/runs/{run_id}` — response includes `last_phase`.
- **Script**: `fix_stuck_runs.py --list` prints `last_phase` for each stuck run.

Interpretation (data vs code):

| last_phase             | Often indicates |
|-----------------------|------------------|
| `load_reference_data` | **Data**: Missing/wrong reference files (MASTER_SHEET, Underwriting_Grids_COMAP, current_assets), or bad path. Less often: code bug in Excel/CSV read. |
| `load_input_files`    | **Data**: Missing Tape20Loans/SFY/PRIME files, wrong folder, or file discovery (dates). Less often: code in file discovery or normalize. |
| `normalize_loans`     | **Data or code**: Bad column names, types, or content in loan/SFY/Prime files. Check logs for the exact exception. |
| `underwriting`        | **Data or code**: Bad underwriting grid or loan data; or bug in underwriting rules. |
| `comap`               | **Data or code**: Missing CoMAP columns, wrong FICO/values, or bug in CoMAP lookup. |
| `eligibility`         | **Data or code**: Bad data in final dataframe or bug in eligibility checks. |
| `export_reports`      | **Data or code**: Export path/permissions or bug in export. |
| `save_db`             | **Code or infra**: DB write failure, constraint, or connection. |

Phases at the **start** (load_reference_data, load_input_files) usually point to **data or environment** (files, paths). Phases in the **middle** (underwriting, comap, eligibility) can be **data** (bad values) or **code** (bug). **Logs** (next section) give the exact error.

### 2. Use **application logs**

The best way to see the actual failure is **backend logs** (e.g. `backend/logs/loan_engine.log` or the console where uvicorn runs). The pipeline logs at each step and logs the full exception on failure.

- **Look at the last log lines** for that run (match by timestamp or `run_id` in log messages). The last message before the process stopped is the phase it was in.
- **If there is an exception/traceback**, that’s the direct cause:
  - `FileNotFoundError`, `No file found` → **Data/environment** (missing file or path).
  - `KeyError`, `Column X not in index` → Often **data** (wrong/missing column) or **code** (wrong column name).
  - `AttributeError` (e.g. `.lower()` on None/float) → Often **data** (unexpected type/NaN) or **code** (missing type check).
  - `ValueError`, `InvalidTextRepresentation` → **Data** (bad value) or **code** (validation).

So: **logs tell you the exact error; last_phase tells you where in the pipeline it happened.** Together they answer “was it data or code?” for most cases.

### 3. Apply the migration so **last_phase** is stored

For **new** runs to get `last_phase`, add the column if you haven’t already:

```bash
psql -d loan_engine -f backend/db/migrations/add_last_phase_column.sql
```

Existing stuck runs (from before this change) will have `last_phase` empty; for those, rely on **logs** and **input_file_path** (which folder was used) to investigate.

---

## Quick reference

| Goal                         | Action |
|-----------------------------|--------|
| See stuck runs               | `GET /api/runs?status=running` or `fix_stuck_runs.py --list` |
| See where run stopped        | Check `last_phase` in API or `fix_stuck_runs.py --list` |
| Data vs code                 | Use `last_phase` + application logs (see above) |
| Mark one run as failed       | `fix_stuck_runs.py --run-id <id> --mark failed` |
| Mark one run as cancelled    | `fix_stuck_runs.py --run-id <id> --mark cancelled` |
| Mark old running runs       | `fix_stuck_runs.py --mark failed --older-than-minutes 60` |
