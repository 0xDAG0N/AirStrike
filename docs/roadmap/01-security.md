# 01 — Security  *(highest priority)*

**Objective:** eliminate the "a security tool that is itself trivially rootable" irony.
**Current → Target:** D (2/10) → B (7/10)
**Why it matters:** three *confirmed* unauthenticated remote-root-RCE chains sit behind zero
auth on a `0.0.0.0` bind. Until this is closed, public promotion is net-negative — it's the
first thing a security-literate reviewer will find, and it invalidates the whole pitch.

## Workstreams (in order)

### S1 — Kill command execution through a shell  *(blocker)*
- Remove **every** `shell=True` and `os.popen`. Locations:
  - `app/engine/evil_twin.py` → `run_command()` uses `subprocess.run(cmd, shell=True)`; the
    `capture_worker` cleanup uses `subprocess.run(f"sudo rm -f {prefix}*", shell=True)`.
  - `app/services/attack_service.py` → `run_hostapd`/`run_dnsmasq` use `os.popen(f"…")`.
- Replace with **argv lists**: `subprocess.run(["ifconfig", iface, "up", …])`,
  `subprocess.Popen(["hostapd", cfg], …)` with non-blocking output draining.
- Change `app/core/sudo.py::run_with_sudo` to accept an **argv list**, never a string +
  `.split()`.

### S2 — Input validation layer  *(blocker)*
- Add `app/core/validation.py`: `is_valid_bssid()` (MAC regex), `is_valid_interface()`
  (enumerate real interfaces + allow-list), `safe_path()` (jail `output_dir`/wordlist under
  a base dir), `sanitize_ssid()` (reject/escape shell + hostapd-config metacharacters).
- Enforce at **every entry point**: `/start_attack`, `/set_interface`, `/save_wordlist`,
  `/save_output_dir`, `/run_diagnostic`. Reject with 400 on failure.
- SSID is currently written verbatim into `hostapd.conf` → config-injection; sanitize before
  templating.

### S3 — Authentication + CSRF  *(blocker)*
- Add a login gate (single operator password from env → hashed; or token). No route that
  starts an attack or mutates config is reachable unauthenticated.
- Add `Flask-WTF` `CSRFProtect` (or a token check) on all state-changing POSTs.
- Default **bind to `127.0.0.1`**, not `0.0.0.0`. Make remote bind an explicit, warned opt-in.

### S4 — Frontend XSS  *(blocker — see also 03)*
- Add an `escapeHtml()` helper; replace the 21 unescaped `innerHTML` sinks
  (`displayNetworks`, `displayNetworkInfo`, `updateAttackLog`, `scan.js`) with escaped
  insertion or `textContent`. Attacker-broadcast SSIDs must never execute.

### S5 — Harden the diagnostics allow-list
- `app/blueprints/diagnostics.py` allow-list is prefix-based (`startswith`) and one entry has
  a shell pipe `command.split()` can't honor. Switch to **exact-match** command allow-list
  mapped to fixed argv lists.

### S6 — Secrets, audit, defense-in-depth
- Keep `SECRET_KEY` from env (already done); document it.
- Add an **audit log** of who triggered which attack against which target + timestamp (feeds
  07 Legal).
- Add rate-limiting / single-attack lock enforcement (already have the `threading.Lock`).

## Effort
~4–6 focused days. S1–S4 are the blocking majority (~3 days).

## Dependencies
None upstream — this is the gate. Blocks: all public promotion, and 07 (auth gate + audit
log are shared).

## Definition of done
- `grep -rn "shell=True\|os.popen" app/` returns nothing.
- Every attack/config route requires auth + a valid CSRF token; server binds loopback by default.
- Fuzzing BSSID/interface/SSID/paths with shell metacharacters cannot execute commands or
  escape the output jail (add tests under `tests/test_security.py`).
- A written **threat model** section exists (see 07 + the portfolio story in 02).
