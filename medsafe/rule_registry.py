"""Reviewed, source-specific medication thresholds; fail closed on incomplete evidence.

This registry intentionally ships with NO real-drug rules. Loading an entry
never implies that the product has undergone external clinical validation.
"""
from __future__ import annotations
from datetime import date, datetime, timezone
import json
import math
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse

REQUIRED = (
    'ingredient', 'product_identifier', 'route', 'indication', 'population',
    'dose_unit', 'max_single', 'max_daily', 'source_url',
    'source_section', 'reviewer', 'review_date', 'version'
)
CONTEXT_KEYS = ('ingredient','product_identifier','route','indication','population')

class RuleRegistryError(ValueError):
    """A reviewed-rule file is malformed or inadequately documented."""

def _positive_finite_number(value):
    return type(value) in (int,float) and math.isfinite(value) and value>0

def _date(value, label):
    try:return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise RuleRegistryError('Invalid '+label) from exc


def _active(rule):
    if not isinstance(rule, dict) or rule.get('review_status') != 'APPROVED_BY_QUALIFIED_REVIEWER':
        return False
    try:
        return not rule.get('expires_on') or _date(rule['expires_on'], 'expiry') >= date.today()
    except RuleRegistryError:
        return False

def load_reviewed_rules(path: str | Path):
    try:
        data=json.loads(Path(path).read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        raise RuleRegistryError('Invalid registry JSON') from exc
    if not isinstance(data,list):
        raise RuleRegistryError('Rule registry must be a JSON list')
    result=[]
    seen=set()
    for i,entry in enumerate(data):
        if not isinstance(entry,dict):
            raise RuleRegistryError(f'Rule {i} is not an object')
        if entry.get('schema_version', 1) not in (1, 2, 3):
            raise RuleRegistryError(f'Rule {i} unsupported schema version')
        for key in REQUIRED:
            value=entry.get(key)
            if key in ('max_single','max_daily'):
                if not _positive_finite_number(value):
                    raise RuleRegistryError(f'Rule {i} invalid {key}')
            elif not isinstance(value,str) or not value.strip():
                raise RuleRegistryError(f'Rule {i} missing {key}')
        if entry.get('review_status')!='APPROVED_BY_QUALIFIED_REVIEWER':
            raise RuleRegistryError(f'Rule {i} is not approved by a qualified reviewer')
        if entry.get('schema_version') in (2, 3):
            mandatory = ('source_label_id', 'source_revision', 'source_retrieved_utc',
                         'reviewer_credentials', 'reviewer_institution',
                         'second_reviewer', 'second_reviewer_credentials',
                         'second_review_date', 'approval_record_id', 'expires_on')
            if any(not isinstance(entry.get(key), str) or not entry[key].strip()
                   for key in mandatory):
                raise RuleRegistryError(f'Rule {i} missing independent approval provenance')
            if entry['reviewer'].casefold().strip() == entry['second_reviewer'].casefold().strip():
                raise RuleRegistryError(f'Rule {i} requires a distinct second reviewer')
            if _date(entry['second_review_date'], f'rule {i} second review date') > date.today():
                raise RuleRegistryError(f'Rule {i} second review date is in the future')
            try:
                retrieved = datetime.fromisoformat(entry['source_retrieved_utc'].replace('Z', '+00:00'))
                if retrieved.tzinfo is None or retrieved > datetime.now(timezone.utc):
                    raise ValueError('Missing timezone or future retrieval')
            except (TypeError, ValueError) as exc:
                raise RuleRegistryError(f'Rule {i} invalid source retrieval time') from exc
        if entry['dose_unit'] not in ('mg','mcg','g'):
            raise RuleRegistryError(f'Rule {i} invalid dose unit')
        concentration=entry.get('concentration_mg_per_ml')
        if concentration is not None and (
            entry['dose_unit']!='mg' or not _positive_finite_number(concentration) or
            not str(entry.get('concentration_source_section') or '').strip() or
            entry.get('concentration_product_identifier')!=entry['product_identifier']
        ):
            raise RuleRegistryError(f'Rule {i} has unverified or inconsistent concentration')
        try:url=urlparse(entry['source_url'])
        except ValueError as exc:raise RuleRegistryError(f'Rule {i} invalid source URL') from exc
        if url.scheme!='https' or not url.hostname or url.username or url.password:
            raise RuleRegistryError(f'Rule {i} invalid HTTPS evidence URL')
        reviewed=_date(entry['review_date'],f'rule {i} review date')
        if reviewed>date.today():
            raise RuleRegistryError(f'Rule {i} review date is in the future')
        if entry.get('schema_version') in (2, 3) and _date(entry['second_review_date'],
                f'rule {i} second review date') < reviewed:
            raise RuleRegistryError(f'Rule {i} second review precedes first review')
        if entry.get('schema_version') == 3:
            for key in ('formulation', 'strength', 'source_type', 'approval_date', 'exclusions'):
                if not isinstance(entry.get(key), str) or not entry[key].strip():
                    raise RuleRegistryError(f'Rule {i} missing {key}')
            approved = _date(entry['approval_date'], f'rule {i} approval date')
            if approved < _date(entry['second_review_date'], f'rule {i} second review date') or approved > date.today():
                raise RuleRegistryError(f'Rule {i} invalid approval date')
        if 'expires_on' in entry:
            expiry=_date(entry['expires_on'],f'rule {i} expiry')
            if expiry<date.today():
                raise RuleRegistryError(f'Rule {i} expired')
            if expiry<reviewed:
                raise RuleRegistryError(f'Rule {i} expires before its review')
        lo,hi=entry.get('min_age_years'),entry.get('max_age_years')
        if lo is not None or hi is not None:
            if (type(lo) not in (int,float) or type(hi) not in (int,float) or
                not math.isfinite(lo) or not math.isfinite(hi) or not 0<=lo<=hi<=120):
                raise RuleRegistryError(f'Rule {i} invalid age interval')
        single_kg=entry.get('max_single_mg_per_kg')
        daily_kg=entry.get('max_daily_mg_per_kg')
        if single_kg is not None or daily_kg is not None:
            if (entry['dose_unit']!='mg' or
                not _positive_finite_number(single_kg) or
                not _positive_finite_number(daily_kg)):
                raise RuleRegistryError(f'Rule {i} invalid mg/kg dosing context')
        effects=entry.get('overdose_adverse_effects',[])
        if (not isinstance(effects,list) or any(
            not isinstance(v,str) or not v.strip() or len(v)>200 for v in effects
        ) or (effects and not str(entry.get('overdose_warning_source_section') or '').strip())):
            raise RuleRegistryError(f'Rule {i} has unsourced or invalid adverse-effect text')
        key=tuple(entry[k].casefold().strip() for k in CONTEXT_KEYS) + (
            entry.get('formulation', '').casefold().strip(), entry.get('strength', '').casefold().strip())
        if key in seen:
            raise RuleRegistryError(f'Rule {i} duplicates an existing context')
        seen.add(key)
        result.append(entry)
    return result

def match_rule(rules, *, ingredient, product_identifier, route, indication, population,
               formulation='', strength=''):
    target=(ingredient,product_identifier,route,indication,population)
    if not all(isinstance(v,str) and v.strip() for v in target):
        return None
    normalized=tuple(v.casefold().strip() for v in target)
    matches=[r for r in rules if
             _active(r) and all(isinstance(r.get(k),str) for k in CONTEXT_KEYS)
             and tuple(r[k].casefold().strip() for k in CONTEXT_KEYS)==normalized
             and all(not r.get(k) or (isinstance(v,str) and v.casefold().strip()==r[k].casefold().strip())
                     for k,v in (('formulation',formulation),('strength',strength)))]
    return matches[0] if len(matches)==1 else None

def assess_reviewed_rule(rule, *, dose, unit, frequency, weight_kg=None):
    """Return screening flags only; a below-threshold value never means safe."""
    unresolved={'status':'NOT_EVALUATED','clinical_clearance':False,
                'reason':'Missing exact reviewed rule, unit, or valid administered dose context'}
    if (not isinstance(rule,dict) or type(frequency) is not int or
        not 1<=frequency<=24 or not _positive_finite_number(dose) or
        not all(_positive_finite_number(rule.get(k)) for k in ('max_single','max_daily'))):
        return unresolved
    # Mass conversions are exact; a volume requires an explicitly reviewed,
    # formulation-specific concentration in the matching product rule.
    mass_to_mg={'mcg':0.001,'mg':1.0,'g':1000.0}
    if rule.get('dose_unit') not in mass_to_mg:
        return unresolved
    try:
        quantity = Decimal(str(dose))
    except (InvalidOperation, TypeError, ValueError):
        return unresolved
    if unit and unit.lower()=='ml':
        concentration=rule.get('concentration_mg_per_ml')
        if (rule.get('dose_unit')!='mg' or not _positive_finite_number(concentration)
            or not str(rule.get('concentration_source_section') or '').strip()
            or rule.get('concentration_product_identifier')!=rule.get('product_identifier')):
            return {**unresolved, 'reason':'Verified product concentration is required for a volume dose'}
        normalized_dose=quantity*Decimal(str(concentration))
    elif unit in mass_to_mg:
        normalized_dose=quantity * Decimal(str(mass_to_mg[unit])) / Decimal(str(mass_to_mg[rule['dose_unit']]))
    else:
        return unresolved
    if not normalized_dose.is_finite() or normalized_dose<=0:
        return unresolved
    # Direct callers must not bypass the approval gate by omitting the status.
    if not _active(rule):
        return unresolved
    weighted=('max_single_mg_per_kg' in rule or 'max_daily_mg_per_kg' in rule)
    if weighted and (rule.get('dose_unit')!='mg' or not _positive_finite_number(weight_kg) or
                     not all(_positive_finite_number(rule.get(k)) for k in
                             ('max_single_mg_per_kg','max_daily_mg_per_kg'))):
        return {**unresolved,'reason':'Valid verified weight and matching mg/kg thresholds are required'}
    absolute_single=Decimal(str(rule['max_single']))
    absolute_daily=Decimal(str(rule['max_daily']))
    max_single=absolute_single
    max_daily=absolute_daily
    weight_single=weight_daily=None
    if weighted:
        weight_single=Decimal(str(rule['max_single_mg_per_kg']))*Decimal(str(weight_kg))
        weight_daily=Decimal(str(rule['max_daily_mg_per_kg']))*Decimal(str(weight_kg))
        max_single=min(max_single,weight_single)
        max_daily=min(max_daily,weight_daily)
    total=normalized_dose*frequency
    if not total.is_finite():
        return unresolved
    single_exceeded=normalized_dose>max_single
    daily_exceeded=total>max_daily
    exceeded=single_exceeded or daily_exceeded
    comparisons=[]
    if single_exceeded:
        comparisons.append('EXCEEDS_REVIEWED_SINGLE_DOSE_THRESHOLD')
    if daily_exceeded:
        comparisons.append('EXCEEDS_REVIEWED_DAILY_DOSE_THRESHOLD')
    if weighted and (normalized_dose>weight_single or total>weight_daily):
        comparisons.append('EXCEEDS_REVIEWED_WEIGHT_BASED_THRESHOLD')
    if not comparisons:
        comparisons.append('BELOW_REVIEWED_THRESHOLD_NOT_PROOF_OF_SAFETY')
    return {
        'status':'REVIEW_THRESHOLD_EXCEEDED' if exceeded
                 else 'BELOW_REVIEWED_THRESHOLD_NOT_PROOF_OF_SAFETY',
        'comparison_outcomes':comparisons,
        'reason':'Reviewed threshold exceeded; professional assessment required' if exceeded else 'Below reviewed threshold is not proof of safety',
        'ingredient':rule.get('ingredient'),'product_identifier':rule.get('product_identifier'),
        'formulation':rule.get('formulation'),'strength':rule.get('strength'),
        'indication':rule.get('indication'),'population':rule.get('population'),
        'source_url':rule.get('source_url'),'source_section':rule.get('source_section'),
        'source_label_id':rule.get('source_label_id'),'source_revision':rule.get('source_revision'),
        'rule_identifier':rule.get('approval_record_id'),
        'reviewer':rule.get('reviewer'),'rule_version':rule.get('version'),
        'dose_unit':rule['dose_unit'],'reported_dose':dose,'reported_unit':unit,
        'administered_single':float(normalized_dose),'administered_daily':float(total),
        'reviewed_max_single':float(max_single),'reviewed_max_daily':float(max_daily),
        'weight_based':weighted,
        'concentration_mg_per_ml':rule.get('concentration_mg_per_ml') if unit and unit.lower()=='ml' else None,
        'concentration_source_section':rule.get('concentration_source_section') if unit and unit.lower()=='ml' else None,
        'reviewed_adverse_effects':list(rule.get('overdose_adverse_effects',[])) if exceeded else [],
        'clinical_clearance':False
    }
