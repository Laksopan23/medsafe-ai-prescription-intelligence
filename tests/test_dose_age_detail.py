"""Fictional rule checks; these are software tests, not clinical validation."""
import json
from datetime import date, datetime, timedelta, timezone

import pytest

from medsafe.rule_registry import RuleRegistryError, assess_reviewed_rule, load_reviewed_rules, match_rule


def rule():
    today = date.today()
    return {
        'schema_version': 3, 'ingredient': 'FICTIONAL-MED',
        'product_identifier': 'TEST-1', 'formulation': 'tablet', 'strength': '10 mg',
        'route': 'oral', 'indication': 'fictional condition', 'population': 'test adults',
        'dose_unit': 'mg', 'max_single': 10, 'max_daily': 20,
        'min_age_years': 18, 'max_age_years': 75,
        'source_url': 'https://example.org/fictional', 'source_type': 'TEST_ONLY',
        'source_section': 'fictional dose table', 'source_label_id': 'TEST-LABEL',
        'source_revision': '20260101',
        'source_retrieved_utc': datetime.now(timezone.utc).isoformat(),
        'reviewer': 'Fictional Reviewer One', 'reviewer_credentials': 'TEST_ONLY',
        'reviewer_institution': 'Fictional test institution', 'review_date': today.isoformat(),
        'second_reviewer': 'Fictional Reviewer Two',
        'second_reviewer_credentials': 'TEST_ONLY', 'second_review_date': today.isoformat(),
        'approval_record_id': 'TEST-NOT-CLINICAL-APPROVAL',
        'approval_date': today.isoformat(), 'expires_on': (today + timedelta(days=30)).isoformat(),
        'exclusions': 'PRN and unclear product identity', 'version': '3',
        'review_status': 'APPROVED_BY_QUALIFIED_REVIEWER',
    }


def test_v3_import_and_exact_formulation(tmp_path):
    path = tmp_path / 'rules.json'
    path.write_text(json.dumps([rule()]), encoding='utf-8')
    loaded = load_reviewed_rules(path)
    context = dict(ingredient='FICTIONAL-MED', product_identifier='TEST-1',
                   route='oral', indication='fictional condition', population='test adults')
    assert match_rule(loaded, **context, formulation='tablet', strength='10 mg')
    assert match_rule(loaded, **context, formulation='syrup', strength='10 mg') is None
    assert match_rule(loaded, **context, formulation='tablet', strength='20 mg') is None
    assert match_rule(loaded, **context) is None


@pytest.mark.parametrize('field,value', [
    ('formulation', ''), ('approval_date', '2099-01-01'),
    ('exclusions', ''), ('source_type', ''),
])
def test_v3_rejects_missing_governance(tmp_path, field, value):
    item = rule()
    item[field] = value
    path = tmp_path / 'rules.json'
    path.write_text(json.dumps([item]), encoding='utf-8')
    with pytest.raises(RuleRegistryError):
        load_reviewed_rules(path)


def test_decimal_threshold_detail_and_no_clearance():
    item = rule()
    result = assess_reviewed_rule(item, dose=10.1, unit='mg', frequency=2)
    assert result['status'] == 'REVIEW_THRESHOLD_EXCEEDED'
    assert result['comparison_outcomes'] == [
        'EXCEEDS_REVIEWED_SINGLE_DOSE_THRESHOLD',
        'EXCEEDS_REVIEWED_DAILY_DOSE_THRESHOLD',
    ]
    assert result['administered_daily'] == 20.2
    assert result['clinical_clearance'] is False
    assert result['source_label_id'] == 'TEST-LABEL'
    assert assess_reviewed_rule(item, dose=10, unit='mg', frequency=2)['status'] == 'BELOW_REVIEWED_THRESHOLD_NOT_PROOF_OF_SAFETY'
    assert assess_reviewed_rule(item, dose=10, unit='mg', frequency=None)['status'] == 'NOT_EVALUATED'


def test_weight_flag_requires_weight_threshold_itself_to_be_exceeded():
    item = {**rule(), 'max_single_mg_per_kg': 2, 'max_daily_mg_per_kg': 4}
    # At 10 kg, the absolute 10 mg ceiling is lower than the 20 mg weight ceiling.
    absolute_only = assess_reviewed_rule(item, dose=11, unit='mg', frequency=1, weight_kg=10)
    assert absolute_only['status'] == 'REVIEW_THRESHOLD_EXCEEDED'
    assert 'EXCEEDS_REVIEWED_WEIGHT_BASED_THRESHOLD' not in absolute_only['comparison_outcomes']
    weight_exceeded = assess_reviewed_rule(item, dose=22, unit='mg', frequency=1, weight_kg=10)
    assert 'EXCEEDS_REVIEWED_WEIGHT_BASED_THRESHOLD' in weight_exceeded['comparison_outcomes']


def test_duplicate_medication_blocks_abstain_even_with_matching_rule(tmp_path, monkeypatch):
    from backend.app.services.review_service import assess_report
    from medsafe.pipeline import analyze_text

    path = tmp_path / 'rules.json'
    path.write_text(json.dumps([rule()]), encoding='utf-8')
    monkeypatch.setenv('MEDSAFE_REVIEWED_RULES', str(path))
    context = ('Medicine: FICTIONAL-MED\nProduct identifier: TEST-1\n'
               'Formulation: tablet\nStrength: 10 mg\nRoute: oral\n'
               'Indication: fictional condition\nPopulation: test adults\n'
               'Dose: 11 mg\nFrequency: twice daily\n')
    transcript = 'Age: 30 years\n' + context + context
    report = assess_report(analyze_text(transcript))
    assert any(issue['code']=='DUPLICATE_MEDICATION_REGIMEN' for issue in report['issues'])
    assert all(m['reviewed_dose_rule']['status']=='NOT_EVALUATED' for m in report['medications'])
    assert all(m['reviewed_age_rule']['status']=='UNABLE_TO_VALIDATE' for m in report['medications'])
