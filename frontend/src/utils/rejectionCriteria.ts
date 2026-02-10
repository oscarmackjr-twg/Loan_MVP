/**
 * Human-readable labels for rejection criteria keys (maps to notebook logic).
 * Used in Exceptions, Run Detail, and Rejected Loans views.
 */
const REJECTION_CRITERIA_LABELS: Record<string, string> = {
  'notebook.purchase_price_mismatch': 'Purchase price mismatch',
  'notebook.underwriting_sfy': 'Underwriting (SFY)',
  'notebook.underwriting_prime': 'Underwriting (Prime)',
  'notebook.underwriting_notes': 'Underwriting (Notes)',
  'notebook.comap_prime': 'CoMAP (Prime)',
  'notebook.comap_sfy': 'CoMAP (SFY)',
  'notebook.comap_notes': 'CoMAP (Notes)',
  'notebook.eligibility_prime': 'Eligibility (Prime)',
  'notebook.eligibility_sfy': 'Eligibility (SFY)',
}

export function getRejectionCriteriaLabel(key: string | null | undefined): string {
  if (key == null || key === '') return '—'
  return REJECTION_CRITERIA_LABELS[key] ?? key
}

export const REJECTION_CRITERIA_OPTIONS = Object.entries(REJECTION_CRITERIA_LABELS).map(
  ([value, label]) => ({ value, label })
)
