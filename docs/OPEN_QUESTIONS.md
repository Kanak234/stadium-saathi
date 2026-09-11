# Open Questions — StadiumSaathi

## Tracking Status
All core architectural, security, accessibility, and packaging requirements for Tier-2 production hardening (C1–C9) have been resolved. The items below document optional extensions and operational choices for venue deployment.

---

### Q1: Physical Turnstile Telemetry Ingestion (Optional Production Extension)
- **Question:** How should the live crowd control room ingest real physical turnstile data when deployed on-premise at the venue?
- **Status:** RESOLVED for v1.0.0 (offline demo uses deterministic pseudorandom simulation via `numpy.random.default_rng(seed)`).
- **Recommendation for v2.0.0:** Implement an optional local Unix socket or MQTT subscriber client when running on venue infrastructure, falling back seamlessly to simulation mode if the socket is disconnected.

---

### Q2: Additional Regional Language Expansion
- **Question:** What additional languages should be introduced for international attendees beyond English, Hindi, and Hinglish?
- **Status:** RESOLVED for v1.0.0 (FIFA 2026 tri-state area and South Asian diaspora focus on EN, HI, HN).
- **Recommendation for v2.0.0:** Spanish (ES) is the highest-priority subsequent candidate for the New York / New Jersey venue demographic.
