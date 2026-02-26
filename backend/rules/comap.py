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
    prime_comap_new: pd.DataFrame,
) -> List[Tuple[str, str, str]]:
    """Check Prime loans against CoMAP. Uses each loan's Submit Date for date-based grid (mirrors February_Baseline)."""
    loan_not_in_comap = []
    oct25_cutoff = pd.to_datetime('2025-10-24')
    prime_new_cutoff = pd.to_datetime('2020-06-11')

    check_df = buy_df[
        (buy_df['Application Type'] != 'HD NOTE') &
        (buy_df['purchase_price_check'] == True) &
        (buy_df['platform'] == 'prime')
    ].copy()
    if 'Submit Date' in check_df.columns:
        check_df['Submit Date'] = pd.to_datetime(check_df['Submit Date'])
    else:
        check_df['Submit Date'] = pd.NaT

    for _, row in check_df.iterrows():
        fico = row['FICO Borrower']
        prog = row['loan program']
        prog = str(prog) if pd.notna(prog) else ''
        submit_dt = row['Submit Date']
        found = False

        if pd.notna(submit_dt) and submit_dt > oct25_cutoff:
            oct25_cols = ['660-699', '700-739', '740-749', '750+']
            available_oct25_cols = [c for c in oct25_cols if c in prime_comap_oct25.columns]
            if available_oct25_cols and prog in prime_comap_oct25[available_oct25_cols].stack().unique():
                for col in available_oct25_cols:
                    if prog in prime_comap_oct25[col].values and fico >= PRIME_COMAP_COLS_MIN_FICO2[col]:
                        found = True
                        break
            if not found:
                oct25_2_cols = ['660-699', '700-739', '740-749', '750-769', '770+']
                available_oct25_2_cols = [c for c in oct25_2_cols if c in prime_comap_oct25_2.columns]
                if available_oct25_2_cols and prog in prime_comap_oct25_2[available_oct25_2_cols].stack().unique():
                    for col in available_oct25_2_cols:
                        if prog in prime_comap_oct25_2[col].values and fico >= PRIME_COMAP_COLS_MIN_FICO[col]:
                            found = True
                            break
        elif pd.notna(submit_dt) and submit_dt > prime_new_cutoff:
            prime_cols = ['660-699', '700-739', '740-749', '750-769', '770+']
            available_prime_cols = [c for c in prime_cols if c in prime_comap_new.columns]
            for col in available_prime_cols:
                if prog in prime_comap_new[col].values and fico >= PRIME_COMAP_COLS_MIN_FICO[col]:
                    found = True
                    break
        else:
            prime_cols = ['660-699', '700-739', '740-749', '750-769', '770+']
            available_prime_cols = [c for c in prime_cols if c in prime_comap.columns]
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
) -> List[Tuple[str, str, str]]:
    """Check SFY loans against CoMAP. Uses each loan's Submit Date for date-based grid (mirrors February_Baseline)."""
    loan_not_in_comap = []
    oct25_cutoff = pd.to_datetime('2025-10-24')

    check_df = buy_df[
        (buy_df['Application Type'] != 'HD NOTE') &
        (buy_df['purchase_price_check'] == True) &
        (buy_df['platform'] == 'sfy')
    ].copy()
    if 'Submit Date' in check_df.columns:
        check_df['Submit Date'] = pd.to_datetime(check_df['Submit Date'])
    else:
        check_df['Submit Date'] = pd.NaT

    for _, row in check_df.iterrows():
        fico = row['FICO Borrower']
        prog = row['loan program']
        prog = str(prog) if pd.notna(prog) else ''
        submit_dt = row['Submit Date']
        found = False

        if pd.notna(submit_dt) and submit_dt > oct25_cutoff:
            oct25_cols = ['660-719', '720-779', '780+']
            available_oct25_cols = [c for c in oct25_cols if c in sfy_comap_oct25.columns]
            if available_oct25_cols and prog in sfy_comap_oct25[available_oct25_cols].stack().unique():
                for col in available_oct25_cols:
                    if prog in sfy_comap_oct25[col].values and fico >= SFY_COMAP_COLS_MIN_FICO3[col]:
                        found = True
                        break
            if not found:
                oct25_2_cols = ['660-699', '700-739', '740-749', '750-769', '770+']
                available_oct25_2_cols = [c for c in oct25_2_cols if c in sfy_comap_oct25_2.columns]
                if available_oct25_2_cols and prog in sfy_comap_oct25_2[available_oct25_2_cols].stack().unique():
                    for col in available_oct25_2_cols:
                        if prog in sfy_comap_oct25_2[col].values and fico >= SFY_COMAP_COLS_MIN_FICO2[col]:
                            found = True
                            break
        else:
            sfy_cols = ['660-719', '720-779', '780-799', '800+']
            available_sfy_cols = [c for c in sfy_cols if c in sfy_comap.columns]
            if available_sfy_cols and prog in sfy_comap[available_sfy_cols].stack().unique():
                for col in available_sfy_cols:
                    if prog in sfy_comap[col].values and fico >= SFY_COMAP_COLS_MIN_FICO[col]:
                        found = True
                        break
            if not found:
                sfy2_cols = ['660-699', '700-739', '740-749', '750-769', '770+']
                available_sfy2_cols = [c for c in sfy2_cols if c in sfy_comap2.columns]
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
