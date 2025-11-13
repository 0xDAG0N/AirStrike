/**
 * API Module - Handles all API calls with consistent error handling
 */

import { showAlert } from './ui.js';

// Initialize Socket.IO connection
export const socket = io();

// Socket.IO event handlers
socket.on('connect', () => {
    console.log('Connected to server via WebSocket');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
});

// Sudo authentication handling removed since we enforce root execution at startup

/**
 * Make a GET request to the specified endpoint
 * @param {string} url - The endpoint URL
 * @returns {Promise} - Promise resolving to the JSON response
 */
export async function apiGet(url) {
    try {
        const response = await fetch(url);
        
        // Root execution is enforced at startup, so 401 errors should not happen
        // If they do occur, they are handled by the general error case below
        
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`API GET error for ${url}:`, error);
        showAlert(`API Error: ${error.message}`, 'danger');
        throw error;
    }
}

/**
 * Make a POST request to the specified endpoint
 * @param {string} url - The endpoint URL
 * @param {Object} data - The data to send in the request body
 * @returns {Promise} - Promise resolving to the JSON response
 */
export async function apiPost(url, data) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        // Root execution is enforced at startup, so 401 errors should not happen
        // If they do occur, they are handled by the general error case below
        
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`API POST error for ${url}:`, error);
        showAlert(`API Error: ${error.message}`, 'danger');
        throw error;
    }
}

// Sudo required message removed since we enforce root execution at startup

/**
 * Network API functions
 */
export const networkApi = {
    /**
     * Scan for available WiFi networks
     * @returns {Promise<Array>} Array of network objects
     */
    async scanNetworks() {
        try {
            const response = await fetch('/scan_wifi');
            
            // Root execution is enforced at startup, so 401 errors should not happen
            // If they do occur, they are handled by the general error case below
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success === false) {
                // Handle other error responses
                if (data.error) {
                    throw new Error(data.error || 'Unknown error scanning networks');
                }
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            showAlert(`Network scan error: ${error.message}`, 'danger');
            throw error;
        }
    },
    
    /**
     * Check interface status
     * @returns {Promise<Object>} Interface status data
     */
    async checkInterfaceStatus() {
        try {
            const response = await fetch('/scan_wifi?check_only=true');
            
            // Root execution is enforced at startup, so 401 errors should not happen
            // If they do occur, they are handled by the general error case below
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            showAlert(`Interface status check error: ${error.message}`, 'danger');
            return { 
                success: false, 
                error: error.message,
                interface_status: {
                    exists: false,
                    name: 'unknown',
                    is_wireless: false
                }
            };
        }
    },
    
    /**
     * Set the wireless interface
     * @param {string} interfaceName - The name of the interface to use
     * @returns {Promise} - Promise resolving to the result
     */
    setInterface: (interfaceName) => apiPost('/set_interface', { interface: interfaceName })
};

/**
 * API functions for attacks
 */
export const attackApi = {
    /**
     * Start an attack
     * @param {Object} network - The target network
     * @param {string} attackType - The type of attack
     * @param {Object} config - The attack configuration
     * @returns {Promise} - Promise resolving to the result
     */
    startAttack: (network, attackType, config) => 
        apiPost('/start_attack', { network, attack_type: attackType, config }),
    
    /**
     * Stop the running attack
     * @returns {Promise} - Promise resolving to the result
     */
    stopAttack: () => apiPost('/stop_attack', {}),
    
    /**
     * Get the status of the running attack
     * @returns {Promise} - Promise resolving to the attack status
     */
    getStatus: () => apiGet('/attack_status'),
    
    /**
     * Get the attack log
     * @returns {Promise} - Promise resolving to the attack log
     */
    getLog: () => apiGet('/attack_log')
};

/**
 * API functions for dashboard statistics
 */
export const statsApi = {
    /**
     * Get dashboard statistics
     * @returns {Promise} - Promise resolving to the dashboard statistics
     */
    getDashboardStats: () => apiGet('/dashboard_stats')
}; 