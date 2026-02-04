"""Tests for eligibility validation rules."""
import pytest
import pandas as pd
import numpy as np
from rules.eligibility import (
    check_eligibility_prime,
    check_eligibility_sfy
)


class TestCheckEligibilityPrime:
    """Test Prime eligibility checks."""
    
    def test_check_a_term_144_standard_fico_700(self):
        """Test Check A: Term <= 144, standard, FICO < 700."""
        df = pd.DataFrame({
            'platform': ['prime', 'prime', 'prime'],
            'Repurchase': [False, False, False],
            'Term': [120, 144, 180],
            'type': ['standard', 'standard', 'standard'],
            'FICO Borrower': [680, 690, 720],
            'Orig. Balance': [10000, 20000, 30000],
        })
        
        result = check_eligibility_prime(df)
        
        assert 'check_a' in result
        assert 'value' in result['check_a']
        assert 'pass' in result['check_a']
    
    def test_check_b_term_144_standard_fico_700(self):
        """Test Check B: Term > 144, standard, FICO < 700."""
        df = pd.DataFrame({
            'platform': ['prime', 'prime'],
            'Repurchase': [False, False],
            'Term': [180, 180],
            'type': ['standard', 'standard'],
            'FICO Borrower': [680, 690],
            'Orig. Balance': [10000, 20000],
        })
        
        result = check_eligibility_prime(df)
        
        assert 'check_b1' in result
        assert 'check_b3' in result  # Count-based check
    
    def test_check_c_term_144_standard_fico_700_plus(self):
        """Test Check C: Term > 144, standard, FICO >= 700."""
        df = pd.DataFrame({
            'platform': ['prime', 'prime'],
            'Term': [180, 180],
            'type': ['standard', 'standard'],
            'FICO Borrower': [720, 750],
            'Orig. Balance': [10000, 20000],
        })
        
        result = check_eligibility_prime(df)
        
        assert 'check_c' in result
        assert result['check_c']['pass'] == (result['check_c']['value'] < 0.35)
    
    def test_check_d_hybrid(self):
        """Test Check D: Hybrid type."""
        df = pd.DataFrame({
            'platform': ['prime', 'prime', 'prime'],
            'type': ['hybrid', 'standard', 'hybrid'],
            'Orig. Balance': [10000, 20000, 15000],
        })
        
        result = check_eligibility_prime(df)
        
        assert 'check_d' in result
        hybrid_ratio = result['check_d']['value']
        assert hybrid_ratio < 1.0  # Should be ratio
    
    def test_check_l_fico(self):
        """Test Check L: FICO distribution."""
        df = pd.DataFrame({
            'platform': ['prime', 'prime', 'prime'],
            'FICO Borrower': [650, 700, 750],
            'Orig. Balance': [10000, 20000, 30000],
        })
        
        result = check_eligibility_prime(df)
        
        assert 'check_l1' in result  # < 680
        assert 'check_l2' in result  # < 700
        assert 'check_l3' in result  # Weighted average
    
    def test_empty_dataframe(self):
        """Test handling empty dataframe."""
        df = pd.DataFrame({
            'platform': [],
            'Orig. Balance': [],
        })
        
        result = check_eligibility_prime(df)
        
        assert result == {}


