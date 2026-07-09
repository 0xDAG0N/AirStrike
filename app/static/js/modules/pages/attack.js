/**
 * Attack Page Module
 */

import { getState } from '../state.js';
import { displayNetworkInfo } from '../ui.js';
import { initAttacks } from '../attacks/index.js';
import { loadSavedState } from '../state.js';

/**
 * Initialize attack page
 */
export function initAttackPage() {
    // Load saved state from session storage
    loadSavedState();
    
    // Display selected network info
    const state = getState();
    displayNetworkInfo(state.selectedNetwork);
    
    // Initialize attack functionality
    initAttacks();
} 