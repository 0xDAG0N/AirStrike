"""
Scan Blueprint
--------------

This blueprint handles all functionality related to network scanning,
including starting, stopping, and viewing scan results.
"""

import subprocess
import threading
import time
import re
from flask import Blueprint, jsonify, request
from scapy.all import sniff, Dot11, Dot11Beacon, Dot11ProbeResp, Dot11Elt
from airstrike import state
from airstrike import utils

scan_bp = Blueprint('scan', __name__, url_prefix='/scan')

def packet_handler(packet):
    """
    Processes sniffed packets to identify access points and clients.
    """
    if packet.haslayer(Dot11):
        # Identify Access Points from Beacon and Probe Response frames
        if packet.type == 0 and (packet.subtype == 8 or packet.subtype == 5): # Beacon or Probe Response
            bssid = packet.addr2
            if bssid not in state.access_points:
                try:
                    essid = packet[Dot11Elt].info.decode()
                except UnicodeDecodeError:
                    essid = packet[Dot11Elt].info.hex() # Fallback for weird ESSIDs
                
                if essid: # Only add if ESSID is not empty
                    stats = packet[Dot11Beacon].network_stats()
                    channel = stats.get("channel")
                    crypto = stats.get("crypto")
                    
                    state.access_points[bssid] = {
                        'essid': essid,
                        'bssid': bssid,
                        'channel': channel,
                        'crypto': crypto,
                        'clients': {}
                    }
                    state.socketio.emit('new_ap', state.access_points[bssid])
        
        # Identify Clients from data frames
        elif packet.type == 2: # Data Frame
            addr1 = packet.addr1 # Destination
            addr2 = packet.addr2 # Source

            # Client to AP
            if addr1 and addr2 and addr1 in state.access_points:
                if addr2 not in state.access_points[addr1]['clients']:
                    state.access_points[addr1]['clients'][addr2] = {'mac': addr2}
                    state.socketio.emit('new_client', {'bssid': addr1, 'client': state.access_points[addr1]['clients'][addr2]})
            
            # AP to Client
            elif addr1 and addr2 and addr2 in state.access_points:
                 if addr1 not in state.access_points[addr2]['clients']:
                    state.access_points[addr2]['clients'][addr1] = {'mac': addr1}
                    state.socketio.emit('new_client', {'bssid': addr2, 'client': state.access_points[addr2]['clients'][addr1]})


def start_sniffing(interface):
    """
    Starts the sniffing process in a separate thread.
    """
    print(f"Starting sniffing on interface {interface}")
    sniff(iface=interface, prn=packet_handler, store=0, stop_filter=lambda x: not state.is_scanning)
    print("Sniffing stopped.")

@scan_bp.route('/start', methods=['POST'])
def start_scan():
    """API endpoint to start a network scan."""
    if state.is_scanning:
        return jsonify({"status": "error", "message": "Scan already in progress."}), 400

    if not state.interface:
        return jsonify({"status": "error", "message": "Network interface not set."}), 400

    # Reset previous scan results
    state.access_points.clear()
    state.clients.clear()
    state.socketio.emit('scan_reset')

    state.is_scanning = True
    
    # Run sniffing in a background thread to not block the web server
    scan_thread = threading.Thread(target=start_sniffing, args=(state.interface,))
    scan_thread.daemon = True
    scan_thread.start()
    
    state.socketio.emit('scan_started')
    print("Scan started.")
    return jsonify({"status": "success", "message": "Scan started."})


@scan_bp.route('/stop', methods=['POST'])
def stop_scan():
    """API endpoint to stop the current network scan."""
    if not state.is_scanning:
        return jsonify({"status": "error", "message": "No scan is in progress."}), 400

    state.is_scanning = False
    state.socketio.emit('scan_stopped')
    print("Scan stopped.")
    return jsonify({"status": "success", "message": "Scan stopped."})

@scan_bp.route('/results', methods=['GET'])
def get_scan_results():
    """API endpoint to get the current scan results."""
    return jsonify(list(state.access_points.values()))

