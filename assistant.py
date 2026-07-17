"""
StadiumSaathi - Offline AI Assistant Engine
--------------------------------------------
A lightweight NLU + NLG engine that runs 100% offline:
  1. Intent detection  : keyword + fuzzy matching (difflib), Hindi + English + Hinglish
  2. Entity extraction : gate numbers/letters via regex
  3. Response building : template-based natural language generation, filled
                         live from stadium_data.json and the user's current zone

No external API, no database, no internet needed at runtime.
"""

import json
import os
import re
import difflib
import random

# ---------------------------------------------------------------- data
DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stadium_data.json")

with open(DATA_PATH, encoding="utf-8") as f:
    DATA = json.load(f)

LANGS = ["English", "\u0939\u093f\u0902\u0926\u0940 (Hindi)", "Hinglish"]

def _lang_key(lang: str) -> str:
    if "Hindi" in lang or "\u0939\u093f" in lang:
        return "hi"
    if lang == "Hinglish":
        return "hn"
    return "en"

# ---------------------------------------------------------------- intents
# Each intent: list of trigger keywords (English + romanised Hindi + Devanagari)
INTENT_KEYWORDS = {
    "greeting":      ["hello", "hi", "hey", "namaste", "namaskar", "hola",
                      "\u0928\u092e\u0938\u094d\u0924\u0947", "good morning", "good evening"],
    "thanks":        ["thanks", "thank you", "dhanyawad", "shukriya",
                      "\u0927\u0928\u094d\u092f\u0935\u093e\u0926", "\u0936\u0941\u0915\u094d\u0930\u093f\u092f\u093e"],
    "gate":          ["gate", "entry", "entrance", "dwar", "darwaza", "enter",
                      "\u0917\u0947\u091f", "\u092a\u094d\u0930\u0935\u0947\u0936",
                      "which gate", "kaun sa gate", "kis gate"],
    "food":          ["food", "khana", "khaana", "eat", "restaurant", "stall", "snack",
                      "burger", "pizza", "taco", "biryani", "hungry", "bhookh", "bhukh",
                      "\u0916\u093e\u0928\u093e", "\u092d\u094b\u091c\u0928", "veg", "vegan", "halal",
                      "chai", "coffee", "drink"],
    "washroom":      ["washroom", "toilet", "bathroom", "restroom", "loo",
                      "shauchalay", "sochalay", "\u0936\u094c\u091a\u093e\u0932\u092f",
                      "\u091f\u0949\u092f\u0932\u0947\u091f", "\u092c\u093e\u0925\u0930\u0942\u092e"],
    "first_aid":     ["first aid", "medical", "doctor", "injury", "hurt", "ambulance",
                      "medicine", "dawai", "ilaj", "\u0921\u0949\u0915\u094d\u091f\u0930",
                      "\u092a\u094d\u0930\u093e\u0925\u092e\u093f\u0915", "\u0907\u0932\u093e\u091c", "unwell", "sick"],
    "parking":       ["parking", "park", "car", "bike", "vehicle", "gaadi", "gadi",
                      "\u092a\u093e\u0930\u094d\u0915\u093f\u0902\u0917", "\u0917\u093e\u0921\u093c\u0940"],
    "emergency":     ["emergency", "exit", "evacuate", "fire", "danger", "help me",
                      "bahar", "nikas", "\u0906\u092a\u093e\u0924\u0915\u093e\u0932",
                      "\u0928\u093f\u0915\u093e\u0938", "\u092c\u093e\u0939\u0930", "police", "security"],
    "accessibility": ["wheelchair", "accessible", "accessibility", "divyang", "disabled",
                      "ramp", "viklang", "\u0926\u093f\u0935\u094d\u092f\u093e\u0902\u0917",
                      "\u0935\u094d\u0939\u0940\u0932\u091a\u0947\u092f\u0930", "sensory", "sign language",
                      "deaf", "blind"],
    "match":         ["match", "game", "final", "schedule", "kickoff", "kick off",
                      "timing", "kab hai", "\u092e\u0948\u091a", "\u092b\u093e\u0907\u0928\u0932",
                      "score", "team", "world cup", "semi"],
    "crowd":         ["crowd", "rush", "bheed", "bhid", "queue", "line", "busy",
                      "\u092d\u0940\u0921\u093c", "\u0932\u093e\u0907\u0928", "waiting", "kitni der"],
    "wifi":          ["wifi", "wi-fi", "internet", "network", "password",
                      "\u0935\u093e\u0908\u092b\u093e\u0908", "\u0907\u0902\u091f\u0930\u0928\u0947\u091f"],
    "water":         ["water", "paani", "pani", "\u092a\u093e\u0928\u0940", "refill",
                      "bottle", "thirsty", "pyaas", "\u092a\u094d\u092f\u093e\u0938"],
    "atm":           ["atm", "cash", "money", "paisa", "paise", "\u092a\u0948\u0938\u093e",
                      "\u090f\u091f\u0940\u090f\u092e", "bank"],
    "recycling":     ["recycle", "recycling", "dustbin", "bin", "garbage", "trash",
                      "kachra", "kuda", "\u0915\u091a\u0930\u093e", "\u0915\u0942\u0921\u093c\u093e",
                      "waste", "sustainability", "eco"],
    "prayer":        ["prayer", "pray", "namaz", "namaaz", "puja", "pooja", "mandir",
                      "masjid", "\u0928\u092e\u093e\u091c\u093c", "\u092a\u094d\u0930\u093e\u0930\u094d\u0925\u0928\u093e",
                      "\u092a\u0942\u091c\u093e", "worship"],
    "lost_found":    ["lost", "found", "kho", "khoya", "gum", "\u0916\u094b", "\u0917\u0941\u092e",
                      "missing", "lost and found", "wallet kho", "phone kho"],
    "merch":         ["merchandise", "jersey", "store", "shop", "souvenir", "tshirt",
                      "t-shirt", "kit", "\u091c\u0930\u094d\u0938\u0940", "\u0926\u0941\u0915\u093e\u0928",
                      "buy", "kharidna", "\u0916\u0930\u0940\u0926"],
    "help_desk":     ["helpline", "help desk", "contact", "phone number", "support",
                      "complaint", "shikayat", "\u0936\u093f\u0915\u093e\u092f\u0924",
                      "\u092e\u0926\u0926", "madad", "sahayta", "\u0938\u0939\u093e\u092f\u0924\u093e"],
}

