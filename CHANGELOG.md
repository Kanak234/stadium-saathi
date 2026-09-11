# Changelog

All notable changes to **StadiumSaathi** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-12

### Added
- **Production Hardening (C1–C9):**
  - **Packaging (C1, C7):** Full PEP 621 manifest (`pyproject.toml`) with standard build-backend `setuptools.build_meta`, console entry point `stadium-saathi = "assistant:cli"`, and automated wheel/sdist packaging.
  - **Containerization (C1, C7):** Multi-stage unprivileged `Dockerfile` running as system user `appuser` (UID 10001) with integrated Streamlit healthcheck on port 8501.
  - **CLI Interface (C7):** Headless terminal command `stadium-saathi` supporting `--query`, `--lang`, `--zone`, and `--version` options for kiosk automation and scripting.
  - **Test Suite & Verification (C2, C6):** Expanded pytest suite to 114 automated tests achieving **99.04%** statement coverage with zero synthetic mocks. Enforced `--cov-fail-under=85` coverage barrier.
  - **Code Quality & Linting (C3):** Full Ruff static analysis configuration and automated Python bytecode compilation (`compileall`).
  - **CI/CD Automation (C5, C8):**
    - Multi-version testing matrix across Python 3.10, 3.11, 3.12, and 3.13 (`.github/workflows/ci.yml`).
    - GitHub CodeQL static application security testing (`.github/workflows/codeql.yml`).
    - Repository Guard security syntax analyzer (`.github/workflows/repository-guard.yml`).
    - Automated weekly dependency update scans (`.github/dependabot.yml`).
    - Automated release workflow with SHA256 checksum generation (`.github/workflows/release.yml`).
  - **Documentation & Context (C9):**
    - Product Requirements Document (`docs/PRD.md`).
    - Technical Requirements Document (`docs/TRD.md`).
    - UI/UX Design Brief (`docs/UIUX_BRIEF.md`).
    - Open Questions Tracker (`docs/OPEN_QUESTIONS.md`).
    - Implementation Plan (`docs/IMPLEMENTATION_PLAN.md`).
    - Comprehensive `SECURITY.md` and updated `README.md`.
