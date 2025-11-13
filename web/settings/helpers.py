import os
import subprocess
from web.shared import *

def get_available_interfaces():
    """
    Get a list of available network interfaces.
    
    In a real implementation, this would use a library like netifaces
    or subprocess to get actual interfaces from the system.
    
    Returns:
        list: List of interface names.
    """
    # This is a placeholder - in a real implementation, you would
    # use a library like netifaces or subprocess to get actual interfaces
    try:
        # Example of how this might be implemented with subprocess
        # result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True, check=True)
        # Parse the output to extract interface names
        # For now, return a static list
        return ['wlan0', 'wlan1', 'eth0']
    except Exception as e:
        return ['wlan0']  # Fallback to default

def save_interface_setting(interface_name):
    """
    Save the selected interface to the configuration.
    
    Args:
        interface_name (str): The name of the interface to set.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        if interface_name:
            config['interface'] = interface_name
            return True
        return False
    except Exception:
        return False

def save_wordlist_setting(wordlist_path):
    """
    Save the wordlist path to the configuration.
    
    Args:
        wordlist_path (str): The path to the wordlist file.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        if wordlist_path:
            config['wordlist'] = wordlist_path
            return True
        return False
    except Exception:
        return False

def save_output_dir_setting(output_dir):
    """
    Save the output directory to the configuration and create it if it doesn't exist.
    
    Args:
        output_dir (str): The path to the output directory.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        if output_dir:
            config['output_dir'] = output_dir
            # Create directory if it doesn't exist
            os.makedirs(config['output_dir'], exist_ok=True)
            return True
        return False
    except Exception:
        return False 