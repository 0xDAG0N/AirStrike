/**
 * Deauth Attack Module
 */

/**
 * Generate HTML for deauth attack configuration
 * @param {Object} network - The selected network
 * @returns {string} HTML for the configuration form
 */
export function configureDeauth(network) {
    return `
        <div class="form-group">
            <label for="deauth-client">Target Client MAC (optional):</label>
            <input type="text" id="deauth-client" class="form-control" placeholder="FF:FF:FF:FF:FF:FF for all clients">
        </div>
        <div class="form-group">
            <label for="deauth-count">Packet Count:</label>
            <input type="number" id="deauth-count" class="form-control" value="10" min="1">
        </div>
        <div class="form-group">
            <label for="deauth-interval">Interval (seconds):</label>
            <input type="number" id="deauth-interval" class="form-control" value="0.1" min="0.1" step="0.1">
        </div>
        <div class="alert alert-info">
            <p><strong>Deauthentication Attack:</strong> This attack will send deauthentication packets to force clients to disconnect from the selected access point.</p>
            <p><strong>Target:</strong> ${network?.essid || 'Hidden Network'} (${network?.bssid || 'Unknown'})</p>
        </div>
    `;
} 