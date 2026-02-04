"""Tests for underwriting validation rules."""
import pytest
import pandas as pd
from rules.underwriting import (
    check_underwriting,
    get_underwriting_exceptions
)


class TestCheckUnderwriting:
    """Test underwriting checks."""
    
    def test_pass_criteria(self, sample_buy_df, sample_underwriting_df):
        """Test loans that pass underwriting criteria."""
        # Loan that meets all criteria
        buy_df = pd.DataFrame({
            'SELLER Loan #': ['SFC_1001'],
            'loan program': ['Unsec Std - 999 - 120'],
            'Application Type': ['STANDARD'],
            'Income': [60000],  # $5000/month
            'FICO Borrower': [720],
            'DTI': [0.35],  # 35%
            'PTI': [0.15],  # 15%
            'Orig. Balance': [15000],
            'Stamp fee': [0],
        })
        
        flagged, min_income = check_underwriting(
            buy_df,
            sample_underwriting_df,
            is_notes=False,
            tuloans=[]
        )
        
        assert len(flagged) == 0
    
    def test_fail_balance_criteria(self, sample_underwriting_df):
        """Test loan that fails balance criteria."""
        buy_df = pd.DataFrame({
            'SELLER Loan #': ['SFC_1001'],
            'loan program': ['Unsec Std - 999 - 120'],
            'Application Type': ['STANDARD'],
            'Income': [60000],
            'FICO Borrower': [720],
            'DTI': [0.35],
            'PTI': [0.15],
            'Orig. Balance': [50000],  # Too high
            'Stamp fee': [0],
        })
        
        flagged, min_income = check_underwriting(
            buy_df,
            sample_underwriting_df,
            is_notes=False,
            tuloans=[]
        )
        
        assert len(flagged) > 0
        assert 'SFC_1001' in flagged
    
    def test_fail_dti_criteria(self, sample_underwriting_df):
        """Test loan that fails DTI criteria."""
        buy_df = pd.DataFrame({
            'SELLER Loan #': ['SFC_1001'],
            'loan program': ['Unsec Std - 999 - 120'],
            'Application Type': ['STANDARD'],
            'Income': [60000],
            'FICO Borrower': [720],
            'DTI': [0.60],  # Too high (60%)
            'PTI': [0.15],
            'Orig. Balance': [15000],
            'Stamp fee': [0],
        })
        
        flagged, min_income = check_underwriting(
            buy_df,
            sample_underwriting_df,
            is_notes=False,
            tuloans=[]
        )
        
        assert len(flagged) > 0
    
    def test_high_fico_income_exception(self, sample_underwriting_df):
        """Test high FICO loan with income exception."""
        buy_df = pd.DataFrame({
            'SELLER Loan #': ['SFC_1001'],
            'loan program': ['Unsec Std - 999 - 120'],
            'Application Type': ['STANDARD'],
            'Income': [20000],  # Low income
            'FICO Borrower': [750],  # High FICO
            'DTI': [0.35],
            'PTI': [0.15],
            'Orig. Balance': [15000],
            'Stamp fee': [0],
        })
        
        flagged, min_income = check_underwriting(
            buy_df,
            sample_underwriting_df,
            is_notes=False,
            tuloans=[]
        )
        
        # Should pass with min_income exception
        assert len(flagged) == 0
        assert len(min_income) > 0
    
    def test_notes_loans(self, sample_underwriting_df):
        """Test notes loan checking."""
        buy_df = pd.DataFrame({
            'SELLER Loan #': ['SFC_1001'],
            'loan program': ['Unsec Std - 999 - 120notes'],
            'Application Type': ['HD NOTE'],
            'Income': [60000],
            'FICO Borrower': [720],
            'DTI': [0.35],
            'PTI': [0.15],
            'Orig. Balance': [15000],
            'Stamp fee': [0],
        })
        
        flagged, min_income = check_underwriting(
            buy_df,
            sample_underwriting_df,
            is_notes=True,
            tuloans=[]
        )
        
        # Should check notes program (without 'notes' suffix)
        assert isinstance(flagged, list)
    
    def test_tuloans_exclusion(self, sample_underwriting_df):
        """Test TU loans exclusion."""
        buy_df = pd.DataFrame({
            'SELLER Loan #': ['SFC_1001', 'SFC_1002'],
            'loan program': ['Unsec Std - 999 - 120', 'Unsec Std - 999 - 120'],
            'Application Type': ['STANDARD', 'STANDARD'],
            'Income': [60000, 60000],
            'FICO Borrower': [720, 720],
            'DTI': [0.35, 0.35],
            'PTI': [0.15, 0.15],
            'Orig. Balance': [15000, 15000],
            'Stamp fee': [0, 0],
        })
        
        flagged, min_income = check_underwriting(
            buy_df,
            sample_underwriting_df,
            is_notes=False,
            tuloans=['SFC_1001']
        )
        
        # SFC_1001 should be excluded from checking
        assert 'SFC_1001' not in flagged


class TestGetUnderwritingExceptions:
    """Test underwriting exception generation."""
    
    def test_exception_generation(self, sample_buy_df):
        """Test generating exceptions for flagged loans."""
        flagged_loans = ['SFC_1001', 'SFC_1002']
        
        exceptions = get_underwriting_exceptions(
            sample_buy_df,
            flagged_loans,
            exception_type='underwriting'
        )
        
        assert len(exceptions) == len(flagged_loans)
        assert all(exc['exception_type'] == 'underwriting' for exc in exceptions)
        assert all(exc['severity'] == 'error' for exc in exceptions)
