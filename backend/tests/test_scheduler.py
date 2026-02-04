"""Tests for scheduler implementation."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from scheduler.job_scheduler import (
    run_daily_pipeline,
    schedule_daily_runs,
    reschedule_daily_runs,
    scheduler
)
from db.models import SalesTeam, PipelineRun, RunStatus
from config.settings import settings


class TestRunDailyPipeline:
    """Test daily pipeline execution."""
    
    @pytest.mark.asyncio
    async def test_run_daily_pipeline_success(self, test_db_session, sample_sales_team, temp_dir):
        """Test successful pipeline run."""
        # Mock settings
        with patch('scheduler.job_scheduler.settings') as mock_settings:
            mock_settings.INPUT_DIR = str(temp_dir)
            mock_settings.OUTPUT_DIR = str(temp_dir / "output")
            mock_settings.IRR_TARGET = 8.05
            
            # Create input directory structure
            input_dir = temp_dir / f"sales_team_{sample_sales_team.id}" / "files_required"
            input_dir.mkdir(parents=True)
            
            # Mock pipeline execution
            with patch('scheduler.job_scheduler.PipelineExecutor') as mock_executor:
                mock_executor.return_value.__enter__.return_value.execute.return_value = {
                    'run_id': 'test_run_123',
                    'total_loans': 10,
                    'total_balance': 100000.0,
                    'exceptions_count': 2
                }
                
                result = await run_daily_pipeline(sample_sales_team.id)
                
                assert result['run_id'] == 'test_run_123'
                assert result['total_loans'] == 10
    
    @pytest.mark.asyncio
    async def test_run_daily_pipeline_no_team(self, test_db_session, temp_dir):
        """Test pipeline run without sales team."""
        with patch('scheduler.job_scheduler.settings') as mock_settings:
            mock_settings.INPUT_DIR = str(temp_dir)
            mock_settings.OUTPUT_DIR = str(temp_dir / "output")
            mock_settings.IRR_TARGET = 8.05
            
            input_dir = temp_dir / "files_required"
            input_dir.mkdir(parents=True)
            
            with patch('scheduler.job_scheduler.PipelineExecutor') as mock_executor:
                mock_executor.return_value.__enter__.return_value.execute.return_value = {
                    'run_id': 'test_run_general',
                    'total_loans': 5
                }
                
                result = await run_daily_pipeline(None)
                
                assert result['run_id'] == 'test_run_general'
    
    @pytest.mark.asyncio
    async def test_run_daily_pipeline_failure(self, test_db_session, sample_sales_team, temp_dir):
        """Test pipeline run failure handling."""
        with patch('scheduler.job_scheduler.settings') as mock_settings:
            mock_settings.INPUT_DIR = str(temp_dir)
            mock_settings.OUTPUT_DIR = str(temp_dir / "output")
            mock_settings.IRR_TARGET = 8.05
            
            with patch('scheduler.job_scheduler.PipelineExecutor') as mock_executor:
                mock_executor.return_value.__enter__.return_value.execute.side_effect = Exception("Test error")
                
                with pytest.raises(Exception):
                    await run_daily_pipeline(sample_sales_team.id)
    
    @pytest.mark.asyncio
    async def test_run_daily_pipeline_path_isolation(self, test_db_session, sample_sales_team, temp_dir):
        """Test that sales team paths are isolated."""
        with patch('scheduler.job_scheduler.settings') as mock_settings:
            mock_settings.INPUT_DIR = str(temp_dir)
            mock_settings.OUTPUT_DIR = str(temp_dir / "output")
            mock_settings.IRR_TARGET = 8.05
            
            with patch('scheduler.job_scheduler.PipelineExecutor') as mock_executor:
                mock_executor.return_value.__enter__.return_value.execute.return_value = {
                    'run_id': 'test_run',
                    'total_loans': 0
                }
                
                await run_daily_pipeline(sample_sales_team.id)
                
                # Verify sales team-specific directory was created
                team_dir = temp_dir / f"sales_team_{sample_sales_team.id}"
                assert team_dir.exists()


class TestScheduleDailyRuns:
    """Test scheduling functionality."""
    
    def test_schedule_daily_runs_disabled(self):
        """Test scheduling when scheduler is disabled."""
        with patch('scheduler.job_scheduler.settings') as mock_settings:
            mock_settings.ENABLE_SCHEDULER = False
            
            # Should not raise and should not schedule
            schedule_daily_runs()
    
    def test_schedule_daily_runs_with_teams(self, test_db_session, sample_sales_team):
        """Test scheduling runs for sales teams."""
        with patch('scheduler.job_scheduler.settings') as mock_settings:
            mock_settings.ENABLE_SCHEDULER = True
            mock_settings.DAILY_RUN_TIME = "02:00"
            
            # Clear existing jobs
            scheduler.remove_all_jobs()
            
            schedule_daily_runs()
            
            # Verify jobs were scheduled
            jobs = scheduler.get_jobs()
            assert len(jobs) > 0
            
            # Verify sales team job exists
            job_ids = [job.id for job in jobs]
            assert f"daily_pipeline_{sample_sales_team.id}" in job_ids
    
    def test_schedule_daily_runs_invalid_time(self):
        """Test scheduling with invalid time format."""
        with patch('scheduler.job_scheduler.settings') as mock_settings:
            mock_settings.ENABLE_SCHEDULER = True
            mock_settings.DAILY_RUN_TIME = "invalid"
            
            # Should handle error gracefully
            schedule_daily_runs()
    
    def test_reschedule_daily_runs(self, test_db_session, sample_sales_team):
        """Test rescheduling runs."""
        with patch('scheduler.job_scheduler.settings') as mock_settings:
            mock_settings.ENABLE_SCHEDULER = True
            mock_settings.DAILY_RUN_TIME = "02:00"
            
            # Add a job first
            scheduler.add_job(
                lambda: None,
                id="test_job",
                trigger="date",
                run_date=datetime.now()
            )
            
            # Reschedule should remove old jobs and add new ones
            reschedule_daily_runs()
            
            # Verify test job was removed
            job_ids = [job.id for job in scheduler.get_jobs()]
            assert "test_job" not in job_ids


class TestSchedulerIntegration:
    """Test scheduler integration with FastAPI."""
    
    def test_scheduler_startup(self):
        """Test scheduler can be started."""
        if scheduler.running:
            scheduler.shutdown()
        
        scheduler.start()
        assert scheduler.running
        
        scheduler.shutdown()
        assert not scheduler.running
    
    def test_scheduler_job_management(self):
        """Test adding and removing jobs."""
        if scheduler.running:
            scheduler.shutdown()
        
        scheduler.start()
        
        try:
            # Add a test job
            job = scheduler.add_job(
                lambda: None,
                id="test_job",
                trigger="date",
                run_date=datetime.now()
            )
            
            assert job.id == "test_job"
            
            # Remove job
            scheduler.remove_job("test_job")
            
            jobs = scheduler.get_jobs()
            assert "test_job" not in [j.id for j in jobs]
        finally:
            scheduler.shutdown()
