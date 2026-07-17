"""StadiumSaathi — Offline AI Assistant Engine.

A lightweight NLU + NLG pipeline that runs 100% offline:
    1. Input sanitization : length limits + control-character stripping.
    2. Intent detection   : fast keyword pass, fuzzy fallback (difflib),
                            cached with ``functools.lru_cache``.
    3. Entity extraction  : precompiled regex (e.g. gate numbers).
    4. Response building  : template-based NLG in English / Hindi / Hinglish,
                            filled live from ``stadium_data.json``.

No external API, no database, no network calls at runtime.
"""

from __future__ import annotations

import difflib
import json
import os
import random
import re
from functools import lru_cache
from typing import Any, Callable

# --------------------------------------------------------------------- data
DATA_PATH: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stadium_data.json")

def _load_data(path: str = DATA_PATH) -> dict[str, Any]:
    """Load and validate the stadium knowledge base.

    Raises:
        RuntimeError: if the file is missing or malformed, with a safe message
            (no internal paths leaked to end users).
    """
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("Stadium knowledge base could not be loaded.") from exc
    for key in ("stadium", "zones", "gates", "food_stalls", "washrooms"):
        if key not in data:
            raise RuntimeError(f"Knowledge base missing required section: {key}")
    return data

DATA: dict[str, Any] = _load_data()

LANGS: list[str] = ["English", "हिंदी (Hindi)", "Hinglish"]

MAX_QUERY_LEN: int = 300  # security: bound user input size

_TOKEN_RE = re.compile(r"[a-z\u0900-\u097f0-9']+")
_GATE_RE = re.compile(r"(?:gate|गेट)\s*-?\s*([a-e1-5])")
_CTRL_RE = re.compile(r"[\x00-\x1f\x7f]")


def sanitize(query: str) -> str:
    """Return a safe, normalised copy of raw user input.

    Strips control characters, collapses whitespace and truncates to
    ``MAX_QUERY_LEN`` characters so downstream matching stays O(1) in
    input size and the UI cannot be flooded.
    """
    if not isinstance(query, str):
        return ""
    query = _CTRL_RE.sub(" ", query)
    query = re.sub(r"\s+", " ", query).strip()
    return query[:MAX_QUERY_LEN]


def _lang_key(lang: str) -> str:
    """Map a UI language label to an internal template key (en/hi/hn)."""
    if "Hindi" in lang or "हि" in lang:
        return "hi"
    if lang == "Hinglish":
        return "hn"
    return "en"

