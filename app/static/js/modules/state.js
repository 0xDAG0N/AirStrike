/**
 * State Management Module
 *
 * A small in-memory store for the current page's selection, mirrored to sessionStorage so
 * it survives full-page navigations.
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

/**
 * Get the current state
 * @returns {Object} A shallow copy of the current state
 */
export function getState() {
    return { ...state };
}

/**
 * Merge new values into the state
 * @param {Object} newState - The values to merge
 */
export function updateState(newState) {
    state = { ...state, ...newState };
}

/**
 * Reset the state to initial values
 */
export function resetState() {
    state = { ...initialState };
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
    } catch (err) {
        console.error('Error loading saved state:', err);
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
    } catch (err) {
        console.error('Error saving network selection:', err);
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
    } catch (err) {
        console.error('Error retrieving stored network:', err);
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
