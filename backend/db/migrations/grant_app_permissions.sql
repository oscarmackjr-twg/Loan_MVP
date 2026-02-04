-- Grant permissions to application database user
-- Run as superuser (e.g. postgres) AFTER tables exist.
--
-- Usage:
--   1. Replace YOUR_APP_USER below with the username from your DATABASE_URL.
--   2. Run: psql -U postgres -d cursor_db -f grant_app_permissions.sql
--
-- Example DATABASE_URL: postgresql://myuser:pass@localhost:5432/cursor_db
--                      -> use myuser as YOUR_APP_USER

-- ============ EDIT THIS: set your application database user ============
-- (Username from DATABASE_URL, e.g. the part before : in user:password@host)
--set app_user 'cursor_app'
-- ========================================================================

GRANT USAGE ON SCHEMA public TO cursor_app;

-- sales_teams (referenced by users.sales_team_id)
GRANT SELECT ON sales_teams TO cursor_app;

-- users
GRANT SELECT, INSERT, UPDATE ON users TO cursor_app;
GRANT USAGE, SELECT ON SEQUENCE users_id_seq TO cursor_app;

-- pipeline_runs
GRANT SELECT, INSERT, UPDATE ON pipeline_runs TO cursor_app;
GRANT USAGE, SELECT ON SEQUENCE pipeline_runs_id_seq TO cursor_app;

-- loan_exceptions
GRANT SELECT, INSERT ON loan_exceptions TO cursor_app;
GRANT USAGE, SELECT ON SEQUENCE loan_exceptions_id_seq TO cursor_app;

-- loan_facts
GRANT SELECT, INSERT ON loan_facts TO cursor_app;
GRANT USAGE, SELECT ON SEQUENCE loan_facts_id_seq TO cursor_app;
