import io

from fastapi.testclient import TestClient
from PIL import Image

from medsafe.api_product import app
from medsafe.extraction import extract_prescription
from backend.app.api.routes import ocr_compare
from medsafe import cloud_ocr as gemini_ocr


def _image():
    output = io.BytesIO()
    Image.new('RGB', (80, 60), 'white').save(output, format='PNG')
    return output.getvalue()


def test_patient_name_is_not_a_medication():
    text = ('Name: Mr. K. Perera\nAge: 45 years\nRx\n'
            '1) Tab. Amoxicillin 500 mg - 1 tab three times daily x 5 days\n'
            '2) Tab. Paracetamol 500 mg - 1 tab three times daily (when required)')
    blocks = extract_prescription(text)
    assert [b['fields']['medicine'] for b in blocks] == ['Amoxicillin', 'Paracetamol']
    assert [b['fields']['age'] for b in blocks] == ['45', '45']
    assert blocks[0]['fields']['frequency'] == 'three times daily'
    assert blocks[1]['fields']['frequency'] == ''
    assert all(b['candidate_only'] for b in blocks)


def test_name_without_medicine_is_not_treated_as_drug():
    block = extract_prescription('Name: Mr. K. Perera\nAge: 45 years')[0]
    assert block['fields']['medicine'] == ''


def test_gemini_is_explicitly_opt_in(monkeypatch):
    monkeypatch.setattr(ocr_compare, 'recognize',
                        lambda data, *, engine: {'text': 'Medicine: Demo', 'regions': []})
    calls = []
    def fake_gemini(data):
        calls.append(data)
        return {'text': 'Medicine: Example', 'regions': [],
                'provider': 'Google Gemini', 'model': 'test-model'}
    monkeypatch.setattr(ocr_compare, 'gemini_transcribe', fake_gemini)
    with TestClient(app) as client:
        local = client.post('/api/compare', files={'file': ('demo.png', _image(), 'image/png')})
        assert local.status_code == 200
        assert local.json()['n_engines'] == 4
        assert 'gemini' not in local.json()['engines']
        assert not calls
        remote = client.post('/api/compare', files={'file': ('demo.png', _image(), 'image/png')},
                             data={'send_to_gemini': 'true'})
        assert remote.status_code == 200
        assert remote.json()['n_engines'] == 5
        assert remote.json()['engines']['gemini']['provider'] == 'Google Gemini'
        assert len(calls) == 1


def test_gemini_adapter_requires_server_key(monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    from medsafe import cloud_local as gemini_local
    monkeypatch.setattr(gemini_local, 'API_KEY', '')
    try:
        gemini_ocr.transcribe(_image())
    except gemini_ocr.GeminiUnavailable as exc:
        assert 'GEMINI_API_KEY' in str(exc)
    else:
        raise AssertionError('The Gemini request must not run without a key')


def test_local_only_key_is_supported_without_exposing_it(monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    from medsafe import cloud_local as gemini_local
    monkeypatch.setattr(gemini_local, 'API_KEY', 'local-test-secret')
    assert gemini_ocr.configured() is True
    monkeypatch.setenv('GEMINI_API_KEY', 'environment-test-secret')
    assert gemini_ocr._api_key() == 'environment-test-secret'


def test_gemini_request_sends_image_and_returns_transcript_without_exposing_key(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'test-secret-never-use-live')
    observed = {}
    class Response:
        def raise_for_status(self):
            pass
        def json(self):
            return {'candidates': [{'content': {'parts': [{'text': 'Name: Sample\nRx\nTab. Example 10 mg'}]}}]}
    def fake_post(url, **kwargs):
        observed.update(url=url, **kwargs)
        return Response()
    monkeypatch.setattr(gemini_ocr.requests, 'post', fake_post)
    result = gemini_ocr.transcribe(_image())
    assert result['provider'] == 'Google Gemini'
    assert 'Tab. Example' in result['text']
    assert observed['headers']['x-goog-api-key'] == 'test-secret-never-use-live'
    assert observed['json']['contents'][0]['parts'][1]['inline_data']['mime_type'] == 'image/png'
    assert 'test-secret-never-use-live' not in str(result)