# ------------------------------------------------------------------ intents
INTENT_KEYWORDS: dict[str, list[str]] = {
    "greeting":      ["hello", "hi", "hey", "namaste", "namaskar", "hola",
                      "नमस्ते", "good morning", "good evening"],
    "thanks":        ["thanks", "thank you", "dhanyawad", "shukriya",
                      "धन्यवाद", "शुक्रिया"],
    "gate":          ["gate", "entry", "entrance", "dwar", "darwaza", "enter",
                      "गेट", "प्रवेश", "which gate", "kaun sa gate", "kis gate"],
    "food":          ["food", "khana", "khaana", "eat", "restaurant", "stall", "snack",
                      "burger", "pizza", "taco", "biryani", "hungry", "bhookh", "bhukh",
                      "खाना", "भोजन", "veg", "vegan", "halal", "chai", "coffee", "drink"],
    "washroom":      ["washroom", "toilet", "bathroom", "restroom", "loo",
                      "shauchalay", "sochalay", "शौचालय", "टॉयलेट", "बाथरूम"],
    "first_aid":     ["first aid", "medical", "doctor", "injury", "hurt", "ambulance",
                      "medicine", "dawai", "ilaj", "डॉक्टर", "प्राथमिक", "इलाज",
                      "unwell", "sick"],
    "parking":       ["parking", "park", "car", "bike", "vehicle", "gaadi", "gadi",
                      "पार्किंग", "गाड़ी"],
    "emergency":     ["emergency", "exit", "evacuate", "fire", "danger", "help me",
                      "bahar", "nikas", "आपातकाल", "निकास", "बाहर", "police", "security"],
    "accessibility": ["wheelchair", "accessible", "accessibility", "divyang", "disabled",
                      "ramp", "viklang", "दिव्यांग", "व्हीलचेयर", "sensory",
                      "sign language", "deaf", "blind"],
    "match":         ["match", "game", "final", "schedule", "kickoff", "kick off",
                      "timing", "kab hai", "मैच", "फाइनल", "score", "team",
                      "world cup", "semi"],
    "crowd":         ["crowd", "rush", "bheed", "bhid", "queue", "line", "busy",
                      "भीड़", "लाइन", "waiting", "kitni der"],
    "wifi":          ["wifi", "wi-fi", "internet", "network", "password",
                      "वाईफाई", "इंटरनेट"],
    "water":         ["water", "paani", "pani", "पानी", "refill", "bottle",
                      "thirsty", "pyaas", "प्यास"],
    "atm":           ["atm", "cash", "money", "paisa", "paise", "पैसा", "एटीएम", "bank"],
    "recycling":     ["recycle", "recycling", "dustbin", "bin", "garbage", "trash",
                      "kachra", "kuda", "कचरा", "कूड़ा", "waste", "sustainability", "eco"],
    "prayer":        ["prayer", "pray", "namaz", "namaaz", "puja", "pooja", "mandir",
                      "masjid", "नमाज़", "प्रार्थना", "पूजा", "worship"],
    "lost_found":    ["lost", "found", "kho", "khoya", "gum", "खो", "गुम",
                      "missing", "lost and found", "wallet kho", "phone kho"],
    "merch":         ["merchandise", "jersey", "store", "shop", "souvenir", "tshirt",
                      "t-shirt", "kit", "जर्सी", "दुकान", "buy", "kharidna", "खरीद"],
    "help_desk":     ["helpline", "help desk", "contact", "phone number", "support",
                      "complaint", "shikayat", "शिकायत", "मदद", "madad",
                      "sahayta", "सहायता"],
}

INTENT_PRIORITY: list[str] = [
    "emergency", "first_aid", "accessibility", "washroom", "gate", "food",
    "parking", "water", "crowd", "match", "wifi", "atm", "recycling", "prayer",
    "lost_found", "merch", "help_desk", "thanks", "greeting",
]

_FUZZY_THRESHOLD: float = 0.84


@lru_cache(maxsize=512)
def detect_intent(query: str) -> tuple[str | None, int]:
    """Return ``(best_intent, score)`` for a sanitized query.

    Two-pass strategy for efficiency:
        Pass 1 (fast): substring keyword hits, 2 points each.
        Pass 2 (only if pass 1 found nothing): fuzzy token matching.
    Results are memoised via ``lru_cache`` so repeated questions cost O(1).
    """
    q = query.lower().strip()
    if not q:
        return None, 0
    token_set = set(_TOKEN_RE.findall(q))
    scores: dict[str, int] = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        s = 0
        for kw in keywords:
            # single ASCII words match whole tokens only (avoids 'line' matching
            # inside 'helpline'); phrases and Devanagari use substring matching
            if kw.isascii() and kw.isalnum():
                if kw in token_set:
                    s += 2
            elif kw in q:
                s += 2
        if s:
            scores[intent] = s
    if not scores:  # fuzzy fallback, only when needed
        tokens = [t for t in token_set if len(t) > 3]
        for intent, keywords in INTENT_KEYWORDS.items():
            for kw in keywords:
                if any(difflib.SequenceMatcher(None, t, kw).ratio() > _FUZZY_THRESHOLD
                       for t in tokens):
                    scores[intent] = scores.get(intent, 0) + 1
    if not scores:
        return None, 0
    best = max(scores.values())
    for intent in INTENT_PRIORITY:  # deterministic tie-break
        if scores.get(intent) == best:
            return intent, best
    return max(scores, key=lambda k: scores[k]), best


