"""Unit tests for the StadiumSaathi offline assistant engine.

Run with:  pytest -q
Covers: sanitization, intent detection (3 languages), entity extraction,
zone-aware answers, fallbacks and localisation of every response builder.
"""

import pytest

from assistant import (DATA, LANGS, MAX_QUERY_LEN, _extract_gate, _zone_items,
                       answer, detect_intent, quick_suggestions, sanitize)

# ------------------------------------------------------------- sanitization
def test_sanitize_strips_control_chars():
    assert sanitize("hello\x00\x1fworld") == "hello world"

def test_sanitize_collapses_whitespace():
    assert sanitize("  gate   3   ") == "gate 3"

def test_sanitize_truncates_long_input():
    assert len(sanitize("a" * 5000)) == MAX_QUERY_LEN

def test_sanitize_non_string_returns_empty():
    assert sanitize(None) == ""  # type: ignore[arg-type]

# --------------------------------------------------------- intent detection
@pytest.mark.parametrize("query,expected", [
    ("where is gate c", "gate"),
    ("gate 3 kahan hai", "gate"),
    ("खाना कहाँ मिलेगा", "food"),
    ("i am hungry", "food"),
    ("nearest washroom", "washroom"),
    ("शौचालय कहां है", "washroom"),
    ("i need a doctor", "first_aid"),
    ("parking kahan hai", "parking"),
    ("emergency exit", "emergency"),
    ("wheelchair ramp", "accessibility"),
    ("final kab hai", "match"),
    ("kitni bheed hai", "crowd"),
    ("wifi password", "wifi"),
    ("paani kahan milega", "water"),
    ("nearest atm", "atm"),
    ("recycling bin", "recycling"),
    ("prayer room", "prayer"),
    ("mera phone kho gaya", "lost_found"),
    ("jersey kharidna hai", "merch"),
    ("helpline number", "help_desk"),
    ("hello", "greeting"),
    ("dhanyawad", "thanks"),
])
def test_intent_detection(query, expected):
    intent, score = detect_intent(sanitize(query))
    assert intent == expected
    assert score > 0

def test_gibberish_gives_no_intent():
    intent, score = detect_intent("qzx vbnp lorem")
    assert intent is None and score == 0

def test_fuzzy_matching_catches_typo():
    intent, _ = detect_intent("washrom near me")  # typo
    assert intent == "washroom"

# --------------------------------------------------------- entity extraction
@pytest.mark.parametrize("query,gate_id", [
    ("gate 1", "A"), ("gate 3", "C"), ("gate c", "C"),
    ("Gate E please", "E"), ("गेट 2 कहाँ है", "B"),
])
def test_gate_extraction(query, gate_id):
    g = _extract_gate(query)
    assert g is not None and g["id"] == gate_id

def test_gate_extraction_absent():
    assert _extract_gate("where can i eat") is None

# ------------------------------------------------------------- zone routing
def test_zone_items_prefers_user_zone():
    res = _zone_items(DATA["washrooms"], "North Stand")
    assert all(r["zone"] == "North Stand" for r in res)

def test_zone_items_falls_back_to_all():
    res = _zone_items(DATA["first_aid"], "VIP Lounge")  # no VIP first aid
    assert res == DATA["first_aid"]

# ----------------------------------------------------------------- answers
ALL_INTENT_QUERIES = [
    "gate", "food", "washroom", "first aid", "parking", "emergency",
    "wheelchair", "match", "crowd", "wifi", "water", "atm",
    "recycling", "prayer", "lost", "jersey", "helpline",
]

@pytest.mark.parametrize("lang", LANGS)
@pytest.mark.parametrize("query", ALL_INTENT_QUERIES)
def test_every_intent_answers_in_every_language(query, lang):
    reply, intent = answer(query, lang, "North Stand")
    assert isinstance(reply, str) and len(reply) > 10
    assert intent != "fallback"

def test_fallback_reply():
    reply, intent = answer("qzx vbnp", "English", "North Stand")
    assert intent == "fallback" and "Sorry" in reply

def test_invalid_zone_defaults_safely():
    reply, intent = answer("washroom", "English", "Mars Base")
    assert intent == "washroom" and len(reply) > 10

def test_hindi_reply_contains_devanagari():
    reply, _ = answer("गेट 2 कहाँ है", "हिंदी (Hindi)", "East Stand")
    assert "गेट B" in reply

def test_specific_gate_answer_mentions_gate():
    reply, intent = answer("gate 3 kahan hai", "Hinglish", "North Stand")
    assert intent == "gate" and "Gate C" in reply

def test_quick_suggestions_localised():
    for lang in LANGS:
        s = quick_suggestions(lang)
        assert len(s) == 4 and all(isinstance(x, str) for x in s)
