```
                            _     _        ____   _          _  _
                           / \   (_) _ __ / ___| | |_  _ __ (_)| | __  ___ 
                          / _ \  | || '__|\___ \ | __|| '__|| || |/ / / _ \
                         / ___ \ | || |    ___) || |_ | |   | ||   < |  __/
                        /_/   \_\|_||_|   |____/  \__||_|   |_||_|\_\ \___|
```

AirStrike is a Flask + Socket.IO web interface for orchestrating Wi-Fi assessment tools from a browser.  
This build intentionally focuses on the three most stable attacks in the suite: **Deauthentication**, **Cracking (handshake capture + aircrack-ng)**, and **Evil Twin**.

## Supported Attacks
- **Deauthentication** – kicks associated clients off the selected AP by flooding crafted 802.11 deauth frames.
- **Cracking (Handshake)** – captures WPA/WPA2 handshakes while simultaneously brute-forcing them with `aircrack-ng` and a configurable wordlist.
- **Evil Twin** – clones the target SSID via `hostapd`/`dnsmasq`, sets up DHCP/DNS spoofing, and can optionally front a captive portal.

All other experimental attack stubs were removed to keep the UI, API, and code paths lean.

## Requirements
1. Python 3.10+ and `pip`
2. Install the package and its dependencies
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .          # installs deps + the `airstrike` console script
   # or: pip install -r requirements.txt
   ```
3. Root access (AirStrike refuses to start otherwise)
4. External CLI tooling available in `$PATH`:
   - `aircrack-ng` suite (`airmon-ng`, `airodump-ng`, `aircrack-ng`)
   - `iw`, `ip`, `ifconfig`/`net-tools`
   - `hostapd`, `dnsmasq`, `iptables`, `dnsspoof`
   - A wireless adapter that supports monitor mode and injection

## Running AirStrike
```bash
sudo python run.py
```

The runner enforces sudo, exports the required environment variables, and ensures `/etc/hosts` contains `127.0.0.1 airstrike.local`.
The server binds to **`127.0.0.1:5000` (loopback only)** by default; browse to `http://airstrike.local:5000` or `http://127.0.0.1:5000`. (`sudo airstrike` runs the same thing via the console script.)

On first launch AirStrike prints a generated **login password** — set `AIRSTRIKE_PASSWORD` to choose your own, and `AIRSTRIKE_SECRET_KEY` to keep sessions across restarts. Sign in, then use the **Scan** tab to discover networks, select one, and switch to **Attack**. You must confirm authorization before an attack starts, and every launch/stop is written to `airstrike-audit.log`. Live logs and capture summaries are under **Results**.

To reach it from another machine, prefer an SSH tunnel (`ssh -L 5000:127.0.0.1:5000 <host>`). Exposing it on all interfaces (`AIRSTRIKE_BIND_ALL=1`) serves the panel over plaintext HTTP and is discouraged — see [THREAT_MODEL.md](THREAT_MODEL.md).

## Configuration Notes
- Runtime defaults (interface, wordlist path, capture directory) live in `app/config.py` under the `config` dict; the **Settings** tab edits them live.
- Environment variables: `AIRSTRIKE_PASSWORD` (login), `AIRSTRIKE_SECRET_KEY` (persistent sessions), `AIRSTRIKE_BIND_ALL=1` (expose on all interfaces — discouraged), `AIRSTRIKE_ORIGINS` (Socket.IO CORS allowlist when not on loopback), `AIRSTRIKE_AUDIT_LOG` (audit-file path).
- Captured handshakes are stored per-BSSID inside `captures/`.
- `run.py` is a thin shim into `app.cli:main` (also installed as the `airstrike` console script); it enforces root, maps `airstrike.local`, and starts Socket.IO.

## Repository Layout
The backend is a single installable `app/` package (restructured from the original flat layout — see PR #8):
- `app/engine/` – framework-agnostic attack workers (deauth, handshake capture/cracking, evil twin); importable without Flask.
- `app/core/` – shared plumbing: network/monitor-mode utils, sudo, logging, plus the **validation**, **auth**, and **audit** modules.
- `app/services/` – orchestration (attack/scan/settings) between the blueprints and the engine.
- `app/blueprints/` – Flask routes; `app/__init__.py` is the `create_app()` factory.
- `app/static/` · `app/templates/` – the front-end (per-attack config lives in `app/static/js/modules/attacks/`).
- `run.py` · `pyproject.toml` – entry-point shim + packaging.
- `tests/` – pytest suite (factory/route contract, parsers, and the security/auth regression tests).

## Troubleshooting
- Interface stuck in monitor mode? Use the **Settings → Interface** tools or `utils/network_utils.set_managed_mode`.
- Missing binaries (e.g., `airodump-ng`, `hostapd`) will surface in the attack log pane. Install them through your package manager and restart AirStrike.
- Ensure your wireless chipset supports the required modes; USB adapters with Atheros or Ralink chipsets are typically reliable.

## Security
AirStrike runs as root, so its own security matters. Hardening includes: no shell execution (argv only), input validation on all OS-bound values, a login gate + CSRF + same-origin enforcement, loopback-by-default binding, XSS escaping, an authenticated Socket.IO channel, and an authorization gate + audit log. The full trust model, residual risks (notably: **no TLS — use an SSH tunnel**), and a safe-operation checklist are in **[THREAT_MODEL.md](THREAT_MODEL.md)**. Run the test suite with `pytest`.

## Authorization & Legal
AirStrike performs **active, offensive** attacks (deauthentication, handshake capture, rogue AP). Running them against networks you do not own — or lack **written** authorization to assess — is illegal in most jurisdictions (e.g. US CFAA, FCC §333 for deauthentication, UK CMA, German StGB §202c). This is a lab / research / portfolio tool: use it only on your own equipment or within an authorized engagement. The in-app authorization gate records your confirmation; it does **not** grant permission. You are responsible for how you use it.