def _extract_gate(query: str) -> dict[str, str] | None:
    """Return the gate record referenced in the query, if any.

    Accepts letters (``gate c``) or numbers (``gate 3`` → Gate C) in
    English or Hindi (``गेट 2``).
    """
    m = _GATE_RE.search(query.lower())
    if not m:
        return None
    val = m.group(1).upper()
    if val.isdigit():
        val = "ABCDE"[int(val) - 1]
    return next((g for g in DATA["gates"] if g["id"] == val), None)


def _zone_items(items: list[dict[str, Any]], zone: str) -> list[dict[str, Any]]:
    """Prefer items in the user's zone; fall back to all items."""
    same = [i for i in items if i.get("zone") == zone]
    return same if same else items

# ------------------------------------------------------------- NLG templates
T: dict[str, dict[str, str]] = {
    "greeting": {
        "en": "Hello! 👋 I am StadiumSaathi, your stadium assistant for the FIFA World Cup 2026. Ask me about gates, food, washrooms, parking, first aid, matches — anything!",
        "hi": "नमस्ते! 👋 मैं StadiumSaathi हूँ — FIFA World Cup 2026 के लिए आपका स्टेडियम सहायक। गेट, खाना, शौचालय, पार्किंग, मैच — कुछ भी पूछिए!",
        "hn": "Namaste! 👋 Main StadiumSaathi hoon — FIFA World Cup 2026 ke liye aapka stadium assistant. Gate, khana, washroom, parking, match — kuch bhi poochhiye!",
    },
    "thanks": {
        "en": "You're welcome! Enjoy the match! ⚽",
        "hi": "आपका स्वागत है! मैच का आनंद लीजिए! ⚽",
        "hn": "Welcome! Match enjoy kijiye! ⚽",
    },
    "fallback": {
        "en": "Sorry, I didn't fully get that. Try asking: 'Where is Gate C?', 'Where can I eat?', 'Nearest washroom?', 'When is the final?'",
        "hi": "माफ़ कीजिए, मैं समझ नहीं पाया। ऐसे पूछिए: 'गेट C कहाँ है?', 'खाना कहाँ मिलेगा?', 'नज़दीकी शौचालय?', 'फाइनल कब है?'",
        "hn": "Sorry, samajh nahi paya. Aise poochhiye: 'Gate C kahan hai?', 'Khana kahan milega?', 'Nearest washroom?', 'Final kab hai?'",
    },
}


def _fmt_list(lines: list[str]) -> str:
    """Render a list of strings as markdown bullets."""
    return "\n".join("• " + l for l in lines)

# --------------------------------------------- intent → answer builders
def _ans_gate(q: str, lk: str, zone: str) -> str:
    g = _extract_gate(q)
    if g:
        return {
            "en": f"**Gate {g['id']}** is on the **{g['zone']}** side. It serves {g['serves']}. Landmark: {g['landmark']}.",
            "hi": f"**गेट {g['id']}** **{g['zone']}** की तरफ है। यह {g['serves']} के लिए है। पहचान: {g['landmark']}।",
            "hn": f"**Gate {g['id']}** **{g['zone']}** side par hai. Ye {g['serves']} ke liye hai. Landmark: {g['landmark']}.",
        }[lk]
    lines = [f"Gate {x['id']} — {x['zone']} ({x['serves']})" for x in DATA["gates"]]
    head = {"en": "Here are all the entry gates:\n",
            "hi": "सभी प्रवेश गेट ये हैं:\n",
            "hn": "Saare entry gates ye hain:\n"}
    tip = {
        "en": f"\n\nTip: your ticket section number tells your gate. You are currently near **{zone}**.",
        "hi": f"\n\nसुझाव: टिकट पर लिखा सेक्शन नंबर आपका गेट बताता है। आप अभी **{zone}** के पास हैं।",
        "hn": f"\n\nTip: ticket ka section number aapka gate batata hai. Aap abhi **{zone}** ke paas hain.",
    }
    return head[lk] + _fmt_list(lines) + tip[lk]


_CUISINE_FILTERS: list[tuple[str, str]] = [
    ("vegan", "vegan"), ("veg", "veg"), ("halal", "halal"), ("pizza", "pizza"),
    ("burger", "burger"), ("taco", "mexican"), ("indian", "indian"),
    ("coffee", "beverage"), ("chai", "beverage"),
]


