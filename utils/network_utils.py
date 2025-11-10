import subprocess
import re
import sys
from scapy.all import sniff
from scapy.layers.dot11 import Dot11, Dot11ProbeReq, Dot11Elt

try:
    from web.shared import run_with_sudo as shared_run_with_sudo
except Exception:
    shared_run_with_sudo = None
def set_monitor_mode(interface_name):
    """
    Set wireless interface to monitor mode.
    
    Args:
        interface_name (str): Name of the wireless interface
        
    Returns:
        bool: True if successful
        
    Raises:
        RuntimeError: If setting monitor mode fails
        FileNotFoundError: If required tools are not found
    """
    try:
        # First ensure interface exists and is recognized
        subprocess.run(['sudo', 'rfkill', 'unblock', 'all'], check=True, capture_output=True)
        
        # Try to reset interface first
        subprocess.run(['sudo', 'ip', 'link', 'set', interface_name, 'down'], check=True, capture_output=True)
        subprocess.run(['sudo', 'iw', interface_name, 'set', 'type', 'managed'], check=False, capture_output=True)
        subprocess.run(['sudo', 'ip', 'link', 'set', interface_name, 'up'], check=True, capture_output=True)
        
        # Now set monitor mode
        subprocess.run(['sudo', 'ip', 'link', 'set', interface_name, 'down'], check=True, capture_output=True)
        subprocess.run(['sudo', 'iw', interface_name, 'set', 'type', 'monitor'], check=True, capture_output=True)
        subprocess.run(['sudo', 'ip', 'link', 'set', interface_name, 'up'], check=True, capture_output=True)
        
        # Verify monitor mode was set
        for _ in range(3):  # Try up to 3 times
            if is_monitor_mode(interface_name):
                print(f"[Setup] Interface {interface_name} set to monitor mode.")
                return True
            import time
            time.sleep(1)
            
        raise RuntimeError("Interface exists but failed to enter monitor mode")
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        print(f"[Setup] Error setting {interface_name} to monitor mode: {error_msg}")
        raise RuntimeError(f"Failed to set monitor mode: {error_msg}")
    except FileNotFoundError:
        print("[Setup] Error: required tools not found (ip/iw).")
        raise FileNotFoundError("Required tools (ip/iw) not found")

def is_monitor_mode(interface):
    """Check if interface is in monitor mode"""
    try:
        # Try iw first (more reliable)
        result = subprocess.run(
            ["sudo", "iw", interface, "info"],
            capture_output=True,
            text=True,
            check=False
        )
        if "type monitor" in result.stdout.lower():
            return True
            
        # Fallback to iwconfig
        result = subprocess.run(
            ["iwconfig", interface],
            capture_output=True,
            text=True,
            check=False
        )
        return "mode:monitor" in result.stdout.lower()
    except Exception as e:
        print(f"Error checking mode for {interface}: {e}")
        return False

def set_managed_mode(interface_name):
    try:
        subprocess.run(['sudo', 'ifconfig', interface_name, 'down'], check=True, capture_output=True)
        subprocess.run(['sudo', 'iwconfig', interface_name, 'mode', 'managed'], check=True, capture_output=True)
        subprocess.run(['sudo', 'ifconfig', interface_name, 'up'], check=True, capture_output=True)
        print(f"[Setup] Interface {interface_name} set to managed mode.")
    except subprocess.CalledProcessError as e:
        print(f"[Setup] Error setting {interface_name} to managed mode: {e.stderr.decode()}")
        sys.exit(1)
    except FileNotFoundError:
        print("[Setup] Error: 'ifconfig' or 'iwconfig' command not found. Ensure network tools are installed.")
        sys.exit(1)

