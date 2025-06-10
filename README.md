```
                            _     _        ____   _          _  _
                           / \   (_) _ __ / ___| | |_  _ __ (_)| | __  ___ 
                          / _ \  | || '__|\___ \ | __|| '__|| || |/ / / _ \
                         / ___ \ | || |    ___) || |_ | |   | ||   < |  __/
                        /_/   \_\|_||_|   |____/  \__||_|   |_||_|\_\ \___|
```

### **AirStrike: A Unified Wi-Fi Pentesting Framework**

[cite_start]AirStrike is an advanced wireless security assessment framework designed to simplify and enhance Wi-Fi penetration testing through an integrated, web-based interface. [cite_start]Developed as a graduation project at Zarqa University, it addresses critical gaps in existing cybersecurity tools by unifying fragmented command-line utilities like `aircrack-ng`, `tshark`, and `hostapd` into a single, cohesive, and automated workflow.

[cite_start]By abstracting technical complexities behind an intuitive interface, AirStrike empowers cybersecurity students, penetration testers, and network administrators to conduct comprehensive security assessments with guided, efficient, and powerful tools.

> ⚠️ **Warning:** AirStrike is intended for educational and authorized penetration testing only. Unauthorized use against networks you do not own or have permission to test is illegal and unethical. [cite_start]The authors are not responsible for misuse.

---
### Key Highlights & Achievements

[cite_start]This framework was engineered to solve the real-world challenges of modern Wi-Fi security testing.

* [cite_start]**Unified & Simplified Workflow:** AirStrike eliminates the "command-line chaos" of traditional pentesting. [cite_start]It streamlines complex attack chains—like WPA handshake capture and cracking—into a few clicks, drastically reducing manual effort.
* [cite_start]**Proven Effectiveness:** Rigorous testing has validated the framework's reliability and performance.
    * [cite_start]**100%** accuracy in network discovery tests.
    * [cite_start]**98%** success rate in deauthentication attacks against WPA2 clients.
    * [cite_start]**83%** improvement in task completion time for intermediate users (reducing a 90-minute manual assessment to just 15 minutes).
* [cite_start]**High User Satisfaction:** In a comparative survey with 15 participants, AirStrike received an **8.5/10** overall satisfaction score, significantly higher than traditional tools like Aircrack-ng (5.9/10).
* [cite_start]**Comprehensive Attack Arsenal:** AirStrike integrates 10 distinct Wi-Fi attacks, making it one of the most comprehensive open-source tools available, surpassing even well-known frameworks like Wifite and Airgeddon in attack variety.

### Features

[cite_start]AirStrike's functionality is delivered through a clean web interface powered by Flask and real-time WebSockets for live feedback.

* [cite_start]**Web-Based Dashboard:** An intuitive central console to manage all operations, from initial scans to final results, accessible from any browser on the host machine.
* **Network Scanning & Reconnaissance:**
    * [cite_start]**Live Network Discovery:** Scan for all nearby Wi-Fi networks and display their ESSID, BSSID, channel, encryption, and signal strength.
    * [cite_start]**Probe Request Capture:** Passively listen for and identify the networks that nearby devices are actively searching for.
* **Automated Attack Modules:**
    * [cite_start]**Deauthentication Attack:** Force any client to disconnect from its access point, either to disrupt service or prime for other attacks.
    * [cite_start]**WPA/WPA2 Handshake Capture & Crack:** An automated, one-click process that deauthenticates a client, captures the re-connection handshake, and attempts to crack it using a wordlist.
    * [cite_start]**Evil Twin & Karma Attacks:** Create a rogue AP that mimics a legitimate network or intelligently impersonates any SSID probed by a client, luring them to connect.
    * [cite_start]**Man-in-the-Middle (MITM):** Use ARP spoofing to intercept and relay traffic between two parties on a network.
    * [cite_start]**Denial of Service (DoS):** Launch various DoS attacks, including Beacon, ICMP, and DHCP floods, to disrupt network services.

---

### System Architecture

The framework is designed for modularity and ease of use. It consists of a Python backend that controls system-level tools, a Flask web server that handles user interaction, and a set of isolated attack modules that are called via API requests.

