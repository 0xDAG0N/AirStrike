# AirStrike

AirStrike is a Flask + Socket.IO web interface for orchestrating Wi-Fi assessment tools from a browser.  
This build intentionally focuses on the three most stable attacks in the suite: **Deauthentication**, **Cracking (handshake capture + aircrack-ng)**, and **Evil Twin**.

## Supported Attacks
- **Deauthentication** – kicks associated clients off the selected AP by flooding crafted 802.11 deauth frames.
- **Cracking (Handshake)** – captures WPA/WPA2 handshakes while simultaneously brute-forcing them with `aircrack-ng` and a configurable wordlist.
- **Evil Twin** – clones the target SSID via `hostapd`/`dnsmasq`, sets up DHCP/DNS spoofing, and can optionally front a captive portal.

All other experimental attack stubs were removed to keep the UI, API, and code paths lean.

## Requirements
1. Python 3.10+ and `pip`
2. Python deps from `requirements.txt`
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
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
# or
sudo ./run_with_sudo.sh
```

The server binds to `0.0.0.0:5000`; browse to `http://localhost:5000`.  
Use the **Scan** tab to discover networks, select one, then switch to **Attack** to configure the chosen attack.  
Live logs and capture summaries are available under **Results**.

## Configuration Notes
- Global defaults (interface, wordlist path, capture directory) live in `web/shared.py` under the `config` dict:
  ```python
  config = {
      'interface': 'wlan0',
      'wordlist': '/usr/share/wordlists/rockyou.txt',
      'output_dir': './captures/'
  }
  ```
- Captured handshakes are stored per-BSSID inside `captures/`.
- The `start.sh` helper script launches the app with logging into `logs/errors.log`.

## Repository Layout
- `attacks/` – Python workers for deauth, handshake capture/cracking, and evil twin orchestration.
- `web/` – Flask blueprints, Socket.IO events, templates, and front-end modules (per-attack config lives in `web/static/js/modules/attacks/`).
- `utils/` – helpers for interface/monitor-mode management.
- `run.py` / `run_with_sudo.sh` / `start.sh` – entry points that enforce root execution.

## Troubleshooting
- Interface stuck in monitor mode? Use the **Settings → Interface** tools or `utils/network_utils.set_managed_mode`.
- Missing binaries (e.g., `airodump-ng`, `hostapd`) will surface in the attack log pane. Install them through your package manager and restart AirStrike.
- Ensure your wireless chipset supports the required modes; USB adapters with Atheros or Ralink chipsets are typically reliable.

## Disclaimer
AirStrike is intended for lab use, red-team exercises, and research on networks you own or are explicitly authorized to test. Misuse may violate law or policy—operate responsibly.

