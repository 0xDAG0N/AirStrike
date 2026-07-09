/**
 * Scanner Module - Network scanning functionality
 */

import { networkApi } from './api.js';
import { showAlert, displayNetworks } from './ui.js';
import { saveNetworkSelection } from './state.js';

/**
 * Scan for available networks
 */
export async function scanNetworks() {
    const scanBtn = document.getElementById('scan-networks-btn');
    const networkList = document.getElementById('network-list');
    const troubleshootingTips = document.getElementById('troubleshooting-tips');
    
    if (scanBtn) {
        scanBtn.disabled = true;
        scanBtn.textContent = 'Scanning...';
    }
    
    if (networkList) {
        networkList.innerHTML = '<div class="network-item">Scanning for networks...</div>';
    }
    
    try {
        const networks = await networkApi.scanNetworks();
        
        // If networks is null or empty array, it might be due to auth redirect
        if (!networks || networks.length === 0) {
            if (networkList) {
                networkList.innerHTML = '<div class="network-item error">Authentication required or no networks found. Please check settings.</div>';
            }
            if (troubleshootingTips) troubleshootingTips.classList.remove('d-none');
            return;
        }
        
        // Display networks if we have them
        if (Array.isArray(networks) && networks.length > 0) {
        displayNetworks(networks);
            if (troubleshootingTips) troubleshootingTips.classList.add('d-none');
        } else {
            if (networkList) {
                networkList.innerHTML = '<div class="network-item error">No networks found. Try running diagnostics.</div>';
            }
            if (troubleshootingTips) troubleshootingTips.classList.remove('d-none');
        }
    } catch (error) {
        console.error('Error scanning networks:', error);
        if (networkList) {
            networkList.innerHTML = `<div class="network-item error">Error: ${error.message || 'Failed to scan networks'}</div>`;
        }
        if (troubleshootingTips) troubleshootingTips.classList.remove('d-none');
        showAlert('Error scanning networks. Please try again.', 'danger');
    } finally {
        if (scanBtn) {
            scanBtn.disabled = false;
            scanBtn.textContent = 'Scan Networks';
        }
    }
}

/**
 * Check interface status
 */
export async function checkInterfaceStatus() {
    const statusDiv = document.getElementById('interface-status');
    const troubleshootingTips = document.getElementById('troubleshooting-tips');
    
    if (!statusDiv) return;
    
    try {
        const data = await networkApi.checkInterfaceStatus();
        
        // If authentication failed or other error occurred
        if (data.success === false) {
            // Show authentication error message
            statusDiv.className = 'alert alert-warning mb-3';
            statusDiv.innerHTML = `
                <strong>Authentication Required:</strong> ${data.error || 'Administrator privileges needed'}
                <div class="mt-2">
                    <a href="/settings" class="btn btn-sm btn-warning">Configure Authentication</a>
                </div>
            `;
            if (troubleshootingTips) troubleshootingTips.classList.remove('d-none');
            return;
        }
        
        if (data.interface_status) {
            if (data.interface_status.exists) {
                if (data.interface_status.is_wireless) {
                    statusDiv.className = 'alert alert-success mb-3';
                    statusDiv.innerHTML = `
                        <strong>Interface Ready:</strong> ${data.interface_status.name} is a wireless interface.
                        <div class="mt-2">
                            <small>Mode: ${data.interface_status.mode || 'Unknown'}</small><br>
                            <small>Status: ${data.interface_status.status || 'Unknown'}</small>
                        </div>
                    `;
                } else {
                    statusDiv.className = 'alert alert-warning mb-3';
                    statusDiv.innerHTML = `
                        <strong>Warning:</strong> ${data.interface_status.name} does not appear to be a wireless interface.
                        <div class="mt-2">
                            <a href="/settings" class="btn btn-sm btn-warning">Change Interface</a>
                        </div>
                    `;
                    if (troubleshootingTips) troubleshootingTips.classList.remove('d-none');
                }
            } else {
                statusDiv.className = 'alert alert-danger mb-3';
                statusDiv.innerHTML = `
                    <strong>Error:</strong> Interface ${data.interface_status.name} not found.
                    <div class="mt-2">
                        <a href="/settings" class="btn btn-sm btn-danger">Configure Interface</a>
                    </div>
                `;
                if (troubleshootingTips) troubleshootingTips.classList.remove('d-none');
            }
        } else {
            statusDiv.className = 'alert alert-warning mb-3';
            statusDiv.innerHTML = `
                <strong>Warning:</strong> Could not check interface status.
                <div class="mt-2">
                    <a href="/settings" class="btn btn-sm btn-warning">Configure Interface</a>
                </div>
            `;
            if (troubleshootingTips) troubleshootingTips.classList.remove('d-none');
        }
    } catch (error) {
        console.error('Error checking interface status:', error);
        statusDiv.className = 'alert alert-danger mb-3';
        statusDiv.innerHTML = `
            <strong>Error:</strong> Could not check interface status.
            <div class="mt-2">
                <a href="/settings" class="btn btn-sm btn-danger">Configure Interface</a>
            </div>
        `;
        if (troubleshootingTips) troubleshootingTips.classList.remove('d-none');
    }
}

/**
 * Initialize network scanning functionality
 * This is called by the scan page module
 */
export function initScanner() {
    // Add event delegation for network selection
    const networkList = document.getElementById('network-list');
    if (networkList) {
        networkList.addEventListener('click', handleNetworkSelection);
    }
}

/**
 * Handle network selection
 * @param {Event} e - The click event
 */
function handleNetworkSelection(e) {
    const networkItem = e.target.closest('.network-item');
    if (!networkItem) return;
    
    // Skip if this is an error message
    if (networkItem.classList.contains('error')) return;
    
    // Remove selection from all networks
    document.querySelectorAll('.network-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Add selection to clicked network
    networkItem.classList.add('selected');
    
    // Store selected network data
    const selectedNetwork = {
        bssid: networkItem.dataset.bssid,
        essid: networkItem.dataset.essid,
        channel: networkItem.dataset.channel
    };
    
    // Save to state and session storage
    saveNetworkSelection(selectedNetwork);
    
    // Enable the continue button
    const continueBtn = document.getElementById('continue-btn');
    if (continueBtn) {
        continueBtn.disabled = false;
    }
} 