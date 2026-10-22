"""Live public drug-label lookup; deliberately does not extract clinical maximum doses."""
from __future__ import annotations
import re
import os
from copy import deepcopy
from datetime import datetime, timezone
from threading import Lock
from time import monotonic
from urllib.parse import quote
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DM = 'https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json'
FDA = 'https://api.fda.gov/drug/label.json'
RXN = 'https://rxnav.nlm.nih.gov/REST/rxcui.json'

LABEL_SECTIONS = ('dosage_and_administration', 'pediatric_use', 'geriatric_use',
                  'contraindications', 'warnings', 'boxed_warning', 'overdosage',
                  'adverse_reactions', 'drug_interactions', 'use_in_specific_populations')
_CACHE = {}
_CACHE_LOCK = Lock()
_CACHE_SECONDS = 600


def _cached(key):
    with _CACHE_LOCK:
        value = _CACHE.get(key)
        if value and value[0] > monotonic():
            return deepcopy(value[1])
        _CACHE.pop(key, None)
    return None


def _remember(key, value):
    with _CACHE_LOCK:
        if len(_CACHE) >= 128:
            _CACHE.pop(next(iter(_CACHE)))
        _CACHE[key] = (monotonic() + _CACHE_SECONDS, deepcopy(value))


def _official_session():
    session = requests.Session()
    retry = Retry(total=2, backoff_factor=0.3, status_forcelist=(429, 502, 503, 504),
                  allowed_methods=frozenset({'GET'}), respect_retry_after_header=False)
    session.mount('https://', HTTPAdapter(max_retries=retry))
    return session


def _fetch(session, url, params):
    try:
        res = session.get(url, params=params, timeout=(3, 7), headers={'Accept': 'application/json'})
        if res.status_code == 404:
            return {'state': 'NOT_FOUND', 'results': []}
        if res.status_code == 429:
            return {'state': 'RATE_LIMITED', 'results': []}
        res.raise_for_status()
        data = res.json()
        if not isinstance(data, dict):
            return {'state': 'UNAVAILABLE', 'results': []}
        return {'state': 'OK', 'json': data}
    except (requests.RequestException, ValueError, TypeError):
        return {'state': 'UNAVAILABLE', 'results': []}


def _same_name(title: str, name: str) -> bool:
    # Product titles often include salt, strength or manufacturer: don't assert exact drug identity.
    # Case-insensitive *whole-token* mention is only a search candidate.
    return bool(re.search(r'(?<![a-z0-9])' + re.escape(name.lower()) + r'(?![a-z0-9])', title.lower()))


