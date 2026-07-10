/**
 * Cracking (Handshake) Attack Module
 */

import { escapeHtml } from '../ui.js';

/**
 * Generate HTML for handshake attack configuration
 * @param {Object} network - The selected network
 * @returns {string} HTML for the configuration form
 */
export function configureHandshake(network) {
    return `
        <div class="form-group">
            <label for="handshake-wordlist">Wordlist Path:</label>
            <input type="text" id="handshake-wordlist" class="form-control" value="/usr/share/wordlists/rockyou.txt">
        </div>
        <div class="form-group">
            <label for="handshake-duration">Capture Duration (minutes):</label>
            <input type="number" id="handshake-duration" class="form-control" value="5" min="1">
        </div>
        <div class="alert alert-info">
            <p><strong>Cracking Attack:</strong> This attack captures the WPA/WPA2 handshake and immediately attempts to crack it with the selected wordlist.</p>
            <p><strong>Target:</strong> ${escapeHtml(network?.essid || 'Hidden Network')} (${escapeHtml(network?.bssid || 'Unknown')})</p>
        </div>
    `;
} 
