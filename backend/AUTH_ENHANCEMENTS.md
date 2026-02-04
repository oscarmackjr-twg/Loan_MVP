# Authentication & Authorization Enhancements

## Overview

This document outlines the enhancements made to authentication and authorization for sales teams, addressing critical security gaps and improving data isolation.

## Enhancements Implemented

### 1. Sales Team Assignment Validation

**Problem**: Users with `SALES_TEAM` role could be created without a `sales_team_id`, breaking data isolation.

**Solution**:

- Added `validate_sales_team_assignment()` function
- Enforces `sales_team_id` requirement for `SALES_TEAM` users
- Validates that sales team exists and is active
- Applied in user registration and update endpoints

**Files Modified**:

- `backend/auth/validators.py` (new)
- `backend/auth/routes.py`

### 2. Database Constraint

**Problem**: No database-level enforcement of sales team assignment.

**Solution**:

- Created migration script for check constraint
- Constraint: `role != 'sales_team' OR sales_team_id IS NOT NULL`

**Files Created**:

- `backend/db/migrations/add_sales_team_constraint.sql`

**To Apply**:

```sql
-- Run migration
\i backend/db/migrations/add_sales_team_constraint.sql
```

### 3. Enhanced Access Control

**Problem**: Inconsistent sales team access validation across endpoints.

**Solution**:

- Added `validate_sales_team_access()` function
- Centralized access control logic
- Applied to all data access endpoints

**Files Modified**:

- `backend/auth/validators.py`
- `backend/api/routes.py`

### 4. File Path Isolation

**Problem**: All sales teams used same input/output directories, risking data leakage.

**Solution**:

- Created path utility functions
- Sales team-specific directories: `{base}/sales_team_{id}/`
- Automatic path isolation for sales team users

**Files Created**:

- `backend/utils/path_utils.py`

**Files Modified**:

- `backend/orchestration/pipeline.py`
- `backend/api/routes.py`

**Directory Structure**:

```
data/
├── sales_team_1/
│   ├── files_required/
│   ├── output/
│   └── output_share/
├── sales_team_2/
│   ├── files_required/
│   ├── output/
│   └── output_share/
└── (general)/
    ├── files_required/
    ├── output/
    └── output_share/
```

### 5. User Management Endpoints

**Problem**: No way to update users or list users.

**Solution**:

- Added `PUT /api/auth/users/{user_id}` endpoint
- Added `GET /api/auth/users` endpoint
- Both require admin role
- Includes validation for sales team assignment

**Files Modified**:

- `backend/auth/routes.py`

### 6. Audit Logging

**Problem**: No audit trail for authentication and authorization events.

**Solution**:

- Created audit logging module
- Logs user actions (login, create, update)
- Logs data access events
- Logs authorization failures

**Files Created**:

- `backend/auth/audit.py`

**Files Modified**:

- `backend/auth/routes.py`
- `backend/api/routes.py`

**Log Events**:

- `login`: User login
- `create_user`: User creation
- `update_user`: User update
- `data_access`: Data access events
- `authorization_failure`: Failed authorization attempts

### 7. Enhanced Security Dependencies

**Problem**: Limited security dependency functions.

**Solution**:

- Added `require_sales_team_assignment()` dependency
- Enhanced existing dependencies
- Better error messages

**Files Modified**:

- `backend/auth/security.py`

### 8. Comprehensive Tests

**Problem**: Limited test coverage for authentication/authorization.

**Solution**:

- Created comprehensive test suite
- Tests for all validators
- Tests for all routes
- Tests for edge cases

**Files Created**:

- `backend/tests/test_auth_validators.py`
- `backend/tests/test_auth_routes.py`

## Security Improvements

### Before

- ❌ Sales team users could be created without assignment
- ❌ No database-level constraints
- ❌ Shared file paths (data leakage risk)
- ❌ No audit logging
- ❌ Limited access control validation

### After

- ✅ Sales team assignment enforced at API and DB level
- ✅ Database constraint prevents invalid states
- ✅ File path isolation per sales team
- ✅ Comprehensive audit logging
- ✅ Centralized access control validation
- ✅ User management endpoints with proper validation

