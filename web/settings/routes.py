from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
import os
import sys

# Add the project root directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from web.shared import *
from .helpers import (
    get_available_interfaces, 
    save_interface_setting, 
    save_wordlist_setting, 
    save_output_dir_setting
)

settings_bp = Blueprint('settings', __name__)
@settings_bp.route('/settings')
def show_settings():
    # Get available interfaces
    interfaces = get_available_interfaces()
    return render_template('settings.html', 
                          interfaces=interfaces, 
                          current_interface=config['interface'],
                          default_wordlist=config['wordlist'],
                          output_dir=config['output_dir'])

# API Endpoints


@settings_bp.route('/get_interfaces')
def get_interfaces():
    interfaces = get_available_interfaces()
    return jsonify({
        'interfaces': interfaces,
        'current_interface': config['interface']
    })

@settings_bp.route('/set_interface', methods=['POST'])
def set_interface():
    data = request.json
    if 'interface' in data:
        success = save_interface_setting(data['interface'])
        return jsonify({'success': success})
    return jsonify({'success': False, 'error': 'No interface provided'})

@settings_bp.route('/save_wordlist', methods=['POST'])
def save_wordlist():
    data = request.json
    if 'wordlist' in data:
        success = save_wordlist_setting(data['wordlist'])
        return jsonify({'success': success})
    return jsonify({'success': False, 'error': 'No wordlist provided'})

@settings_bp.route('/save_output_dir', methods=['POST'])
def save_output_dir():
    data = request.json
    if 'output_dir' in data:
        success = save_output_dir_setting(data['output_dir'])
        return jsonify({'success': success})
    return jsonify({'success': False, 'error': 'No output directory provided'})

# Removed sudo_auth route since we're enforcing root execution at startup
