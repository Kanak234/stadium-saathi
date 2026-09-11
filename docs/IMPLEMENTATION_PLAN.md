# Implementation Plan — StadiumSaathi Production Hardening (C1–C9)

## 1. Scope & Objective
Bring `Kanak234/stadium-saathi` to enterprise production readiness fulfilling all 9 criteria (C1–C9):
- Strict PEP 621 packaging with console script entry point.
- Multi-stage unprivileged Docker containerization.
- Comprehensive test coverage (>90% target, enforced >=85% gate, zero synthetic mocks).
- Full CI/CD matrix across Python 3.10–3.13, CodeQL security scanning, Repository Guard, Dependabot.
- Threat modeling, input sanitization, and release automation.

---

## 2. Work Breakdown Structure

### Phase 1: Context & Specifications [COMPLETE]
- [x] Establish PRD (`docs/PRD.md`)
- [x] Establish TRD (`docs/TRD.md`)
- [x] Establish UI/UX Brief (`docs/UIUX_BRIEF.md`)
- [x] Track Open Questions (`docs/OPEN_QUESTIONS.md`)
- [x] Establish Implementation Plan (`docs/IMPLEMENTATION_PLAN.md`)

### Phase 2: CLI Integration & Hardening (C1, C6, C7)
- [ ] Add `cli(argv: list[str] | None = None) -> int` to `assistant.py` with argument parsing (`--query`, `--lang`, `--zone`, `--version`).
- [ ] Add version metadata `__version__ = "1.0.0"` in `assistant.py`.
- [ ] Update `pyproject.toml` with PEP 621 metadata, `stadium-saathi` console script, module packaging, and tool configs (pytest, ruff).
- [ ] Create `.gitignore` to prevent cache and build artifacts from leaking into git.
- [ ] Create multi-stage `Dockerfile` (`appuser` UID 10001, port 8501, healthcheck) and `.dockerignore`.

### Phase 3: Test Expansion & Verification (C2, C3)
- [ ] Expand `test_assistant.py`:
  - Test CLI argument handling and execution directly.
  - Test `_load_data()` error handling with missing and malformed JSON files.
  - Test edge cases in response builders and entity extractions.
- [ ] Run `ruff check .` and fix any linting issues.
- [ ] Run `python -m compileall -q .` for byte-compilation validation.
- [ ] Execute `pytest` with coverage measurement (`--cov=assistant --cov-fail-under=85`).

### Phase 4: CI/CD & Security Workflows (C4, C5, C8)
- [ ] Update `.github/workflows/ci.yml` (Python 3.10–3.13 matrix, ruff, compileall, pytest coverage gate, CLI test, package build).
- [ ] Add `.github/workflows/codeql.yml` for static security analysis.
- [ ] Verify `.github/workflows/repository-guard.yml`.
- [ ] Add `.github/dependabot.yml`.
- [ ] Update `.github/workflows/release.yml` with SHA256 checksum generation.
- [ ] Update `SECURITY.md` and `CHANGELOG.md`.
- [ ] Update `README.md` with status badges and CLI documentation.

### Phase 5: Release, PR & Portfolio Reporting (C9)
- [ ] Inspect `git diff --check` and verify clean working tree.
- [ ] Commit all hardening changes to `prod-hardening`.
- [ ] Push to `origin/prod-hardening`.
- [ ] Create GitHub Pull Request against `main`.
- [ ] Verify GitHub Actions CI runs pass.
- [ ] Create portfolio report `STADIUM_SAATHI_REPORT.md` in `/home/kanak/prod-hardening/`.
- [ ] Update portfolio tracking docs (`STATUS.md`, `PROGRESS.md`, `PORTFOLIO_HARDENING_MATRIX.md`, `PRODUCTION_READINESS_REPORT.md`, `TIER2_CANDIDATES.md`).
