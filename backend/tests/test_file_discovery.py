"""Tests for file discovery utilities."""
import pytest
from pathlib import Path
import pandas as pd
from utils.file_discovery import (
    find_file_by_pattern,
    find_tape_loans_file,
    find_sfy_file,
    find_prime_file,
    discover_input_files
)
from utils.date_utils import calculate_last_month_end


class TestFindFileByPattern:
    """Test file pattern matching."""
    
    def test_find_exact_match(self, temp_dir):
        """Test finding exact file match."""
        test_file = temp_dir / "test_file.csv"
        test_file.write_text("test")
        
        result = find_file_by_pattern(str(temp_dir), "test_file.csv", required=False)
        assert result == test_file
    
    def test_find_wildcard_match(self, temp_dir):
        """Test finding file with wildcard pattern."""
        test_file = temp_dir / "Tape20Loans_10-21-2025.csv"
        test_file.write_text("test")
        
        result = find_file_by_pattern(str(temp_dir), "Tape20Loans_*.csv", required=False)
        assert result == test_file
    
    def test_find_with_date_substitution(self, temp_dir):
        """Test finding file with date substitution."""
        test_file = temp_dir / "Tape20Loans_10-21-2025.csv"
        test_file.write_text("test")
        
        result = find_file_by_pattern(
            str(temp_dir),
            "Tape20Loans_{date}.csv",
            date_str="10-21-2025",
            required=False
        )
        assert result == test_file
    
    def test_file_not_found_required(self, temp_dir):
        """Test error when required file not found."""
        with pytest.raises(FileNotFoundError):
            find_file_by_pattern(str(temp_dir), "nonexistent.csv", required=True)
    
    def test_file_not_found_optional(self, temp_dir):
        """Test None return when optional file not found."""
        result = find_file_by_pattern(str(temp_dir), "nonexistent.csv", required=False)
        assert result is None
    
    def test_multiple_matches_uses_most_recent(self, temp_dir):
        """Test that multiple matches use most recent file."""
        old_file = temp_dir / "Tape20Loans_10-20-2025.csv"
        old_file.write_text("old")
        
        new_file = temp_dir / "Tape20Loans_10-21-2025.csv"
        new_file.write_text("new")
        
        # Touch new file to make it more recent
        import time
        time.sleep(0.1)
        new_file.touch()
        
        result = find_file_by_pattern(str(temp_dir), "Tape20Loans_*.csv", required=False)
        assert result == new_file


class TestFindTapeLoansFile:
    """Test Tape20Loans file discovery."""
    
    def test_find_tape_loans_file(self, sample_input_dir):
        """Test finding Tape20Loans file."""
        from datetime import datetime, timedelta
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%m-%d-%Y')
        
        result = find_tape_loans_file(str(sample_input_dir), yesterday, required=False)
        assert result is not None
        assert "Tape20Loans" in result.name


class TestFindSfyFile:
    """Test SFY file discovery."""
    
    def test_find_sfy_file_with_date(self, sample_input_dir):
        """Test finding SFY file with specific date."""
        from datetime import datetime, timedelta
        date_str = (datetime.now() - timedelta(days=1)).strftime('%m-%d-%Y')
        
        result = find_sfy_file(str(sample_input_dir), date_str, required=False)
        assert result is not None
        assert "SFY" in result.name
    
    def test_find_sfy_file_auto(self, sample_input_dir):
        """Test finding SFY file automatically."""
        result = find_sfy_file(str(sample_input_dir), required=False)
        assert result is not None
        assert "SFY" in result.name


class TestFindPrimeFile:
    """Test PRIME file discovery."""
    
    def test_find_prime_file_with_date(self, sample_input_dir):
        """Test finding PRIME file with specific date."""
        from datetime import datetime, timedelta
        date_str = (datetime.now() - timedelta(days=1)).strftime('%m-%d-%Y')
        
        result = find_prime_file(str(sample_input_dir), date_str, required=False)
        assert result is not None
        assert "PRIME" in result.name


class TestDiscoverInputFiles:
    """Test input file discovery."""
    
    def test_discover_all_files(self, sample_input_dir):
        """Test discovering all input files."""
        from datetime import datetime, timedelta
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%m-%d-%Y')
        
        files = discover_input_files(
            str(sample_input_dir),
            yesterday,
            sfy_date=None,
            prime_date=None
        )
        
        assert files['loans'] is not None
        assert files['sfy_file'] is not None
        assert files['prime_file'] is not None
        # FX files are optional
        assert 'fx3_file' in files
        assert 'fx4_file' in files
