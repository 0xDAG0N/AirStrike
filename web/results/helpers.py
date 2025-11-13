import os
from web.shared import *

def get_attack_status():
    """
    Get the current status of any running attack.
    
    Returns:
        dict: Dictionary containing attack status information.
    """
    return {
        'running': attack_state['running'],
        'attack_type': attack_state['attack_type'],
        'target_network': attack_state['target_network'],
        'progress': attack_state['progress']
    }

def get_attack_log():
    """
    Get the log messages from the current or last attack.
    
    Returns:
        list: List of log message strings.
    """
    return attack_state['log']

def get_captured_handshakes():
    """
    Get a list of captured handshake files.
    
    Returns:
        list: List of dictionaries containing handshake information.
    """
    handshakes = []
    try:
        if not os.path.exists(config['output_dir']):
            return handshakes
            
        # Iterate through directories in the output directory
        for bssid_dir in os.listdir(config['output_dir']):
            bssid_path = os.path.join(config['output_dir'], bssid_dir)
            if os.path.isdir(bssid_path):
                # Look for capture files
                for file in os.listdir(bssid_path):
                    if file.endswith('.cap'):
                        file_path = os.path.join(bssid_path, file)
                        handshakes.append({
                            'bssid': bssid_dir.replace('-', ':'),
                            'file': file,
                            'path': file_path,
                            'size': os.path.getsize(file_path),
                            'date': os.path.getmtime(file_path)
                        })
    except Exception as e:
        print(f"Error getting handshakes: {e}")
    
    return handshakes 