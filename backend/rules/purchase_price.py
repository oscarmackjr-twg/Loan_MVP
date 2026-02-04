"""Purchase price validation rules."""
import pandas as pd
from typing import List, Dict, Any


def check_purchase_price(df: pd.DataFrame) -> pd.DataFrame:
    """Check if purchase price matches modeled price."""
    df = df.copy()
    
    if 'Lender Price(%)' in df.columns and 'modeled_purchase_price' in df.columns:
        df['purchase_price_check'] = (
            df['Lender Price(%)'] == round(df['modeled_purchase_price'] * 100, 2)
        )
    else:
        df['purchase_price_check'] = False
    
    return df


def get_purchase_price_exceptions(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Get loans with purchase price mismatches."""
    exceptions = []
    
    if 'purchase_price_check' in df.columns:
        mismatched = df[df['purchase_price_check'] == False]
        
        for _, row in mismatched.iterrows():
            exceptions.append({
                'seller_loan_number': row.get('SELLER Loan #', 'UNKNOWN'),
                'exception_type': 'purchase_price',
                'exception_category': 'mismatch',
                'severity': 'error',
                'message': f"Purchase price mismatch: Lender Price={row.get('Lender Price(%)')}, Modeled={row.get('modeled_purchase_price', 0) * 100}",
                'loan_data': row.to_dict()
            })
    
    return exceptions
