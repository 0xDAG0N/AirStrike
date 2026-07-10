/**
 * Page load handling for AirStrike.
 *
 * Applies the saved theme before first paint (prevents a flash of the wrong theme), then
 * reveals the content and hides the loading overlay once the page has finished loading.
 */

// Run immediately: apply theme and make html/body visible before paint.
(function () {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);

    document.documentElement.style.visibility = 'visible';
    document.body.style.visibility = 'visible';

    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.style.visibility = 'visible';
        loadingOverlay.style.opacity = '1';
    }
})();

// Reveal content and fade out the overlay once everything has loaded.
window.addEventListener('load', function () {
    const contentContainer = document.querySelector('.content-container');
    if (contentContainer) {
        contentContainer.classList.add('loaded');
        contentContainer.style.visibility = 'visible';
        contentContainer.style.opacity = '1';
        contentContainer.style.pointerEvents = 'auto';
    }

    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.style.opacity = '0';
        setTimeout(function () {
            loadingOverlay.classList.add('hidden');
            loadingOverlay.style.visibility = 'hidden';
            loadingOverlay.style.pointerEvents = 'none';
        }, 150);
    }
});
