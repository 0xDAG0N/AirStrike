/**
 * UI Module - Common UI manipulation functions
 */

let lastPasswordAlert = null;

/**
 * Escape a value for safe interpolation into HTML (text or double-quoted attribute).
 * Attacker-controlled data — e.g. a nearby AP's SSID, or a log line echoing one — must
 * never reach innerHTML unescaped.
 * @param {*} value
 * @returns {string}
 */
export function escapeHtml(value) {
    return String(value === null || value === undefined ? '' : value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

/**
 * Show an alert message
 * @param {string} message - The message to display
 * @param {string} type - The alert type (success, danger, warning, info)
 * @param {number} duration - How long to show the alert in milliseconds
 */
export function showAlert(message, type = 'info', duration = 5000) {
    try {
    const alertsContainer = document.getElementById('alerts-container');
    if (!alertsContainer) return;
    
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type}`;
    alertElement.textContent = message;
    
    alertsContainer.appendChild(alertElement);
    
    // Auto-remove after specified duration
    setTimeout(() => {
        alertElement.remove();
    }, duration);
    } catch (error) {
        console.error('Error showing alert:', error);
    }
}

/**
 * Update attack status in UI
 * @param {boolean} isRunning - Whether the attack is running
 */
export function updateAttackStatus(isRunning) {
    try {
    const startBtn = document.getElementById('start-attack-btn');
    const stopBtn = document.getElementById('stop-attack-btn');
    
    if (startBtn && stopBtn) {
        startBtn.disabled = isRunning;
        stopBtn.disabled = !isRunning;
    }
    
    const statusIndicator = document.getElementById('attack-status');
    if (statusIndicator) {
        statusIndicator.className = isRunning ? 'status-running' : 'status-stopped';
        statusIndicator.textContent = isRunning ? 'Running' : 'Stopped';
        }
    } catch (error) {
        console.error('Error updating attack status:', error);
    }
}

/**
 * Update attack log with latest entries
 * @param {Array} logEntries - The log entries to display
 */
export function updateAttackLog(logEntries) {
    try {
    const logContainer = document.getElementById('attack-log');
    if (!logContainer) return;
    
    let logHTML = '';
    logEntries.forEach(entry => {
        const { className, message } = formatLogEntry(entry);
        logHTML += `<div class="log-entry ${className}">${escapeHtml(message)}</div>`;
    });
    
    logContainer.innerHTML = logHTML;
    logContainer.scrollTop = logContainer.scrollHeight; // Auto-scroll to bottom
    } catch (error) {
        console.error('Error updating attack log:', error);
    }
}

function formatLogEntry(entry) {
    const safeEntry = entry || '';
    let className = '';
    let message = safeEntry;
    
    const passwordMatch = safeEntry.match(/Password found:\s*(.+)$/i);
    if (passwordMatch) {
        const password = passwordMatch[1].trim();
        className = 'password';
        message = `Password: ${password}`;
        triggerPasswordAlert(password);
    } else {
        if (safeEntry.includes('[+]')) className = 'success';
        if (safeEntry.includes('[-]')) className = 'error';
        if (safeEntry.includes('[!]')) className = 'warning';
    }
    
    return { className, message };
}

function triggerPasswordAlert(password) {
    if (!password || typeof window === 'undefined') return;
    if (lastPasswordAlert === password) return;
    
    lastPasswordAlert = password;
    // Surface the cracked password as a persistent success toast (was a blocking window.alert
    // that froze the UI and is inaccessible to screen readers).
    showAlert(`Password found: ${password}`, 'success', 30000);
}

/**
 * Update dashboard statistics
 * @param {Object} stats - The statistics to display
 */
export function updateDashboardStats(stats) {
    try {
    const networksCount = document.getElementById('networks-count');
    const attacksCount = document.getElementById('attacks-count');
    const capturesCount = document.getElementById('captures-count');
    
    if (networksCount) networksCount.textContent = stats.networks_count;
    if (attacksCount) attacksCount.textContent = stats.attacks_count;
    if (capturesCount) capturesCount.textContent = stats.captures_count;
    } catch (error) {
        console.error('Error updating dashboard stats:', error);
    }
}

/**
 * Display networks in the UI
 * @param {Array} networks - Array of network objects
 */
export function displayNetworks(networks) {
    try {
    const networkList = document.getElementById('network-list');
    if (!networkList) return;
    
    let html = '';
    networks.forEach(network => {
        const bssid = escapeHtml(network.BSSID);
        const essid = escapeHtml(network.ESSID || 'Hidden Network');
        const essidAttr = escapeHtml(network.ESSID || '');
        const channel = escapeHtml(network.Channel);
        html += `
                <div class="network-item" role="option" tabindex="0" aria-selected="false" aria-label="Network ${essid}, BSSID ${bssid}, channel ${channel}" data-bssid="${bssid}" data-essid="${essidAttr}" data-channel="${channel}">
                <div class="network-name">${essid}</div>
                <div class="network-details">
                    <span class="network-bssid">${bssid}</span>
                    <span class="network-channel">CH: ${channel}</span>
                </div>
            </div>
        `;
    });
    
    networkList.innerHTML = html;
    } catch (error) {
        console.error('Error displaying networks:', error);
        showAlert('Error displaying networks', 'danger');
    }
}

/**
 * Display network info in the UI
 * @param {Object} network - The network to display
 */
export function displayNetworkInfo(network) {
    try {
    const networkInfo = document.getElementById('selected-network-info');
    if (!networkInfo) return;
    
    if (network) {
        networkInfo.innerHTML = `
            <div class="card">
                <div class="card-header">Selected Network</div>
                <div class="card-body">
                    <p><strong>SSID:</strong> ${escapeHtml(network.essid || 'Hidden Network')}</p>
                    <p><strong>BSSID:</strong> ${escapeHtml(network.bssid)}</p>
                    <p><strong>Channel:</strong> ${escapeHtml(network.channel)}</p>
                </div>
            </div>
        `;
    } else {
        networkInfo.innerHTML = `
            <div class="alert alert-warning">
                No network selected. Please <a href="/scan">scan and select a network</a> first.
            </div>
        `;
        }
    } catch (error) {
        console.error('Error displaying network info:', error);
    }
} 
