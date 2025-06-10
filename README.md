```
                            _     _        ____   _          _  _
                           / \   (_) _ __ / ___| | |_  _ __ (_)| | __  ___ 
                          / _ \  | || '__|\___ \ | __|| '__|| || |/ / / _ \
                         / ___ \ | || |    ___) || |_ | |   | ||   < |  __/
                        /_/   \_\|_||_|   |____/  \__||_|   |_||_|\_\ \___|
```

AirStrike is a modular, Python-based WiFi hacking framework developed as a graduation project. It provides powerful tools for:

- **Deauthentication Attacks**: Force clients to disconnect from their access point.
- **WPA/WPA2 Handshake Capture & Cracking**: Capture four-way handshakes and attempt to recover the network password using a wordlist.
- **Evil Twin Attack**: Clone a legitimate Wi-Fi network to trick users into connecting to a rogue access point, allowing interception of data or further attacks like phishing or DNS spoofing.

> ⚠️ **Warning:** AirStrike is intended for educational and authorized penetration testing only. Unauthorized use against networks you do not own or have permission to test is illegal and unethical.

---

## Features

1. **Deauthentication Attack** (`deauth_attack.py`)

   - Scan for nearby WiFi networks.
   - Select an AP by BSSID and channel.
   - Switch your wireless interface to monitor mode.
   - Launch a continuous deauth flood targeting all clients or a specific client.
   - Automatically restore the interface to managed mode when finished.

2. **Handshake Capture & Cracker** (`capture_attack.py` + handshake logic in `main.py`)

   - Scan and select the target AP.
   - Capture EAPOL (four-way handshake) packets by pairing a deauth flood with a packet capture.
   - Validate captured handshakes using `tshark`.
   - Crack the handshake offline with `aircrack-ng` and a provided wordlist.

3. **Evil Twin Attack** (`evil_twin.py`)

   - Set up a rogue access point with the same SSID and channel as the target.
   - Respond to client connection attempts and enable redirection/sniffing potential.

> Other modules (`mitm.py`) are scaffolded for future expansion.

---

## Repository Structure

```
├── attacks
│   ├── capture_attack.py      # Worker for capturing WPA handshakes
│   ├── deauth_attack.py       # Worker for performing deauthentication floods
│   ├── evil_twin.py           # Evil Twin attack module
│   ├── mitm.py                # (Planned) Man-in-the-Middle module
│   └── __init__.py
├── utils
│   ├── banner.py              # ASCII art and team banner
│   └── network_utils.py       # Scanning, mode-switching, and AP selection helpers
├── main.py                    # CLI menu and orchestration
├── captures                   # Directory for saving handshake
│   └── 10-A4-DA-1C-00-00      # sub-dir for every AP with its BSSID
├── requirements.txt           # Python package dependencies
└── README.md                  # This documentation
```

---

## Prerequisites

- **Operating System:** Linux (e.g., Kali, Ubuntu).
- **Wireless NIC**: A network interface card that supports monitor mode, AP mode, and packet injection
- **Root Privileges:** Many operations require `sudo` (monitor mode, channel lock).
- **Installed Tools:**
  - `iwconfig` / `aircrack-ng` suite
  - `tshark` (part of Wireshark CLI)

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/airstrike.git
   cd airstrike
   ```

2. **Install Python dependencies**

   ```bash
   sudo apt update
   sudo apt install -y python3-pip aircrack-ng tshark
   pip3 install -r requirements.txt
   ```

3. **Set up your wireless interface**

   - Identify your WiFi interface (e.g., `wlan0`):
     ```bash
     iwconfig
     ```
   - Confirm it supports monitor mode.
     ```bash
     iw list | grep -A 10 "Supported interface modes"
     ```

---

## Usage

1. **Run the main script**

   ```bash
   sudo python3 main.py
   ```

2. **Main Menu**

   ```text
   ========================================
   AirStrike - Main Menu
   ========================================
   1. Deauth Attack
   2. Handshake Cracker
   3. Evil Twin Attack
   4. MITM Attack (Coming Soon)
   0. Exit
   ```

3. **Deauthentication Attack**

   - Choose option `1`.
   - Scan results display nearby APs: select one by index.
   - AirStrike switches to monitor mode and locks channel.
   - Press `Ctrl+C` to stop the attack.
   - Interface is restored to managed mode and returns to main menu.

4. **Handshake Cracker**

   - Choose option `2`.
   - Select the target AP.
   - If no previous capture, AirStrike starts a capture thread and deauth flood concurrently.
   - Captured handshake is validated (`tshark`).
   - If valid, launch `aircrack-ng` with the default wordlist (`/usr/share/wordlists/rockyou.txt`).
   - Cracking results (found password or failure) are printed on screen.

5. **Evil Twin Attack**

   - Choose option `3`.
   - Clone a legitimate access point by entering the SSID and channel.
   - AirStrike sets up a fake AP using hostapd and dnsmasq, and optionally runs dnsspoof for DNS redirection.
   - Great for simulating rogue AP attacks or testing captive portals.

6. **MITM Attack** *(Planned)*

   - Will simulate classic man-in-the-middle scenarios such as ARP poisoning, SSL stripping, and credential interception.
   - Currently under development and will be available in future versions.

---

## Wordlist and Captures

- Default wordlist path: `/usr/share/wordlists/rockyou.txt`. You can modify `wordlist` in `main.py`.
- Captured handshakes are stored under:
  ```
  ./captures/<BSSID-MAC>/capture-01.cap
  ```

---

## Contributing

Contributions, bug reports, and feature requests are welcome! Please open an issue or pull request on GitHub.

---

## Disclaimer

Use AirStrike responsibly. Only test on networks you own or have explicit permission to test. The author is not responsible for misuse.
