# 05 — Technology & Stack

**Objective:** keep the (already good) stack current, coherent, and honest about how it runs.
**Current → Target:** B (7/10) → A− (8/10)
**Why it matters:** the stack choices are the tool's high mark — Flask + SocketIO + scapy +
aircrack-ng + buildless ESM are the right-sized tools. The gaps are dated pins and a couple of
runtime-honesty issues, not architecture.

## Workstreams

### D1 — Fix the dependency pins  *(blocker, shared with 04/T1)*
- Resolve the `Flask 2.2.5 / Werkzeug 3.1.3` incoherence: **upgrade to Flask 3.x** (preferred —
  actively maintained, fixes the mismatch) or pin `Werkzeug<2.3`.
- Refresh `Flask-SocketIO`/`python-socketio`/`python-engineio`/`scapy` to current, compatible
  releases; regenerate the lockfile; verify the T1 smoke test.
- Prune genuinely unused deps (`flasgger`, `art`, `termcolor`, `Flask-RESTful` already removed)
  now that `pyproject.toml` is the source of truth.

### D2 — Runtime honesty
- The app runs on the **Werkzeug dev server** with threading `async_mode`. For a lab tool
  that's acceptable — but say so, and gate remote bind behind a warning. If any "real" use is
  intended, document a `gunicorn`/`eventlet` (or `uvicorn`+ASGI) production path.
- `GEVENT_SUPPORT=1` is set but gevent isn't installed → remove the misleading env or add the
  dependency intentionally.

### D3 — Selectively close the 2026 technique gap (only if extending the tool; see 08)
- **PMKID** capture via `hcxdumptool` (clientless — the modern default).
- **`hashcat` GPU cracking** as an option alongside CPU `aircrack-ng`.
- **WPS pixie-dust** (`reaver`/`bully`).
- **WPA3 / PMF detection** — critically, *detect* when deauth will fail (802.11w) and tell the
  user, instead of silently degrading. This alone keeps the tool honest as WPA3 spreads.

### D4 — Frontend build hygiene (light touch)
- Keep buildless ESM (a legit choice), but **vendor** third-party assets locally (05 ↔ 03/F5).
  No CDN dependencies for a tool that runs air-gapped.

## Effort
~1–2 days for D1/D2/D4. D3 is a larger, optional feature investment (weeks) tied to 08.

## Dependencies
D1 unblocks 04/T1. D3 depends on 06/08 (only worth it if pursuing the "real tool" path).

## Definition of done
- Clean install on current Python with coherent, current pins.
- Runtime model documented; no misleading env flags.
- (If extending) at least WPA3/PMF detection shipped so the tool never lies about what will work.
