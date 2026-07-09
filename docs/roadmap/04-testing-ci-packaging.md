# 04 — Testing, CI & Packaging

**Objective:** make correctness enforced, not aspirational.
**Current → Target:** B− (6/10) → A (9/10)
**Why it matters:** PR #8 bought a testable design and the first tests — but nothing runs
them, the pinned deps fail a clean install, and the README describes the old tree. These are
the cheapest, most visible "finish" wins.

## Workstreams

### T1 — Fix reproducibility  *(blocker)*
- The `Flask 2.2.5 / Werkzeug 3.1.3` pin is incoherent and can fail a clean install. Either
  upgrade to Flask 3.x or pin `Werkzeug<2.3` (see 05).
- Add a **clean-install smoke test**: fresh venv → `pip install -e .` → `python -c "import app"`
  → route map builds. Run it in CI.

### T2 — Add CI  *(blocker)*
- `.github/workflows/ci.yml`: on push/PR, run `ruff check`, `pytest`, and the T1 smoke test on
  a matrix of supported Python versions. A red build blocks merge.

### T3 — Broaden the test suite toward the risk surface
- Current tests cover parsers + factory/routes only. Add:
  - `tests/test_security.py` — validation rejects shell metacharacters; paths stay jailed
    (pairs with 01).
  - `run_with_sudo` builds correct argv and never invokes a shell.
  - Service orchestration (mock subprocess/scapy): attack start/stop transitions, thread
    lifecycle, emit contracts.
  - The scan parser against both `iwlist` and `iw` fixtures.
  - Route-contract test asserting **auth is required** on state-changing routes.
- Target a coverage floor (e.g. 70%) enforced in CI.

### T4 — Packaging & docs finish
- Rewrite the **stale README** to the `app/` package (it still describes `web/`). Lead with
  architecture + the refactor story (02/A4) + a candid limitations/threat-model section.
- Ensure `pyproject.toml` ships templates/static (already configured) and the `airstrike`
  console script works from a wheel install.
- Add `CONTRIBUTING.md` + a short `docs/development.md` (how to run tests, the lab-only stance).

## Effort
~2 days.

## Dependencies
T1 depends on the 05 pin decision. T3 pairs with 01 (security tests). Enables safe work in
02/05.

## Definition of done
- Green CI (ruff + pytest + clean-install smoke) required on every PR.
- Coverage ≥ target; auth + validation covered by tests.
- README matches the actual codebase and tells the portfolio story.
