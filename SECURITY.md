# Security Policy — StadiumSaathi

## Threat model & design decisions

- **No personal data**: the app collects and stores no user data. Chat history
  lives only in the browser session and is wiped on reload.
- **No secrets**: there are no API keys, tokens or credentials anywhere in the
  codebase — nothing to leak.
- **Input hardening**: all user input passes through `assistant.sanitize()`
  (control-character stripping, whitespace normalisation, 300-char limit) and
  the chat input itself enforces `max_chars=300`.
- **Offline runtime**: the assistant makes **zero network calls**, eliminating
  SSRF / data-exfiltration surface at runtime.
- **Safe rendering**: user text is rendered via Streamlit markdown (HTML
  escaped by default); `unsafe_allow_html` is used only for static,
  developer-authored theming CSS — never for user content.
- **Fail-safe data loading**: `stadium_data.json` is validated on startup;
  malformed data raises a clean error without leaking internal paths.
- **Pinned entrypoint**: minimal dependency surface (streamlit, pandas, numpy).

## Reporting

Found an issue? Open a GitHub issue with the `security` label.
