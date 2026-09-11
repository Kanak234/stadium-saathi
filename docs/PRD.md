# Product Requirements Document (PRD) — StadiumSaathi

## 1. Product Overview
StadiumSaathi is an offline-first, multilingual tournament operations assistant and fan self-service platform designed for large-scale sporting events, specifically modeled for FIFA World Cup 2026 at MetLife Stadium (New York New Jersey Stadium). It delivers second-by-second situational awareness, intelligent crowd management recommendations, and trilingual guidance (English, Hindi, Hinglish) with zero network dependency.

## 2. Problem Statement
High-density sporting venues (80,000+ attendees) consistently suffer from cellular network congestion, overloaded venue staff, attendee disorientation, gate bottlenecks, and accessibility shortcomings. Traditional event apps fail completely when mobile networks jam, leaving fans stranded and venue managers without situational telemetry.

StadiumSaathi solves this problem by executing 100% locally at runtime:
1. Fans access instant wayfinding, accessibility accommodations, match schedules, and facility locators without cellular data.
2. Operators receive real-time crowd density alerts, gate redirection guidance, and threshold-driven dispatch suggestions.
3. Natural language assistance bridges linguistic barriers with trilingual NLU supporting English, Hindi (Devanagari), and colloquial Hinglish.

## 3. Goals and Non-Goals

### Goals
- **100% Offline Runtime:** Zero external API keys, zero cloud databases, zero runtime network calls.
- **Trilingual NLU & NLG:** Seamlessly process queries in English, Hindi, and mixed Hinglish with sub-millisecond keyword and fuzzy matching.
- **Zone-Aware Facility Locator:** Automatically sort stadium amenities (gates, water refill stations, first aid, washrooms, food stalls) by proximity to attendee seating zones.
- **Real-Time Operator Decision Support:** Translate crowd density measurements into actionable staff interventions (gate lane expansions, corridor redirections, steward dispatches).
- **Accessibility by Design:** Full support for wheelchair ramps, sensory decompression rooms, sign-language stations, along with high-contrast and large-text display modes.
- **Enterprise Hardening (C1–C9):** Standard PEP 621 packaging, multi-stage unprivileged containerization (UID 10001), automated CI matrix testing across Python 3.10–3.13, CodeQL security scanning, and >90% test coverage with zero synthetic mocks.

### Non-Goals
- **Live Ticket Transaction Processing:** StadiumSaathi guides fans to physical amenities and provides operational intelligence; it does not process financial transactions or seat ticketing purchases.
- **Facial Recognition / Biometric Surveillance:** StadiumSaathi respects complete user privacy and collects zero personal identifiable information (PII).

## 4. Target Users
- **Stadium Attendees & Fans:** Seeking rapid, offline wayfinding to gates, restrooms, water refill stations, and emergency exits.
- **Venue Operations & Event Control Room:** Monitoring zone congestion, gate queue lengths, and executing automated crowd dispatch protocols.
- **Volunteers & Stewards:** Field personnel requiring immediate answers to attendee inquiries across language barriers.

## 5. Functional Requirements

### FR-1: Natural Language Chat Assistant (`assistant.py`)
- Input sanitization: control character stripping, whitespace normalization, strict 300-character ceiling.
- Two-pass intent classification across 20 intents (fast keyword matching followed by bounded fuzzy matching), memoized via `lru_cache(512)`.
- Zone-prioritized entity extraction and template-driven NLG in English, Hindi, and Hinglish.
- Localized quick suggestion chips for common tournament inquiries.

### FR-2: Wayfinding & Amenities Knowledge Base (`stadium_data.json`)
- Comprehensive stadium directory covering MetLife Stadium: 5 stadium gates (A–E), 4 primary seating zones (North, South, East, West), food stalls with cuisine tags, accessibility services, and emergency protocols.
- Deterministic data validation on application initialization with sanitized exception masking.

### FR-3: Operational Decision Support & Crowd Control
- Live occupancy simulation and threshold rule evaluation converting raw metrics into prioritized operator recommendations.
- Visual alerts categorized into Normal (Green), Warning (Amber), and Critical (Red).

### FR-4: CLI & Web Interfaces
- Dual execution surface: headless CLI command `stadium-saathi --query "<text>"` for instant terminal responses and Streamlit dashboard (`streamlit run app.py`) for visual operations.

## 6. Acceptance Criteria
1. Clean PEP 621 `pyproject.toml` with console script entry point `stadium-saathi = "assistant:cli"`.
2. Multi-stage unprivileged `Dockerfile` (`appuser` UID 10001) with embedded healthcheck.
3. Test suite with >= 90% statement coverage on core assistant engine with zero synthetic mocks.
4. Passing CI matrix across Python 3.10, 3.11, 3.12, and 3.13.
5. CodeQL static analysis and Repository Guard passing without warnings.
6. Comprehensive `SECURITY.md`, `CHANGELOG.md`, and enriched `README.md`.