INTENT_PRIORITY = [
    "emergency", "first_aid", "accessibility", "washroom", "gate", "food",
    "parking", "water", "crowd", "match", "wifi", "atm", "recycling", "prayer",
    "lost_found", "merch", "help_desk", "thanks", "greeting",
]


def detect_intent(query: str):
    """Return (best_intent, score). Keyword hit = 2 points, fuzzy hit = 1 point."""
    q = query.lower().strip()
    tokens = re.findall(r"[a-z\u0900-\u097f0-9']+", q)
    scores = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        s = 0
        for kw in keywords:
            if kw in q:
                s += 2
            else:
                for t in tokens:
                    if len(t) > 3 and difflib.SequenceMatcher(None, t, kw).ratio() > 0.84:
                        s += 1
                        break
        if s:
            scores[intent] = s
    if not scores:
        return None, 0
    best = max(scores.values())
    for intent in INTENT_PRIORITY:  # tie-break by priority
        if scores.get(intent) == best:
            return intent, best
    return max(scores, key=scores.get), best


def _extract_gate(query: str):
    """Find a specific gate mentioned in the query, e.g. 'gate 3' or 'gate C'."""
    q = query.lower()
    m = re.search(r"(?:gate|\u0917\u0947\u091f)\s*-?\s*([a-e1-5])", q)
    if not m:
        return None
    val = m.group(1).upper()
    if val.isdigit():
        val = "ABCDE"[int(val) - 1]
    for g in DATA["gates"]:
        if g["id"] == val:
            return g
    return None


def _zone_items(items, zone):
    same = [i for i in items if i.get("zone") == zone]
    return same if same else items

