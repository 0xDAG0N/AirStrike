"""
Helper functions for diagnostics module.
"""

import os
import sys
import platform
import re
import subprocess
from datetime import datetime

# Add the project root directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from web.shared import logger, config, run_with_sudo

def get_interface_details(interface):
    """
    Get detailed information about a network interface.
    
    Args:
        interface (str): The network interface name
        
    Returns:
        dict: Dictionary containing interface details
    """
    details = {
        'name': interface,
        'exists': False,
        'is_wireless': False,
        'mode': 'Unknown',
        'status': 'Unknown',
        'mac_address': 'Unknown',
        'driver': 'Unknown',
        'chipset': 'Unknown',
        'supports_monitor': False
    }
    
    try:
        # Check if interface exists
        success, output, _ = run_with_sudo(f"ip link show {interface}")
        if success:
            details['exists'] = True
            
            # Check if it's UP
            if "UP" in output:
                details['status'] = "UP"
            elif "DOWN" in output:
                details['status'] = "DOWN"
            
            # Get MAC address
            mac_match = re.search(r'link/ether\s+([0-9a-f:]{17})', output, re.IGNORECASE)
            if mac_match:
                details['mac_address'] = mac_match.group(1)
        
        # Check if it's a wireless interface
        success, output, _ = run_with_sudo(f"iwconfig {interface}")
        if success and "no wireless extensions" not in output.lower():
            details['is_wireless'] = True
            
            # Check mode
            mode_match = re.search(r"Mode:(\w+)", output)
            if mode_match:
                details['mode'] = mode_match.group(1)
        
        # Try to get driver information
        success, output, _ = run_with_sudo(f"ethtool -i {interface}")
        if success:
            driver_match = re.search(r"driver:\s+(\w+)", output)
            if driver_match:
                details['driver'] = driver_match.group(1)
            
            # Try to get chipset info
            chipset_match = re.search(r"bus-info:\s+(.+)", output)
            if chipset_match:
                details['chipset'] = chipset_match.group(1)
        
        # Check if monitor mode is supported
        success, output, _ = run_with_sudo(f"iw phy `iw dev {interface} info | grep wiphy | awk '{{print $2}}'` info")
        if success and "monitor" in output:
            details['supports_monitor'] = True
        
        return details
    except Exception as e:
        logger.error(f"Error getting interface details: {str(e)}")
        return details

def get_system_info():
    """
    Get system information.
    
    Returns:
        dict: Dictionary containing system information
    """
    info = {
        'os': 'Unknown',
        'kernel': 'Unknown',
        'hostname': 'Unknown',
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'python_version': platform.python_version(),
        'network_manager': 'Not detected'
    }
    
    try:
        # Get OS information
        if os.path.exists('/etc/os-release'):
            with open('/etc/os-release', 'r') as f:
                os_release = f.read()
                name_match = re.search(r'PRETTY_NAME="(.+)"', os_release)
                if name_match:
                    info['os'] = name_match.group(1)
        
        # Get kernel version
        success, output, _ = run_with_sudo("uname -r")
        if success:
            info['kernel'] = output.strip()
        
        # Get hostname
        success, output, _ = run_with_sudo("hostname")
        if success:
            info['hostname'] = output.strip()
        
        # Check if NetworkManager is running
        success, output, _ = run_with_sudo("systemctl is-active NetworkManager")
        if success and "active" in output:
            info['network_manager'] = 'Active'
        else:
            # Try another method
            success, output, _ = run_with_sudo("ps aux | grep NetworkManager")
            if success and "NetworkManager" in output and not output.strip().endswith("grep NetworkManager"):
                info['network_manager'] = 'Running'
        
        return info
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return info 