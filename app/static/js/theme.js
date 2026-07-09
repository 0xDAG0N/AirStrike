/**
 * Theme Switcher for AirStrike
 * Handles switching between dark and light modes
 */

// Immediately apply the saved theme before DOM loads to prevent flashing
(function() {
    // Check if there's a saved theme preference in localStorage
    const savedTheme = localStorage.getItem('theme') || 'dark';
    
    // Apply the theme to the HTML element
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Make only the loading overlay visible initially
    document.addEventListener('DOMContentLoaded', () => {
        document.body.style.visibility = 'visible';
        
        // Set toggle position immediately
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.checked = savedTheme === 'light';
        }
    });
})();

// Handle page loading and transitions
document.addEventListener('DOMContentLoaded', () => {
    // Get elements
    const themeToggle = document.getElementById('theme-toggle');
    
    // Check if there's a saved theme preference in localStorage
    const savedTheme = localStorage.getItem('theme') || 'dark';
    
    if (themeToggle) {
        // Update the toggle state
        themeToggle.checked = savedTheme === 'light';
        
        // Add event listener to toggle theme
        themeToggle.addEventListener('change', function() {
            if (this.checked) {
                // Switch to light theme
                document.documentElement.setAttribute('data-theme', 'light');
                localStorage.setItem('theme', 'light');
            } else {
                // Switch to dark theme
                document.documentElement.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
            }
        });
    }
    
    // Note: Navigation is now handled by navigation.js
    // We no longer need to handle navigation here
}); 