/**
 * Dashboard Page Module
 */

import { statsApi } from '../api.js';
import { updateDashboardStats } from '../ui.js';

/**
 * Initialize dashboard page
 */
export function initDashboard() {
    fetchDashboardStats();
    
    // Update stats every 30 seconds
    setInterval(fetchDashboardStats, 30000);
}

/**
 * Fetch and update dashboard statistics
 */
async function fetchDashboardStats() {
    try {
        const stats = await statsApi.getDashboardStats();
        updateDashboardStats(stats);
    } catch (error) {
        console.error('Error fetching dashboard stats:', error);
    }
} 