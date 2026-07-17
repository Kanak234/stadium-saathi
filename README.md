# 🏟️ StadiumSaathi — Smart Stadium & Tournament Operations Assistant

**PromptWars — [Challenge 4] Smart Stadiums & Tournament Operations**
**Event context: FIFA World Cup 2026 · Demo venue: New York New Jersey Stadium (MetLife)**

StadiumSaathi is an AI-powered assistant that helps **fans, organizers, volunteers and venue staff** during FIFA World Cup 2026 — navigation, crowd management, accessibility, multilingual help, sustainability and real-time decision support — in one Streamlit app.

> ⚡ Works **100% offline** at runtime: no external API keys, no database, no internet dependency. Designed for crowded stadiums where mobile networks get congested.

---

## 🎯 Problem assessment

**Who hurts, and how:** 82,500 fans in one venue means jammed networks, long gate queues, lost visitors, language barriers (World Cup fans speak dozens of languages), overloaded staff, and accessibility gaps for disabled fans. Organizers meanwhile need second-by-second situational awareness to prevent crushes and bottlenecks.

**Our approach:** one lightweight app serving **two user groups** — a trilingual self-service assistant for fans, and a live decision-support control room for organizers — built to survive the exact environment it targets (offline-first, low compute, zero cost).

**Impact metrics (design targets):** answer any facility question in < 1 s with zero network; cut average gate-choice mistakes via zone-aware sorting; convert raw crowd numbers into concrete staff actions automatically.

## ✨ Features → Challenge mapping

| Challenge requirement | How StadiumSaathi delivers |
|---|---|
| **Navigation** | Facility finder (gates, food, washrooms, parking, ATMs, exits) sorted by the fan's current zone + chat-based directions |
| **Crowd management** | Live crowd control room: zone occupancy, gate queues, red/amber/green alerts |
| **Real-time decision support** | Auto-generated action recommendations (redirect crowds, open gate lanes, deploy stewards) from live thresholds |
| **Multilingual assistance** | Trilingual assistant — **English, हिंदी (Devanagari), Hinglish** — understands mixed queries like *"gate 3 kahan hai"* |
| **Accessibility** | Wheelchair info, sensory room, sign-language desk **plus** in-app high-contrast mode, large-text mode, chart data-table alternatives |
| **Sustainability** | Free water-refill points, recycling-bin locator, shuttle guidance |
| **Transportation** | Parking lots, shuttle/bus lot, metro-side gate info |

## 🏗️ Architecture

```
┌─────────────────────────── Streamlit UI (app.py) ───────────────────────────┐
│  💬 Chat   🗺️ Navigate   👥 Crowd Room   📅 Matches   ♿ Access/Green      │
└──────────────┬──────────────────────────────┬───────────────────────────────┘
               │ sanitized query              │ cached facility tables
┌──────────────▼──────────────┐   ┌───────────▼───────────────┐
│  Offline AI engine          │   │  Decision-support rules   │
│  (assistant.py)             │   │  thresholds → actions     │
│  sanitize → intent (cached) │   └───────────┬───────────────┘
│  → entities → trilingual NLG│               │
└──────────────┬──────────────┘   ┌───────────▼───────────────┐
               └─────────────────►│  stadium_data.json (KB)   │
                                  └───────────────────────────┘
```

## 🧠 How the AI works (offline)

1. **Sanitization** — control-char stripping, whitespace normalisation, 300-char cap.
2. **Intent detection** — two-pass matcher over 20 intents: fast token/phrase pass first, fuzzy (`difflib`) fallback only when needed; memoised with `lru_cache(512)`.
3. **Entity extraction** — precompiled regex (e.g. "gate 3" / "गेट 2" → Gate C/B).
4. **Response generation** — template-based NLG filled live from the knowledge base and the user's zone, in the user's language.
5. **Decision support** — threshold rules convert live crowd numbers into plain-language operator actions.

Generative AI tools were used end-to-end to **design, build, test and deploy** this solution (per event rules: *"YOU CAN USE ANY AI TOOL TO BUILD & DEPLOY"*). The runtime is offline-first for reliability inside a packed stadium; a cloud LLM can be plugged into `assistant.answer()` later without UI changes.

## ⚡ Performance & efficiency

- Token-set intent matching (word-boundary safe) with fuzzy matching **only as fallback** — typical query answered in well under a millisecond.
- `lru_cache(512)` on intent detection: repeated questions are O(1).
- `st.cache_data` on facility tables: dataframes built once per facility, not per rerun.
- Precompiled regexes; zero network I/O; three small dependencies only.

## ✅ Testing

**100 automated tests** (pytest) across two suites, running in < 0.1 s:

- `test_assistant.py` — sanitization, all 20 intents in 3 languages, typo/fuzzy handling, gate entity extraction (letters, numbers, Devanagari), zone routing, fallbacks, invalid-zone safety.
- `test_stadium_data.py` — knowledge-base integrity: required sections, valid zones everywhere, water coverage per zone, parseable match dates.

```bash
pip install -r requirements.txt
pytest -q        # 100 passed
```

Continuous integration: GitHub Actions runs the full suite on every push (`.github/workflows/tests.yml`).

## 🔒 Security

No personal data collected · no secrets in code · hardened input pipeline · zero runtime network calls · HTML-escaped rendering of user text · validated data loading. Full details in [SECURITY.md](SECURITY.md).

## ♿ Accessibility (app itself)

High-contrast mode and large-text mode (sidebar toggles) · descriptive labels and help tooltips on every control · screen-reader-friendly data tables as alternatives to charts · keyboard-navigable Streamlit widgets · emoji used alongside text, never alone.

## 📁 Project structure

```
stadium-saathi/
├── app.py                     # Streamlit UI (5 tabs)
├── assistant.py               # Offline AI engine (typed, documented)
├── stadium_data.json          # Static stadium knowledge base
├── test_assistant.py          # 90+ engine tests
├── test_stadium_data.py       # Data-integrity tests
├── .github/workflows/tests.yml  # CI: pytest on every push
├── SECURITY.md                # Threat model & policies
├── requirements.txt
└── README.md
```

## ▶️ Run locally

```bash
pip install -r requirements.txt
streamlit run app.py     # open http://localhost:8501
```

## 🚀 Deploy free on Streamlit Community Cloud

1. Push all files to the **root** of a public GitHub repo.
2. Go to **https://share.streamlit.io** → sign in with GitHub.
3. **Create app** → select repo, branch `main`, main file **`app.py`** → **Deploy**.
4. Share the `https://<app>.streamlit.app` link.

## 🔮 Future scope

Real sensor/turnstile integration for the crowd room · pluggable cloud LLM for open-ended queries · per-stadium JSON packs (16 World Cup venues) · voice input/output for hands-free accessibility.

## 👤 Team

**Kanak Prabhakar** — BCA, AISECT University, Hazaribagh
PromptWars (Hack2Skill) — Challenge 4 submission

---

*StadiumSaathi = Stadium + Saathi (साथी, "companion") — your companion inside the stadium.*
