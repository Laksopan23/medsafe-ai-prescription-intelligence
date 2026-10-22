"""Notebook 61 LAYOUT_V2 geometry and decoding are preserved in the app."""
from contextlib import nullcontext
import sys
from types import SimpleNamespace

from PIL import Image
import pytest

from medsafe import ocr_product


def test_craft_thresholds_and_conservative_merge(monkeypatch):
    calls = {}

    class Reader:
        def detect(self, image, **kwargs):
            calls.update(kwargs)
            return [[[10, 40, 10, 30], [44, 70, 10, 30],
                     [170, 200, 10, 30]]], [[]]

    monkeypatch.setattr(ocr_product, '_craft', lambda: Reader())
    boxes = ocr_product._boxes(Image.new('RGB', (240, 80), 'white'))
    assert calls == {'min_size': 8, 'text_threshold': .55,
                     'low_text': .25, 'link_threshold': .25,
                     'canvas_size': 2560, 'mag_ratio': 1.5, 'add_margin': .06}
    assert (10, 10, 70, 30) in boxes
    assert (170, 10, 200, 30) in boxes
    assert len(boxes) == 2


def test_notebook61_crop_and_generation_settings(monkeypatch):
    seen = {}
    monkeypatch.setitem(sys.modules, 'torch', SimpleNamespace(inference_mode=nullcontext))

    class Pixels:
        def to(self, device):
            return self

    class Processor:
        def __call__(self, *, images, return_tensors):
            seen['size'] = images[0].size
            return type('Batch', (), {'pixel_values': Pixels()})()

        def batch_decode(self, ids, *, skip_special_tokens):
            return ['SYNTHMED']

    class Model:
        def generate(self, pixels, **kwargs):
            seen['generation'] = kwargs
            return [[1, 2]]

    monkeypatch.setattr(ocr_product, '_recognizer', lambda: (Processor(), Model(), 'cpu'))
    result = ocr_product._trocr_lines(Image.new('RGB', (120, 60), 'white'),
                                      [(10, 10, 50, 30)])
    assert result == ['SYNTHMED']
    assert seen['generation'] == {'max_new_tokens': 64, 'num_beams': 2}
    assert seen['size'][0] > 40 and seen['size'][1] > 20


def test_craft_never_silently_truncates_many_regions(monkeypatch):
    class Reader:
        def detect(self, image, **kwargs):
            return [[(i*30, i*30+10, 10, 30) for i in range(257)]], [[]]

    monkeypatch.setattr(ocr_product, '_craft', lambda: Reader())
    with pytest.raises(ocr_product.OCRUnavailable, match='silently discarding'):
        ocr_product._boxes(Image.new('RGB', (8000, 50), 'white'))
