import pytest
from ai.anpr.anpr_engine import ANPREngine

def test_anpr_normalizer_clean_plate():
    norm = ANPREngine.normalize_plate("GJ 01 AB 1234")
    assert norm == "GJ01AB1234"

def test_anpr_normalizer_ocr_confusion_repair():
    # O in district code replaced with 0
    norm = ANPREngine.normalize_plate("GJO1AB1234")
    assert norm == "GJ01AB1234"

def test_anpr_normalizer_hyphenated():
    norm = ANPREngine.normalize_plate("GJ-01-AB-1234")
    assert norm == "GJ01AB1234"

def test_anpr_normalizer_lowercase():
    norm = ANPREngine.normalize_plate("gj01ab1234")
    assert norm == "GJ01AB1234"

def test_anpr_normalizer_invalid_short_text():
    norm = ANPREngine.normalize_plate("GJ1")
    assert norm is None
