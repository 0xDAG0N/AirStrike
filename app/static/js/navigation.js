/**
 * Navigation handler for AirStrike
 * Handles browser history navigation events
 */

// Store the current page URL when it loads
let currentPage = window.location.href;

// Listen for popstate events (back/forward browser buttons)
window.addEventListener('popstate', function(event) {
    // Mark as navigating to prevent double loading screens
    sessionStorage.setItem('airstrike_navigating', 'true');
    
    // Navigate directly without showing loading overlay
    window.location.href = window.location.href;
});

// Set up navigation links
document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners to all navigation items
    document.querySelectorAll('.nav-item').forEach(link => {
        link.addEventListener('click', function(e) {
            // Only handle if this is not the active link
            if (!this.classList.contains('active')) {
                e.preventDefault();
                const targetUrl = this.getAttribute('href');
                
                // Set navigating flag
                sessionStorage.setItem('airstrike_navigating', 'true');
                
                // Navigate directly
                window.location.href = targetUrl;
            }
        });
    });
    
    // Add event listeners to other internal links
    document.querySelectorAll('a:not(.nav-item)').forEach(link => {
        // Only handle internal links
        if (link.getAttribute('href') && 
            link.getAttribute('href').startsWith('/') && 
            !link.classList.contains('nav-item')) {
            
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const targetUrl = this.getAttribute('href');
                
                // Set navigating flag
                sessionStorage.setItem('airstrike_navigating', 'true');
                
                // Navigate directly
                window.location.href = targetUrl;
            });
        }
    });
}); 