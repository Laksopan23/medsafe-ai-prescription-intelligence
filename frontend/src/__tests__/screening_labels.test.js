import {describe,expect,it} from 'vitest';
import {ageLabel,comparisonLabel,doseLabel} from '../lib/screeningLabels.js';

describe('plain-language findings',()=>{
  it('does not present an unresolved result as safe',()=>{
    expect(doseLabel('NOT_EVALUATED')).toBe('Could not check');
    expect(ageLabel('UNABLE_TO_VALIDATE')).toBe('Could not check');
  });
  it('keeps a threshold warning distinct from a within-range finding',()=>{
    expect(doseLabel('REVIEW_THRESHOLD_EXCEEDED')).toBe('Above a reviewed limit');
    expect(ageLabel('REVIEW_AGE_RANGE_FLAG')).toBe('Outside the reviewed age range');
    expect(comparisonLabel('EXCEEDS_REVIEWED_DAILY_DOSE_THRESHOLD')).toMatch(/daily total is above/i);
  });
});