def _ans_food(q: str, lk: str, zone: str) -> str:
    ql = q.lower()
    stalls = DATA["food_stalls"]
    for word, key in _CUISINE_FILTERS:
        if word in ql:
            hit = [s for s in stalls if key in (s["cuisine"] + s["name"]).lower()]
            if hit:
                stalls = hit
            break
    near = _zone_items(stalls, zone)
    lines = [f"**{s['name']}** ({s['cuisine']}) — {s['zone']}, {s['near']}" for s in near[:5]]
    head = {"en": f"Food options near **{zone}**:\n",
            "hi": f"**{zone}** के पास खाने के विकल्प:\n",
            "hn": f"**{zone}** ke paas khane ke options:\n"}
    return head[lk] + _fmt_list(lines)


def _ans_washroom(q: str, lk: str, zone: str) -> str:
    near = _zone_items(DATA["washrooms"], zone)
    w = near[0]
    acc = {"en": " (wheelchair accessible)", "hi": " (व्हीलचेयर सुलभ)", "hn": " (wheelchair accessible)"}
    extra = acc[lk] if w.get("accessible") else ""
    base = {
        "en": f"Nearest washroom to **{zone}**: {w['location']}{extra}.",
        "hi": f"**{zone}** के सबसे पास शौचालय: {w['location']}{extra}।",
        "hn": f"**{zone}** ke sabse paas washroom: {w['location']}{extra}.",
    }
    others = [f"{x['zone']}: {x['location']}" for x in DATA["washrooms"] if x is not w][:3]
    more = {"en": "\n\nOther options:\n", "hi": "\n\nअन्य विकल्प:\n", "hn": "\n\nAur options:\n"}
    return base[lk] + more[lk] + _fmt_list(others)


def _ans_first_aid(q: str, lk: str, zone: str) -> str:
    near = _zone_items(DATA["first_aid"], zone)[0]
    return {
        "en": f"🏥 Nearest first aid: **{near['location']}** ({near['zone']}). For serious emergencies call the stadium helpline: {DATA['stadium']['helpline']}.",
        "hi": f"🏥 सबसे पास प्राथमिक चिकित्सा: **{near['location']}** ({near['zone']})। गंभीर स्थिति में हेल्पलाइन: {DATA['stadium']['helpline']}।",
        "hn": f"🏥 Sabse paas first aid: **{near['location']}** ({near['zone']}). Serious emergency mein helpline: {DATA['stadium']['helpline']}.",
    }[lk]


def _ans_parking(q: str, lk: str, zone: str) -> str:
    lines = [f"**{p['lot']}** — {p['for']} ({p['zone']} side, {p['capacity']} vehicles)" for p in DATA["parking"]]
    head = {"en": "Parking lots:\n", "hi": "पार्किंग स्थान:\n", "hn": "Parking lots:\n"}
    return head[lk] + _fmt_list(lines)


def _ans_emergency(q: str, lk: str, zone: str) -> str:
    near = _zone_items(DATA["exits"], zone)
    lines = [f"**{e['id']}** — {e['note']} ({e['zone']})" for e in near]
    base = {"en": "🚨 Stay calm. Nearest emergency exits:\n",
            "hi": "🚨 शांत रहिए। नज़दीकी आपातकालीन निकास:\n",
            "hn": "🚨 Shaant rahiye. Nazdeeki emergency exits:\n"}
    tail = {
        "en": f"\n\nFollow the stewards' instructions. Helpline: {DATA['stadium']['helpline']}.",
        "hi": f"\n\nस्टाफ के निर्देशों का पालन करें। हेल्पलाइन: {DATA['stadium']['helpline']}।",
        "hn": f"\n\nStaff ke instructions follow karein. Helpline: {DATA['stadium']['helpline']}.",
    }
    return base[lk] + _fmt_list(lines) + tail[lk]


