// Presentation only. Backend status and the stored report remain unchanged.
export function doseLabel(status) {
  if (status === 'REVIEW_THRESHOLD_EXCEEDED') return 'Above a reviewed limit';
  if (status === 'BELOW_REVIEWED_THRESHOLD_NOT_PROOF_OF_SAFETY') return 'No reviewed limit exceeded';
  return 'Could not check';
}

export function ageLabel(status) {
  if (status === 'REVIEW_AGE_RANGE_FLAG') return 'Outside the reviewed age range';
  if (status === 'WITHIN_REVIEWED_AGE_RANGE_NOT_PROOF_OF_SAFETY') return 'Within the reviewed age range';
  return 'Could not check';
}

export function comparisonLabel(code) {
  return ({
    EXCEEDS_REVIEWED_SINGLE_DOSE_THRESHOLD: 'Single dose is above the reviewed limit',
    EXCEEDS_REVIEWED_DAILY_DOSE_THRESHOLD: 'Daily total is above the reviewed limit',
    EXCEEDS_REVIEWED_WEIGHT_BASED_THRESHOLD: 'Weight-based amount is above the reviewed limit',
    BELOW_REVIEWED_THRESHOLD_NOT_PROOF_OF_SAFETY: 'No reviewed limit was exceeded',
  })[code] || 'Needs review';
}