## API Changes

### New Endpoints

1. **Update User**

   ```
   PUT /api/auth/users/{user_id}
   Authorization: Bearer {admin_token}
   Body: {
     "email": "string",
     "username": "string",
     "full_name": "string",
     "role": "admin|analyst|sales_team",
     "sales_team_id": int | null,
     "is_active": bool,
     "password": "string"
   }
   ```

2. **List Users**
   ```
   GET /api/auth/users?skip=0&limit=100&role=string&sales_team_id=int
   Authorization: Bearer {admin_token}
   ```

### Enhanced Endpoints

1. **Register User** - Now validates sales team assignment
2. **Create Pipeline Run** - Uses sales team-specific paths
3. **All Data Access Endpoints** - Enhanced with audit logging

## Migration Guide

### 1. Apply Database Constraint

```bash
# PostgreSQL
psql -d loan_engine -f backend/db/migrations/add_sales_team_constraint.sql

# Or via Alembic (recommended)
alembic upgrade head
```

### 2. Update Existing Users

```python
# Fix existing SALES_TEAM users without sales_team_id
from db.connection import SessionLocal
from db.models import User, UserRole

db = SessionLocal()
users = db.query(User).filter(
    User.role == UserRole.SALES_TEAM,
    User.sales_team_id == None
).all()

for user in users:
    # Assign to appropriate sales team or change role
    user.sales_team_id = <appropriate_team_id>
    # or
    user.role = UserRole.ANALYST

db.commit()
```

### 3. Migrate File Structure

```bash
# Create sales team directories
for team_id in 1 2 3; do
  mkdir -p data/sales_team_${team_id}/{files_required,output,output_share}
done
```

## Testing

### Run Tests

```bash
# Test validators
pytest tests/test_auth_validators.py -v

# Test routes
pytest tests/test_auth_routes.py -v

# Test all auth tests
pytest tests/test_auth*.py -v
```

### Test Coverage

- ✅ Sales team assignment validation
- ✅ Access control validation
- ✅ User update validation
- ✅ User registration with validation
- ✅ User update endpoint
- ✅ User listing endpoint
- ✅ File path isolation
- ✅ Audit logging

## Best Practices

### 1. User Creation

- Always assign `sales_team_id` when creating `SALES_TEAM` users
- Validate sales team exists and is active
- Use admin role for user management

### 2. Access Control

- Always use `filter_by_sales_team()` for queries
- Validate access before returning data
- Log all data access events

### 3. File Paths

- Use `get_sales_team_*_path()` utilities
- Never hardcode paths
- Ensure directory structure exists

### 4. Audit Logging

- Log all user actions
- Log data access events
- Monitor authorization failures

## Future Enhancements

### Planned

1. **Role-Based Permissions**: Fine-grained permissions beyond roles
2. **API Rate Limiting**: Per-user and per-sales-team limits
3. **Session Management**: Track active sessions
4. **Password Policies**: Enforce password complexity
5. **Two-Factor Authentication**: Additional security layer
6. **Audit Dashboard**: UI for viewing audit logs

### Considerations

- **Performance**: Audit logging may impact performance at scale
- **Storage**: Audit logs may require archival strategy
- **Compliance**: May need additional logging for regulatory requirements

## Troubleshooting

### Common Issues

1. **"Sales team user must be assigned to a sales team"**

   - Ensure `sales_team_id` is provided when creating/updating `SALES_TEAM` users
   - Verify sales team exists and is active

2. **"Access denied: Cannot access other sales team's data"**

   - User is trying to access data from different sales team
   - Verify user's `sales_team_id` matches data's `sales_team_id`

3. **File not found errors**

   - Check if sales team directory exists
   - Verify path isolation is working correctly
   - Check file permissions

4. **Database constraint violation**
   - Existing `SALES_TEAM` users without `sales_team_id`
   - Run migration script to fix existing data

## References

- [Analysis Document](./ANALYSIS.md) - Original gap analysis
- [Security Module](./auth/security.py) - Security utilities
- [Validators](./auth/validators.py) - Validation functions
- [Audit Module](./auth/audit.py) - Audit logging
