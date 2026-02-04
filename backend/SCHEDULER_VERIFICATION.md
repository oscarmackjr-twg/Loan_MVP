# Scheduler Implementation Verification

## Overview

This document verifies the scheduler implementation for daily pipeline runs, including fixes and enhancements made to address identified gaps.

## Issues Identified and Fixed

### 1. ✅ File Path Isolation

**Issue**: Scheduler was using `settings.INPUT_DIR` and `settings.OUTPUT_DIR` directly without sales team isolation.

**Fix**:

- Updated `run_daily_pipeline()` to use `get_sales_team_input_path()` and `get_sales_team_output_path()`
- Ensures sales team-specific directories are used
- Creates directories if they don't exist

**Code Location**: `backend/scheduler/job_scheduler.py:31-37`

### 2. ✅ Dynamic File Discovery

**Issue**: Scheduler passed hardcoded paths, but pipeline already handles dynamic file discovery.

**Status**: ✅ **Already Working**

- Pipeline's `load_input_files()` uses `discover_input_files()` which handles dynamic file discovery
- No changes needed

### 3. ✅ Date Calculation

**Issue**: Scheduler used `pdate=None` which defaults to next Tuesday.

**Status**: ✅ **Working as Intended**

- `RunContext.create()` with `pdate=None` uses `calculate_next_tuesday()` by default
- This matches notebook behavior (next Tuesday for purchase date)

### 4. ✅ Error Handling and Notifications

**Issue**: Basic error handling existed but no notifications.

**Fix**:

- Added notification module (`scheduler/notifications.py`)
- Integrated notifications for run started, completed, and failed events
- Enhanced error handling with proper run status updates

**Code Location**:

- `backend/scheduler/notifications.py` (new)
- `backend/scheduler/job_scheduler.py:45-75`

### 5. ✅ Scheduler Initialization

**Issue**: Scheduler was initialized on import, which could cause issues.

**Fix**:

- Removed initialization on import
- Scheduler is now started in FastAPI lifespan handler
- `schedule_daily_runs()` is called after scheduler starts

**Code Location**:

- `backend/scheduler/job_scheduler.py:87-89` (removed auto-init)
- `backend/api/main.py:33-35` (startup handler)

### 6. ✅ Rescheduling Capability

**Issue**: No way to reschedule when sales teams are added/removed.

**Fix**:

- Added `reschedule_daily_runs()` function
- Can be called after sales team changes
- Removes all jobs and reschedules

**Code Location**: `backend/scheduler/job_scheduler.py:95-107`

## Current Implementation Status

### ✅ Working Features

1. **Per-Sales-Team Scheduling**

   - Each active sales team gets its own scheduled run
   - General run (no sales team) also scheduled
   - Jobs are uniquely identified by sales team ID

2. **File Path Isolation**

   - Sales team-specific input/output directories
   - Automatic directory creation
   - Prevents data leakage between teams

3. **Dynamic Date Calculation**

   - Uses next Tuesday for purchase date (matching notebook)
   - Automatic date calculation for file discovery

4. **Error Handling**

   - Proper exception handling
   - Run status updates on failure
   - Comprehensive logging

5. **Notifications**

   - Run started notifications
   - Run completed notifications
   - Run failed notifications
   - Currently logs to logger (can be extended to email/Slack)

6. **Job Management**
   - `max_instances=1` prevents concurrent runs
   - `misfire_grace_time=3600` allows missed runs to catch up
   - `replace_existing=True` updates existing jobs

### ⚠️ Known Limitations

1. **Notification Integration**

   - Currently only logs notifications
   - Email/Slack integration needs to be implemented
   - See `scheduler/notifications.py` for TODO

2. **Retry Logic**

   - No automatic retry on failure
   - Failed runs are logged but not retried
   - Could add retry logic with exponential backoff

3. **Run Monitoring**
   - No dashboard for monitoring scheduled runs
   - No alerting for consecutive failures
   - Could add monitoring endpoint

## Configuration

### Settings

```python
# config/settings.py
ENABLE_SCHEDULER: bool = True
DAILY_RUN_TIME: str = "02:00"  # 2 AM
INPUT_DIR: str = "./data/inputs"
OUTPUT_DIR: str = "./data/outputs"
```

### Environment Variables

```bash
ENABLE_SCHEDULER=true
DAILY_RUN_TIME=02:00
INPUT_DIR=/path/to/inputs
OUTPUT_DIR=/path/to/outputs
```

## Usage

### Starting the Scheduler

The scheduler starts automatically when the FastAPI application starts (if `ENABLE_SCHEDULER=true`).

