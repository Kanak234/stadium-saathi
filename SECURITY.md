# Security Policy — StadiumSaathi

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## Threat Model & Security Controls

StadiumSaathi is architected under an offline-first, zero-trust design for high-density public event deployments:

1. **Zero Runtime Network Connectivity & Data Privacy:**
   - The assistant and UI execute 100% offline with zero runtime external API calls, zero database connections, and zero telemetry collection.
   - User chat interactions exist exclusively in ephemeral in-memory session state and are completely destroyed when the browser session terminates.
   - Zero Personally Identifiable Information (PII) is gathered, processed, or persisted.

2. **No Embedded Secrets or Credentials:**
   - Zero hardcoded credentials, tokens, or encryption keys exist in the codebase.

3. **Rigorous Input Sanitization & Denial-of-Service Defense:**
   - All inbound queries pass through `assistant.sanitize()` before lexical or regex parsing.
   - Non-printable ASCII control characters (`\x00-\x1f\x7f`) are stripped.
   - Redundant whitespace is collapsed.
   - Strict length ceiling (`MAX_QUERY_LEN = 300`) bounds regex search and memoized cache lookups to O(1) in input size, preventing computational algorithmic complexity attacks.

4. **Context-Aware Safe HTML/Markdown Rendering:**
   - Attendee input strings are processed through standard Streamlit markdown components where user inputs are escaped by default.
   - `unsafe_allow_html` is restricted exclusively to static, developer-controlled CSS theming rules for accessibility and never interpolates user queries.

5. **Path Traversal & Knowledge Base Integrity:**
   - `stadium_data.json` undergoes structural schema validation upon startup.
   - Failure conditions mask internal filesystem paths to prevent directory traversal disclosure.

6. **Container Isolation & Non-Root Execution:**
   - The production container image enforces unprivileged execution under `appuser` (UID 10001, GID 10001) without sudo or root capabilities.

---

## Reporting a Vulnerability

If you discover a security vulnerability in StadiumSaathi, please report it responsibly:

1. Do NOT disclose the vulnerability publicly in an issue or forum.
2. Submit details via a private GitHub Security Advisory or email `kanak234@users.noreply.github.com`.
3. Provide a detailed description of the vulnerability, reproduction steps, and potential impact.
4. You will receive an initial response within 48 hours, followed by patch timeline updates.
