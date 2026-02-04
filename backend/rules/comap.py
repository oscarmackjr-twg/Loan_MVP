"""CoMAP validation rules."""
import pandas as pd
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


# FICO band mappings
PRIME_COMAP_COLS_MIN_FICO = {
    '660-699': 660,
    '700-739': 700,
    '740-749': 740,
    '750-769': 750,
    '770+': 770
}

PRIME_COMAP_COLS_MIN_FICO2 = {
    '660-699': 660,
    '700-739': 700,
    '740-749': 740,
    '750+': 750
}

SFY_COMAP_COLS_MIN_FICO = {
    '660-719': 660,
    '720-779': 720,
    '780-799': 780,
    '800+': 800
}

SFY_COMAP_COLS_MIN_FICO2 = {
    '660-699': 660,
    '700-739': 700,
    '740-749': 740,
    '750-769': 750,
    '770+': 770
}

SFY_COMAP_COLS_MIN_FICO3 = {
    '660-719': 660,
    '720-779': 720,
    '780+': 780
}

NOTES_COMAP_COLS_MIN_FICO = {
    '680-749': 680,
    '750-769': 750,
    '770-789': 770,
    '790+': 790
}


def check_comap_prime(
    buy_df: pd.DataFrame,
    prime_comap: pd.DataFrame,
    prime_comap_oct25: pd.DataFrame,
    prime_comap_oct25_2: pd.DataFrame,
    submit_date: pd.Timestamp
) -> List[Tuple[str, str, str]]:
    """Check Prime loans against CoMAP."""
    loan_not_in_comap = []
    
    check_df = buy_df[
        (buy_df['Application Type'] != 'HD NOTE') &
        (buy_df['purchase_price_check'] == True) &
        (buy_df['platform'] == 'prime')
    ].copy()
    
    for _, row in check_df.iterrows():
        fico = row['FICO Borrower']
        prog = row['loan program']
        # Convert to string in case it's numeric (numpy.float64, etc.)
        prog = str(prog) if pd.notna(prog) else ''
        found = False
        
        # Check date-based CoMAP tables
        if submit_date > pd.to_datetime('2025-10-24'):
            # Check oct25 tables - verify columns exist first
            oct25_cols = ['660-699', '700-739', '740-749', '750+']
            available_oct25_cols = [col for col in oct25_cols if col in prime_comap_oct25.columns]
            if available_oct25_cols and prog in prime_comap_oct25[available_oct25_cols].stack().unique():
                for col in available_oct25_cols:
                    if prog in prime_comap_oct25[col].values and fico >= PRIME_COMAP_COLS_MIN_FICO2[col]:
                        found = True
                        break
            else:
                oct25_2_cols = ['660-699', '700-739', '740-749', '750-769', '770+']
                available_oct25_2_cols = [col for col in oct25_2_cols if col in prime_comap_oct25_2.columns]
                if available_oct25_2_cols and prog in prime_comap_oct25_2[available_oct25_2_cols].stack().unique():
                    for col in available_oct25_2_cols:
                        if prog in prime_comap_oct25_2[col].values and fico >= PRIME_COMAP_COLS_MIN_FICO[col]:
                            found = True
                            break
        else:
            # Check original tables - verify columns exist first
            prime_cols = ['660-699', '700-739', '740-749', '750-769', '770+']
            available_prime_cols = [col for col in prime_cols if col in prime_comap.columns]
            for col in available_prime_cols:
                if prog in prime_comap[col].values and fico >= PRIME_COMAP_COLS_MIN_FICO[col]:
                    found = True
                    break
        
        if not found:
            loan_not_in_comap.append((row['SELLER Loan #'], prog, 'PRIME'))
    
    return loan_not_in_comap


