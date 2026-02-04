"""Data normalization and cleaning."""
import pandas as pd
from typing import Dict, Any


def normalize_loans_df(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize loan dataframe - clean and standardize columns."""
    df = df.copy()
    
    # Standardize column names
    column_mapping = {
        'Account Number': 'Account Number',
        'Loan Group': 'Loan Group',
        'Status Codes': 'Status Codes',
        'Open Date': 'Open Date',
        'maturityDate': 'maturityDate',
    }
    
    # Ensure required columns exist
    required_cols = ['Account Number', 'Loan Group', 'Status Codes']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Convert dates
    date_cols = ['Open Date', 'maturityDate', 'Submit Date', 'Purchase_Date', 'Monthly Payment Date']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Fill missing status codes
    if 'Status Codes' in df.columns:
        df['Status Codes'].fillna("", inplace=True)
    
    return df


def normalize_sfy_df(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize SFY dataframe from Excel."""
    df = df.copy()
    
    # Skip header rows (typically row 4)
    if len(df) > 4:
        df = df.iloc[4:].reset_index(drop=True)
        df.columns = df.iloc[0]
        df = df[1:].reset_index(drop=True)
    
    # Ensure all column names are strings (handle NaN/numeric column names)
    df.columns = [str(col) if pd.notna(col) else f'Unnamed_{i}' for i, col in enumerate(df.columns)]
    
    # Standardize TU144 column name
    # Convert column names to strings and filter out NaN/None
    tu_cols = [
        col for col in df.columns 
        if isinstance(col, str) and 'tu' in col.lower() and '144' in col.lower()
    ]
    if tu_cols:
        df.rename(columns={tu_cols[0]: 'TU144'}, inplace=True)
    
    return df


def normalize_prime_df(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize Prime dataframe from Excel."""
    df = df.copy()
    
    # Skip header rows (typically row 4)
    if len(df) > 4:
        df = df.iloc[4:].reset_index(drop=True)
        df.columns = df.iloc[0]
        df = df[1:].reset_index(drop=True)
    
    # Ensure all column names are strings (handle NaN/numeric column names)
    df.columns = [str(col) if pd.notna(col) else f'Unnamed_{i}' for i, col in enumerate(df.columns)]
    
    return df
