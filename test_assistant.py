"""Unit tests for the StadiumSaathi offline assistant engine.

Run with:  pytest -q
Covers: sanitization, intent detection (3 languages), entity extraction,
zone-aware answers, fallbacks and localisation of every response builder.
"""

import json
import os
import sys

import pytest

from assistant import (
    DATA,
    LANGS,
    MAX_QUERY_LEN,
    __version__,
    _extract_gate,
    _find_data_path,
    _load_data,
    _zone_items,
    answer,
    cli,
    detect_intent,
    quick_suggestions,
    sanitize,
)


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


# ------------------------------------------------------------- greetings & thanks
def test_greeting_and_thanks_answers():
    reply_greet, intent_greet = answer("hello", "English", "North Stand")
    assert intent_greet == "greeting"
    assert "StadiumSaathi" in reply_greet

    reply_thanks, intent_thanks = answer("dhanyawad", "हिंदी (Hindi)", "East Stand")
    assert intent_thanks == "thanks"
    assert "मदद" in reply_thanks or "स्वागत" in reply_thanks


def test_detect_intent_empty():
    intent, score = detect_intent("")
    assert intent is None
    assert score == 0


def test_detect_intent_tie_break_non_priority():
    # Both "wifi" and "merch" have single word triggers.
    # When queries trigger non-priority intents equally:
    intent, score = detect_intent("wifi jersey")
    assert intent in ("wifi", "merch")
    assert score > 0


# ------------------------------------------------------------- food cuisine filters
def test_food_cuisine_filtering():
    # Query with pizza keyword
    reply_pizza, _ = answer("i want pizza", "English", "North Stand")
    assert "Pizza" in reply_pizza

    # Query with burger keyword
    reply_burger, _ = answer("any burger stall", "English", "West Stand")
    assert "Burger" in reply_burger

    # Query with taco/mexican keyword
    reply_taco, _ = answer("tacos", "English", "South Stand")
    assert "Taco" in reply_taco


# ------------------------------------------------------------- data loading & paths
def test_load_data_missing_file():
    with pytest.raises(RuntimeError, match="could not be loaded"):
        _load_data("/path/to/nonexistent/stadium_data.json")


def test_load_data_malformed_json(tmp_path):
    bad_json_path = tmp_path / "corrupted.json"
    bad_json_path.write_text("{malformed: json", encoding="utf-8")
    with pytest.raises(RuntimeError, match="could not be loaded"):
        _load_data(str(bad_json_path))


def test_load_data_missing_section(tmp_path):
    incomplete_path = tmp_path / "missing_section.json"
    incomplete_path.write_text(json.dumps({"stadium": {}, "zones": []}), encoding="utf-8")
    with pytest.raises(RuntimeError, match="missing required section"):
        _load_data(str(incomplete_path))


def test_find_data_path_resolves():
    path = _find_data_path()
    assert os.path.isfile(path)
    assert path.endswith("stadium_data.json")


# ------------------------------------------------------------- CLI tests
def test_cli_help(capsys):
    with pytest.raises(SystemExit) as exc:
        cli(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "stadium-saathi" in out
    assert "--query" in out


def test_cli_version(capsys):
    with pytest.raises(SystemExit) as exc:
        cli(["--version"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert __version__ in out


def test_cli_query_gate(capsys):
    code = cli(["--query", "gate 3", "--lang", "English", "--zone", "South Stand"])
    assert code == 0
    out = capsys.readouterr().out
    assert "[gate]" in out
    assert "Gate C" in out


def test_cli_query_devanagari(capsys):
    code = cli(["-q", "गेट 2 कहाँ है", "-l", "हिंदी (Hindi)", "-z", "East Stand"])
    assert code == 0
    out = capsys.readouterr().out
    assert "[gate]" in out
    assert "गेट B" in out


def test_cli_no_query_displays_help(capsys):
    code = cli([])
    assert code == 0
    out = capsys.readouterr().out
    assert "usage: stadium-saathi" in out


def test_main_module_execution(monkeypatch, capsys):
    import runpy
    monkeypatch.setattr(sys, "argv", ["assistant.py", "--query", "gate 3"])
    with pytest.raises(SystemExit) as exc:
        runpy.run_path("assistant.py", run_name="__main__")
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "[gate]" in out
    assert "Gate C" in out
