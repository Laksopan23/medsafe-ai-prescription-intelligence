"""Image transcription adapter used by the prescription reader."""
from __future__ import annotations

import base64
import os
import re

import requests


class GeminiUnavailable(RuntimeError):
    pass


def _api_key() -> str:
    environment_key = os.getenv('GEMINI_API_KEY', '').strip()
    if environment_key:
        return environment_key
    try:
        from .cloud_local import API_KEY
    except ImportError:
        return ''
    return API_KEY.strip() if isinstance(API_KEY, str) else ''


def configured() -> bool:
    return bool(_api_key())


def transcribe(image_bytes: bytes) -> dict:
    key = _api_key()
    if not key:
        raise GeminiUnavailable('Reader is not configured. Add the reader access key on the server.')
    model = os.getenv('MEDSAFE_GEMINI_MODEL', 'gemini-3.5-flash').strip()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,79}', model):
        raise GeminiUnavailable('Reader configuration is invalid.')
    payload = {'contents': [{'role': 'user', 'parts': [
        {'text': ('Read this prescription image carefully and return a complete, faithful transcription. '
                  'Do not guess, correct medicines, assess safety, or add commentary. Use [unclear] '
                  'for characters you cannot read. Preserve the original values, numbers, units, '
                  'instructions, and reading order. Normalize the visible content into plain text '
                  'using this exact structure, repeating the medication block for every medicine: '
                  'Patient name: ...; Age: ...; Sex: ...; then Medicine: ...; Dose: ...; '
                  'Strength: ...; Frequency: ...; Route: ...; Duration: ...; Instructions: .... '
                  'Omit a field when it is not visible. Keep the original prescription wording '
                  'after the structured fields when useful.')},
        {'inline_data': {'mime_type': 'image/png',
                         'data': base64.b64encode(image_bytes).decode('ascii')}},
    ]}], 'generationConfig': {'temperature': 0, 'maxOutputTokens': 4096}}
    try:
        response = requests.post(
            f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
            headers={'x-goog-api-key': key, 'Content-Type': 'application/json'},
            json=payload, timeout=45,
        )
        response.raise_for_status()
        body = response.json()
        parts = body.get('candidates', [{}])[0].get('content', {}).get('parts', [])
        text = '\n'.join(p['text'] for p in parts if isinstance(p.get('text'), str)).strip()
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else 'unknown'
        raise GeminiUnavailable(f'Reader request was rejected (HTTP {status}); check the access key, model and quota.') from exc
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
        raise GeminiUnavailable('Reader request failed; check the access key, network, model and quota.') from exc
    if not text:
        raise GeminiUnavailable('Reader returned no readable transcription.')
    return {'text': text, 'regions': [], 'warnings': ['REMOTE_OCR_TRANSCRIPTION_REQUIRES_REVIEW'],
            'provider': 'Reader', 'model': model}
