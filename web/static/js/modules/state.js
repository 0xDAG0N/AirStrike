/**
 * State Management Module
 * 
 * Provides a centralized state store with subscription capabilities
 */

// Define initial state
const initialState = {
    selectedNetwork: null,
    selectedAttack: null,
    attackRunning: false,
    attackLog: []
};

// Current state
let state = { ...initialState };

// Subscribers to state changes
const subscribers = [];

/**
 * Get the current state
 * @returns {Object} The current state
 */
export function getState() {
    return { ...state };
}

/**
 * Update the state
 * @param {Object} newState - The new state to merge with current state
 */
export function updateState(newState) {
    state = { ...state, ...newState };
    notifySubscribers();
}

/**
 * Reset the state to initial values
 */
export function resetState() {
    state = { ...initialState };
    notifySubscribers();
}

/**
 * Subscribe to state changes
 * @param {Function} callback - Function to call when state changes
 * @returns {Function} Unsubscribe function
 */
export function subscribe(callback) {
    subscribers.push(callback);
    
    // Return unsubscribe function
    return () => {
        const index = subscribers.indexOf(callback);
        if (index !== -1) {
            subscribers.splice(index, 1);
        }
    };
}

/**
 * Notify all subscribers of state changes
 */
function notifySubscribers() {
    subscribers.forEach(callback => callback(state));
}

/**
 * Load saved state from session storage
 */
export function loadSavedState() {
    try {
        const savedNetwork = sessionStorage.getItem('selectedNetwork');
        if (savedNetwork) {
            updateState({ selectedNetwork: JSON.parse(savedNetwork) });
        }
    } catch (error) {
        console.error('Error loading saved state:', error);
    }
}

/**
 * Save network selection to session storage and update state
 * @param {Object} network - The selected network
 */
export function saveNetworkSelection(network) {
    try {
        sessionStorage.setItem('selectedNetwork', JSON.stringify(network));
        updateState({ selectedNetwork: network });
    } catch (error) {
        console.error('Error saving network selection:', error);
    }
}

/**
 * Get stored network from session storage
 * @returns {Object|null} The stored network object or null if not found
 */
export function getStoredNetwork() {
    try {
        const storedNetwork = sessionStorage.getItem('selectedNetwork');
        return storedNetwork ? JSON.parse(storedNetwork) : null;
    } catch (error) {
        console.error('Error retrieving stored network:', error);
        return null;
    }
}

/**
 * Set selected attack type
 * @param {string} attackType - The selected attack type
 */
export function setSelectedAttack(attackType) {
    updateState({ selectedAttack: attackType });
}

/**
 * Set attack running state
 * @param {boolean} isRunning - Whether the attack is running
 */
export function setAttackRunning(isRunning) {
    updateState({ attackRunning: isRunning });
}

/**
 * Update attack log
 * @param {Array} log - The attack log entries
 */
export function updateAttackLog(log) {
    updateState({ attackLog: log });
} 