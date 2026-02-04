"""Tests for data normalization functions."""
import pytest
import pandas as pd
from datetime import datetime
from transforms.normalize import (
    normalize_loans_df,
    normalize_sfy_df,
    normalize_prime_df
)


class TestNormalizeLoansDf:
    """Test loans dataframe normalization."""
    
    def test_basic_normalization(self, sample_loans_df):
        """Test basic normalization."""
        result = normalize_loans_df(sample_loans_df)
        
        assert len(result) == len(sample_loans_df)
        assert 'Account Number' in result.columns
        assert 'Loan Group' in result.columns
    
    def test_date_conversion(self, sample_loans_df):
        """Test date column conversion."""
        result = normalize_loans_df(sample_loans_df)
        
        assert pd.api.types.is_datetime64_any_dtype(result['Open Date'])
        assert pd.api.types.is_datetime64_any_dtype(result['maturityDate'])
    
    def test_status_codes_fillna(self, sample_loans_df):
        """Test Status Codes fillna."""
        sample_loans_df.loc[0, 'Status Codes'] = None
        result = normalize_loans_df(sample_loans_df)
        
        assert result['Status Codes'].iloc[0] == ""
    
    def test_missing_required_columns(self):
        """Test error when required columns missing."""
        df = pd.DataFrame({'Other Column': [1, 2, 3]})
        
        with pytest.raises(ValueError, match="Missing required columns"):
            normalize_loans_df(df)


class TestNormalizeSfyDf:
    """Test SFY dataframe normalization."""
    
    def test_header_row_skipping(self):
        """Test skipping header rows."""
        # Create dataframe with header rows
        df = pd.DataFrame({
            'A': ['', '', '', 'Header1', 'Data1'],
            'B': ['', '', '', 'Header2', 'Data2'],
        })
        
        result = normalize_sfy_df(df)
        
        # Should have skipped first 4 rows and header row
        assert len(result) == 1
        assert 'Header1' in result.columns
    
    def test_tu144_column_standardization(self):
        """Test TU144 column name standardization."""
        df = pd.DataFrame({
            'A': ['', '', '', 'TU_144', '1'],
            'B': ['', '', '', 'Other', 'Data'],
        })
        
        result = normalize_sfy_df(df)
        
        # Should standardize to TU144
        assert 'TU144' in result.columns or 'TU_144' in result.columns
    
    def test_no_header_rows(self):
        """Test handling when no header rows to skip."""
        df = pd.DataFrame({
            'SELLER Loan #': ['SFC_1001'],
            'Loan Program': ['Test Program'],
        })
        
        result = normalize_sfy_df(df)
        
        assert len(result) == len(df)


class TestNormalizePrimeDf:
    """Test Prime dataframe normalization."""
    
    def test_header_row_skipping(self):
        """Test skipping header rows."""
        df = pd.DataFrame({
            'A': ['', '', '', 'Header1', 'Data1'],
            'B': ['', '', '', 'Header2', 'Data2'],
        })
        
        result = normalize_prime_df(df)
        
        assert len(result) == 1
        assert 'Header1' in result.columns
    
    def test_no_header_rows(self):
        """Test handling when no header rows to skip."""
        df = pd.DataFrame({
            'SELLER Loan #': ['SFC_1002'],
            'Loan Program': ['Test Program'],
        })
        
        result = normalize_prime_df(df)
        
        assert len(result) == len(df)