# ---------------------------------------------------------------- NLG templates
T = {
    "greeting": {
        "en": "Hello! \U0001F44B I am StadiumSaathi, your stadium assistant for the FIFA World Cup 2026. Ask me about gates, food, washrooms, parking, first aid, matches - anything!",
        "hi": "\u0928\u092e\u0938\u094d\u0924\u0947! \U0001F44B \u092e\u0948\u0902 StadiumSaathi \u0939\u0942\u0901 - FIFA World Cup 2026 \u0915\u0947 \u0932\u093f\u090f \u0906\u092a\u0915\u093e \u0938\u094d\u091f\u0947\u0921\u093f\u092f\u092e \u0938\u0939\u093e\u092f\u0915\u0964 \u0917\u0947\u091f, \u0916\u093e\u0928\u093e, \u0936\u094c\u091a\u093e\u0932\u092f, \u092a\u093e\u0930\u094d\u0915\u093f\u0902\u0917, \u092e\u0948\u091a - \u0915\u0941\u091b \u092d\u0940 \u092a\u0942\u091b\u093f\u090f!",
        "hn": "Namaste! \U0001F44B Main StadiumSaathi hoon - FIFA World Cup 2026 ke liye aapka stadium assistant. Gate, khana, washroom, parking, match - kuch bhi poochhiye!",
    },
    "thanks": {
        "en": "You're welcome! Enjoy the match! \u26BD",
        "hi": "\u0906\u092a\u0915\u093e \u0938\u094d\u0935\u093e\u0917\u0924 \u0939\u0948! \u092e\u0948\u091a \u0915\u093e \u0906\u0928\u0902\u0926 \u0932\u0940\u091c\u093f\u090f! \u26BD",
        "hn": "Welcome! Match enjoy kijiye! \u26BD",
    },
    "fallback": {
        "en": "Sorry, I didn't fully get that. Try asking: 'Where is Gate C?', 'Where can I eat?', 'Nearest washroom?', 'When is the final?'",
        "hi": "\u092e\u093e\u092b\u093c \u0915\u0940\u091c\u093f\u090f, \u092e\u0948\u0902 \u0938\u092e\u091d \u0928\u0939\u0940\u0902 \u092a\u093e\u092f\u093e\u0964 \u0910\u0938\u0947 \u092a\u0942\u091b\u093f\u090f: '\u0917\u0947\u091f C \u0915\u0939\u093e\u0901 \u0939\u0948?', '\u0916\u093e\u0928\u093e \u0915\u0939\u093e\u0901 \u092e\u093f\u0932\u0947\u0917\u093e?', '\u0928\u091c\u093c\u0926\u0940\u0915\u0940 \u0936\u094c\u091a\u093e\u0932\u092f?', '\u092b\u093e\u0907\u0928\u0932 \u0915\u092c \u0939\u0948?'",
        "hn": "Sorry, samajh nahi paya. Aise poochhiye: 'Gate C kahan hai?', 'Khana kahan milega?', 'Nearest washroom?', 'Final kab hai?'",
    },
}


def _fmt_list(lines):
    return "\n".join("\u2022 " + l for l in lines)


# ------------------------------------------------- intent -> answer builders
def _ans_gate(q, lk, zone):
    g = _extract_gate(q)
    if g:
        base = {
            "en": f"**Gate {g['id']}** is on the **{g['zone']}** side. It serves {g['serves']}. Landmark: {g['landmark']}.",
            "hi": f"**\u0917\u0947\u091f {g['id']}** **{g['zone']}** \u0915\u0940 \u0924\u0930\u092b \u0939\u0948\u0964 \u092f\u0939 {g['serves']} \u0915\u0947 \u0932\u093f\u090f \u0939\u0948\u0964 \u092a\u0939\u091a\u093e\u0928: {g['landmark']}\u0964",
            "hn": f"**Gate {g['id']}** **{g['zone']}** side par hai. Ye {g['serves']} ke liye hai. Landmark: {g['landmark']}.",
        }
        return base[lk]
    lines = [f"Gate {g['id']} - {g['zone']} ({g['serves']})" for g in DATA["gates"]]
    head = {
        "en": "Here are all the entry gates:\n",
        "hi": "\u0938\u092d\u0940 \u092a\u094d\u0930\u0935\u0947\u0936 \u0917\u0947\u091f \u092f\u0947 \u0939\u0948\u0902:\n",
        "hn": "Saare entry gates ye hain:\n",
    }
    tip = {
        "en": f"\n\nTip: your ticket section number tells your gate. You are currently near **{zone}**.",
        "hi": f"\n\n\u0938\u0941\u091d\u093e\u0935: \u091f\u093f\u0915\u091f \u092a\u0930 \u0932\u093f\u0916\u093e \u0938\u0947\u0915\u094d\u0936\u0928 \u0928\u0902\u092c\u0930 \u0906\u092a\u0915\u093e \u0917\u0947\u091f \u092c\u0924\u093e\u0924\u093e \u0939\u0948\u0964 \u0906\u092a \u0905\u092d\u0940 **{zone}** \u0915\u0947 \u092a\u093e\u0938 \u0939\u0948\u0902\u0964",
        "hn": f"\n\nTip: ticket ka section number aapka gate batata hai. Aap abhi **{zone}** ke paas hain.",
    }
    return head[lk] + _fmt_list(lines) + tip[lk]


