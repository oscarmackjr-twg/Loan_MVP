"""Comprehensive tests for all eligibility checks from notebook."""
import pytest
import pandas as pd
import numpy as np
from rules.eligibility import (
    check_eligibility_prime,
    check_eligibility_sfy
)
from outputs.eligibility_reports import format_eligibility_results, export_eligibility_report


class TestPrimeEligibilityComplete:
    """Test all Prime eligibility checks from notebook."""
    
    def test_all_prime_checks_present(self):
        """Verify all Prime checks from notebook are implemented."""
        df = pd.DataFrame({
            'platform': ['prime'] * 10,
            'Repurchase': [False] * 10,
            'Term': [120, 144, 180, 120, 144, 120, 120, 120, 120, 120],
            'type': ['standard', 'standard', 'standard', 'hybrid', 'ninp', 'epni', 'wpdi', 'standard', 'standard', 'standard'],
            'FICO Borrower': [680, 690, 720, 700, 700, 700, 700, 650, 750, 700],
            'Orig. Balance': [10000] * 10,
            'Lender Price(%)': [99.0, 100.0, 101.5, 99.0, 99.0, 99.0, 99.0, 99.0, 99.0, 99.0],
            'Dealer Fee': [0.05] * 10,
            'Property State': ['CA', 'TX', 'NY', 'FL', 'IL', 'CA', 'TX', 'NY', 'FL', 'IL'],
            'new_programs': [False] * 10,
        })
        
        results = check_eligibility_prime(df)
        
        # Verify all expected checks are present
        expected_checks = [
            'check_a', 'check_b1', 'check_b3', 'check_c', 'check_d', 'check_e',
            'check_f', 'check_g', 'check_h1', 'check_h2', 'check_h3',
            'check_i1', 'check_i2', 'check_l1', 'check_l2', 'check_l3', 'check_l4',
            'check_j_state_dist', 'check_s1'
        ]
        
        for check in expected_checks:
            assert check in results, f"Missing check: {check}"
            assert 'value' in results[check]
            assert 'pass' in results[check]
    
    def test_prime_check_a_threshold(self):
        """Test Check A threshold: < 5%."""
        df = pd.DataFrame({
            'platform': ['prime'] * 20,
            'Repurchase': [False] * 20,
            'Term': [120] * 20,
            'type': ['standard'] * 20,
            'FICO Borrower': [680] * 20,
            'Orig. Balance': [10000] * 20,
        })
        
        results = check_eligibility_prime(df)
        
        # Should fail (100% > 5%)
        assert results['check_a']['value'] == 1.0
        assert results['check_a']['pass'] == False
    
    def test_prime_check_b_threshold(self):
        """Test Check B threshold: < 3%."""
        df = pd.DataFrame({
            'platform': ['prime'] * 20,
            'Repurchase': [False] * 20,
            'Term': [180] * 20,
            'type': ['standard'] * 20,
            'FICO Borrower': [680] * 20,
            'Orig. Balance': [10000] * 20,
        })
        
        results = check_eligibility_prime(df)
        
        # Should fail (100% > 3%)
        assert results['check_b1']['value'] == 1.0
        assert results['check_b1']['pass'] == False
    
    def test_prime_check_special_assets(self):
        """Test special assets check (new_programs)."""
        df = pd.DataFrame({
            'platform': ['prime'] * 100,
            'Repurchase': [False] * 100,
            'Orig. Balance': [10000] * 100,
            'new_programs': [False] * 99 + [True],  # 1% new programs
        })
        
        results = check_eligibility_prime(df)
        
        assert 'check_s1' in results
        assert results['check_s1']['value'] == 0.01
        assert results['check_s1']['pass'] == True  # 1% < 2%


