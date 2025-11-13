/**
 * Page Transitions for AirStrike
 * Handles smooth transitions between pages with a simplified approach
 */

// Execute immediately when script loads
(function() {
    // Apply saved theme immediately
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Make html/body visible but keep content hidden
    document.documentElement.style.visibility = 'visible';
    document.body.style.visibility = 'visible';
    
    // Make sure loading overlay is visible
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.style.visibility = 'visible';
        loadingOverlay.style.opacity = '1';
    }
})();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Start animating the progress bar
    animateProgress();
    
    // Set up page transitions
    setupPageTransitions();
});

// Animate the progress bar
function animateProgress() {
    const progressBar = document.querySelector('.loading-progress-bar');
    const statusText = document.querySelector('.loading-status');
    if (!progressBar || !statusText) return;
    
    const steps = [
        { progress: 15, text: 'Loading resources...' },
        { progress: 35, text: 'Loading resources...' },
        { progress: 65, text: 'Loading resources...' },
        { progress: 85, text: 'Loading resources...' },
        { progress: 100, text: 'Loading resources...' }
    ];
    
    let currentStep = 0;
    
    function updateProgress() {
        if (currentStep >= steps.length) return;
        
        const step = steps[currentStep];
        progressBar.style.width = step.progress + '%';
        statusText.textContent = step.text;
        
        currentStep++;
        
        if (currentStep < steps.length) {
            const delay = 10 + Math.random() * 5;
            setTimeout(updateProgress, delay);
        }
    }
    
    updateProgress();
}

// Set up page transitions
function setupPageTransitions() {
    // Wait for all resources to load
    window.addEventListener('load', function() {
        // Show content
        const contentContainer = document.querySelector('.content-container');
        if (contentContainer) {
            contentContainer.classList.add('loaded');
            contentContainer.style.visibility = 'visible';
            contentContainer.style.opacity = '1';
            contentContainer.style.pointerEvents = 'auto';
        }
        
        // Hide loading overlay with a slight delay
        setTimeout(function() {
            const loadingOverlay = document.getElementById('loading-overlay');
            if (loadingOverlay) {
                loadingOverlay.style.opacity = '0';
                
                setTimeout(function() {
                    loadingOverlay.classList.add('hidden');
                    loadingOverlay.style.visibility = 'hidden';
                    loadingOverlay.style.pointerEvents = 'none';
                }, 10);
            }
        }, 10);
    });
}