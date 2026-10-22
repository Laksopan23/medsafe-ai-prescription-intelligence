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
