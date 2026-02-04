"""Underwriting validation rules."""
import pandas as pd
from typing import List, Dict, Any, Optional


def check_underwriting(
    buy_df: pd.DataFrame,
    underwriting_df: pd.DataFrame,
    is_notes: bool = False,
    tuloans: Optional[List[str]] = None
) -> List[str]:
    """Check loans against underwriting criteria."""
    flagged_loans = []
    min_income_loans = []
    
    if tuloans is None:
        tuloans = []
    
    # Filter out TU loans and HD NOTES if checking regular loans
    check_df = buy_df[
        (buy_df['Application Type'] != 'HD NOTE') if not is_notes 
        else (buy_df['Application Type'] == 'HD NOTE')
    ].copy()
    
    if is_notes:
        check_df = check_df[~check_df['SELLER Loan #'].isin(tuloans)]
    
    for _, row in check_df.iterrows():
        if row['SELLER Loan #'] in tuloans:
            continue
        
        prog = row['loan program']
        # Convert to string in case it's numeric (numpy.float64, etc.)
        prog = str(prog) if pd.notna(prog) else ''
        if is_notes:
            prog = prog.replace('notes', '')
        
        mth_income = row['Income'] / 12 if 'Income' in row else 0
        fico = row['FICO Borrower'] if 'FICO Borrower' in row else 0
        dti = row['DTI'] * 100 if 'DTI' in row else 0
        pti = row['PTI'] if 'PTI' in row else 0
        balance = row['Orig. Balance'] - row.get('Stamp fee', 0)
        
        # Filter underwriting rules
        filter_one = underwriting_df[
            (underwriting_df['finance_type_name_nls'] == prog) &
            (underwriting_df['monthly_income_min'] <= mth_income) &
            (underwriting_df['fico_min'] <= fico)
        ].sort_values('approval_high').reset_index(drop=True)
        
        meet_crit = False
        
        # Check if loan meets criteria
        for _, rule in filter_one.iterrows():
            if balance <= rule['approval_high'] and dti <= rule['dti_max']:
                meet_crit = True
                break
        
        # If not met and FICO > 700, try without income requirement
        if not meet_crit and fico > 700:
            filter_one = underwriting_df[
                (underwriting_df['finance_type_name_nls'] == prog) &
                (underwriting_df['fico_min'] <= fico)
            ].sort_values('approval_high').reset_index(drop=True)
            
            for _, rule in filter_one.iterrows():
                if balance <= rule['approval_high'] and dti <= rule['dti_max'] and pti <= rule.get('pti_ratio', 999):
                    meet_crit = True
                    min_income_loans.append(row['SELLER Loan #'])
                    break
        
        if not meet_crit:
            flagged_loans.append(row['SELLER Loan #'])
    
    return flagged_loans, min_income_loans


def get_underwriting_exceptions(
    buy_df: pd.DataFrame,
    flagged_loans: List[str],
    exception_type: str = 'underwriting'
) -> List[Dict[str, Any]]:
    """Get underwriting exception records."""
    exceptions = []
    
    flagged_df = buy_df[buy_df['SELLER Loan #'].isin(flagged_loans)]
    
    for _, row in flagged_df.iterrows():
        exceptions.append({
            'seller_loan_number': row.get('SELLER Loan #', 'UNKNOWN'),
            'exception_type': exception_type,
            'exception_category': 'flagged',
            'severity': 'error',
            'message': f"Loan failed underwriting criteria",
            'loan_data': row.to_dict()
        })
    
    return exceptions
