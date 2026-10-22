"""Offline, draft-first evidence workflow; no automatic clinical approval.

The application cannot verify professional identity or signatures. A separate
governance process must attest to any approved registry supplied at deployment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .references import label_details
from .rule_registry import load_reviewed_rules

RULE_STATUSES = frozenset({'DRAFT', 'AWAITING_REVIEW',
                           'APPROVED_BY_QUALIFIED_REVIEWER', 'REJECTED',
                           'EXPIRED', 'SUPERSEDED'})
_LOCAL_TRANSITIONS = {
    'DRAFT': {'AWAITING_REVIEW', 'REJECTED'},
    'AWAITING_REVIEW': {'REJECTED', 'DRAFT'},
    'APPROVED_BY_QUALIFIED_REVIEWER': {'EXPIRED', 'SUPERSEDED'},
    'REJECTED': set(), 'EXPIRED': set(), 'SUPERSEDED': set(),
}


def transition_nonapproval(record: dict, new_status: str, *, actor: str, reason: str) -> dict:
    """Record local review changes; approval is never granted by the app."""
    if not isinstance(record, dict) or new_status not in _LOCAL_TRANSITIONS.get(record.get('review_status'), set()):
        raise ValueError('Invalid lifecycle transition; qualified approval is an external process')
    if not isinstance(actor, str) or not actor.strip() or not isinstance(reason, str) or not reason.strip():
        raise ValueError('A named actor and reason are required')
    updated = dict(record)
    updated['review_status'] = new_status
    updated['clinical_clearance'] = False
    updated['lifecycle_events'] = [*(record.get('lifecycle_events') or []), {
        'from': record['review_status'], 'to': new_status,
        'actor': actor.strip(), 'reason': reason.strip(),
        'recorded_utc': datetime.now(timezone.utc).isoformat(),
    }]
    return updated


def draft_from_label(setid: str, *, session=None) -> dict:
    evidence = label_details(setid, session=session)
    if evidence.get('status') != 'UNVERIFIED_LABEL_EVIDENCE':
        raise ValueError('An exact official label could not be retrieved; no rule draft was created')
    return {
        'schema_version': 2,
        'review_status': 'DRAFT',
        'ingredient': '', 'product_identifier': '', 'route': '',
        'indication': '', 'population': '', 'dose_unit': '',
        'max_single': None, 'max_daily': None,
        'source_url': evidence['url'], 'source_section': '',
        'source_label_id': evidence['label_id'],
        'source_revision': evidence['effective_time'],
        'source_retrieved_utc': evidence['retrieved_utc'],
        'source_setid': evidence['setid'],
        'source_sections_for_review': evidence['sections'],
        'reviewer': '', 'reviewer_credentials': '', 'reviewer_institution': '',
        'review_date': '', 'second_reviewer': '',
        'second_reviewer_credentials': '', 'second_review_date': '',
        'approval_record_id': '', 'expires_on': '', 'version': '',
        'clinical_clearance': False,
        'warning': 'Candidate evidence only. No dose, age, product or clinical rule has been approved.',
    }


def inspect_offline_registry(path: str | Path) -> dict:
    """Check an externally prepared file; never activate it or assert credentials."""
    file = Path(path)
    rules = load_reviewed_rules(file)
    return {
        'status': 'STRUCTURALLY_VALID_NOT_IDENTITY_VERIFIED',
        'rule_count': len(rules),
        'schema_v2_count': sum(x.get('schema_version') == 2 for x in rules),
        'sha256': hashlib.sha256(file.read_bytes()).hexdigest(),
        'activation': 'NOT_PERFORMED',
        'warning': 'Reviewer credentials, source interpretation and signatures require offline independent verification.',
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Prepare draft label evidence or inspect offline clinical rules')
    commands = parser.add_subparsers(dest='command', required=True)
    draft = commands.add_parser('draft', help='Fetch official label evidence into a non-active draft')
    draft.add_argument('--setid', required=True)
    draft.add_argument('--output', type=Path, required=True)
    inspect = commands.add_parser('inspect', help='Validate a separately approved registry without activation')
    inspect.add_argument('path', type=Path)
    args = parser.parse_args(argv)
    if args.command == 'draft':
        if args.output.exists():
            parser.error('Draft output already exists; refusing to overwrite it')
        data = draft_from_label(args.setid)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        print(json.dumps({'status': 'DRAFT_NOT_ACTIVE', 'output': str(args.output)}))
    else:
        print(json.dumps(inspect_offline_registry(args.path), indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