def check_comap_sfy(
    buy_df: pd.DataFrame,
    sfy_comap: pd.DataFrame,
    sfy_comap2: pd.DataFrame,
    sfy_comap_oct25: pd.DataFrame,
    sfy_comap_oct25_2: pd.DataFrame,
    submit_date: pd.Timestamp
) -> List[Tuple[str, str, str]]:
    """Check SFY loans against CoMAP."""
    loan_not_in_comap = []
    
    check_df = buy_df[
        (buy_df['Application Type'] != 'HD NOTE') &
        (buy_df['purchase_price_check'] == True) &
        (buy_df['platform'] == 'sfy')
    ].copy()
    
    for _, row in check_df.iterrows():
        fico = row['FICO Borrower']
        prog = row['loan program']
        # Convert to string in case it's numeric (numpy.float64, etc.)
        prog = str(prog) if pd.notna(prog) else ''
        found = False
        
        if submit_date > pd.to_datetime('2025-10-24'):
            # Check oct25 tables - verify columns exist first
            oct25_cols = ['660-719', '720-779', '780+']
            available_oct25_cols = [col for col in oct25_cols if col in sfy_comap_oct25.columns]
            missing_cols = [col for col in oct25_cols if col not in sfy_comap_oct25.columns]
            if missing_cols:
                logger.warning(f"SFY CoMAP oct25 missing columns: {missing_cols}. Available: {list(sfy_comap_oct25.columns)}")
            if available_oct25_cols and prog in sfy_comap_oct25[available_oct25_cols].stack().unique():
                for col in available_oct25_cols:
                    if prog in sfy_comap_oct25[col].values and fico >= SFY_COMAP_COLS_MIN_FICO3[col]:
                        found = True
                        break
            else:
                oct25_2_cols = ['660-699', '700-739', '740-749', '750-769', '770+']
                available_oct25_2_cols = [col for col in oct25_2_cols if col in sfy_comap_oct25_2.columns]
                if available_oct25_2_cols and prog in sfy_comap_oct25_2[available_oct25_2_cols].stack().unique():
                    for col in available_oct25_2_cols:
                        if prog in sfy_comap_oct25_2[col].values and fico >= SFY_COMAP_COLS_MIN_FICO2[col]:
                            found = True
                            break
        else:
            # Check original tables - verify columns exist first
            sfy_cols = ['660-719', '720-779', '780-799', '800+']
            available_sfy_cols = [col for col in sfy_cols if col in sfy_comap.columns]
            if available_sfy_cols and prog in sfy_comap[available_sfy_cols].stack().unique():
                for col in available_sfy_cols:
                    if prog in sfy_comap[col].values and fico >= SFY_COMAP_COLS_MIN_FICO[col]:
                        found = True
                        break
            else:
                sfy2_cols = ['660-699', '700-739', '740-749', '750-769', '770+']
                available_sfy2_cols = [col for col in sfy2_cols if col in sfy_comap2.columns]
                if available_sfy2_cols and prog in sfy_comap2[available_sfy2_cols].stack().unique():
                    for col in available_sfy2_cols:
                        if prog in sfy_comap2[col].values and fico >= SFY_COMAP_COLS_MIN_FICO2[col]:
                            found = True
                            break
        
        if not found:
            loan_not_in_comap.append((row['SELLER Loan #'], prog, 'SFY'))
    
    return loan_not_in_comap


def check_comap_notes(
    buy_df: pd.DataFrame,
    notes_comap: pd.DataFrame
) -> List[Tuple[str, str, str]]:
    """Check Notes loans against CoMAP."""
    loan_not_in_comap = []
    
    check_df = buy_df[
        (buy_df['Application Type'] == 'HD NOTE') &
        (buy_df['purchase_price_check'] == True)
    ].copy()
    
    for _, row in check_df.iterrows():
        fico = row['FICO Borrower']
        prog = row['loan program']
        # Convert to string in case it's numeric (numpy.float64, etc.)
        prog = str(prog) if pd.notna(prog) else ''
        found = False
        
        # Verify columns exist first
        notes_cols = ['680-749', '750-769', '770-789', '790+']
        available_notes_cols = [col for col in notes_cols if col in notes_comap.columns]
        if not available_notes_cols:
            continue
        
        if prog not in notes_comap[available_notes_cols].stack().unique():
            continue
        
        for col in available_notes_cols:
            if prog in notes_comap[col].values and fico >= NOTES_COMAP_COLS_MIN_FICO[col]:
                found = True
                break
        
        if not found:
            loan_not_in_comap.append((row['SELLER Loan #'], prog, 'NOTES'))
    
    return loan_not_in_comap
