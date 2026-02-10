-- Day-of-week and disposition columns for pipeline runs and loan facts.
-- Run once after existing schema (e.g. after create_tables.sql or init_db.py).

-- PipelineRun: day-of-week from pdate
ALTER TABLE pipeline_runs
  ADD COLUMN IF NOT EXISTS run_weekday INTEGER,
  ADD COLUMN IF NOT EXISTS run_weekday_name VARCHAR(20);

-- LoanException: canonical rejection criteria key
ALTER TABLE loan_exceptions
  ADD COLUMN IF NOT EXISTS rejection_criteria VARCHAR(120);

-- LoanFact: disposition and rejection_criteria
ALTER TABLE loan_facts
  ADD COLUMN IF NOT EXISTS disposition VARCHAR(30) DEFAULT 'projected',
  ADD COLUMN IF NOT EXISTS rejection_criteria VARCHAR(120);

COMMENT ON COLUMN pipeline_runs.run_weekday IS '0=Monday .. 6=Sunday, from pdate';
COMMENT ON COLUMN pipeline_runs.run_weekday_name IS 'Monday, Tuesday, ...';
COMMENT ON COLUMN loan_exceptions.rejection_criteria IS 'Canonical key mapping to notebook; see NOTEBOOK_REJECTION_MAPPING.md';
COMMENT ON COLUMN loan_facts.disposition IS 'to_purchase | projected | rejected';
COMMENT ON COLUMN loan_facts.rejection_criteria IS 'Set when disposition=rejected; see NOTEBOOK_REJECTION_MAPPING.md';
