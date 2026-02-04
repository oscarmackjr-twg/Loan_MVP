"""Loan data enrichment and tagging."""
import pandas as pd
from typing import Optional


def tag_loans_by_group(loans_df: pd.DataFrame) -> pd.DataFrame:
    """Tag loans as SFY or PRIME based on Loan Group."""
    df = loans_df.copy()
    df['tagging'] = df['Loan Group'].apply(
        lambda x: 'SFY' if 'FX3' in str(x) or 'FX1' in str(x) else 'PRIME'
    )
    return df


def add_seller_loan_number(loans_df: pd.DataFrame) -> pd.DataFrame:
    """Add SELLER Loan # column."""
    df = loans_df.copy()
    if 'Account Number' in df.columns:
        df['Account Number'] = df['Account Number'].astype(int)
        df['SELLER Loan #'] = df['Account Number'].apply(lambda x: f"SFC_{x}")
    return df


def mark_repurchased_loans(loans_df: pd.DataFrame) -> pd.DataFrame:
    """Mark repurchased loans based on Status Codes."""
    df = loans_df.copy()
    if 'Status Codes' in df.columns:
        df['Status Codes'].fillna("", inplace=True)
        df['Repurchased'] = df['Status Codes'].apply(
            lambda x: True if 'REPURCHASE' in [i.strip() for i in str(x).split(";")] else False
        )
    else:
        df['Repurchased'] = False
    return df


def enrich_buy_df(
    buy_df: pd.DataFrame,
    df_loans_types: pd.DataFrame,
    pdate: str,
    irr_target: float
) -> pd.DataFrame:
    """Enrich buy dataframe with loan types and metadata."""
    df = buy_df.copy()
    
    # Add platform
    if 'Platform' not in df.columns:
        if 'tagging' in df.columns:
            df['Platform'] = df['tagging']
        else:
            df['Platform'] = 'UNKNOWN'
    
    # Merge with loan types
    if 'loan program' in df.columns and 'Platform' in df.columns:
        df = df.merge(
            df_loans_types,
            on=['loan program', 'Platform'],
            how='left'
        )
    
    # Add metadata
    df['Repurchase'] = False
    df['Repurchase_Date'] = None
    df['Purchase_Date'] = pd.to_datetime(pdate)
    df['Excess_Asset'] = False
    df['Borrowing_Base_eligible'] = True
    df['IRR Support Target'] = irr_target
    
    # Convert dealer fee to decimal
    if 'Dealer Fee' in df.columns:
        df['Dealer Fee'] = df['Dealer Fee'] / 100
    
    return df
