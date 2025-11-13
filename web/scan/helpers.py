"""
Helper functions for network scanning functionality.
"""

import os
import sys
import time
import re
from web.shared import stats, logger, config, run_with_sudo

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from utils.network_utils import run_scan

def check_interface_status(interface='wlan0'):
    """
    Check if the specified interface exists and is a wireless interface.
    
    Args:
        interface (str): The network interface to check
    
    Returns:
        dict: Dictionary containing interface status information
    """
    status = {
        'name': interface,
        'exists': False,
        'is_wireless': False,
        'mode': None,
        'status': None
    }
    
    try:
        # Check if interface exists
        success, output, _ = run_with_sudo(f"ip link show {interface}")
        if success:
            status['exists'] = True
            
            # Check if it's UP
            if "UP" in output:
                status['status'] = "UP"
            elif "DOWN" in output:
                status['status'] = "DOWN"
            
            # Check if it's a wireless interface
            success, output, _ = run_with_sudo(f"iwconfig {interface}")
            if success and "no wireless extensions" not in output.lower():
                status['is_wireless'] = True
                
                # Check mode
                mode_match = re.search(r"Mode:(\w+)", output)
                if mode_match:
                    status['mode'] = mode_match.group(1)
        
        return status
    except Exception as e:
        logger.error(f"Error checking interface status: {str(e)}")
        return status

def scan_wifi_networks(interface='wlan0'):
    """
    Scan for available WiFi networks using the specified interface.
    
    Args:
        interface (str): The network interface to use for scanning
    
    Returns:
        tuple: (list of networks, error message or None)
            - List of network dictionaries, or empty list if an error occurs
            - Error message string or None if successful
    """
    try:
        logger.info(f"Scanning for WiFi networks on interface {interface}")
        
        # First check if the interface exists
        success, output, error = run_with_sudo(f"ip link show {interface}")
        if not success:
            logger.error(f"Interface {interface} does not exist or cannot be accessed: {error}")
            return [], f"Interface {interface} not found or inaccessible"
        
        # Check if NetworkManager is managing the interface and might be causing conflicts
        success, output, error = run_with_sudo("ps aux | grep NetworkManager")
        if success and "NetworkManager" in output:
            logger.warning("NetworkManager detected, may interfere with scanning")
            
            # Try to temporarily disable NetworkManager for this interface
            try:
                run_with_sudo(f"nmcli device set {interface} managed no")
                logger.info(f"Temporarily disabled NetworkManager for {interface}")
                # Remember to re-enable it later
            except Exception as nm_err:
                logger.warning(f"Could not disable NetworkManager: {nm_err}")
        
        # Run the scan
        networks = run_scan(interface)
        
        # Re-enable NetworkManager if we disabled it
        try:
            run_with_sudo(f"nmcli device set {interface} managed yes")
        except Exception:
            pass  # Ignore errors here
        
        # Update stats
        if networks:
            stats['networks_count'] = len(networks)
            logger.info(f"Found {len(networks)} WiFi networks")
        else:
            logger.info("No WiFi networks found")
            
        return networks, None
    except Exception as e:
        logger.error(f"Error scanning WiFi networks: {str(e)}")
        
        # Try to restore NetworkManager if needed
        try:
            run_with_sudo(f"nmcli device set {interface} managed yes")
        except Exception:
            pass  # Ignore errors here
            
        return [], str(e) 