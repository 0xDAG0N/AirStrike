import subprocess
import re
import sys

def set_monitor_mode(interface_name):
    try:
        subprocess.run(['sudo', 'ifconfig', interface_name, 'down'], check=True)
        subprocess.run(['sudo', 'iwconfig',   interface_name, 'mode',    'monitor'], check=True)
        subprocess.run(['sudo', 'ifconfig', interface_name, 'up'],   check=True)
        print(f"[Setup] Interface {interface_name} set to monitor mode.")
    except subprocess.CalledProcessError as e:
        print(f"[Setup] Error setting {interface_name} to monitor mode: {e.stderr.decode()}")
        sys.exit(1)
    except FileNotFoundError:
        print("[Setup] Error: required tools not found (ifconfig/iwconfig).")
        sys.exit(1)


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

def run_scan(interface):
    """
    Scans for available Wi-Fi networks and returns a list of dictionaries
    containing network information.

    Args:
        interface (str): The network interface to use for scanning (e.g., "wlan0").

    Returns:
        list: A list of dictionaries, where each dictionary represents a Wi-Fi network
              and contains its details. Returns an empty list if an error occurs or
              no networks are found.
    """
    print(f"Scanning for Wi-Fi networks on interface {interface}...")
    try:
        # Using iw scan is often preferred over iwlist nowadays if available
        # Trying iwlist first as it was in the original code
        try:
            result = subprocess.run(['sudo', 'iwlist', interface, 'scanning'], capture_output=True, text=True, check=True, timeout=20)
        except FileNotFoundError:
             print(f"iwlist not found. Trying 'iw dev {interface} scan'...")
             result = subprocess.run(['sudo', 'iw', 'dev', interface, 'scan'], capture_output=True, text=True, check=True, timeout=20)
        except subprocess.CalledProcessError as e:
             # Sometimes scanning immediately after bringing interface up fails
             # Or permissions might be wrong even with sudo
             print(f"Error running scan command with iwlist: {e}")
             print(f"Trying 'iw dev {interface} scan' as fallback...")
             try:
                 result = subprocess.run(['sudo', 'iw', 'dev', interface, 'scan'], capture_output=True, text=True, check=True, timeout=20)
             except Exception as iw_err:
                 print(f"Error running scan command with iw: {iw_err}")
                 return []
        except subprocess.TimeoutExpired:
            print("Scanning timed out.")
            return []


        output = result.stdout
        aps = []

        # --- Parsing Logic for iwlist ---
        if 'iwlist' in result.args[1]:
            current_ap = {}
            for line in output.split('\n'):
                line = line.strip()
                if line.startswith('Cell'):
                    if current_ap:  # Save the previous AP before starting a new one
                        # Basic check for essential info before adding
                        if 'BSSID' in current_ap and 'ESSID' in current_ap and 'Channel' in current_ap:
                            aps.append(current_ap)
                        else:
                            pass # Skip incomplete entries quietly
                    current_ap = {}
                    match = re.search(r'Address:\s*([\da-fA-F:]+)', line, re.IGNORECASE)
                    if match:
                        current_ap['BSSID'] = match.group(1).upper() # Standardize BSSID case
                elif line.startswith('ESSID:"'):
                    current_ap['ESSID'] = line.split('"')[1]
                elif line.startswith('Channel:'):
                     # Handle potential extra text like "(secondary)"
                    channel_match = re.search(r'Channel:(\d+)', line)
                    if channel_match:
                        current_ap['Channel'] = channel_match.group(1)
                # Add other fields if needed (like Quality, Signal Strength etc.)

            if current_ap: # Add the last AP found
                 if 'BSSID' in current_ap and 'ESSID' in current_ap and 'Channel' in current_ap:
                    aps.append(current_ap)

        # --- Parsing Logic for iw (more modern) ---
        elif 'iw' in result.args[1]:
             current_ap = {}
             blocks = output.split('BSS ') # Split output by AP blocks
             for block in blocks[1:]: # Skip the first part before the first BSS
                lines = block.strip().split('\n')
                current_ap = {}
                bssid_match = re.match(r'([\da-fA-F:]+)\(on', lines[0])
                if bssid_match:
                    current_ap['BSSID'] = bssid_match.group(1).upper()

                for line in lines[1:]:
                    line = line.strip()
                    if line.startswith('SSID:'):
                        current_ap['ESSID'] = line.split(':', 1)[1].strip()
                    elif line.startswith('DS Parameter set: channel'):
                        current_ap['Channel'] = line.split('channel')[1].strip()
                    elif line.startswith('freq:'): # Alternative way to find channel for some outputs
                         if 'Channel' not in current_ap:
                             freq = int(line.split(':')[1].strip())
                             if 2412 <= freq <= 2484: # 2.4 GHz band
                                 channel = str(int((freq - 2407) / 5))
                                 current_ap['Channel'] = channel
                             elif 5180 <= freq <= 5825: # 5 GHz band (approximate mapping)
                                 channel = str(int((freq - 5000) / 5))
                                 current_ap['Channel'] = channel

                # Basic check for essential info before adding
                if 'BSSID' in current_ap and current_ap.get('ESSID') and 'Channel' in current_ap:
                     aps.append(current_ap)


        if not aps:
             print("No Wi-Fi networks found or parsed.")
        else:
             print(f"Found {len(aps)} Wi-Fi networks.")
        return aps

    except FileNotFoundError:
        print(f"Error: 'iwlist' or 'iw' command not found. Please ensure wireless tools are installed.")
        return []
    except subprocess.CalledProcessError as e:
        print(f"Error scanning APs: {e}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred during scanning: {e}")
        return []


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

# --- Main Execution ---
if __name__ == "__main__":
    # --- Configuration ---
    # !!!!! IMPORTANT: Replace "wlan0" with your actual wireless interface name !!!!!
    wireless_interface = "wlan0"
    # --- End Configuration ---

    # 1. Scan for Networks
    #banner("AirStrike")

    available_aps = run_scan(wireless_interface)
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

    else:
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