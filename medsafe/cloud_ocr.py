"""Opt-in, comparison-only image transcription using Google's Gemini API."""
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
        raise GeminiUnavailable('Cloud reader is not configured. Set GEMINI_API_KEY or add a key to medsafe/cloud_local.py on the server.')
    model = os.getenv('MEDSAFE_GEMINI_MODEL', 'gemini-2.5-flash').strip()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,79}', model):
        raise GeminiUnavailable('Invalid Gemini model name.')
    payload = {'contents': [{'role': 'user', 'parts': [
        {'text': ('Transcribe all visible text in this prescription image in reading order. '
                  'Preserve line breaks, numbers, units and headings. Do not infer missing '
                  'words, correct medicines, summarize, assess safety, or add commentary. '
                  'Use [unclear] for characters you cannot read.')},
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
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
        raise GeminiUnavailable('Gemini request failed; check the key, network, model and quota.') from exc
    if not text:
        raise GeminiUnavailable('Gemini returned no readable transcription.')
    return {'text': text, 'regions': [], 'warnings': ['REMOTE_OCR_TRANSCRIPTION_REQUIRES_REVIEW'],
            'provider': 'Google Gemini', 'model': model}