def _ans_food(q, lk, zone):
    ql = q.lower()
    stalls = DATA["food_stalls"]
    filt = None
    for word, key in [("veg", "veg"), ("vegan", "vegan"), ("halal", "halal"),
                      ("pizza", "pizza"), ("burger", "burger"), ("taco", "mexican"),
                      ("indian", "indian"), ("coffee", "beverage"), ("chai", "beverage")]:
        if word in ql:
            filt = [s for s in stalls if key.lower() in (s["cuisine"] + s["name"]).lower()]
            if filt:
                stalls = filt
            break
    near = _zone_items(stalls, zone)
    lines = [f"**{s['name']}** ({s['cuisine']}) - {s['zone']}, {s['near']}" for s in near[:5]]
    head = {
        "en": f"Food options near **{zone}**:\n" if near != stalls or True else "",
        "hi": f"**{zone}** \u0915\u0947 \u092a\u093e\u0938 \u0916\u093e\u0928\u0947 \u0915\u0947 \u0935\u093f\u0915\u0932\u094d\u092a:\n",
        "hn": f"**{zone}** ke paas khane ke options:\n",
    }
    return head[lk] + _fmt_list(lines)


def _ans_washroom(q, lk, zone):
    near = _zone_items(DATA["washrooms"], zone)
    w = near[0]
    acc = {"en": " (wheelchair accessible)", "hi": " (\u0935\u094d\u0939\u0940\u0932\u091a\u0947\u092f\u0930 \u0938\u0941\u0932\u092d)", "hn": " (wheelchair accessible)"}
    extra = acc[lk] if w.get("accessible") else ""
    base = {
        "en": f"Nearest washroom to **{zone}**: {w['location']}{extra}.",
        "hi": f"**{zone}** \u0915\u0947 \u0938\u092c\u0938\u0947 \u092a\u093e\u0938 \u0936\u094c\u091a\u093e\u0932\u092f: {w['location']}{extra}\u0964",
        "hn": f"**{zone}** ke sabse paas washroom: {w['location']}{extra}.",
    }
    others = [f"{x['zone']}: {x['location']}" for x in DATA["washrooms"] if x is not w][:3]
    more = {"en": "\n\nOther options:\n", "hi": "\n\n\u0905\u0928\u094d\u092f \u0935\u093f\u0915\u0932\u094d\u092a:\n", "hn": "\n\nAur options:\n"}
    return base[lk] + more[lk] + _fmt_list(others)


def _ans_first_aid(q, lk, zone):
    near = _zone_items(DATA["first_aid"], zone)[0]
    base = {
        "en": f"\U0001F3E5 Nearest first aid: **{near['location']}** ({near['zone']}). For serious emergencies call the stadium helpline: {DATA['stadium']['helpline']}.",
        "hi": f"\U0001F3E5 \u0938\u092c\u0938\u0947 \u092a\u093e\u0938 \u092a\u094d\u0930\u093e\u0925\u092e\u093f\u0915 \u091a\u093f\u0915\u093f\u0924\u094d\u0938\u093e: **{near['location']}** ({near['zone']})\u0964 \u0917\u0902\u092d\u0940\u0930 \u0938\u094d\u0925\u093f\u0924\u093f \u092e\u0947\u0902 \u0939\u0947\u0932\u094d\u092a\u0932\u093e\u0907\u0928: {DATA['stadium']['helpline']}\u0964",
        "hn": f"\U0001F3E5 Sabse paas first aid: **{near['location']}** ({near['zone']}). Serious emergency mein helpline: {DATA['stadium']['helpline']}.",
    }
    return base[lk]


