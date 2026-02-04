"""Eligibility check reporting and export."""
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
import json


def format_eligibility_results(
    eligibility_prime: Dict[str, Any],
    eligibility_sfy: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Format eligibility check results for display/export.
    
    Args:
        eligibility_prime: Prime eligibility check results
        eligibility_sfy: SFY eligibility check results
    
    Returns:
        Formatted results dictionary
    """
    formatted = {
        'prime': {
            'checks': {},
            'summary': {
                'total_checks': 0,
                'passed': 0,
                'failed': 0,
                'informational': 0
            }
        },
        'sfy': {
            'checks': {},
            'summary': {
                'total_checks': 0,
                'passed': 0,
                'failed': 0,
                'informational': 0
            }
        }
    }
    
    # Format Prime checks
    for check_name, check_result in eligibility_prime.items():
        if isinstance(check_result, dict) and 'value' in check_result:
            formatted['prime']['checks'][check_name] = {
                'value': check_result['value'],
                'pass': check_result.get('pass', False),
                'threshold': _get_threshold(check_name, 'prime')
            }
            formatted['prime']['summary']['total_checks'] += 1
            if check_result.get('pass', False):
                formatted['prime']['summary']['passed'] += 1
            elif check_result.get('pass') is True:  # Informational (explicitly True)
                formatted['prime']['summary']['informational'] += 1
            else:
                formatted['prime']['summary']['failed'] += 1
    
    # Format SFY checks
    for check_name, check_result in eligibility_sfy.items():
        if isinstance(check_result, dict) and 'value' in check_result:
            formatted['sfy']['checks'][check_name] = {
                'value': check_result['value'],
                'pass': check_result.get('pass', False),
                'threshold': _get_threshold(check_name, 'sfy')
            }
            formatted['sfy']['summary']['total_checks'] += 1
            if check_result.get('pass', False):
                formatted['sfy']['summary']['passed'] += 1
            elif check_result.get('pass') is True:  # Informational
                formatted['sfy']['summary']['informational'] += 1
            else:
                formatted['sfy']['summary']['failed'] += 1
    
    return formatted


def _get_threshold(check_name: str, platform: str) -> Optional[str]:
    """Get threshold description for a check."""
    thresholds = {
        'prime': {
            'check_a': '< 5%',
            'check_b1': '< 3%',
            'check_b3': '< 3%',
            'check_c': '< 35%',
            'check_d': '< 35%',
            'check_e': '< 15%',
            'check_f': '< 18%',
            'check_g': '< 15%',
            'check_h1': '< 101.87',
            'check_h2': '< 35%',
            'check_h3': '< 15%',
            'check_i1': '< 38%',
            'check_i2': '< $20,000',
            'check_l1': '< 50%',
            'check_l2': '< 70%',
            'check_l3': '> 700',
            'check_s1': '< 2%',
        },
        'sfy': {
            'check_a1': '< 85%',
            'check_a2': '< 25%',
            'check_b1': '< 30%',
            'check_b2': '< 27%',
            'check_b3': '< 15%',
            'check_b4': '<= 0%',
            'check_c1': '<= 25%',
            'check_d1': '<= 17%',
            'check_d2': '<= 17%',
            'check_d3': '<= 9%',
            'check_d4': '<= 9%',
            'check_e1': '<= 30%',
            'check_e2': '<= 30%',
            'check_e3': '<= 28%',
            'check_e4': '<= 28%',
            'check_f1': '<= 101.21',
            'check_f2': '<= 40%',
            'check_f3': '<= 37%',
            'check_f4': '<= 15%',
            'check_g1': '<= 38%',
            'check_g2': '<= $20,000',
            'check_j1': '<= 50%',
            'check_j2': '<= 70%',
            'check_j3': '>= 700',
            'check_j4': '>= 700',
            'check_l1': '<= 1%',
            'check_s1': '< 2%',
        }
    }
    return thresholds.get(platform, {}).get(check_name, None)


def export_eligibility_report(
    eligibility_prime: Dict[str, Any],
    eligibility_sfy: Dict[str, Any],
    output_dir: str
) -> str:
    """
    Export eligibility check results to JSON file.
    
    Args:
        eligibility_prime: Prime eligibility check results
        eligibility_sfy: SFY eligibility check results
        output_dir: Output directory path
    
    Returns:
        Path to exported file
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Format results
    formatted = format_eligibility_results(eligibility_prime, eligibility_sfy)
    
    # Export to JSON
    file_path = f"{output_dir}/eligibility_checks.json"
    with open(file_path, 'w') as f:
        json.dump(formatted, f, indent=2, default=str)
    
    # Also create Excel summary
    excel_path = f"{output_dir}/eligibility_checks_summary.xlsx"
    _export_eligibility_excel(formatted, excel_path)
    
    return file_path


def _export_eligibility_excel(formatted: Dict[str, Any], file_path: str):
    """Export eligibility checks to Excel format."""
    rows = []
    
    # Prime checks
    for check_name, check_data in formatted['prime']['checks'].items():
        rows.append({
            'Platform': 'Prime',
            'Check': check_name,
            'Value': check_data['value'],
            'Threshold': check_data.get('threshold', 'N/A'),
            'Status': 'PASS' if check_data['pass'] else 'FAIL' if check_data['pass'] is False else 'INFO'
        })
    
    # SFY checks
    for check_name, check_data in formatted['sfy']['checks'].items():
        rows.append({
            'Platform': 'SFY',
            'Check': check_name,
            'Value': check_data['value'],
            'Threshold': check_data.get('threshold', 'N/A'),
            'Status': 'PASS' if check_data['pass'] else 'FAIL' if check_data['pass'] is False else 'INFO'
        })
    
    if rows:
        df = pd.DataFrame(rows)
        df.to_excel(file_path, index=False, sheet_name='Eligibility Checks')