def _ans_accessibility(q: str, lk: str, zone: str) -> str:
    a = DATA["accessibility"]
    lines = [a["wheelchair_ramps"], a["assistance_desk"], a["accessible_parking"],
             a["sensory_room"], a["sign_language"]]
    head = {"en": "♿ Accessibility services:\n",
            "hi": "♿ दिव्यांगजन सुविधाएँ:\n",
            "hn": "♿ Accessibility services:\n"}
    return head[lk] + _fmt_list(lines)


def _ans_match(q: str, lk: str, zone: str) -> str:
    lines = [f"**{m['match']}** — {m['teams']} | {m['date']}, {m['time']} | {m['status']}" for m in DATA["matches"]]
    head = {"en": "Match schedule at this stadium:\n",
            "hi": "इस स्टेडियम में मैच:\n",
            "hn": "Is stadium ke matches:\n"}
    return head[lk] + _fmt_list(lines)


def _ans_crowd(q: str, lk: str, zone: str) -> str:
    dens = {z: random.randint(35, 95) for z in DATA["zones"]}
    calm = min(dens, key=lambda k: dens[k])
    lines = [f"{'🔴' if d > 85 else '🟡' if d > 60 else '🟢'} {z}: ~{d}% full"
             for z, d in dens.items()]
    head = {"en": "Live crowd status:\n", "hi": "लाइव भीड़ स्थिति:\n", "hn": "Live crowd status:\n"}
    tail = {
        "en": f"\n\nLeast crowded right now: **{calm}**. (Live estimate — see the Crowd Dashboard tab for details.)",
        "hi": f"\n\nअभी सबसे कम भीड़: **{calm}**। (लाइव अनुमान — विस्तार के लिए Crowd Dashboard देखें।)",
        "hn": f"\n\nAbhi sabse kam bheed: **{calm}**. (Live estimate — details ke liye Crowd Dashboard tab dekhein.)",
    }
    return head[lk] + _fmt_list(lines) + tail[lk]


def _ans_wifi(q: str, lk: str, zone: str) -> str:
    w = DATA["stadium"]["wifi"]
    return {
        "en": f"📶 Free WiFi network: **{w['network']}**. {w['password']}.",
        "hi": f"📶 मुफ़्त WiFi नेटवर्क: **{w['network']}**। {w['password']}।",
        "hn": f"📶 Free WiFi network: **{w['network']}**. {w['password']}.",
    }[lk]


def _ans_water(q: str, lk: str, zone: str) -> str:
    near = _zone_items(DATA["water_stations"], zone)[0]
    return {
        "en": f"💧 Free water refill nearest to you: {near['location']} ({near['zone']}). Bring your own bottle — it keeps the stadium plastic-free!",
        "hi": f"💧 आपके सबसे पास मुफ़्त पानी रिफिल: {near['location']} ({near['zone']})। अपनी बोतल लाएं — प्लास्टिक मुक्त स्टेडियम!",
        "hn": f"💧 Aapke sabse paas free water refill: {near['location']} ({near['zone']}). Apni bottle laayein — plastic-free stadium!",
    }[lk]


def _ans_atm(q: str, lk: str, zone: str) -> str:
    lines = [f"{a['zone']} — {a['location']}" for a in DATA["atms"]]
    head = {"en": "🏧 ATMs inside the stadium:\n", "hi": "🏧 स्टेडियम में ATM:\n", "hn": "🏧 Stadium ke ATM:\n"}
    return head[lk] + _fmt_list(lines)


def _ans_recycling(q: str, lk: str, zone: str) -> str:
    near = _zone_items(DATA["recycling_points"], zone)[0]
    return {
        "en": f"♻️ Nearest recycling point: {near['location']} ({near['zone']}). Please separate plastic, paper and food waste — help us make World Cup 2026 the greenest ever!",
        "hi": f"♻️ नज़दीकी रीसाइकलिंग पॉइंट: {near['location']} ({near['zone']})। प्लास्टिक, कागज़ और खाना अलग डालें!",
        "hn": f"♻️ Nazdeeki recycling point: {near['location']} ({near['zone']}). Plastic, paper aur food waste alag daalein!",
    }[lk]