def reset_wifi_mode(interface='wlan0'):
    """
    Reset wireless interface to managed mode.
    
    Args:
        interface (str): Name of the wireless interface (default: 'wlan0')
    
    Returns:
        bool: True if successful, False if any error occurred
    """
    commands = [
        ['sudo', 'ifconfig', interface, 'down'],
        ['sudo', 'iwconfig', interface, 'mode', 'managed'],
        ['sudo', 'ifconfig', interface, 'up']
    ]
    
    try:
        for cmd in commands:
            result = subprocess.run(cmd, 
                                  check=True, 
                                  stderr=subprocess.PIPE, 
                                  stdout=subprocess.PIPE,
                                  text=True)
            if result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode, 
                    cmd, 
                    result.stdout, 
                    result.stderr
                )
        
        print(f"Successfully reset {interface} to managed mode")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(e.cmd)}")
        print(f"Error: {e.stderr.strip()}")
        return False
    except Exception as e:
        print(f"Unexpected error resetting {interface}: {str(e)}")
        return False

global available_aps
def run_scan(interface):
    """
    Scan for Wi-Fi networks on the given interface.

    Returns:
        tuple[list, str|None]: (networks, error message)
    """
    available_aps = []
    try:
        if is_monitor_mode(interface):
            reset_wifi_mode(interface)

        if shared_run_with_sudo:
            success, output, stderr = shared_run_with_sudo(f"iwlist {interface} scanning")
            if not success:
                error_msg = stderr.strip() or f"Failed to scan interface {interface}"
                return [], error_msg
        else:
            result = subprocess.run(
                ['iwlist', interface, 'scanning'],
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout

        aps = []
        lines = output.split('\n')
        ap = {}

        for line in lines:
            line = line.strip()
            if line.startswith('Cell'):
                if ap:
                    aps.append(ap)
                ap = {}
                match = re.search(r'Address: ([\da-fA-F:]+)', line)
                if match:
                    ap['BSSID'] = match.group(1)

            elif line.startswith('ESSID:"'):
                ap['ESSID'] = line.split('"')[1]

            elif line.startswith('Mode:'):
                ap['Mode'] = line.split(':')[1].strip()

            elif line.startswith('Frequency:'):
                # Example: Frequency:2.412 GHz (Channel 1)
                freq_part = line.split(':')[1].strip()
                freq_clean = re.sub(r'\s(Channel.?)', '', freq_part)
                ap['Frequency'] = freq_clean

                # Extract channel number
                channel_match = re.search(r'Channel\s*(\d+)', line)
                if channel_match:
                    ap['Channel'] = channel_match.group(1)

            elif line.startswith('Encryption key:'):
                ap['Encryption'] = line.split(':')[1].strip()

            elif 'Signal level=' in line:
                # Example: Quality=70/70  Signal level=-39 dBm
                signal_match = re.search(r'Signal level=([-\d]+)', line)
                if signal_match:
                    ap['Signal'] = signal_match.group(1) + " dBm"

        if ap:
            aps.append(ap)

        available_aps = aps
        return available_aps, None

    except subprocess.CalledProcessError as e:
        error_msg = (e.stderr or "").strip() or str(e)
        print(f"Error scanning APs: {error_msg}")
        return [], error_msg
    except Exception as e:
        error_msg = str(e)
        print(f"Error scanning APs: {error_msg}")
        return [], error_msg



def display_and_choose_ap(ap_list):
    """
    Displays a numbered list of APs and prompts the user to choose one.

    Args:
        ap_list (list): A list of AP dictionaries from run_scan.

    Returns:
        tuple: A tuple containing the BSSID and Channel of the chosen AP
               (bssid, channel), or (None, None) if no AP is chosen or
               an error occurs.
    """
    if not ap_list:
        print("No APs available to choose from.")
        return None, None

    print("\nAvailable Access Points:")
    print("-" * 30)
    for i, ap in enumerate(ap_list):
        # Ensure essential keys exist, provide defaults if not
        essid = ap.get('ESSID', 'N/A')
        bssid = ap.get('BSSID', 'N/A')
        channel = ap.get('Channel', 'N/A')
        print(f"{i + 1}. ESSID: {essid:<20} BSSID: {bssid}  Channel: {channel}")
    print("-" * 30)

    while True:
        try:
            choice = input(f"Enter the number of the AP you want to select (1-{len(ap_list)}), or 'q' to quit: ")
            if choice.lower() == 'q':
                print("Selection cancelled.")
                return None, None

            choice_index = int(choice) - 1

            if 0 <= choice_index < len(ap_list):
                selected_ap = ap_list[choice_index]
                selected_bssid = selected_ap.get('BSSID')
                selected_channel = selected_ap.get('Channel')

                if selected_bssid and selected_channel:
                    # Print confirmation of selection, but not the final result later
                    print(f"\nYou selected: {selected_ap.get('ESSID', 'N/A')} ({selected_bssid}) on channel {selected_channel}")
                    return selected_bssid, selected_channel
                else:
                    print("Error: Selected AP data is incomplete (missing BSSID or Channel). Please try again.")
                    return None, None

            else:
                print("Invalid choice. Please enter a number from the list.")

        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
             print("\nSelection cancelled by user.")
             return None, None
         
def sniff_probe_requests(interface, duration=20):
    """
    Sniff for probe requests on the given interface.
    
    Args:
        interface (str): Network interface to use
        duration (int): Duration to sniff in seconds
        
    Returns:
        list: List of unique SSIDs from probe requests
    """
    try:
        # Ensure interface is in monitor mode
        if not is_monitor_mode(interface):
            set_monitor_mode(interface)
        
        print(f"[*] Sniffing for probe requests on {interface} for {duration} seconds...")
        ssids = set()

        def packet_handler(pkt):
            if pkt.haslayer(Dot11ProbeReq):
                if pkt.haslayer(Dot11Elt) and pkt.ID == 0:  # SSID element
                    try:
                        ssid = pkt.info.decode(errors="ignore").strip()
                        if ssid and not ssid.isspace():  # Only add non-empty SSIDs
                            ssids.add(ssid)
                            print(f"[+] Detected probe request for: {ssid}")
                    except Exception as e:
                        print(f"[-] Error decoding SSID: {e}")

        # Start sniffing
        sniff(iface=interface, prn=packet_handler, timeout=duration)
        
        # Convert set to sorted list
        result = sorted(list(ssids))
        print(f"[*] Found {len(result)} unique networks: {result}")
        return result
        
    except Exception as e:
        print(f"[-] Error during probe request sniffing: {e}")
        return []
    finally:
        try:
            # Always try to reset to managed mode
            set_managed_mode(interface)
        except Exception as e:
            print(f"[-] Error resetting interface mode: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    # --- Configuration ---
    # !!!!! IMPORTANT: Replace "wlan0" with your actual wireless interface name !!!!!
    wireless_interface = "wlan0"
    # --- End Configuration ---

    # 1. Scan for Networks
    #banner("AirStrike")

    available_aps, scan_error = run_scan(wireless_interface)
    if scan_error:
        print(f"[-] Scan error: {scan_error}")
    else:
        print(available_aps)

    # 2. Let the user choose
    chosen_bssid = None
    chosen_channel = None
    if available_aps: # Proceed only if scanning was successful and found APs
        chosen_bssid, chosen_channel = display_and_choose_ap(available_aps)

    # 3. Use the chosen information (variables are available but not printed here)
    if chosen_bssid and chosen_channel:
        # --- Removed final print statements ---
        # print("\n--- Selected AP Info ---")
        # print(f"BSSID:   {chosen_bssid}")
        # print(f"Channel: {chosen_channel}")
        # print("------------------------")

        # You can now use the variables 'chosen_bssid' and 'chosen_channel'
        # directly if this script is part of a larger application or imported.
        # For example:
        # some_other_function(chosen_bssid, chosen_channel)
        pass # Placeholder, indicates successful selection without printing here

    elif not scan_error:
        # This message is kept as it indicates failure/cancellation
        print("\nNo AP was selected or process cancelled.")

    # The script will now exit. The chosen_bssid and chosen_channel values
    # were obtained but not printed in this final block.
    if not (chosen_bssid and chosen_channel) and not available_aps:
         sys.exit(1) # Exit with error code if scan failed initially
    elif not (chosen_bssid and chosen_channel):
         sys.exit(0) # Exit normally if user cancelled or selection failed after scan
    else:
         sys.exit(0) # Exit normally on successful selection
