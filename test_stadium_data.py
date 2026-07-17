"""Data-integrity tests for stadium_data.json — the assistant's knowledge base."""

import datetime as dt

from assistant import DATA


def test_required_sections_present():
    for key in ("stadium", "zones", "gates", "food_stalls", "washrooms",
                "first_aid", "parking", "exits", "water_stations",
                "recycling_points", "atms", "accessibility", "other", "matches"):
        assert key in DATA, f"missing section: {key}"

def test_capacity_is_positive():
    assert DATA["stadium"]["capacity"] > 0

def test_gates_have_all_fields_and_valid_zones():
    zones = set(DATA["zones"])
    for g in DATA["gates"]:
        assert {"id", "zone", "serves", "landmark"} <= g.keys()
        assert g["zone"] in zones

def test_all_facility_zones_are_valid():
    zones = set(DATA["zones"])
    for section in ("food_stalls", "washrooms", "first_aid", "parking",
                    "exits", "water_stations", "recycling_points", "atms"):
        for item in DATA[section]:
            assert item["zone"] in zones, f"{section}: bad zone {item['zone']}"

def test_every_zone_has_a_water_station():
    covered = {w["zone"] for w in DATA["water_stations"]}
    assert covered == set(DATA["zones"])

def test_match_dates_parse():
    for m in DATA["matches"]:
        dt.date.fromisoformat(m["date"])  # raises if invalid

def test_wifi_and_helpline_present():
    assert DATA["stadium"]["wifi"]["network"]
    assert DATA["stadium"]["helpline"]

def test_accessibility_info_complete():
    a = DATA["accessibility"]
    for key in ("wheelchair_ramps", "assistance_desk", "accessible_parking",
                "sensory_room", "sign_language"):
        assert a[key]