def _ans_parking(q, lk, zone):
    lines = [f"**{p['lot']}** - {p['for']} ({p['zone']} side, {p['capacity']} vehicles)" for p in DATA["parking"]]
    head = {"en": "Parking lots:\n", "hi": "\u092a\u093e\u0930\u094d\u0915\u093f\u0902\u0917 \u0938\u094d\u0925\u093e\u0928:\n", "hn": "Parking lots:\n"}
    return head[lk] + _fmt_list(lines)


def _ans_emergency(q, lk, zone):
    near = _zone_items(DATA["exits"], zone)
    lines = [f"**{e['id']}** - {e['note']} ({e['zone']})" for e in near]
    base = {
        "en": "\U0001F6A8 Stay calm. Nearest emergency exits:\n",
        "hi": "\U0001F6A8 \u0936\u093e\u0902\u0924 \u0930\u0939\u093f\u090f\u0964 \u0928\u091c\u093c\u0926\u0940\u0915\u0940 \u0906\u092a\u093e\u0924\u0915\u093e\u0932\u0940\u0928 \u0928\u093f\u0915\u093e\u0938:\n",
        "hn": "\U0001F6A8 Shaant rahiye. Nazdeeki emergency exits:\n",
    }
    tail = {
        "en": f"\n\nFollow the stewards' instructions. Helpline: {DATA['stadium']['helpline']}.",
        "hi": f"\n\n\u0938\u094d\u091f\u093e\u092b \u0915\u0947 \u0928\u093f\u0930\u094d\u0926\u0947\u0936\u094b\u0902 \u0915\u093e \u092a\u093e\u0932\u0928 \u0915\u0930\u0947\u0902\u0964 \u0939\u0947\u0932\u094d\u092a\u0932\u093e\u0907\u0928: {DATA['stadium']['helpline']}\u0964",
        "hn": f"\n\nStaff ke instructions follow karein. Helpline: {DATA['stadium']['helpline']}.",
    }
    return base[lk] + _fmt_list(lines) + tail[lk]


def _ans_accessibility(q, lk, zone):
    a = DATA["accessibility"]
    lines_en = [a["wheelchair_ramps"], a["assistance_desk"], a["accessible_parking"],
                a["sensory_room"], a["sign_language"]]
    head = {
        "en": "\u267F Accessibility services:\n",
        "hi": "\u267F \u0926\u093f\u0935\u094d\u092f\u093e\u0902\u0917\u091c\u0928 \u0938\u0941\u0935\u093f\u0927\u093e\u090f\u0901:\n",
        "hn": "\u267F Accessibility services:\n",
    }
    return head[lk] + _fmt_list(lines_en)


def _ans_match(q, lk, zone):
    lines = [f"**{m['match']}** - {m['teams']} | {m['date']}, {m['time']} | {m['status']}" for m in DATA["matches"]]
    head = {"en": "Match schedule at this stadium:\n",
            "hi": "\u0907\u0938 \u0938\u094d\u091f\u0947\u0921\u093f\u092f\u092e \u092e\u0947\u0902 \u092e\u0948\u091a:\n",
            "hn": "Is stadium ke matches:\n"}
    return head[lk] + _fmt_list(lines)


def _ans_crowd(q, lk, zone):
    zones = DATA["zones"]
    dens = {z: random.randint(35, 95) for z in zones}
    calm = min(dens, key=dens.get)
    lines = []
    for z, d in dens.items():
        icon = "\U0001F534" if d > 85 else ("\U0001F7E1" if d > 60 else "\U0001F7E2")
        lines.append(f"{icon} {z}: ~{d}% full")
    tail = {
        "en": f"\n\nLeast crowded right now: **{calm}**. (Live estimate - see the Crowd Dashboard tab for details.)",
        "hi": f"\n\n\u0905\u092d\u0940 \u0938\u092c\u0938\u0947 \u0915\u092e \u092d\u0940\u0921\u093c: **{calm}**\u0964 (\u0932\u093e\u0907\u0935 \u0905\u0928\u0941\u092e\u093e\u0928 - \u0935\u093f\u0938\u094d\u0924\u093e\u0930 \u0915\u0947 \u0932\u093f\u090f Crowd Dashboard \u0926\u0947\u0916\u0947\u0902\u0964)",
        "hn": f"\n\nAbhi sabse kam bheed: **{calm}**. (Live estimate - details ke liye Crowd Dashboard tab dekhein.)",
    }
    head = {"en": "Live crowd status:\n", "hi": "\u0932\u093e\u0907\u0935 \u092d\u0940\u0921\u093c \u0938\u094d\u0925\u093f\u0924\u093f:\n", "hn": "Live crowd status:\n"}
    return head[lk] + _fmt_list(lines) + tail[lk]


