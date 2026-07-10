# 02 — Architecture & Code Quality

**Objective:** finish what PR #8 started — a clean, consistent, bug-free backend.
**Current → Target:** C− (4/10) → A− (8/10)
**Why it matters:** the refactor already inverted the god-module and decoupled the engine —
that story is the strongest portfolio signal. Finishing the loose ends converts "in progress"
into "done well."

## Workstreams

### A1 — Kill the preserved latent bugs
- `app/blueprints/attacks.py::stop_attack`: `success = set_managed_mode(...)` but the function
  returns `None` on success → spurious "Failed to set managed mode" warning on every stop.
  Fix the return contract (return `True`/raise).
- `app/blueprints/attacks.py`: `url_for('settings.sudo_auth')` targets a route that no longer
  exists → `BuildError` inside the sudo error path. Remove or re-point.
- `app/core/network_utils.py`: `set_monitor_mode`/`set_managed_mode` call `sys.exit(1)` inside
  worker threads → replace with raised exceptions or `(ok, err)` returns so failures reach the
  request layer.

### A2 — De-duplicate the interface / monitor-mode logic
- Monitor-mode switching is reimplemented **three times** with mismatched tooling
  (`ifconfig`/`iwconfig` vs `ip`/`iw`): `network_utils`, `attack_service.launch_deauth_attack`,
  `diagnostics`. Consolidate into **one** `network_utils` primitive (prefer `ip`/`iw`; the
  `iwconfig`/`ifconfig` tools are deprecated). Every caller uses it.

### A3 — Consistency pass
- Replace all `print()` in engine/services with the injected logger / `app.core.logging`.
- Remove `bare except:` swallowing; catch specific exceptions.
- Return correct HTTP status codes — stop returning `200` with `{"success": false}`.
- Move magic numbers (progress steps 10/20/30…, timeouts, DHCP ranges) into named constants /
  config.
- `setup_fake_ap_network` hardcodes `eth0`/`wlan0` — use the configured interface.

### A4 — Portfolio-grade documentation of the architecture
- Add an **architecture diagram** (`docs/architecture.md`) showing the layered dependency
  direction (blueprints → services/core → Flask-free engine).
- Write the **before/after refactor narrative** — the god-module → factory story is the
  centerpiece of the portfolio value. Link it from the README.

## Effort
~2–3 days (A1 is hours; A2/A3 are the bulk).

## Dependencies
Best done **after** 04 (CI + broadened tests) so refactors have a safety net. A4 supports the
portfolio goal directly.

## Definition of done
- No `sys.exit` outside `app/cli.py`; no `print()` / `bare except` in library code.
- One interface primitive, one tool family.
- `ruff` clean; the three latent bugs have regression tests.
- `docs/architecture.md` + README section published.