class TestCheckEligibilitySfy:
    """Test SFY eligibility checks."""
    
    def test_check_a_hybrid(self):
        """Test Check A: Hybrid type."""
        df = pd.DataFrame({
            'platform': ['sfy', 'sfy', 'sfy'],
            'type': ['hybrid', 'standard', 'hybrid'],
            'APR': [6.5, 7.5, 8.0],
            'Orig. Balance': [10000, 20000, 15000],
        })
        
        result = check_eligibility_sfy(df)
        
        assert 'check_a1' in result  # Hybrid ratio
        assert 'check_a2' in result  # Hybrid with APR < 7.0
    
    def test_check_b_ninp(self):
        """Test Check B: NINP type."""
        df = pd.DataFrame({
            'platform': ['sfy', 'sfy', 'sfy'],
            'type': ['ninp', 'standard', 'ninp'],
            'promo_term': [6, 12, 18],
            'Term': [72, 120, 84],
            'Orig. Balance': [10000, 20000, 15000],
        })
        
        result = check_eligibility_sfy(df)
        
        assert 'check_b1' in result  # NINP ratio
        assert 'check_b2' in result  # promo_term > 6
        assert 'check_b3' in result  # promo_term > 12
        assert 'check_b4' in result  # Term > 84
    
    def test_check_d_wpdi(self):
        """Test Check D: WPDI type."""
        df = pd.DataFrame({
            'platform': ['sfy', 'sfy', 'sfy'],
            'type': ['wpdi', 'wpdi_bd', 'standard'],
            'promo_term': [6, 12, 18],
            'Orig. Balance': [10000, 20000, 15000],
        })
        
        result = check_eligibility_sfy(df)
        
        assert 'check_d1' in result  # wpdi
        assert 'check_d2' in result  # wpdi or wpdi_bd
        assert 'check_d3' in result  # wpdi with promo_term >= 12
        assert 'check_d4' in result  # wpdi/wpdi_bd with promo_term >= 12
    
    def test_check_e_standard_term(self):
        """Test Check E: Standard term > 120."""
        df = pd.DataFrame({
            'platform': ['sfy', 'sfy', 'sfy'],
            'type': ['standard', 'standard_bd', 'standard'],
            'Term': [120, 144, 180],
            'Orig. Balance': [10000, 20000, 15000],
        })
        
        result = check_eligibility_sfy(df)
        
        assert 'check_e1' in result  # standard, Term > 120
        assert 'check_e2' in result  # standard/standard_bd, Term > 120
        assert 'check_e3' in result  # standard, Term > 144
        assert 'check_e4' in result  # standard/standard_bd, Term > 144
    
    def test_check_f_lender_price(self):
        """Test Check F: Lender Price."""
        df = pd.DataFrame({
            'platform': ['sfy', 'sfy', 'sfy'],
            'Lender Price(%)': [99.0, 101.5, 102.5],
            'loan program': ['Unsec Std - 999 - 120', 'Other', 'Unsec Std - 999 - 120'],
            'Dealer Fee': [0.05, 0.05, 0.05],
            'Orig. Balance': [10000, 20000, 15000],
        })
        
        result = check_eligibility_sfy(df)
        
        assert 'check_f1' in result  # Max lender price
        assert 'check_f2' in result  # Price 100-103 ratio
        assert 'check_f3' in result  # Price 100-103 excluding specific program
        assert 'check_f4' in result  # Dealer fee
    
    def test_check_j_fico(self):
        """Test Check J: FICO distribution."""
        df = pd.DataFrame({
            'platform': ['sfy', 'sfy', 'sfy'],
            'FICO Borrower': [650, 700, 750],
            'Orig. Balance': [10000, 20000, 30000],
        })
        
        result = check_eligibility_sfy(df)
        
        assert 'check_j1' in result  # < 680
        assert 'check_j2' in result  # < 700
        assert 'check_j3' in result  # Weighted average
        assert 'check_j4' in result  # Mean
    
    def test_check_l_bd_types(self):
        """Test Check L: BD types."""
        df = pd.DataFrame({
            'platform': ['sfy', 'sfy', 'sfy'],
            'type': ['wpdi_bd', 'standard_bd', 'standard'],
            'Orig. Balance': [10000, 20000, 15000],
        })
        
        buy_df = pd.DataFrame({
            'platform': ['sfy'],
            'type': ['standard_bd'],
            'Orig. Balance': [10000],
        })
        
        result = check_eligibility_sfy(df, buy_df=buy_df)
        
        assert 'check_l1' in result  # wpdi_bd
        assert 'check_l2' in result  # standard_bd
        assert 'check_l5' in result  # From buy_df
