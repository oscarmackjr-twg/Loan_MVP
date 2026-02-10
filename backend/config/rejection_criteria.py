"""
Canonical rejection criteria keys mapping to the original Jupyter Notebook.

Use these constants when setting LoanException.rejection_criteria and
LoanFact.rejection_criteria so reporting and filtering align with notebook logic.
See backend/docs/NOTEBOOK_REJECTION_MAPPING.md for full mapping.
"""
from typing import Optional

# Purchase price (notebook: purchase price / lender price vs modeled)
REJECTION_PURCHASE_PRICE_MISMATCH = "notebook.purchase_price_mismatch"

# Underwriting (notebook: underwriting grid checks)
REJECTION_UNDERWRITING_SFY = "notebook.underwriting_sfy"
REJECTION_UNDERWRITING_PRIME = "notebook.underwriting_prime"
REJECTION_UNDERWRITING_NOTES = "notebook.underwriting_notes"

# CoMAP (notebook: CoMAP grid / FICO band)
REJECTION_COMAP_PRIME = "notebook.comap_prime"
REJECTION_COMAP_SFY = "notebook.comap_sfy"
REJECTION_COMAP_NOTES = "notebook.comap_notes"

# Eligibility (notebook: portfolio eligibility checks; loan-level only when we flag)
REJECTION_ELIGIBILITY_PRIME = "notebook.eligibility_prime"
REJECTION_ELIGIBILITY_SFY = "notebook.eligibility_sfy"

# Disposition values for LoanFact
DISPOSITION_TO_PURCHASE = "to_purchase"
DISPOSITION_PROJECTED = "projected"
DISPOSITION_REJECTED = "rejected"

# Map exception_type (+ category) to canonical rejection_criteria
EXCEPTION_TYPE_TO_CRITERIA = {
    ("purchase_price", "mismatch"): REJECTION_PURCHASE_PRICE_MISMATCH,
    ("underwriting", "flagged"): REJECTION_UNDERWRITING_PRIME,
    ("underwriting_sfy", "flagged"): REJECTION_UNDERWRITING_SFY,
    ("underwriting_prime", "flagged"): REJECTION_UNDERWRITING_PRIME,
    ("underwriting_notes", "flagged"): REJECTION_UNDERWRITING_NOTES,
    ("comap", "not_in_comap"): REJECTION_COMAP_PRIME,  # default; pipeline sets per platform
    ("comap_prime", "not_in_comap"): REJECTION_COMAP_PRIME,
    ("comap_sfy", "not_in_comap"): REJECTION_COMAP_SFY,
    ("comap_notes", "not_in_comap"): REJECTION_COMAP_NOTES,
    ("eligibility", "failed"): REJECTION_ELIGIBILITY_PRIME,
    ("eligibility_prime", "failed"): REJECTION_ELIGIBILITY_PRIME,
    ("eligibility_sfy", "failed"): REJECTION_ELIGIBILITY_SFY,
}


def get_rejection_criteria(exception_type: str, exception_category: str = "") -> Optional[str]:
    """Return canonical rejection_criteria for exception_type + category."""
    key = (exception_type, exception_category)
    return EXCEPTION_TYPE_TO_CRITERIA.get(key) or EXCEPTION_TYPE_TO_CRITERIA.get(
        (exception_type, "")
    )
