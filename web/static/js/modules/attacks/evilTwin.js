/**
 * Evil Twin Attack Module
 */

/**
 * Generate HTML for evil twin attack configuration
 * @param {Object} network - The selected network
 * @returns {string} HTML for the configuration form
 */
export function configureEvilTwin(network) {
    return `
        <div class="form-group">
            <label for="evil-twin-channel">Channel:</label>
            <input type="number" id="evil-twin-channel" class="form-control" value="${network?.channel || '1'}" min="1" max="14">
        </div>
        <div class="form-group">
            <label for="evil-twin-captive">Enable Captive Portal:</label>
            <select id="evil-twin-captive" class="form-control">
                <option value="true">Yes</option>
                <option value="false">No</option>
            </select>
        </div>
        <div class="alert alert-info">
            <p><strong>Evil Twin Attack:</strong> This attack will create a fake access point with the same SSID as the target network.</p>
            <p><strong>Target:</strong> ${network?.essid || 'Hidden Network'} (${network?.bssid || 'Unknown'})</p>
        </div>
    `;
} 