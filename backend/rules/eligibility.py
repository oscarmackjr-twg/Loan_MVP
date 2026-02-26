"""Eligibility checks for portfolio compliance."""
import pandas as pd
from typing import Dict, Any
import numpy as np


def check_eligibility_prime(final_df_all: pd.DataFrame) -> Dict[str, Any]:
    """
    Run Prime eligibility checks.
    
    Returns dictionary with check results:
    {
        'check_a': {'value': float, 'pass': bool},
        'check_b1': {'value': float, 'pass': bool},
        'check_b3': {'value': float, 'pass': bool},
        ...
    }
    """
    """Run Prime eligibility checks."""
    results = {}
    
    prime_df = final_df_all[final_df_all['platform'] == 'prime'].copy()
    total_balance = prime_df['Orig. Balance'].sum()
    
    if total_balance == 0:
        return results
    
    # Check A: Term <= 144, standard, FICO < 700
    check_a = prime_df[
        (prime_df['Repurchase'] == False) &
        (prime_df['Term'] <= 144) &
        (prime_df['type'] == 'standard') &
        (prime_df['FICO Borrower'] < 700)
    ]['Orig. Balance'].sum() / total_balance
    results['check_a'] = {'value': check_a, 'pass': check_a < 0.05}
    
    # Check B: Term > 144, standard, FICO < 700
    check_b1 = prime_df[
        (prime_df['Repurchase'] == False) &
        (prime_df['Term'] > 144) &
        (prime_df['type'] == 'standard') &
        (prime_df['FICO Borrower'] < 700)
    ]['Orig. Balance'].sum() / total_balance
    results['check_b1'] = {'value': check_b1, 'pass': check_b1 < 0.03}
    
    # Check B3: Count-based check (from notebook)
    check_b3 = prime_df[
        (prime_df['Term'] > 144) &
        (prime_df['type'] == 'standard') &
        (prime_df['FICO Borrower'] < 700)
    ]['Orig. Balance'].shape[0] / prime_df['Orig. Balance'].shape[0]
    results['check_b3'] = {'value': check_b3, 'pass': check_b3 < 0.03}
    
    # Check C: Term > 144, standard, FICO >= 700
    check_c = prime_df[
        (prime_df['Term'] > 144) &
        (prime_df['type'] == 'standard') &
        (prime_df['FICO Borrower'] >= 700)
    ]['Orig. Balance'].sum() / total_balance
    results['check_c'] = {'value': check_c, 'pass': check_c < 0.35}
    
    # Check D: Hybrid
    check_d = prime_df[prime_df['type'] == 'hybrid']['Orig. Balance'].sum() / total_balance
    results['check_d'] = {'value': check_d, 'pass': check_d < 0.35}
    
    # Check E: NINP
    check_e = prime_df[prime_df['type'] == 'ninp']['Orig. Balance'].sum() / total_balance
    results['check_e'] = {'value': check_e, 'pass': check_e < 0.15}
    
    # Check F: EPNI
    check_f = prime_df[prime_df['type'] == 'epni']['Orig. Balance'].sum() / total_balance
    results['check_f'] = {'value': check_f, 'pass': check_f < 0.18}
    
    # Check G: WPDI
    check_g = prime_df[prime_df['type'] == 'wpdi']['Orig. Balance'].sum() / total_balance
    results['check_g'] = {'value': check_g, 'pass': check_g < 0.15}
    
    # Check H: Lender Price
    check_h1 = prime_df['Lender Price(%)'].max()
    check_h2 = prime_df[
        (prime_df['Lender Price(%)'] > 100) &
        (prime_df['Lender Price(%)'] <= 103)
    ]['Orig. Balance'].sum() / total_balance
    check_h3 = (prime_df['Dealer Fee'] * prime_df['Orig. Balance']).sum() / total_balance
    results['check_h1'] = {'value': check_h1, 'pass': check_h1 <= 102}  # notebook: h1<=102
    results['check_h2'] = {'value': check_h2, 'pass': check_h2 < 0.35}
    results['check_h3'] = {'value': check_h3, 'pass': check_h3 < 0.15}
    
    # Check I: Balance > 50000
    check_i1 = prime_df[prime_df['Orig. Balance'] > 50000]['Orig. Balance'].sum() / total_balance
    check_i2 = prime_df['Orig. Balance'].mean()
    results['check_i1'] = {'value': check_i1, 'pass': check_i1 < 0.38}
    results['check_i2'] = {'value': check_i2, 'pass': check_i2 < 20000}
    
    # Check J: Property State distribution (from notebook - informational)
    try:
        state_distribution = pd.pivot_table(
            prime_df,
            values='Orig. Balance',
            aggfunc='sum',
            columns='Property State'
        ) / total_balance
        results['check_j_state_dist'] = {
            'value': state_distribution.T.sort_values('Orig. Balance', ascending=False).to_dict() if not state_distribution.empty else {},
            'pass': True  # Informational only
        }
    except Exception:
        results['check_j_state_dist'] = {'value': {}, 'pass': True}
    
    # Check L: FICO
    check_l1 = prime_df[prime_df['FICO Borrower'] < 680]['Orig. Balance'].sum() / total_balance
    check_l2 = prime_df[prime_df['FICO Borrower'] < 700]['Orig. Balance'].sum() / total_balance
    check_l3 = (prime_df['Orig. Balance'] * prime_df['FICO Borrower']).sum() / total_balance
    check_l4 = prime_df['FICO Borrower'].mean()  # Mean FICO (from notebook)
    results['check_l1'] = {'value': check_l1, 'pass': check_l1 < 0.5}
    results['check_l2'] = {'value': check_l2, 'pass': check_l2 < 0.7}
    results['check_l3'] = {'value': check_l3, 'pass': check_l3 > 700}
    results['check_l4'] = {'value': check_l4, 'pass': True}  # Informational
    
    # Special asset check (new_programs) - from notebook
    non_repurchase_prime = prime_df[prime_df['Repurchase'] == False]
    if len(non_repurchase_prime) > 0:
        non_repurchase_total = non_repurchase_prime['Orig. Balance'].sum()
        check_s1 = non_repurchase_prime[
            non_repurchase_prime.get('new_programs', False) == True
        ]['Orig. Balance'].sum() / non_repurchase_total if non_repurchase_total > 0 else 0
        results['check_s1'] = {'value': check_s1, 'pass': check_s1 < 0.02}
    else:
        results['check_s1'] = {'value': 0, 'pass': True}
    
    return results


