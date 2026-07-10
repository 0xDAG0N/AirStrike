# AirStrike — Threat Model & Security Posture

AirStrike is an **offensive** wireless-assessment tool that runs as **root** and shells out to
system radios. A tool like this is only responsible if it is honest about its own risk surface.
This document states what it protects, what it does not, and how to run it safely. It is
deliberately candid — the goal is a tool you can reason about, not marketing.

## What it is

A Flask + Socket.IO web panel over a Python attack engine (deauth flood, WPA-handshake
capture/crack, evil-twin AP). Single operator, single host, Linux + root only.

## Assets & trust boundaries

| Asset | Why it matters |
|---|---|
| The host root shell | The whole app runs as root; any code-exec bug = host compromise. |
| The control panel (`:5000`) | Whoever reaches it commands root-level RF attacks. |
| The operator's browser session | Holds the auth cookie + CSRF token. |
| Captured handshakes / audit log | Sensitive artifacts of an engagement. |

**Trusted:** the operator, the local host, `127.0.0.1`.
**Untrusted:** the network, other machines, other websites the operator visits, and — critically —
**the RF environment itself** (a nearby AP's SSID is attacker-controlled input).

## Controls in place (P0 hardening)

- **No shell execution.** Every subprocess uses an argv list; there is no `shell=True` / `os.popen`
  anywhere in `app/` (enforced by a test). This removes the command-injection → root-RCE class.
- **Input validation** (`app/core/validation.py`) on every value that reaches the OS/engine:
  BSSID (MAC regex), interface (anchored, no leading `-`), channel, SSID (control-char/length),
  and output paths (traversal-jailed).
- **Authentication** — a session login gates every route (`AIRSTRIKE_PASSWORD` or a generated
  one shown once); brute-force lockout per IP; session regenerated on login.
- **CSRF** — per-session token on all state-changing requests, plus a same-origin check and
  `SameSite=Strict` cookies, so cross-site pages can't drive the panel.
- **Loopback by default** — binds `127.0.0.1`; exposing to the network is an explicit
  `AIRSTRIKE_BIND_ALL=1` opt-in that prints a plaintext-HTTP warning.
- **XSS** — all attacker-controlled RF data (SSID/BSSID/log) is HTML-escaped before rendering.
- **Socket.IO** — the WebSocket handshake requires an authenticated session; CORS is scoped to
  the loopback origins.
- **Authorization gate + audit** — an attack cannot start without an explicit authorization
  confirmation, and every start/stop is written to an audit trail (`airstrike-audit.log`).

## Residual risks (known limitations — read before deploying)

- **Plaintext HTTP.** There is no TLS. The default loopback bind makes this a non-issue locally,
  but with `AIRSTRIKE_BIND_ALL=1` the session cookie is sniffable on the wire. **Do not expose it
  directly** — use an SSH tunnel (`ssh -L 5000:127.0.0.1:5000 host`) or terminate TLS in front.
- **Single-operator model.** State is one process-global dict; there are no roles, no per-user
  isolation, and one attack at a time.
- **Root by design.** Any future bug in the attack engine is a root bug. Run it on a
  dedicated/lab machine, not a workstation you care about.
- **Legality is on you.** Deauth is FCC §333-regulated; evil-twin/deauth without authorization
  is a crime in most jurisdictions (CFAA, UK CMA, StGB §202c, …). The authorization gate records
  your confirmation — it does not grant permission.

## Safe-operation checklist

1. Run on a disposable/lab Linux box with a supported wireless adapter.
2. Keep the default loopback bind; reach it via SSH tunnel if remote.
3. Set a strong `AIRSTRIKE_PASSWORD` and a persistent `AIRSTRIKE_SECRET_KEY`.
4. Only target networks you own or have **written** authorization to assess.
5. Review `airstrike-audit.log` after engagements.

## Reporting

Found a security issue? Open a GitHub issue marked *security* (or contact the maintainer
privately for anything sensitive). This is a learning/portfolio project — responsible reports
are welcome and credited.
