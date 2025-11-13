import subprocess
import re
import sys
import os
import time

# Import the shared module for sudo functionality
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from web.shared import run_with_sudo, config, logger

def set_monitor_mode(interface_name):
    """
    Set the wireless interface to monitor mode.
    
    Args:
        interface_name (str): Name of the wireless interface
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Use our sudo function instead of direct subprocess calls
        success1, out1, err1 = run_with_sudo(f"ifconfig {interface_name} down")
        success2, out2, err2 = run_with_sudo(f"iwconfig {interface_name} mode monitor")
        success3, out3, err3 = run_with_sudo(f"ifconfig {interface_name} up")
        
        if success1 and success2 and success3:
            logger.info(f"Interface {interface_name} set to monitor mode")
            return True
        else:
            # Log the errors
            if not success1:
                logger.error(f"Failed to bring interface down: {err1}")
            if not success2:
                logger.error(f"Failed to set monitor mode: {err2}")
            if not success3:
                logger.error(f"Failed to bring interface up: {err3}")
                
            # If we need sudo authentication, return False to trigger the auth flow
            if "incorrect password" in (err1 + err2 + err3).lower() or "sudo" in (err1 + err2 + err3).lower():
                config['sudo_configured'] = False
                
            return False
    except Exception as e:
        logger.error(f"Error setting {interface_name} to monitor mode: {str(e)}")
        return False


def set_managed_mode(interface_name):
    """
    Set the wireless interface to managed mode.
    
    Args:
        interface_name (str): Name of the wireless interface
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Use our sudo function instead of direct subprocess calls
        success1, out1, err1 = run_with_sudo(f"ifconfig {interface_name} down")
        success2, out2, err2 = run_with_sudo(f"iwconfig {interface_name} mode managed")
        success3, out3, err3 = run_with_sudo(f"ifconfig {interface_name} up")
        
        if success1 and success2 and success3:
            logger.info(f"Interface {interface_name} set to managed mode")
            return True
        else:
            # Log the errors
            if not success1:
                logger.error(f"Failed to bring interface down: {err1}")
            if not success2:
                logger.error(f"Failed to set managed mode: {err2}")
            if not success3:
                logger.error(f"Failed to bring interface up: {err3}")
                
            # If we need sudo authentication, return False to trigger the auth flow
            if "incorrect password" in (err1 + err2 + err3).lower() or "sudo" in (err1 + err2 + err3).lower():
                config['sudo_configured'] = False
                
            return False
    except Exception as e:
        logger.error(f"Error setting {interface_name} to managed mode: {str(e)}")
        return False

global available_aps
def run_scan(interface):
    available_aps = []
    try:
        result = subprocess.run(['iwlist', interface, 'scanning'], capture_output=True, text=True, check=True)
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
        return available_aps

    except subprocess.CalledProcessError as e:
        print(f"Error scanning APs: {e}")
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