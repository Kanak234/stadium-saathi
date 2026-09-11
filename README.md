# 🏟️ StadiumSaathi — Smart Stadium & Tournament Operations Assistant

[![CI](https://github.com/Kanak234/stadium-saathi/actions/workflows/ci.yml/badge.svg)](https://github.com/Kanak234/stadium-saathi/actions/workflows/ci.yml)
[![CodeQL](https://github.com/Kanak234/stadium-saathi/actions/workflows/codeql.yml/badge.svg)](https://github.com/Kanak234/stadium-saathi/actions/workflows/codeql.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](pyproject.toml)
[![Coverage](https://img.shields.io/badge/coverage-99%25-brightgreen.svg)](pyproject.toml)

**PromptWars — [Challenge 4] Smart Stadiums & Tournament Operations**<br>
**Event context: FIFA World Cup 2026 · Demo venue: New York New Jersey Stadium (MetLife)**

StadiumSaathi is an enterprise-hardened AI assistant that helps **fans, organizers, volunteers and venue staff** during FIFA World Cup 2026 — navigation, crowd management, accessibility, multilingual help, sustainability and real-time decision support — through both a Streamlit web application and a headless terminal CLI.

> ⚡ Works **100% offline** at runtime: no external API keys, no database, no internet dependency. Designed for crowded stadiums where mobile networks get congested.

---

## 🎯 Problem Assessment

**Who hurts, and how:** 82,500 fans in one venue means jammed networks, long gate queues, lost visitors, language barriers (World Cup fans speak dozens of languages), overloaded staff, and accessibility gaps for disabled fans. Organizers meanwhile need second-by-second situational awareness to prevent crushes and bottlenecks.

**Our approach:** One lightweight platform serving **two user groups** — a trilingual self-service assistant for fans, and a live decision-support control room for organizers — built to survive the exact environment it targets (offline-first, low compute, zero cost).

**Impact metrics (design targets):** Answer any facility question in < 1 ms with zero network; cut average gate-choice mistakes via zone-aware sorting; convert raw crowd numbers into concrete staff actions automatically.

---

## ✨ Features → Challenge Mapping

| Challenge requirement | How StadiumSaathi delivers |
|---|---|
| **Navigation** | Facility finder (gates, food, washrooms, parking, ATMs, exits) sorted by the fan's current zone + chat-based directions |
| **Crowd management** | Live crowd control room: zone occupancy, gate queues, red/amber/green alerts |
| **Real-time decision support** | Auto-generated action recommendations (redirect crowds, open gate lanes, deploy stewards) from live thresholds |
| **Multilingual assistance** | Trilingual assistant — **English, हिंदी (Devanagari), Hinglish** — understands mixed queries like *"gate 3 kahan hai"* |
| **Accessibility** | Wheelchair info, sensory room, sign-language desk **plus** in-app high-contrast mode, large-text mode, chart data-table alternatives |
| **Sustainability** | Free water-refill points, recycling-bin locator, shuttle guidance |
| **Transportation** | Parking lots, shuttle/bus lot, metro-side gate info |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           User Interface Surfaces                           │
│     Streamlit Web App (app.py)       │    Headless Terminal CLI (assistant) │
└──────────────────────┬────────────────────────────────┬─────────────────────┘
                       │ sanitized input query          │ cached tables
        ┌──────────────▼──────────────┐   ┌─────────────▼─────────────┐
        │  Offline AI Engine          │   │  Decision Support Rules   │
        │  (assistant.py)             │   │  thresholds → actions     │
        │  sanitize → intent (cached) │   └─────────────┬─────────────┘
        │  → entities → trilingual NLG│                 │
        └──────────────┬──────────────┘   ┌─────────────▼─────────────┐
                       └─────────────────►│  stadium_data.json (KB)   │
                                          └───────────────────────────┘
```

---

## 🧠 How the AI Works (Offline)

1. **Sanitization** — control-char stripping, whitespace normalisation, 300-char cap.
2. **Intent detection** — two-pass matcher over 20 intents: fast token/phrase pass first, fuzzy (`difflib`) fallback only when needed; memoised with `lru_cache(512)`.
3. **Entity extraction** — precompiled regex (e.g. "gate 3" / "गेट 2" → Gate C/B).
4. **Response generation** — template-based NLG filled live from the knowledge base and the user's zone, in the user's language.
5. **Decision support** — threshold rules convert live crowd numbers into plain-language operator actions.

---

## 💻 CLI Usage

StadiumSaathi includes a native console CLI entry point `stadium-saathi`:

```bash
# Install package
pip install .

# Ask query in English
stadium-saathi --query "where is gate 3"

# Ask query in Hindi (Devanagari)
stadium-saathi --query "गेट 2 कहाँ है" --lang "हिंदी (Hindi)"

# Query with zone proximity filter
stadium-saathi --query "where can i eat" --zone "West Stand"

# Inspect version
stadium-saathi --version
```

---

## ▶️ Run Locally & Containerization

### Run with Streamlit

```bash
pip install -r requirements.txt
streamlit run app.py     # open http://localhost:8501
```

### Run with Docker (Multi-Stage, Non-Root UID 10001)

```bash
docker build -t stadium-saathi .
docker run -d -p 8501:8501 --name stadium-saathi stadium-saathi
curl http://localhost:8501/_stcore/health
```

---

## ✅ Testing & Verification

**114 automated tests** with **99.04%** statement coverage with zero synthetic mocks:

- `test_assistant.py` — sanitization, all 20 intents in 3 languages, typo/fuzzy handling, gate entity extraction, zone routing, CLI entry points, data loading error handling, food cuisine filters, fallbacks, invalid-zone safety.
- `test_stadium_data.py` — knowledge-base integrity: required sections, valid zones everywhere, water coverage per zone, parseable match dates.

```bash
pip install -r requirements.txt
pytest -v --cov=assistant --cov-fail-under=85
```

---

## 🔒 Security

- **Zero runtime network calls:** Eliminates SSRF, remote code execution, and data exfiltration vectors.
- **No PII or secrets:** In-memory session state wiped on tab close; zero credentials stored in codebase.
- **Sanitized inputs:** Hard 300-char boundary prevents algorithmic denial of service.
- **Unprivileged container:** Non-root system user `appuser` (UID 10001).
- Full security policy and vulnerability reporting instructions are detailed in [SECURITY.md](SECURITY.md).

---

## 📁 Project Structure

```
stadium-saathi/
├── app.py                            # Streamlit Web UI (5 tabs)
├── assistant.py                      # Offline AI engine & CLI entry point
├── stadium_data.json                 # Static stadium knowledge base
├── Dockerfile                        # Multi-stage unprivileged Docker build (UID 10001)
├── .dockerignore                     # Docker build exclusion rules
├── .gitignore                        # Git exclusion rules
├── MANIFEST.in                       # Source distribution manifest
├── pyproject.toml                    # PEP 621 packaging & tool configuration
├── requirements.txt                  # Minimal runtime dependencies
├── test_assistant.py                 # Engine & CLI test suite
├── test_stadium_data.py              # Data-integrity test suite
├── SECURITY.md                       # Security policy & threat model
├── CHANGELOG.md                      # Release changelog
├── docs/                             # Context-first documentation
│   ├── PRD.md                        # Product Requirements Document
│   ├── TRD.md                        # Technical Requirements Document
│   ├── UIUX_BRIEF.md                 # UI/UX Design Brief
│   ├── OPEN_QUESTIONS.md             # Open questions & resolution log
│   └── IMPLEMENTATION_PLAN.md        # Hardening implementation plan
└── .github/                          # CI/CD & Automation workflows
    ├── dependabot.yml                # Dependabot weekly updates
    └── workflows/
        ├── ci.yml                    # Matrix tests (Python 3.10-3.13) + coverage gate
        ├── codeql.yml                # GitHub CodeQL SAST scanning
        ├── release.yml               # Release automation with SHA256 checksums
        └── repository-guard.yml      # Syntax-only repository guard
```

---

## 👤 Team

**Kanak Prabhakar** — BCA, AISECT University, Hazaribagh<br>
PromptWars (Hack2Skill) — Challenge 4 submission

---

*StadiumSaathi = Stadium + Saathi (साथी, "companion") — your companion inside the stadium.*
