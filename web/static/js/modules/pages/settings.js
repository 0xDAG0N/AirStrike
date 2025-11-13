/**
 * Settings Page Module
 */

import { networkApi } from '../api.js';
import { showAlert } from '../ui.js';

/**
 * Initialize settings page
 */
export function initSettingsPage() {
    try {
        console.log("Initializing settings page...");
        
    // Add event listener for interface selection
    const interfaceSelect = document.getElementById('interface-select');
    if (interfaceSelect) {
        interfaceSelect.addEventListener('change', function() {
            setInterface(this.value);
        });
        }
        
        // Add event listener for sudo password form
        const sudoForm = document.getElementById('sudo-auth-form');
        if (sudoForm) {
            sudoForm.addEventListener('submit', function(e) {
                e.preventDefault();
                const passwordInput = document.getElementById('sudo-password');
                if (passwordInput) {
                    submitSudoPassword(passwordInput.value);
                }
            });
        }
    } catch (error) {
        console.error('Error initializing settings page:', error);
        showAlert('Error initializing settings page. Please refresh and try again.', 'danger');
    }
}

/**
 * Set wireless interface
 * @param {string} interfaceName - The name of the interface to use
 */
async function setInterface(interfaceName) {
    try {
        const result = await networkApi.setInterface(interfaceName);
        
        if (result && result.success) {
            showAlert(`Interface set to ${interfaceName}`, 'success');
        } else if (result) {
            showAlert(`Failed to set interface: ${result.error}`, 'danger');
        }
    } catch (error) {
        console.error('Error setting interface:', error);
        showAlert('Error setting interface. Please try again.', 'danger');
    }
}

/**
 * Submit sudo password
 * @param {string} password - The sudo password
 */
async function submitSudoPassword(password) {
    try {
        // Get the form and button
        const submitBtn = document.getElementById('sudo-submit-btn');
        const form = document.getElementById('sudo-auth-form');
        
        if (submitBtn) {
            // Disable button and show loading state
            submitBtn.disabled = true;
            submitBtn.textContent = 'Authenticating...';
        }
        
        // Submit the form directly (let the browser handle the POST)
        if (form && form instanceof HTMLFormElement) {
            form.submit();
        }
    } catch (error) {
        console.error('Error submitting sudo password:', error);
        showAlert('Error submitting password. Please try again.', 'danger');
        
        const submitBtn = document.getElementById('sudo-submit-btn');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Authenticate';
        }
    }
} 