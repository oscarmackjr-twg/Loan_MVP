"""Tests for date calculation utilities."""
import pytest
from datetime import datetime, timedelta
from utils.date_utils import (
    calculate_next_tuesday,
    calculate_yesterday,
    calculate_last_month_end,
    calculate_pipeline_dates
)


class TestCalculateNextTuesday:
    """Test next Tuesday calculation."""
    
    def test_next_tuesday_from_monday(self, monkeypatch):
        """Test calculation from Monday."""
        # Mock Monday
        monday = datetime(2024, 10, 7)  # Monday
        from unittest.mock import patch
        with patch('utils.date_utils.datetime') as mock_dt:
            mock_dt.today.return_value = monday
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            result = calculate_next_tuesday()
            assert result == "2024-10-08"  # Next day (Tuesday)
    
    def test_next_tuesday_from_tuesday(self, monkeypatch):
        """Test calculation from Tuesday (should return next Tuesday)."""
        tuesday = datetime(2024, 10, 8)  # Tuesday
        from unittest.mock import patch
        with patch('utils.date_utils.datetime') as mock_dt:
            mock_dt.today.return_value = tuesday
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            result = calculate_next_tuesday()
            assert result == "2024-10-15"  # Next Tuesday (7 days)
    
    def test_next_tuesday_from_sunday(self, monkeypatch):
        """Test calculation from Sunday."""
        sunday = datetime(2024, 10, 6)  # Sunday
        from unittest.mock import patch
        with patch('utils.date_utils.datetime') as mock_dt:
            mock_dt.today.return_value = sunday
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            result = calculate_next_tuesday()
            assert result == "2024-10-08"  # 2 days away


class TestCalculateYesterday:
    """Test yesterday calculation."""
    
    def test_yesterday_format(self, monkeypatch):
        """Test yesterday returns correct format."""
        today = datetime(2024, 10, 15)
        from unittest.mock import patch
        with patch('utils.date_utils.datetime') as mock_dt:
            mock_dt.today.return_value = today
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            result = calculate_yesterday()
            assert result == "10-14-2024"
    
    def test_yesterday_month_boundary(self, monkeypatch):
        """Test yesterday across month boundary."""
        today = datetime(2024, 10, 1)
        from unittest.mock import patch
        with patch('utils.date_utils.datetime') as mock_dt:
            mock_dt.today.return_value = today
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            result = calculate_yesterday()
            assert result == "09-30-2024"


class TestCalculateLastMonthEnd:
    """Test last month end calculation."""
    
    def test_last_month_end_format(self, monkeypatch):
        """Test last month end returns correct format."""
        today = datetime(2024, 10, 15)
        from unittest.mock import patch
        with patch('utils.date_utils.datetime') as mock_dt:
            mock_dt.today.return_value = today
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            result = calculate_last_month_end()
            assert result == "2024_009_30"  # September 30, 2024
    
    def test_last_month_end_year_boundary(self, monkeypatch):
        """Test last month end across year boundary."""
        today = datetime(2024, 1, 15)
        from unittest.mock import patch
        with patch('utils.date_utils.datetime') as mock_dt:
            mock_dt.today.return_value = today
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            result = calculate_last_month_end()
            assert result == "2023_012_31"  # December 31, 2023


class TestCalculatePipelineDates:
    """Test pipeline date calculation."""
    
    def test_calculate_with_override(self):
        """Test with pdate override."""
        pdate, yesterday, last_end = calculate_pipeline_dates("2024-11-18")
        assert pdate == "2024-11-18"
        assert yesterday is not None
        assert last_end is not None
    
    def test_calculate_without_override(self):
        """Test without pdate override (uses next Tuesday, or next US business day if that Tuesday is a holiday)."""
        pdate, yesterday, last_end = calculate_pipeline_dates()
        assert pdate is not None
        assert len(pdate) == 10  # YYYY-MM-DD format
        assert yesterday is not None
        assert last_end is not None
        assert len(yesterday) == 10  # MM-DD-YYYY format
        assert len(last_end) >= 11  # YYYY_MM_DD format (e.g. 2026_001_31)

    def test_next_tuesday_skips_us_holiday(self):
        """When next Tuesday is a US holiday (e.g. July 4), pdate is the following business day."""
        # July 4, 2023 is a Tuesday (US Independence Day). Base = Monday July 3 -> next Tuesday = July 4 (holiday) -> pdate should be July 5
        from datetime import datetime
        base = datetime(2023, 7, 3)  # Monday
        pdate = calculate_next_tuesday(base_date=base)
        assert pdate == "2023-07-05"  # Wednesday, first US business day after the holiday Tuesday