![AirStrike System Architecture Diagram](https://i.imgur.com/vHqjZUM.png)
[cite_start]*A diagram illustrating the interaction between the user, web interface, backend, and underlying system tools.*

```
┌──(dagon㉿kali)-[~/AirStrike]
└─$ tree                                    
.
├── attacks
│   ├── capture_attack.py
│   ├── deauth_attack.py
│   ├── evil_twin.py
│   ├── __init__.py
│   ├── karma_attack.py
│   └── mitm.py
├── __init__.py
├── LICENSE
├── main_cli.py
├── README.md
├── requirements.txt
├── run.py
├── utils
│   ├── banner.py
│   └── network_utils.py
└── web
    ├── app.py
    ├── attacks
    │   ├── helpers.py
    │   └── routes.py
    ├── diagnostics
    │   ├── helpers.py
    │   ├── __init__.py
    │   └── routes.py
    ├── end_points
    │   └── wifi_scan.py
    ├── __init__.py
    ├── main
    │   └── routes.py
    ├── results
    │   ├── helpers.py
    │   └── routes.py
    ├── scan
    │   ├── helpers.py
    │   └── routes.py
    ├── settings
    │   ├── helpers.py
    │   └── routes.py
    ├── shared.py
    ├── socket_io.py
    ├── static
    │   ├── css
    │   │   ├── loading.css
    │   │   ├── navigation.css
    │   │   ├── style.css
    │   │   ├── theme.css
    │   │   └── theme-toggle.css
    │   └── js
    │       ├── main.js
    │       ├── modules
    │       │   ├── api.js
    │       │   ├── attacks
    │       │   │   ├── deauth.js
    │       │   │   ├── dosAttack.js
    │       │   │   ├── evilTwin.js
    │       │   │   ├── handshake.js
    │       │   │   ├── index.js
    │       │   │   └── karmaAttack.js
    │       │   ├── notifications.js
    │       │   ├── pages
    │       │   │   ├── attack.js
    │       │   │   ├── dashboard.js
    │       │   │   ├── results.js
    │       │   │   ├── scan.js
    │       │   │   └── settings.js
    │       │   ├── scanner.js
    │       │   ├── state.js
    │       │   └── ui.js
    │       ├── navigation.js
    │       ├── page-transitions.js
    │       └── theme.js
    ├── templates
    │   ├── attack.html
    │   ├── base.html
    │   ├── command_result.html
    │   ├── diagnostics.html
    │   ├── error.html
    │   ├── index.html
    │   ├── results.html
    │   ├── scan.html
    │   └── settings.html
    └── utils
        └── network_utils.py

19 directories, 67 files
```

---

### Prerequisites

-   [cite_start]**Operating System:** Linux (Kali Linux is recommended for its pre-installed tools).
-   **Hardware:** A wireless network adapter that supports **monitor mode and packet injection** is required. [cite_start]The Alfa AWUS036NHA or Panda PAU09 are highly recommended for their excellent Linux compatibility.
-   [cite_start]**Software:** Python 3.8+, and the `aircrack-ng`, `tshark`, `hostapd`, and `dnsmasq` tool suites.


### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/yourusername/airstrike.git](https://github.com/yourusername/airstrike.git)
    cd airstrike
    ```
2.  **Install system dependencies:**
    ```bash
    sudo apt update
    sudo apt install -y python3-pip aircrack-ng tshark hostapd dnsmasq
    ```
3.  **Install Python packages:**
    ```bash
    pip3 install -r requirements.txt
    ```

### Usage

1.  **Run the application with root privileges:**
    ```bash
    sudo python3 run.py
    ```
2.  **Access the Web Interface:**
    Open your web browser and navigate to **`http://localhost:5000`**. You will be greeted by the main dashboard, where you can begin scanning and launching attacks.

### Disclaimer

This tool is intended for use in authorized security testing and educational environments only. Using AirStrike against networks without explicit, written permission is illegal and unethical. The creators of this software assume no liability and are not responsible for any misuse or damage.