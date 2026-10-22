"""Exact evidence lookup and fail-closed offline rule lifecycle contracts."""
import json
from datetime import date, datetime, timedelta, timezone

import pytest

from medsafe.references import label_details
from medsafe.rule_registry import (RuleRegistryError, assess_reviewed_rule,
                                   load_reviewed_rules, match_rule)
from medsafe.rule_workflow import (draft_from_label, inspect_offline_registry,
                                   transition_nonapproval)


class Response:
    status_code = 200

    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


class LabelSession:
    def get(self, url, **kwargs):
        return Response({'results': [{
            'set_id': 'aabbccdd-1234', 'id': 'label-version-1',
            'effective_time': '20260101', 'version': '4',
            'dosage_and_administration': ['Fictional label evidence only.'],
            'pediatric_use': ['Age context requires review.'],
        }]})


def rule():
    return {
        'schema_version': 2, 'ingredient': 'SYNTHMED',
        'product_identifier': 'SYNTH-001', 'route': 'oral',
        'indication': 'fictional simulation', 'population': 'synthetic test',
        'dose_unit': 'mg', 'max_single': 100, 'max_daily': 200,
        'source_url': 'https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=aabbccdd-1234',
        'source_section': 'dosage and administration',
        'source_label_id': 'label-version-1', 'source_revision': '20260101',
        'source_retrieved_utc': datetime.now(timezone.utc).isoformat(),
        'reviewer': 'First Reviewer', 'reviewer_credentials': 'test-only',
        'reviewer_institution': 'fictional institution',
        'review_date': date.today().isoformat(),
        'second_reviewer': 'Second Reviewer',
        'second_reviewer_credentials': 'test-only',
        'second_review_date': date.today().isoformat(),
        'approval_record_id': 'FICTIONAL-TEST-APPROVAL',
        'expires_on': (date.today() + timedelta(days=30)).isoformat(),
        'version': '2', 'review_status': 'APPROVED_BY_QUALIFIED_REVIEWER',
        'concentration_mg_per_ml': 10,
        'concentration_product_identifier': 'SYNTH-001',
        'concentration_source_section': 'description',
    }


def test_exact_label_details_are_evidence_not_approval():
    evidence = label_details('aabbccdd-1234', session=LabelSession())
    assert evidence['status'] == 'UNVERIFIED_LABEL_EVIDENCE'
    assert evidence['label_id'] == 'label-version-1'
    assert evidence['sections']['pediatric_use'].startswith('Age context')
    assert 'max_single' not in evidence
    assert label_details('../private', session=LabelSession())['status'] == 'INVALID_SETID'


def test_public_label_route_never_returns_approved_dose(monkeypatch):
    from fastapi.testclient import TestClient
    from medsafe import api_product
    monkeypatch.setattr(api_product, 'label_details',
                        lambda setid: label_details(setid, session=LabelSession()))
    with TestClient(api_product.app) as client:
        result = client.get('/api/reference/label/aabbccdd-1234')
    assert result.status_code == 200
    assert result.json()['status'] == 'UNVERIFIED_LABEL_EVIDENCE'
    assert 'clinical_clearance' not in result.json()
    assert 'max_daily' not in result.json()


def test_draft_cannot_be_activated(tmp_path):
    draft = draft_from_label('aabbccdd-1234', session=LabelSession())
    assert draft['review_status'] == 'DRAFT'
    assert draft['max_single'] is None and draft['clinical_clearance'] is False
    path = tmp_path / 'registry.json'
    path.write_text(json.dumps([draft]), encoding='utf-8')
    with pytest.raises(RuleRegistryError):
        inspect_offline_registry(path)
    awaiting = transition_nonapproval(draft, 'AWAITING_REVIEW', actor='test submitter', reason='Send for external review')
    assert awaiting['review_status'] == 'AWAITING_REVIEW'
    assert awaiting['lifecycle_events'][0]['to'] == 'AWAITING_REVIEW'
    with pytest.raises(ValueError):
        transition_nonapproval(awaiting, 'APPROVED_BY_QUALIFIED_REVIEWER',
                               actor='test submitter', reason='self approval is forbidden')


def test_v2_offline_import_and_volume_only_with_reviewed_concentration(tmp_path):
    entry = rule()
    path = tmp_path / 'registry.json'
    path.write_text(json.dumps([entry]), encoding='utf-8')
    assert inspect_offline_registry(path)['status'] == 'STRUCTURALLY_VALID_NOT_IDENTITY_VERIFIED'
    approved = load_reviewed_rules(path)[0]
    assert assess_reviewed_rule(approved, dose=11, unit='mL', frequency=2)['status'] == 'REVIEW_THRESHOLD_EXCEEDED'
    assert assess_reviewed_rule(approved, dose=1, unit='mL', frequency=1)['clinical_clearance'] is False
    altered = {**approved, 'concentration_product_identifier': 'OTHER-PRODUCT'}
    assert assess_reviewed_rule(altered, dose=11, unit='mL', frequency=2)['status'] == 'NOT_EVALUATED'
    weighted = {**approved, 'max_single_mg_per_kg': 2, 'max_daily_mg_per_kg': 4}
    assert assess_reviewed_rule(weighted, dose=3, unit='mL', frequency=2,
                                weight_kg=10)['status'] == 'REVIEW_THRESHOLD_EXCEEDED'


def test_second_review_and_expiry_fail_closed(tmp_path):
    entry = rule()
    entry['second_reviewer'] = entry['reviewer']
    path = tmp_path / 'registry.json'
    path.write_text(json.dumps([entry]), encoding='utf-8')
    with pytest.raises(RuleRegistryError):
        load_reviewed_rules(path)
    entry = rule()
    entry['expires_on'] = (date.today() - timedelta(days=1)).isoformat()
    assert assess_reviewed_rule(entry, dose=300, unit='mg', frequency=2)['status'] == 'NOT_EVALUATED'
    assert match_rule([entry], ingredient='SYNTHMED', product_identifier='SYNTH-001',
                      route='oral', indication='fictional simulation', population='synthetic test') is None
