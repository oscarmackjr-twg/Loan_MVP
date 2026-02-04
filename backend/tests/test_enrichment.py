"""Tests for data enrichment functions."""
import pytest
import pandas as pd
from transforms.enrichment import (
    tag_loans_by_group,
    add_seller_loan_number,
    mark_repurchased_loans,
    enrich_buy_df
)


class TestTagLoansByGroup:
    """Test loan tagging by group."""
    
    def test_sfy_tagging(self):
        """Test SFY tagging."""
        df = pd.DataFrame({
            'Loan Group': ['FX3_GROUP', 'FX1_GROUP', 'FX3_SOMETHING']
        })
        
        result = tag_loans_by_group(df)
        
        assert all(result['tagging'] == 'SFY')
    
    def test_prime_tagging(self):
        """Test PRIME tagging."""
        df = pd.DataFrame({
            'Loan Group': ['PRIME_GROUP', 'OTHER_GROUP', 'STANDARD']
        })
        
        result = tag_loans_by_group(df)
        
        assert all(result['tagging'] == 'PRIME')
    
    def test_mixed_tagging(self):
        """Test mixed SFY and PRIME tagging."""
        df = pd.DataFrame({
            'Loan Group': ['FX3_GROUP', 'PRIME_GROUP', 'FX1_GROUP']
        })
        
        result = tag_loans_by_group(df)
        
        assert result['tagging'].iloc[0] == 'SFY'
        assert result['tagging'].iloc[1] == 'PRIME'
        assert result['tagging'].iloc[2] == 'SFY'


class TestAddSellerLoanNumber:
    """Test seller loan number generation."""
    
    def test_add_seller_loan_number(self):
        """Test adding SELLER Loan # column."""
        df = pd.DataFrame({
            'Account Number': [1001, 1002, 1003]
        })
        
        result = add_seller_loan_number(df)
        
        assert 'SELLER Loan #' in result.columns
        assert result['SELLER Loan #'].iloc[0] == 'SFC_1001'
        assert result['SELLER Loan #'].iloc[1] == 'SFC_1002'
    
    def test_account_number_conversion(self):
        """Test Account Number type conversion."""
        df = pd.DataFrame({
            'Account Number': ['1001', '1002']  # String
        })
        
        result = add_seller_loan_number(df)
        
        assert pd.api.types.is_integer_dtype(result['Account Number'])


class TestMarkRepurchasedLoans:
    """Test repurchased loan marking."""
    
    def test_repurchased_detection(self):
        """Test detecting repurchased loans."""
        df = pd.DataFrame({
            'Status Codes': ['', 'REPURCHASE', 'ACTIVE;REPURCHASE', 'ACTIVE']
        })
        
        result = mark_repurchased_loans(df)
        
        assert result['Repurchased'].iloc[0] == False
        assert result['Repurchased'].iloc[1] == True
        assert result['Repurchased'].iloc[2] == True
        assert result['Repurchased'].iloc[3] == False
    
    def test_missing_status_codes(self):
        """Test handling missing Status Codes column."""
        df = pd.DataFrame({
            'Other Column': [1, 2, 3]
        })
        
        result = mark_repurchased_loans(df)
        
        assert 'Repurchased' in result.columns
        assert all(result['Repurchased'] == False)


class TestEnrichBuyDf:
    """Test buy dataframe enrichment."""
    
    def test_basic_enrichment(self, sample_buy_df, sample_loans_types_df):
        """Test basic enrichment."""
        result = enrich_buy_df(
            sample_buy_df,
            sample_loans_types_df,
            pdate="2024-11-18",
            irr_target=8.05
        )
        
        assert 'Platform' in result.columns
        assert 'Purchase_Date' in result.columns
        assert 'IRR Support Target' in result.columns
        assert all(result['IRR Support Target'] == 8.05)
    
    def test_dealer_fee_conversion(self, sample_buy_df, sample_loans_types_df):
        """Test dealer fee percentage to decimal conversion."""
        sample_buy_df['Dealer Fee'] = [5.0, 5.0, 5.0, 5.0, 5.0]  # 5%
        
        result = enrich_buy_df(
            sample_buy_df,
            sample_loans_types_df,
            pdate="2024-11-18",
            irr_target=8.05
        )
        
        assert all(result['Dealer Fee'] == 0.05)
    
    def test_merge_with_loan_types(self, sample_buy_df, sample_loans_types_df):
        """Test merging with loan types."""
        result = enrich_buy_df(
            sample_buy_df,
            sample_loans_types_df,
            pdate="2024-11-18",
            irr_target=8.05
        )
        
        # Should have merged columns from loan types
        assert 'type' in result.columns or 'platform' in result.columns
