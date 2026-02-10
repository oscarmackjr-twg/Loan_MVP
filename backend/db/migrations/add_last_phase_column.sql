-- Add last_phase to pipeline_runs for diagnosing stuck runs (where execution stopped).
-- Run with: psql -d loan_engine -f backend/db/migrations/add_last_phase_column.sql

ALTER TABLE pipeline_runs
ADD COLUMN IF NOT EXISTS last_phase VARCHAR(80) NULL;

COMMENT ON COLUMN pipeline_runs.last_phase IS 'Last pipeline phase reached (load_reference_data, load_input_files, normalize_loans, underwriting, comap, eligibility, export_reports, save_db). Used to diagnose stuck runs.';