def check_eligibility_sfy(final_df_all: pd.DataFrame, buy_df: pd.DataFrame = None) -> Dict[str, Any]:
    """
    Run SFY eligibility checks.
    
    Args:
        final_df_all: Complete dataframe with all loans
        buy_df: Optional buy dataframe for new loans only (used for check_l5)
    
    Returns dictionary with check results:
    {
        'check_a1': {'value': float, 'pass': bool},
        'check_a2': {'value': float, 'pass': bool},
        ...
    }
    """
    """Run SFY eligibility checks."""
    results = {}
    
    sfy_df = final_df_all[final_df_all['platform'] == 'sfy'].copy()
    total_balance = sfy_df['Orig. Balance'].sum()
    
    if total_balance == 0:
        return results
    
    # Check A: Hybrid
    check_a1 = sfy_df[sfy_df['type'] == 'hybrid']['Orig. Balance'].sum() / total_balance
    check_a2 = sfy_df[
        (sfy_df['type'] == 'hybrid') &
        (sfy_df['APR'] < 7.0)
    ]['Orig. Balance'].sum() / total_balance
    results['check_a1'] = {'value': check_a1, 'pass': check_a1 < 0.85}
    results['check_a2'] = {'value': check_a2, 'pass': check_a2 < 0.25}
    
    # Check B: NINP
    check_b1 = sfy_df[sfy_df['type'] == 'ninp']['Orig. Balance'].sum() / total_balance
    check_b2 = sfy_df[
        (sfy_df['type'] == 'ninp') &
        (sfy_df['promo_term'] > 6)
    ]['Orig. Balance'].sum() / total_balance
    check_b3 = sfy_df[
        (sfy_df['type'] == 'ninp') &
        (sfy_df['promo_term'] > 12)
    ]['Orig. Balance'].sum() / total_balance
    check_b4 = sfy_df[
        (sfy_df['type'] == 'ninp') &
        (sfy_df['Term'] > 84)
    ]['Orig. Balance'].sum() / total_balance
    results['check_b1'] = {'value': check_b1, 'pass': check_b1 < 0.3}
    results['check_b2'] = {'value': check_b2, 'pass': check_b2 < 0.27}
    results['check_b3'] = {'value': check_b3, 'pass': check_b3 < 0.15}
    results['check_b4'] = {'value': check_b4, 'pass': check_b4 <= 0}
    
    # Check C: EPNI
    check_c1 = sfy_df[sfy_df['type'] == 'epni']['Orig. Balance'].sum() / total_balance
    results['check_c1'] = {'value': check_c1, 'pass': check_c1 <= 0.25}
    
    # Check D: WPDI
    check_d1 = sfy_df[sfy_df['type'] == 'wpdi']['Orig. Balance'].sum() / total_balance
    check_d2 = sfy_df[sfy_df['type'].isin(['wpdi', 'wpdi_bd'])]['Orig. Balance'].sum() / total_balance
    check_d3 = sfy_df[
        (sfy_df['type'] == 'wpdi') &
        (sfy_df['promo_term'] >= 12)
    ]['Orig. Balance'].sum() / total_balance
    check_d4 = sfy_df[
        (sfy_df['type'].isin(['wpdi', 'wpdi_bd'])) &
        (sfy_df['promo_term'] >= 12)
    ]['Orig. Balance'].sum() / total_balance
    results['check_d1'] = {'value': check_d1, 'pass': check_d1 <= 0.17}
    results['check_d2'] = {'value': check_d2, 'pass': check_d2 <= 0.17}
    results['check_d3'] = {'value': check_d3, 'pass': check_d3 <= 0.09}
    results['check_d4'] = {'value': check_d4, 'pass': check_d4 <= 0.09}
    
    # Check E: Standard Term > 120
    check_e1 = sfy_df[
        (sfy_df['type'] == 'standard') &
        (sfy_df['Term'] > 120)
    ]['Orig. Balance'].sum() / total_balance
    check_e2 = sfy_df[
        (sfy_df['type'].isin(['standard', 'standard_bd'])) &
        (sfy_df['Term'] > 120)
    ]['Orig. Balance'].sum() / total_balance
    check_e3 = sfy_df[
        (sfy_df['type'] == 'standard') &
        (sfy_df['Term'] > 144)
    ]['Orig. Balance'].sum() / total_balance
    check_e4 = sfy_df[
        (sfy_df['type'].isin(['standard', 'standard_bd'])) &
        (sfy_df['Term'] > 144)
    ]['Orig. Balance'].sum() / total_balance
    results['check_e1'] = {'value': check_e1, 'pass': check_e1 <= 0.3}
    results['check_e2'] = {'value': check_e2, 'pass': check_e2 <= 0.3}
    results['check_e3'] = {'value': check_e3, 'pass': check_e3 <= 0.28}
    results['check_e4'] = {'value': check_e4, 'pass': check_e4 <= 0.28}
    
    # Check F: Lender Price
    check_f1 = sfy_df['Lender Price(%)'].max()
    check_f2 = sfy_df[
        (sfy_df['Lender Price(%)'] > 100) &
        (sfy_df['Lender Price(%)'] <= 103)
    ]['Orig. Balance'].sum() / total_balance
    check_f3 = sfy_df[
        (sfy_df['Lender Price(%)'] > 100) &
        (sfy_df['Lender Price(%)'] <= 103) &
        (sfy_df['loan program'] != "Unsec Std - 999 - 120")
    ]['Orig. Balance'].sum() / total_balance
    check_f4 = (sfy_df['Dealer Fee'] * sfy_df['Orig. Balance']).sum() / total_balance
    results['check_f1'] = {'value': check_f1, 'pass': check_f1 <= 101.25}  # notebook: f1<=101.25
    results['check_f2'] = {'value': check_f2, 'pass': check_f2 <= 0.4}
    results['check_f3'] = {'value': check_f3, 'pass': check_f3 <= 0.37}
    results['check_f4'] = {'value': check_f4, 'pass': check_f4 <= 0.15}
    
    # Check G: Balance > 50000
    check_g1 = sfy_df[sfy_df['Orig. Balance'] > 50000]['Orig. Balance'].sum() / total_balance
    check_g2 = sfy_df['Orig. Balance'].mean()
    results['check_g1'] = {'value': check_g1, 'pass': check_g1 <= 0.38}
    results['check_g2'] = {'value': check_g2, 'pass': check_g2 <= 20000}
    
    # Check J: FICO
    check_j1 = sfy_df[sfy_df['FICO Borrower'] < 680]['Orig. Balance'].sum() / total_balance
    check_j2 = sfy_df[sfy_df['FICO Borrower'] < 700]['Orig. Balance'].sum() / total_balance
    check_j3 = (sfy_df['Orig. Balance'] * sfy_df['FICO Borrower']).sum() / total_balance
    check_j4 = sfy_df['FICO Borrower'].mean()
    results['check_j1'] = {'value': check_j1, 'pass': check_j1 <= 0.5}
    results['check_j2'] = {'value': check_j2, 'pass': check_j2 <= 0.7}
    results['check_j3'] = {'value': check_j3, 'pass': check_j3 >= 700}
    results['check_j4'] = {'value': check_j4, 'pass': check_j4 >= 700}
    
    # Check H: Property State distribution (from notebook - informational)
    try:
        state_distribution = pd.pivot_table(
            sfy_df,
            values='Orig. Balance',
            aggfunc='sum',
            columns='Property State'
        ) / total_balance
        results['check_h_state_dist'] = {
            'value': state_distribution.T.sort_values('Orig. Balance', ascending=False).to_dict() if not state_distribution.empty else {},
            'pass': True  # Informational only
        }
    except Exception:
        results['check_h_state_dist'] = {'value': {}, 'pass': True}
    
    # Check L: BD types
    check_l1 = sfy_df[sfy_df['type'] == 'wpdi_bd']['Orig. Balance'].sum() / total_balance
    check_l2 = sfy_df[sfy_df['type'] == 'standard_bd']['Orig. Balance'].sum() / total_balance
    check_l3 = final_df_all[
        final_df_all['type'].isin(['standard_bd', 'wpdi_bd'])
    ]['Purchase Price'].sum() / final_df_all['Purchase Price'].sum()
    check_l4 = final_df_all[
        (final_df_all['type'].isin(['standard_bd', 'wpdi_bd'])) &
        (final_df_all['Excess_Asset'] != True)
    ]['Purchase Price'].sum() / final_df_all['Purchase Price'].sum()
    results['check_l1'] = {'value': check_l1, 'pass': check_l1 <= 0.01}
    results['check_l2'] = {'value': check_l2, 'pass': True}  # Informational
    results['check_l3'] = {'value': check_l3, 'pass': True}  # Informational
    results['check_l4'] = {'value': check_l4, 'pass': True}  # Informational
    
    # Check L5: From buy_df (new loans only)
    if buy_df is not None:
        buy_sfy = buy_df[buy_df['platform'] == 'sfy']
        if len(buy_sfy) > 0:
            buy_total = buy_sfy['Orig. Balance'].sum()
            check_l5 = buy_sfy[buy_sfy['type'] == 'standard_bd']['Orig. Balance'].sum() / buy_total
            results['check_l5'] = {'value': check_l5, 'pass': True}  # Informational
    
    # Special asset check (new_programs)
    check_s1 = final_df_all[
        (final_df_all.get('new_programs', False) == True) &
        (final_df_all['Repurchase'] == False) &
        (final_df_all['platform'] == 'sfy')
    ]['Orig. Balance'].sum() / final_df_all[
        (final_df_all['Repurchase'] == False) &
        (final_df_all['platform'] == 'sfy')
    ]['Orig. Balance'].sum() if len(final_df_all[
        (final_df_all['Repurchase'] == False) &
        (final_df_all['platform'] == 'sfy')
    ]) > 0 else 0
    results['check_s1'] = {'value': check_s1, 'pass': check_s1 < 0.02}
    
    return results