def _ans_wifi(q, lk, zone):
    w = DATA["stadium"]["wifi"]
    base = {
        "en": f"\U0001F4F6 Free WiFi network: **{w['network']}**. {w['password']}.",
        "hi": f"\U0001F4F6 \u092e\u0941\u092b\u093c\u094d\u0924 WiFi \u0928\u0947\u091f\u0935\u0930\u094d\u0915: **{w['network']}**\u0964 {w['password']}\u0964",
        "hn": f"\U0001F4F6 Free WiFi network: **{w['network']}**. {w['password']}.",
    }
    return base[lk]


def _ans_water(q, lk, zone):
    near = _zone_items(DATA["water_stations"], zone)[0]
    base = {
        "en": f"\U0001F4A7 Free water refill nearest to you: {near['location']} ({near['zone']}). Bring your own bottle - it keeps the stadium plastic-free!",
        "hi": f"\U0001F4A7 \u0906\u092a\u0915\u0947 \u0938\u092c\u0938\u0947 \u092a\u093e\u0938 \u092e\u0941\u092b\u093c\u094d\u0924 \u092a\u093e\u0928\u0940 \u0930\u093f\u092b\u093f\u0932: {near['location']} ({near['zone']})\u0964 \u0905\u092a\u0928\u0940 \u092c\u094b\u0924\u0932 \u0932\u093e\u090f\u0902 - \u092a\u094d\u0932\u093e\u0938\u094d\u091f\u093f\u0915 \u092e\u0941\u0915\u094d\u0924 \u0938\u094d\u091f\u0947\u0921\u093f\u092f\u092e!",
        "hn": f"\U0001F4A7 Aapke sabse paas free water refill: {near['location']} ({near['zone']}). Apni bottle laayein - plastic-free stadium!",
    }
    return base[lk]


def _ans_atm(q, lk, zone):
    lines = [f"{a['zone']} - {a['location']}" for a in DATA["atms"]]
    head = {"en": "\U0001F3E7 ATMs inside the stadium:\n", "hi": "\U0001F3E7 \u0938\u094d\u091f\u0947\u0921\u093f\u092f\u092e \u092e\u0947\u0902 ATM:\n", "hn": "\U0001F3E7 Stadium ke ATM:\n"}
    return head[lk] + _fmt_list(lines)


def _ans_recycling(q, lk, zone):
    near = _zone_items(DATA["recycling_points"], zone)[0]
    base = {
        "en": f"\u267B\uFE0F Nearest recycling point: {near['location']} ({near['zone']}). Please separate plastic, paper and food waste - help us make World Cup 2026 the greenest ever!",
        "hi": f"\u267B\uFE0F \u0928\u091c\u093c\u0926\u0940\u0915\u0940 \u0930\u0940\u0938\u093e\u0907\u0915\u0932\u093f\u0902\u0917 \u092a\u0949\u0907\u0902\u091f: {near['location']} ({near['zone']})\u0964 \u092a\u094d\u0932\u093e\u0938\u094d\u091f\u093f\u0915, \u0915\u093e\u0917\u091c\u093c \u0914\u0930 \u0916\u093e\u0928\u093e \u0905\u0932\u0917 \u0921\u093e\u0932\u0947\u0902!",
        "hn": f"\u267B\uFE0F Nazdeeki recycling point: {near['location']} ({near['zone']}). Plastic, paper aur food waste alag daalein!",
    }
    return base[lk]


def _ans_prayer(q, lk, zone):
    p = DATA["other"]["prayer_room"]
    base = {"en": f"\U0001F64F Multi-faith prayer room: {p}.",
            "hi": f"\U0001F64F \u092a\u094d\u0930\u093e\u0930\u094d\u0925\u0928\u093e \u0915\u0915\u094d\u0937: {p}\u0964",
            "hn": f"\U0001F64F Prayer room: {p}."}
    return base[lk]


