/**
 * Handshake Attack Module
 */

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
            <p><strong>Handshake Capture Attack:</strong> This attack will capture the WPA/WPA2 handshake and attempt to crack the password using the specified wordlist.</p>
            <p><strong>Target:</strong> ${network?.essid || 'Hidden Network'} (${network?.bssid || 'Unknown'})</p>
        </div>
    `;
} 