def lookup(name: str, session=None) -> dict:
    """Provide candidates and official links; don't infer approval/safety from search hits."""
    if not name or not re.fullmatch(r'[A-Za-z][A-Za-z0-9\- ]{1,79}', name.strip()):
        return {'status': 'INVALID_QUERY', 'dailymed': [], 'openfda': [], 'errors': []}
    name = ' '.join(name.strip().split())
    use_cache = session is None
    cache_key = ('lookup', name.casefold())
    if use_cache and (cached := _cached(cache_key)) is not None:
        return cached
    session = session or _official_session()
    retrieved_at = datetime.now(timezone.utc).isoformat()
    dm = _fetch(session, DM, {'drug_name': name, 'pagesize': 5})
    entries = []
    if dm['state'] == 'OK' and isinstance(dm.get('json'), dict):
        for item in dm['json'].get('data', [])[:5]:
            if not isinstance(item, dict):
                continue
            title, sid = str(item.get('title', '')), str(item.get('setid', ''))
            if not _same_name(title, name) or not re.fullmatch(r'[a-zA-Z0-9-]{10,70}', sid):
                continue
            entries.append({'title': title[:160], 'setid': sid,
                            'spl_version': str(item.get('spl_version') or ''),
                            'published_date': str(item.get('published_date') or ''),
                            'retrieved_utc': retrieved_at,
                            'url': f'https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={quote(sid)}'})
    # Exact-name field search, not a wildcard; unmatched results are not accepted as validated drugs.
    fda_params = {'search': f'openfda.generic_name.exact:"{name}"', 'limit': 3}
    if os.getenv('OPENFDA_API_KEY'):
        fda_params['api_key'] = os.environ['OPENFDA_API_KEY']
    fda = _fetch(session, FDA, fda_params)
    fda_entries = []
    if fda['state'] == 'OK' and isinstance(fda.get('json'), dict):
        for label in fda['json'].get('results', [])[:3]:
            metadata = label.get('openfda', {}) if isinstance(label, dict) else {}
            generic_names = metadata.get('generic_name', [])
            if not any(n.lower().strip() == name.lower() for n in generic_names if isinstance(n, str)):
                continue
            setid = str(label.get('set_id', ''))
            sections={}
            for key in LABEL_SECTIONS:
                raw=label.get(key,[]) if isinstance(label,dict) else []
                if isinstance(raw,list) and raw and isinstance(raw[0],str):
                    sections[key]=raw[0][:550]
            fda_entries.append({'name': name, 'setid': setid,
                                'label_id': str(label.get('id') or ''),
                                'effective_time': str(label.get('effective_time') or ''),
                                'version': str(label.get('version') or ''),
                                'retrieved_utc': retrieved_at,
                                'label_sections_UNVERIFIED_FOR_PRODUCT':sections,
                                'url': f'https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={quote(setid)}' if re.fullmatch(r'[a-zA-Z0-9-]{10,70}', setid) else 'https://open.fda.gov/apis/drug/label/'})
    # RxNorm exact-or-normalized concept search helps flag unrecognized drug
    # names. A negative result is NEVER proof that a drug is invalid.
    rxn = _fetch(session, RXN, {'name': name, 'search': '2', 'allsrc': '0'})
    rxn_ids = []
    if rxn['state'] == 'OK' and isinstance(rxn.get('json'), dict):
        group = rxn['json'].get('idGroup') or {}
        if isinstance(group,dict):
            rxn_ids = [str(i) for i in (group.get('rxnormId') or []) if str(i).isdigit()][:10]
    result = {
        'status': ('REFERENCE_UNAVAILABLE' if all(x['state'] in ('UNAVAILABLE', 'RATE_LIMITED') for x in (dm, fda, rxn))
                   else 'CANDIDATES_FOUND' if entries or fda_entries or rxn_ids else 'NO_EXACT_MATCH_FOUND'),
        'rxnorm': {'concept_ids':rxn_ids, 'status': 'CANDIDATES_FOUND' if rxn_ids else 'UNAVAILABLE' if rxn['state']=='UNAVAILABLE' else 'NO_MATCH'},
        'dailymed': entries, 'openfda': fda_entries,
        'errors': [key + (':RATE_LIMITED' if result['state'] == 'RATE_LIMITED' else ':UNAVAILABLE')
                   for key, result in (('DailyMed', dm), ('openFDA', fda), ('RxNorm', rxn))
                   if result['state'] in ('UNAVAILABLE', 'RATE_LIMITED')],
        'dose_threshold_extracted': False,
        'note': 'RxNorm concepts and drug labels are identity candidates, not dosage or age-safety approvals.'
    }
    if use_cache and not result['errors']:
        _remember(cache_key, result)
    return result


def label_details(setid: str, session=None) -> dict:
    """Fetch full official label sections for human review, never auto-approve a rule.

    set_id is a label-family identifier; the caller must verify the exact
    formulation, version, indication, population and all numeric limits.
    """
    if not isinstance(setid, str) or not re.fullmatch(r'[A-Za-z0-9-]{10,70}', setid):
        return {'status': 'INVALID_SETID', 'sections': {}}
    use_cache = session is None
    cache_key = ('label', setid.casefold())
    if use_cache and (cached := _cached(cache_key)) is not None:
        return cached
    session = session or _official_session()
    params = {'search': f'set_id:"{setid}"', 'limit': 5}
    if os.getenv('OPENFDA_API_KEY'):
        params['api_key'] = os.environ['OPENFDA_API_KEY']
    response = _fetch(session, FDA, params)
    if response['state'] != 'OK':
        return {'status': response['state'], 'sections': {}, 'setid': setid}
    matches = [item for item in response['json'].get('results', [])
               if isinstance(item, dict) and str(item.get('set_id') or '').casefold() == setid.casefold()]
    if not matches:
        return {'status': 'NOT_FOUND', 'sections': {}, 'setid': setid}
    if len(matches) != 1:
        return {'status': 'AMBIGUOUS_VERSION', 'sections': {}, 'setid': setid}
    item = matches[0]
    sections = {key: '\n'.join(value)[:100000] for key in LABEL_SECTIONS
                if isinstance(value := item.get(key), list) and all(isinstance(x, str) for x in value)}
    result = {'status': 'UNVERIFIED_LABEL_EVIDENCE', 'setid': setid,
            'label_id': str(item.get('id') or ''),
            'effective_time': str(item.get('effective_time') or ''),
            'version': str(item.get('version') or ''),
            'retrieved_utc': datetime.now(timezone.utc).isoformat(),
            'url': f'https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={quote(setid)}',
            'sections': sections,
            'note': 'Source text only. No product identity, dose, age or adverse-effect interpretation is approved.'}
    if use_cache:
        _remember(cache_key, result)
    return result
