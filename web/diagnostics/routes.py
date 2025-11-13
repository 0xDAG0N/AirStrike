from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
import os
import sys
import subprocess
import shutil

# Add the project root directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from web.shared import logger, config, run_with_sudo
from .helpers import get_interface_details, get_system_info

diagnostics_bp = Blueprint('diagnostics', __name__)

@diagnostics_bp.route('/diagnostics')
def show_diagnostics():
    """Render the diagnostics page"""
    # Root execution is enforced at startup, so no need to check here anymore
    
    # Get system info
    system_info = get_system_info()
    # Get interface details
    interface_details = get_interface_details(config['interface'])
    
    # Get available diagnostic commands
    diagnostic_commands = [
        {'name': 'iwconfig', 'description': 'Show wireless interfaces'},
        {'name': 'ifconfig', 'description': 'Show all interfaces'},
        {'name': 'ip a', 'description': 'Show all interfaces (modern version)'},
        {'name': f"iwlist {config['interface']} scanning", 'description': 'Scan for networks'},
        {'name': f"iw dev {config['interface']} scan", 'description': 'Alternative network scan'},
        {'name': 'rfkill list', 'description': 'Check for blocked interfaces'},
        {'name': 'lsmod | grep -E "^(cfg|mac|rtl|ath|iw)"', 'description': 'Show WiFi kernel modules'}
    ]
    
    return render_template('diagnostics.html', 
                          system_info=system_info,
                          interface_details=interface_details,
                          diagnostic_commands=diagnostic_commands)

@diagnostics_bp.route('/run_diagnostic', methods=['POST'])
def run_diagnostic():
    """Run a diagnostic command with sudo privileges"""
    # Root execution is enforced at startup, so no need to check here anymore
    
    command = request.form.get('command')
    if not command:
        flash('No command provided', 'danger')
        return redirect(url_for('diagnostics.show_diagnostics'))
    
    # Only allow certain safe diagnostic commands
    allowed_commands = [
        'iwconfig', 
        'ifconfig',
        'ip a',
        'iwlist',
        'iw dev',
        'rfkill list',
        'lsmod | grep -E "^(cfg|mac|rtl|ath|iw)"'
    ]
    
    # Check if the command is allowed
    command_allowed = False
    for allowed in allowed_commands:
        if command.startswith(allowed):
            command_allowed = True
            break
    
    if not command_allowed:
        flash(f'Command not allowed. Allowed commands: {", ".join(allowed_commands)}', 'danger')
        return redirect(url_for('diagnostics.show_diagnostics'))
    
    # Run the command
    success, output, error = run_with_sudo(command)
    
    # Show the result
    if success:
        result = output
        flash('Command executed successfully', 'success')
    else:
        result = f"Error: {error}"
        flash('Command failed', 'danger')
    
    return render_template('command_result.html', 
                          command=command, 
                          result=result,
                          success=success,
                          back_url=url_for('diagnostics.show_diagnostics'))

@diagnostics_bp.route('/check_permissions')
def check_permissions():
    """Check if the application has the necessary permissions."""
    results = {
        'root_privileges': os.geteuid() == 0,
        'scapy_installed': shutil.which('scapy') is not None,
        'iwconfig_installed': shutil.which('iwconfig') is not None,
        'ifconfig_installed': shutil.which('ifconfig') is not None,
        'aircrack_installed': shutil.which('aircrack-ng') is not None,
        'tshark_installed': shutil.which('tshark') is not None,
        'can_set_monitor_mode': False,
        'can_inject_packets': False
    }
    
    # Check if we can set monitor mode (requires root)
    if results['root_privileges'] and results['iwconfig_installed']:
        interface = config['interface']
        try:
            # Try to briefly set monitor mode and check if it works
            subprocess.run(['sudo', 'iwconfig', interface, 'mode', 'monitor'], 
                          check=True, capture_output=True, timeout=5)
            results['can_set_monitor_mode'] = True
            
            # Set it back to managed mode
            subprocess.run(['sudo', 'iwconfig', interface, 'mode', 'managed'], 
                          check=True, capture_output=True, timeout=5)
        except Exception as e:
            results['error_monitor_mode'] = str(e)
    
    # Check if we can inject packets (requires root and monitor mode)
    if results['root_privileges'] and results['can_set_monitor_mode']:
        try:
            from scapy.all import RadioTap, Dot11, Dot11Deauth, conf
            results['can_inject_packets'] = True
        except ImportError:
            results['error_scapy'] = "Scapy not properly installed"
        except Exception as e:
            results['error_scapy'] = str(e)
    
    return jsonify(results)

@diagnostics_bp.route('/test_deauth')
def test_deauth():
    """Test a single deauthentication packet (without actually sending it)."""
    try:
        from scapy.all import RadioTap, Dot11, Dot11Deauth, conf
        test_bssid = "00:11:22:33:44:55"  # Dummy BSSID for testing
        test_client = "FF:FF:FF:FF:FF:FF"  # Broadcast
        
        # Create but don't send the packet
        dot11 = Dot11(addr1=test_client, addr2=test_bssid, addr3=test_bssid)
        deauth_frame = RadioTap()/dot11/Dot11Deauth(reason=7)
        
        return jsonify({
            'success': True,
            'packet_created': True,
            'root_privileges': os.geteuid() == 0,
            'message': "Deauth packet created successfully but not sent. This confirms scapy is working correctly.",
            'would_send_to': {
                'interface': conf.iface,
                'bssid': test_bssid,
                'client': test_client
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'root_privileges': os.geteuid() == 0
        }) 