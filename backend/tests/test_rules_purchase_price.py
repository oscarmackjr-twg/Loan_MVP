"""Tests for purchase price validation rules."""
import pytest
import pandas as pd
from rules.purchase_price import (
    check_purchase_price,
    get_purchase_price_exceptions
)


class TestCheckPurchasePrice:
    """Test purchase price checking."""
    
    def test_exact_match(self):
        """Test exact price match."""
        df = pd.DataFrame({
            'Lender Price(%)': [99.0, 100.0, 101.5],
            'modeled_purchase_price': [0.99, 1.0, 1.015],
        })
        
        result = check_purchase_price(df)
        
        assert all(result['purchase_price_check'] == True)
    
    def test_rounding_match(self):
        """Test rounding edge cases."""
        df = pd.DataFrame({
            'Lender Price(%)': [99.0, 99.01, 99.005],
            'modeled_purchase_price': [0.99005, 0.9901, 0.99005],
        })
        
        result = check_purchase_price(df)
        
        # 99.005 should round to 99.01, so first should pass, second should pass
        assert result['purchase_price_check'].iloc[0] == True
        assert result['purchase_price_check'].iloc[1] == True
    
    def test_mismatch(self):
        """Test price mismatch detection."""
        df = pd.DataFrame({
            'Lender Price(%)': [99.0, 100.0],
            'modeled_purchase_price': [0.98, 1.01],  # Mismatches
        })
        
        result = check_purchase_price(df)
        
        assert all(result['purchase_price_check'] == False)
    
    def test_missing_columns(self):
        """Test handling missing columns."""
        df = pd.DataFrame({
            'Other Column': [1, 2, 3]
        })
        
        result = check_purchase_price(df)
        
        assert all(result['purchase_price_check'] == False)


class TestGetPurchasePriceExceptions:
    """Test purchase price exception generation."""
    
    def test_exception_generation(self):
        """Test generating exceptions for mismatches."""
        df = pd.DataFrame({
            'SELLER Loan #': ['SFC_1001', 'SFC_1002'],
            'Lender Price(%)': [99.0, 100.0],
            'modeled_purchase_price': [0.98, 1.01],
            'purchase_price_check': [False, False],
        })
        
        exceptions = get_purchase_price_exceptions(df)
        
        assert len(exceptions) == 2
        assert exceptions[0]['exception_type'] == 'purchase_price'
        assert exceptions[0]['severity'] == 'error'
        assert 'SFC_1001' in exceptions[0]['message']
    
    def test_no_exceptions(self):
        """Test no exceptions when all match."""
        df = pd.DataFrame({
            'SELLER Loan #': ['SFC_1001'],
            'Lender Price(%)': [99.0],
            'modeled_purchase_price': [0.99],
            'purchase_price_check': [True],
        })
        
        exceptions = get_purchase_price_exceptions(df)
        
        assert len(exceptions) == 0
