# Technical Requirements Document (TRD) — StadiumSaathi

## 1. Technical Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Surfaces                        │
│   Streamlit Web App (app.py)  │  Terminal CLI (assistant.py) │
└────────────┬───────────────────────────────┬────────────┘
             │                               │
             ▼                               ▼
┌─────────────────────────────────────────────────────────┐
│              Input Sanitization & Guardrails            │
│         - Strip non-printable / control ASCII chars     │
│         - Collapse redundant whitespace                 │
│         - Bound input length (MAX_QUERY_LEN = 300)      │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│                Two-Pass Intent Classifier               │
│  Pass 1: Token-set keyword intersection (O(1) tokens)   │
│  Pass 2: Bounded fuzzy sequence matching (difflib)      │
│  Memoization: functools.lru_cache(maxsize=512)          │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│            Entity Extraction & Response Builders        │
│  - Gate extraction (Letters A-E, Digits 1-5, Devanagari)│
│  - Cuisine and dietary filters (veg, vegan, halal)      │
│  - Proximity-based zone item sorting                    │
│  - Trilingual localized NLG templates (EN, HI, HN)      │
└────────────┬───────────────────────────────┬────────────┘
             │                               │
             └───────────────┬───────────────┘
                             ▼
┌─────────────────────────────────────────────────────────┐
│           Knowledge Base (stadium_data.json)            │
│  - Stadium metadata, gates, zones, amenities, matches   │
└─────────────────────────────────────────────────────────┘
```

## 2. Technology Stack & Runtime Dependencies
- **Python Version:** Python >= 3.10 (tested and verified across 3.10, 3.11, 3.12, 3.13).
- **Core Dependencies:**
  - `streamlit>=1.36.0`: Web application framework and dashboard interface.
  - `pandas>=2.0.0`: Tabular data manipulation for crowd statistics and amenities tables.
  - `numpy>=1.24.0`: Numerical calculations for queue estimates and load factors.
- **Development & Verification Dependencies:**
  - `pytest>=7.0.0`: Automated test execution.
  - `pytest-cov>=4.0.0`: Statement and branch coverage measurement.
  - `ruff>=0.4.0`: Static code analysis and linting.
  - `build`: Distribution package creation.

## 3. Subsystem Specifications

### 3.1 NLU Intent Detection Engine
- **Vocabulary:** 20 canonical intents (`gate`, `food`, `washroom`, `first_aid`, `parking`, `emergency`, `accessibility`, `match`, `crowd`, `wifi`, `water`, `atm`, `recycling`, `prayer`, `lost_found`, `merch`, `help_desk`, `greeting`, `thanks`, `fallback`).
- **Priority Resolution:** Tie-breaking ordered by safety-critical priority (`emergency` > `first_aid` > `gate` > `washroom` > `water`).
- **Devanagari Normalization:** Direct Unicode phrase matching without phonetic loss.

### 3.2 Knowledge Base Validation
- `_load_data(path)` validates the schema of `stadium_data.json` on startup.
- Requires keys: `stadium`, `zones`, `gates`, `food_stalls`, `washrooms`.
- Missing files or JSON decode errors raise a sanitized `RuntimeError("Stadium knowledge base could not be loaded.")` preventing internal path disclosure.

### 3.3 CLI Interface (`assistant:cli`)
- Headless invocation: `stadium-saathi --query "where is gate 3" --lang English --zone "East Stand"`
- Outputs intent tag and markdown response string.
- Returns exit code 0 on success.

## 4. Packaging, Containerization & CI/CD
- **Package Manifest:** `pyproject.toml` with `setuptools.build_meta`, `py-modules = ["app", "assistant"]`, and `package-data` ensuring `stadium_data.json` is packaged inside wheels and source distributions.
- **Docker Image:** Multi-stage build based on `python:3.12-slim`, running as non-root user `appuser` (UID 10001), healthcheck via `curl` on `/_stcore/health`.
- **CI Matrix:** GitHub Actions validating across Python 3.10, 3.11, 3.12, and 3.13; compileall syntax check, Ruff linting, test coverage gate (`--cov-fail-under=85`).
- **Security & Integrity:** GitHub CodeQL SAST workflow, Repository Guard, and Dependabot.