```python
# Scheduler is started in api/main.py lifespan handler
if settings.ENABLE_SCHEDULER:
    scheduler.start()
    schedule_daily_runs()
```

### Manual Scheduling

```python
from scheduler.job_scheduler import schedule_daily_runs

# Schedule runs for all active sales teams
schedule_daily_runs()
```

### Rescheduling

```python
from scheduler.job_scheduler import reschedule_daily_runs

# After adding/removing sales teams
reschedule_daily_runs()
```

### Manual Run Execution

```python
from scheduler.job_scheduler import run_daily_pipeline

# Run for specific sales team
await run_daily_pipeline(sales_team_id=1)

# Run for general (no sales team)
await run_daily_pipeline(sales_team_id=None)
```

## Directory Structure

With sales team isolation:

```
data/
├── inputs/
│   ├── sales_team_1/
│   │   └── files_required/
│   ├── sales_team_2/
│   │   └── files_required/
│   └── files_required/  # General
├── outputs/
│   ├── sales_team_1/
│   │   ├── output/
│   │   └── output_share/
│   ├── sales_team_2/
│   │   ├── output/
│   │   └── output_share/
│   └── output/  # General
```

## Testing

### Run Tests

```bash
# Test scheduler functionality
pytest tests/test_scheduler.py -v

# Test with coverage
pytest tests/test_scheduler.py --cov=scheduler
```

### Test Coverage

- ✅ Successful pipeline execution
- ✅ Pipeline execution without sales team
- ✅ Pipeline failure handling
- ✅ Path isolation verification
- ✅ Scheduling functionality
- ✅ Rescheduling functionality
- ✅ Scheduler startup/shutdown

## Monitoring

### Logs

Scheduler events are logged at INFO level:

```
INFO: Starting scheduled pipeline run for sales_team_id=1
INFO: Scheduled pipeline run completed: run_abc123 (sales_team_id=1, loans=100)
ERROR: Scheduled pipeline run failed for sales_team_id=1: File not found
```

### Database

Check `pipeline_runs` table for run history:

```sql
SELECT
    run_id,
    status,
    sales_team_id,
    total_loans,
    exceptions_count,
    started_at,
    completed_at
FROM pipeline_runs
WHERE sales_team_id = 1
ORDER BY created_at DESC;
```

## Troubleshooting

### Scheduler Not Starting

1. Check `ENABLE_SCHEDULER` setting
2. Check logs for errors
3. Verify database connection
4. Check if scheduler is already running

### Jobs Not Executing

1. Verify jobs are scheduled: `scheduler.get_jobs()`
2. Check scheduler is running: `scheduler.running`
3. Verify cron expression is correct
4. Check for errors in logs

### File Not Found Errors

1. Verify input directory exists
2. Check sales team directory structure
3. Verify file discovery is working
4. Check file naming patterns match expected format

### Path Isolation Issues

1. Verify `get_sales_team_*_path()` functions are used
2. Check directory creation logic
3. Verify sales_team_id is being passed correctly

## Future Enhancements

### Planned

1. **Email Notifications**

   - Send email on run completion/failure
   - Configurable recipient list per sales team

2. **Slack Integration**

   - Post notifications to Slack channel
   - Include run summary in message

3. **Retry Logic**

   - Automatic retry on transient failures
   - Exponential backoff
   - Max retry attempts

4. **Monitoring Dashboard**

   - Real-time run status
   - Historical run metrics
   - Alert configuration

5. **Run Dependencies**
   - Wait for reference data updates
   - Chain multiple runs
   - Conditional execution

### Considerations

- **Performance**: Multiple concurrent runs may impact system resources
- **Storage**: Run history may require archival strategy
- **Scalability**: May need distributed scheduler for large deployments

## Verification Checklist

- [x] Scheduler starts with application
- [x] Jobs are scheduled for all active sales teams
- [x] File paths are isolated per sales team
- [x] Dynamic file discovery works
- [x] Date calculation uses next Tuesday
- [x] Error handling updates run status
- [x] Notifications are logged
- [x] Jobs can be rescheduled
- [x] Concurrent runs are prevented
- [x] Tests cover all scenarios

## Conclusion

The scheduler implementation is **verified and working** with all critical gaps addressed:

✅ File path isolation implemented
✅ Dynamic file discovery working
✅ Date calculation correct
✅ Error handling enhanced
✅ Notifications integrated
✅ Rescheduling capability added
✅ Comprehensive tests added

The scheduler is ready for production use with the enhancements made.