class TestSfyEligibilityComplete:
    """Test all SFY eligibility checks from notebook."""
    
    def test_all_sfy_checks_present(self):
        """Verify all SFY checks from notebook are implemented."""
        df = pd.DataFrame({
            'platform': ['sfy'] * 10,
            'type': ['hybrid', 'ninp', 'epni', 'wpdi', 'standard', 'standard', 'standard', 'standard', 'wpdi_bd', 'standard_bd'],
            'Term': [120, 72, 120, 120, 120, 144, 180, 120, 120, 120],
            'promo_term': [0, 6, 0, 12, 0, 0, 0, 0, 12, 0],
            'APR': [6.5, 7.5, 8.0, 7.0, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0],
            'Orig. Balance': [10000] * 10,
            'Lender Price(%)': [99.0] * 10,
            'Dealer Fee': [0.05] * 10,
            'FICO Borrower': [720] * 10,
            'loan program': ['Unsec Std - 999 - 120'] * 10,
            'Property State': ['CA'] * 10,
            'new_programs': [False] * 10,
            'Repurchase': [False] * 10,
            'Excess_Asset': [False] * 10,
            'Purchase Price': [9900] * 10,
        })
        
        buy_df = pd.DataFrame({
            'platform': ['sfy'],
            'type': ['standard_bd'],
            'Orig. Balance': [10000],
        })
        
        results = check_eligibility_sfy(df, buy_df=buy_df)
        
        # Verify all expected checks are present
        expected_checks = [
            'check_a1', 'check_a2', 'check_b1', 'check_b2', 'check_b3', 'check_b4',
            'check_c1', 'check_d1', 'check_d2', 'check_d3', 'check_d4',
            'check_e1', 'check_e2', 'check_e3', 'check_e4',
            'check_f1', 'check_f2', 'check_f3', 'check_f4',
            'check_g1', 'check_g2',
            'check_j1', 'check_j2', 'check_j3', 'check_j4',
            'check_h_state_dist',
            'check_l1', 'check_l2', 'check_l3', 'check_l4', 'check_l5',
            'check_s1'
        ]
        
        for check in expected_checks:
            assert check in results, f"Missing check: {check}"
            assert 'value' in results[check]
            assert 'pass' in results[check]
    
    def test_sfy_check_a1_threshold(self):
        """Test Check A1 threshold: < 85%."""
        df = pd.DataFrame({
            'platform': ['sfy'] * 10,
            'type': ['hybrid'] * 10,
            'Orig. Balance': [10000] * 10,
        })
        
        results = check_eligibility_sfy(df)
        
        # Should fail (100% > 85%)
        assert results['check_a1']['value'] == 1.0
        assert results['check_a1']['pass'] == False
    
    def test_sfy_check_b4_threshold(self):
        """Test Check B4 threshold: <= 0%."""
        df = pd.DataFrame({
            'platform': ['sfy'] * 10,
            'type': ['ninp'] * 10,
            'Term': [72] * 10,  # All <= 84
            'Orig. Balance': [10000] * 10,
        })
        
        results = check_eligibility_sfy(df)
        
        # Should pass (0% <= 0%)
        assert results['check_b4']['value'] == 0.0
        assert results['check_b4']['pass'] == True
    
    def test_sfy_check_l5_with_buy_df(self):
        """Test Check L5 requires buy_df."""
        df = pd.DataFrame({
            'platform': ['sfy'] * 10,
            'type': ['standard'] * 10,
            'Orig. Balance': [10000] * 10,
        })
        
        buy_df = pd.DataFrame({
            'platform': ['sfy'] * 5,
            'type': ['standard_bd'] * 5,
            'Orig. Balance': [10000] * 5,
        })
        
        results_with_buy = check_eligibility_sfy(df, buy_df=buy_df)
        results_without_buy = check_eligibility_sfy(df, buy_df=None)
        
        # check_l5 should only be present when buy_df is provided
        assert 'check_l5' in results_with_buy
        assert 'check_l5' not in results_without_buy


class TestEligibilityReporting:
    """Test eligibility reporting functionality."""
    
    def test_format_eligibility_results(self):
        """Test formatting eligibility results."""
        prime_results = {
            'check_a': {'value': 0.03, 'pass': True},
            'check_b1': {'value': 0.02, 'pass': True},
        }
        
        sfy_results = {
            'check_a1': {'value': 0.80, 'pass': True},
            'check_a2': {'value': 0.20, 'pass': True},
        }
        
        formatted = format_eligibility_results(prime_results, sfy_results)
        
        assert 'prime' in formatted
        assert 'sfy' in formatted
        assert formatted['prime']['summary']['total_checks'] == 2
        assert formatted['prime']['summary']['passed'] == 2
        assert formatted['sfy']['summary']['total_checks'] == 2
        assert formatted['sfy']['summary']['passed'] == 2
    
    def test_export_eligibility_report(self, temp_dir):
        """Test exporting eligibility report."""
        prime_results = {
            'check_a': {'value': 0.03, 'pass': True},
        }
        
        sfy_results = {
            'check_a1': {'value': 0.80, 'pass': True},
        }
        
        file_path = export_eligibility_report(
            prime_results,
            sfy_results,
            str(temp_dir)
        )
        
        assert Path(file_path).exists()
        
        # Verify Excel file was also created
        excel_path = str(temp_dir / "eligibility_checks_summary.xlsx")
        assert Path(excel_path).exists()
