-- Migration: Add constraint to ensure SALES_TEAM users have sales_team_id
-- This enforces data integrity at the database level

-- Add check constraint (PostgreSQL syntax)
ALTER TABLE users 
ADD CONSTRAINT check_sales_team_assignment 
CHECK (
    role != 'sales_team' OR sales_team_id IS NOT NULL
);

-- Add comment for documentation
COMMENT ON CONSTRAINT check_sales_team_assignment ON users IS 
'Ensures that users with SALES_TEAM role must have a sales_team_id assigned';
