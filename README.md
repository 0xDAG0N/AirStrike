# AirStrike

AirStrike is a Flask-based wireless security assessment platform that exposes common Wi-Fi reconnaissance and attack workflows through a modern web dashboard. The application bundles scanning utilities, automated attack orchestration, capture management, and diagnostics into an interface that is easy to operate once the host has the required wireless tooling.

## Features

- **Web dashboard** that tracks scan, attack, and capture metrics in real time and provides quick links to all major workflows.
- **Network scanning** endpoints that enumerate nearby access points and sniff probe requests with configurable interfaces and durations.
- **Attack automation** for deauthentication, handshake capture, evil twin, denial of service, and KARMA-style attacks with live Socket.IO status updates.
- **Result management** for viewing stored captures and logs produced by previous runs.
- **Diagnostics & settings** pages to verify wireless interface state, adjust defaults such as the monitored interface or wordlist, and review application logs.
- **Socket.IO integration** for streaming attack state, log output, and background task progress to the browser without manual refreshes.

## Project Structure

```
├── run.py                # Entry point that enforces root execution and starts the Socket.IO server
├── web/                  # Flask blueprints, templates, static assets, and shared configuration
│   ├── app.py            # Flask application factory and blueprint registration
│   ├── scan/             # Network scanning routes and helpers
│   ├── attacks/          # Attack orchestration, helpers, and Socket.IO events
│   ├── results/          # Capture/result viewing routes
│   ├── diagnostics/      # Health checks and interface diagnostics
│   ├── settings/         # User-configurable application defaults
│   └── templates/        # Dashboard, scan, attack, results, diagnostics, and error views
├── utils/
│   └── network_utils.py  # Wireless interface helpers and packet sniffing utilities
├── attacks/              # Lower-level attack implementations and scripts
├── requirements.txt      # Python dependencies
└── LICENSE
```

## Requirements

AirStrike targets Linux systems with wireless hardware capable of monitor mode. The application expects the following system-level prerequisites:

- Python 3.9+
- Wireless tools such as `iw`, `iwconfig`, `ifconfig`, and `iwlist`
- Packet manipulation libraries like `scapy`
- Root (UID 0) privileges to switch interfaces into monitor mode and run attacks

All Python dependencies are listed in `requirements.txt` and can be installed with `pip`.

```bash
pip install -r requirements.txt
```

## Running the Application

1. **Ensure root access**. AirStrike enforces root execution. Launching `run.py` as a non-root user will terminate with a warning.
2. **Install dependencies** using the command above.
3. **Start the web interface**:

   ```bash
   sudo python run.py
   ```

   On startup, the script:

   - Adds `127.0.0.1 airstrike.local` to `/etc/hosts` if missing.
   - Creates the capture output directory configured in `web/shared.py`.
   - Exposes the dashboard at `http://airstrike.local:5000`.

4. **Open the dashboard** in a browser and use the sidebar to scan networks, launch attacks, review results, or adjust settings.

## Configuration

Global settings live in `web/shared.py`. Key defaults include:

- `interface`: Wireless interface to operate on (defaults to `wlan0`).
- `wordlist`: Path to the wordlist used for password attacks.
- `output_dir`: Directory where capture files and attack logs are stored.

These values can be customized via the Settings page in the web UI or by editing the file directly.

## Development Notes

- Socket.IO events are defined in `web/socket_io.py` and used by the scan and attack blueprints for realtime updates.
- Attack helpers emit log messages through `web.shared.log_message`, ensuring output is visible both in the console and on the dashboard.
- Utility functions in `utils/network_utils.py` manage interface mode transitions and sniff probe requests with Scapy.

## Disclaimer

AirStrike is intended for authorized penetration testing and research on networks you own or have explicit permission to assess. Misuse of this software may violate local laws and regulations. Use responsibly.