def _ans_lost(q, lk, zone):
    l = DATA["other"]["lost_and_found"]
    base = {
        "en": f"For lost items, go to the **Lost & Found**: {l}. Carry your ticket/ID for verification.",
        "hi": f"\u0916\u094b\u092f\u093e \u0938\u093e\u092e\u093e\u0928 \u0915\u0947 \u0932\u093f\u090f **Lost & Found** \u091c\u093e\u090f\u0902: {l}\u0964 \u091f\u093f\u0915\u091f/ID \u0938\u093e\u0925 \u0930\u0916\u0947\u0902\u0964",
        "hn": f"Khoya samaan ke liye **Lost & Found** jaayein: {l}. Ticket/ID saath rakhein.",
    }
    return base[lk]


def _ans_merch(q, lk, zone):
    lines = [f"**{m['name']}** - {m['zone']}, {m['near']}" for m in DATA["other"]["merchandise"]]
    head = {"en": "\U0001F455 Official merchandise stores:\n", "hi": "\U0001F455 \u0906\u0927\u093f\u0915\u093e\u0930\u093f\u0915 \u092e\u0930\u094d\u091a\u0947\u0902\u0921\u093e\u0907\u091c\u093c \u0938\u094d\u091f\u094b\u0930:\n", "hn": "\U0001F455 Official merchandise stores:\n"}
    return head[lk] + _fmt_list(lines)


def _ans_help_desk(q, lk, zone):
    base = {
        "en": f"\u2139\uFE0F Help Desk: Gate B, East Stand. Helpline: {DATA['stadium']['helpline']}.",
        "hi": f"\u2139\uFE0F \u0939\u0947\u0932\u094d\u092a \u0921\u0947\u0938\u094d\u0915: \u0917\u0947\u091f B, East Stand\u0964 \u0939\u0947\u0932\u094d\u092a\u0932\u093e\u0907\u0928: {DATA['stadium']['helpline']}\u0964",
        "hn": f"\u2139\uFE0F Help Desk: Gate B, East Stand. Helpline: {DATA['stadium']['helpline']}.",
    }
    return base[lk]


_BUILDERS = {
    "gate": _ans_gate, "food": _ans_food, "washroom": _ans_washroom,
    "first_aid": _ans_first_aid, "parking": _ans_parking, "emergency": _ans_emergency,
    "accessibility": _ans_accessibility, "match": _ans_match, "crowd": _ans_crowd,
    "wifi": _ans_wifi, "water": _ans_water, "atm": _ans_atm,
    "recycling": _ans_recycling, "prayer": _ans_prayer, "lost_found": _ans_lost,
    "merch": _ans_merch, "help_desk": _ans_help_desk,
}


def answer(query: str, lang: str = "English", user_zone: str = "North Stand"):
    """Main entry: returns (reply_text, detected_intent)."""
    lk = _lang_key(lang)
    intent, score = detect_intent(query)
    if intent in ("greeting", "thanks"):
        return T[intent][lk], intent
    if intent in _BUILDERS:
        return _BUILDERS[intent](query, lk, user_zone), intent
    return T["fallback"][lk], "fallback"


def quick_suggestions(lang: str = "English"):
    lk = _lang_key(lang)
    s = {
        "en": ["Where is Gate C?", "Where can I eat?", "Nearest washroom?", "When is the final?"],
        "hi": ["\u0917\u0947\u091f C \u0915\u0939\u093e\u0901 \u0939\u0948?", "\u0916\u093e\u0928\u093e \u0915\u0939\u093e\u0901 \u092e\u093f\u0932\u0947\u0917\u093e?", "\u0928\u091c\u093c\u0926\u0940\u0915\u0940 \u0936\u094c\u091a\u093e\u0932\u092f?", "\u092b\u093e\u0907\u0928\u0932 \u0915\u092c \u0939\u0948?"],
        "hn": ["Gate C kahan hai?", "Khana kahan milega?", "Nearest washroom?", "Final kab hai?"],
    }
    return s[lk]


if __name__ == "__main__":
    # quick self-test
    tests = ["gate 3 kahan hai", "khana kahan milega", "\u0936\u094c\u091a\u093e\u0932\u092f \u0915\u0939\u093e\u0902 \u0939\u0948",
             "wheelchair help", "final kab hai", "wifi password", "emergency exit",
             "paani", "atm", "mera phone kho gaya", "hello", "random gibberish xyz"]
    for t in tests:
        r, i = answer(t, "Hinglish", "South Stand")
        print(f"[{i}] {t}\n{r}\n{'-'*60}")