def _ans_prayer(q: str, lk: str, zone: str) -> str:
    p = DATA["other"]["prayer_room"]
    return {"en": f"🙏 Multi-faith prayer room: {p}.",
            "hi": f"🙏 प्रार्थना कक्ष: {p}।",
            "hn": f"🙏 Prayer room: {p}."}[lk]


def _ans_lost(q: str, lk: str, zone: str) -> str:
    l = DATA["other"]["lost_and_found"]
    return {
        "en": f"For lost items, go to the **Lost & Found**: {l}. Carry your ticket/ID for verification.",
        "hi": f"खोया सामान के लिए **Lost & Found** जाएं: {l}। टिकट/ID साथ रखें।",
        "hn": f"Khoya samaan ke liye **Lost & Found** jaayein: {l}. Ticket/ID saath rakhein.",
    }[lk]


def _ans_merch(q: str, lk: str, zone: str) -> str:
    lines = [f"**{m['name']}** — {m['zone']}, {m['near']}" for m in DATA["other"]["merchandise"]]
    head = {"en": "👕 Official merchandise stores:\n", "hi": "👕 आधिकारिक मर्चेंडाइज़ स्टोर:\n", "hn": "👕 Official merchandise stores:\n"}
    return head[lk] + _fmt_list(lines)


def _ans_help_desk(q: str, lk: str, zone: str) -> str:
    return {
        "en": f"ℹ️ Help Desk: Gate B, East Stand. Helpline: {DATA['stadium']['helpline']}.",
        "hi": f"ℹ️ हेल्प डेस्क: गेट B, East Stand। हेल्पलाइन: {DATA['stadium']['helpline']}।",
        "hn": f"ℹ️ Help Desk: Gate B, East Stand. Helpline: {DATA['stadium']['helpline']}.",
    }[lk]


_BUILDERS: dict[str, Callable[[str, str, str], str]] = {
    "gate": _ans_gate, "food": _ans_food, "washroom": _ans_washroom,
    "first_aid": _ans_first_aid, "parking": _ans_parking, "emergency": _ans_emergency,
    "accessibility": _ans_accessibility, "match": _ans_match, "crowd": _ans_crowd,
    "wifi": _ans_wifi, "water": _ans_water, "atm": _ans_atm,
    "recycling": _ans_recycling, "prayer": _ans_prayer, "lost_found": _ans_lost,
    "merch": _ans_merch, "help_desk": _ans_help_desk,
}


def answer(query: str, lang: str = "English", user_zone: str = "North Stand") -> tuple[str, str]:
    """Answer a user query. Returns ``(reply_markdown, detected_intent)``.

    The query is sanitized first (security), then routed through cached
    intent detection and the matching response builder.
    """
    q = sanitize(query)
    lk = _lang_key(lang)
    if user_zone not in DATA["zones"]:
        user_zone = DATA["zones"][0]
    intent, _score = detect_intent(q)
    if intent in ("greeting", "thanks"):
        return T[intent][lk], intent
    if intent in _BUILDERS:
        return _BUILDERS[intent](q, lk, user_zone), intent
    return T["fallback"][lk], "fallback"


def quick_suggestions(lang: str = "English") -> list[str]:
    """Four example questions, localised to the selected language."""
    return {
        "en": ["Where is Gate C?", "Where can I eat?", "Nearest washroom?", "When is the final?"],
        "hi": ["गेट C कहाँ है?", "खाना कहाँ मिलेगा?", "नज़दीकी शौचालय?", "फाइनल कब है?"],
        "hn": ["Gate C kahan hai?", "Khana kahan milega?", "Nearest washroom?", "Final kab hai?"],
    }[_lang_key(lang)]


if __name__ == "__main__":  # manual smoke test
    for t in ["gate 3 kahan hai", "khana", "शौचालय", "wheelchair", "final kab hai",
              "wifi", "emergency", "paani", "hello", "xyz gibberish"]:
        r, i = answer(t, "Hinglish", "South Stand")
        print(f"[{i}] {t} -> {r[:70]}")
