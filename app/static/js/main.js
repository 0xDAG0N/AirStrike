/**
 * Main JavaScript for AirStrike Web Interface
 *
 * Entry point that initializes the appropriate module for the current page.
 */

// Import page modules
import { initDashboard } from './modules/pages/dashboard.js';
import { initScanPage } from './modules/pages/scan.js';
import { initAttackPage } from './modules/pages/attack.js';
import { initResultsPage } from './modules/pages/results.js';
import { initSettingsPage } from './modules/pages/settings.js';

// Import state management
import { loadSavedState } from './modules/state.js';

// Import notifications
import { success, info, warning, error } from './modules/notifications.js';

// Debug mode - set to true to enable console logging
const DEBUG = false;

// Simple debug utility
function debug(area, message, data = null) {
    if (!DEBUG) return;
    console.log(`[${area}] ${message}`, data || '');
}

// DOM Ready function
document.addEventListener('DOMContentLoaded', function() {
    debug('PAGE', 'DOM Content Loaded');

    try {
        // Load any saved state from session storage
        loadSavedState();

        // Initialize the appropriate page module based on the current page
        initializePage();

        // Convert flash messages to notifications
        convertFlashMessages();

        // Welcome notification
        const currentPage = getCurrentPage();
        if (currentPage === 'dashboard') {
            setTimeout(() => {
                info('Welcome to AirStrike', 'System Ready', { duration: 7000 });
            }, 1500);
        }
    } catch (err) {
        // NOTE: name the caught error `err`, not `error` — `error` is the imported toast.
        console.error('Error initializing application:', err);
        error('Failed to initialize application. Check console for details.');
    }
});

/**
 * Initialize the appropriate page module based on the current page
 */
function initializePage() {
    const currentPage = getCurrentPage();

    try {
        switch (currentPage) {
            case 'dashboard':
                initDashboard();
                break;
            case 'scan':
                initScanPage();
                success('Scan module initialized', 'Ready');
                break;
            case 'attack':
                initAttackPage();
                warning('Attack module active', 'Caution', { duration: 8000, dismissible: true });
                break;
            case 'results':
                initResultsPage();
                info('Results loaded', 'Data Ready');
                break;
            case 'settings':
                initSettingsPage();
                info('Settings page loaded', 'Configuration');
                break;
            default:
                debug('PAGE', 'Unknown page or no specific initialization needed');
        }
    } catch (err) {
        console.error(`Error initializing ${currentPage} page:`, err);
        error(`Failed to initialize ${currentPage} page`, 'Error');
    }
}

/**
 * Convert Flask flash messages to our notification system
 */
function convertFlashMessages() {
    const alertsContainer = document.getElementById('alerts-container');
    if (!alertsContainer) return;

    const alerts = alertsContainer.querySelectorAll('.alert');

    alerts.forEach((alert, index) => {
        let type = 'info';
        if (alert.classList.contains('alert-danger')) {
            type = 'error';
        } else if (alert.classList.contains('alert-warning')) {
            type = 'warning';
        } else if (alert.classList.contains('alert-success')) {
            type = 'success';
        }

        const message = alert.textContent.trim();

        // Show notification with a slight stagger between each.
        setTimeout(() => {
            switch (type) {
                case 'success': success(message); break;
                case 'error': error(message); break;
                case 'warning': warning(message); break;
                default: info(message);
            }
        }, index * 300);

        // Hide the original alert.
        alert.style.display = 'none';
    });
}

/**
 * Determine the current page based on URL or page elements
 * @returns {string} The current page identifier
 */
function getCurrentPage() {
    const path = window.location.pathname;

    if (path === '/' || path === '/index') {
        return 'dashboard';
    } else if (path === '/scan') {
        return 'scan';
    } else if (path === '/attack') {
        return 'attack';
    } else if (path === '/results') {
        return 'results';
    } else if (path === '/settings') {
        return 'settings';
    }

    // Fallback to checking page elements.
    if (document.getElementById('dashboard-stats')) {
        return 'dashboard';
    } else if (document.getElementById('scan-networks-btn')) {
        return 'scan';
    } else if (document.getElementById('attack-options')) {
        return 'attack';
    } else if (document.getElementById('attack-log')) {
        return 'results';
    } else if (document.getElementById('interface-select')) {
        return 'settings';
    }

    return 'unknown';
}

// Export notification functions for use in other modules
export { success, info, warning, error };
