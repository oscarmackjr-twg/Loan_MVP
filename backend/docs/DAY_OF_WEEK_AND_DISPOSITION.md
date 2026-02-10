# Day-of-Week Segregation and Purchase vs Projected Tracking

## Overview

Processing is segregated by **day of week** (from the run’s purchase date). For each run we track which loans are **to be purchased** (passed all checks), which are **projected** (in the run), and which are **rejected**, with rejection reasons mapped to the original Jupyter Notebook.

## Day-of-Week Segregation

- **Source**: `pdate` (purchase date, YYYY-MM-DD).
- **Stored on `PipelineRun`**:
  - `run_weekday`: integer 0–6 (Monday = 0, Sunday = 6).
  - `run_weekday_name`: string (e.g. `"Tuesday"`).
- **API**: `GET /api/runs?run_weekday=1` returns runs whose purchase date is a Tuesday.

Use this to analyze or report activity by weekday (e.g. “Tuesday purchases” vs “Friday projections”).

## Loan Disposition: To Purchase vs Projected vs Rejected

- **To purchase** (`disposition = to_purchase`): In the buy tape and passed **all** of: purchase price, underwriting (SFY/Prime/notes as applicable), and CoMAP. These are the loans that need to be purchased.
- **Projected** (`disposition = projected`): Included in the run for projection/analytics; not used for “to purchase” when we strictly use the above definition. (Currently we set anyone not rejected to `to_purchase`; `projected` remains available for future use.)
- **Rejected** (`disposition = rejected`): Failed at least one check. `rejection_criteria` holds the canonical key that maps to the notebook (e.g. `notebook.purchase_price_mismatch`).

**API**:

- `GET /api/loans?run_id=<run_id>&disposition=to_purchase`: loans eligible to purchase.
- `GET /api/loans?run_id=<run_id>&disposition=rejected`: rejected loans.
- Each loan object includes `disposition` and `rejection_criteria` (when rejected).

## Rejection Criteria and Notebook Mapping

Rejection reasons are stored under a **canonical key** so they align with the notebook:

- **Config**: `backend/config/rejection_criteria.py` defines keys and maps `exception_type` + `exception_category` to them.
- **Mapping doc**: `backend/docs/NOTEBOOK_REJECTION_MAPPING.md` lists:
  - Notebook concept
  - App function (e.g. `rules.purchase_price.get_purchase_price_exceptions`)
  - `exception_type` / `rejection_criteria` key

So every rejection is traceable to both an app function and a notebook concept.

## Database Changes

- **PipelineRun**: `run_weekday`, `run_weekday_name`.
- **LoanException**: `rejection_criteria`.
- **LoanFact**: `disposition`, `rejection_criteria`.

Apply the migration:

```bash
psql -d your_db -f backend/db/migrations/add_weekday_disposition_columns.sql
```

Or use Alembic/`init_db.py` if you manage schema that way (ensure these columns exist).

## Summary

- **By day of week**: Filter runs with `run_weekday` (0–6) or use `run_weekday_name` for display.
- **What needs to be purchased**: Use `disposition=to_purchase` for that run.
- **What was projected**: All loans in the run; use `disposition=rejected` to exclude rejections.
- **Why rejected**: Use `rejection_criteria` (and `NOTEBOOK_REJECTION_MAPPING.md`) to map back to the notebook and app functions.
