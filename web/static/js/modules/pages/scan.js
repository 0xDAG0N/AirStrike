/**
 * Scan Page Module
 */

import { initScanner, scanNetworks, checkInterfaceStatus } from '../scanner.js';
import { getStoredNetwork } from '../state.js';
import { showAlert } from '../ui.js';

/**
 * Initialize scan page
 */
export function initScanPage() {
    try {
        console.log("Initializing scan page...");
        
        // Initialize scanner functionality (event listeners for network selection)
    initScanner();
        
        // Set initial state of continue button
        const continueBtn = document.getElementById('continue-btn');
        if (continueBtn) {
            continueBtn.disabled = true;
        }
        
        // Check interface status when page loads
        checkInterfaceStatus().catch(error => {
            console.error("Error checking interface status:", error);
            showAlert("Error checking interface status. Please check your settings.", "warning");
        });
        
        // Add event listener for scan button
        const scanBtn = document.getElementById('scan-networks-btn');
        if (scanBtn) {
            scanBtn.addEventListener('click', () => {
                scanNetworks().catch(error => {
                    console.error("Error scanning networks:", error);
                    showAlert("Error scanning networks. Please check your settings.", "danger");
                });
            });
        }
        
        // Check if a network was previously selected
        const storedNetwork = getStoredNetwork();
        if (storedNetwork) {
            const networkList = document.getElementById('network-list');
            if (networkList) {
                // Show a message about the previously selected network
                networkList.innerHTML = `
                    <div class="alert alert-info">
                        Previously selected network: ${storedNetwork.essid || 'Hidden Network'} (${storedNetwork.bssid})
                        <br>
                        Click "Scan Networks" to select a different network.
                    </div>
                `;
                
                // Enable the continue button
                if (continueBtn) {
                    continueBtn.disabled = false;
                }
            }
        }
    } catch (error) {
        console.error('Error initializing scan page:', error);
        showAlert('Error initializing scan page. Please refresh and try again.', 'danger');
    }
} 