/**
 * MovieMania - Main Client-Side JavaScript
 * Modular, vanilla JavaScript for interactive recommendation, watchlist, and UI controls.
 */

document.addEventListener('DOMContentLoaded', () => {
    initWatchlistToggles();
    initDiscoverFilters();
    initImageFallbacks();
    initMobileNav();
    initAlertDismissal();
});

/* ==========================================================================
   1. Watchlist AJAX Toggle
   ========================================================================== */
function initWatchlistToggles() {
    document.addEventListener('click', async (event) => {
        const toggleBtn = event.target.closest('.watchlist-toggle-btn, .btn-watchlist-toggle');
        if (!toggleBtn) return;

        event.preventDefault();
        event.stopPropagation();

        const movieId = toggleBtn.dataset.movieId;
        if (!movieId) return;

        // Check CSRF token from cookie or meta
        const csrfToken = getCookie('csrftoken');
        if (!csrfToken) {
            // User likely not logged in; redirect to login
            window.location.href = `/login/?next=${encodeURIComponent(window.location.pathname)}`;
            return;
        }

        try {
            toggleBtn.style.pointerEvents = 'none';
            const response = await fetch(`/watchlist/toggle/${movieId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                }
            });

            if (response.status === 401 || response.redirected) {
                window.location.href = `/login/?next=${encodeURIComponent(window.location.pathname)}`;
                return;
            }

            const data = await response.json();
            if (data.status === 'success') {
                // Update all instances of this movie's toggle button on current page
                const allButtonsForMovie = document.querySelectorAll(`[data-movie-id="${movieId}"]`);
                allButtonsForMovie.forEach(btn => {
                    if (data.in_watchlist) {
                        btn.classList.add('active');
                        btn.setAttribute('title', 'Remove from Watchlist');
                        if (btn.classList.contains('btn-watchlist-toggle')) {
                            btn.innerHTML = '<span>✓</span> In Watchlist';
                            btn.classList.remove('btn-secondary');
                            btn.classList.add('btn-primary');
                        }
                    } else {
                        btn.classList.remove('active');
                        btn.setAttribute('title', 'Add to Watchlist');
                        if (btn.classList.contains('btn-watchlist-toggle')) {
                            btn.innerHTML = '<span>+</span> Add to Watchlist';
                            btn.classList.remove('btn-primary');
                            btn.classList.add('btn-secondary');
                        }
                    }
                });

                // Update navbar badge
                const badge = document.querySelector('.nav-watchlist-badge');
                if (badge) {
                    badge.textContent = data.watchlist_count;
                    badge.style.display = data.watchlist_count > 0 ? 'inline-flex' : 'none';
                }

                // If on watchlist page and item removed, gracefully fade out card
                const watchlistCard = toggleBtn.closest('.watchlist-item-card');
                if (watchlistCard && !data.in_watchlist) {
                    watchlistCard.style.opacity = '0';
                    watchlistCard.style.transform = 'scale(0.95)';
                    setTimeout(() => {
                        watchlistCard.remove();
                        const remaining = document.querySelectorAll('.watchlist-item-card').length;
                        const countEl = document.querySelector('.watchlist-total-count');
                        if (countEl) countEl.textContent = remaining;
                        if (remaining === 0) {
                            location.reload();
                        }
                    }, 250);
                }

                showToast(data.message, data.in_watchlist ? 'success' : 'info');
            }
        } catch (err) {
            console.error('Failed to toggle watchlist:', err);
        } finally {
            toggleBtn.style.pointerEvents = 'auto';
        }
    });
}

/* ==========================================================================
   2. Discover Page Filter Sync & Live Updates
   ========================================================================== */
function initDiscoverFilters() {
    const filterForm = document.getElementById('discoverFilterForm');
    const ratingSlider = document.getElementById('minRatingSlider');
    const ratingDisplay = document.getElementById('minRatingDisplay');

    if (ratingSlider && ratingDisplay) {
        ratingSlider.addEventListener('input', (e) => {
            const val = parseFloat(e.target.value);
            ratingDisplay.textContent = val > 0 ? `${val.toFixed(1)}+` : 'Any';
        });
    }

    if (!filterForm) return;

    // Auto-update rating slider label on initial load
    if (ratingSlider && ratingDisplay) {
        const val = parseFloat(ratingSlider.value);
        ratingDisplay.textContent = val > 0 ? `${val.toFixed(1)}+` : 'Any';
    }
}

/* ==========================================================================
   3. Poster Image Error Fallback (SVG Film Slate)
   ========================================================================== */
function initImageFallbacks() {
    const posterImgs = document.querySelectorAll('.movie-poster-img, .detail-poster-img');
    posterImgs.forEach(img => {
        img.addEventListener('error', function() {
            const movieTitle = this.getAttribute('alt') || 'Movie';
            this.src = createSvgFallback(movieTitle);
        });
    });
}

function createSvgFallback(title) {
    const cleanTitle = title.replace(/[<>&"]/g, '');
    const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="300" height="450" viewBox="0 0 300 450" fill="none">
        <rect width="300" height="450" fill="#131B2A"/>
        <rect x="20" y="20" width="260" height="410" rx="8" stroke="#1E2B42" stroke-width="2"/>
        <circle cx="150" cy="180" r="45" fill="#1A2436"/>
        <path d="M140 160 L170 180 L140 200 Z" fill="#F59E0B"/>
        <text x="150" y="280" fill="#F8FAFC" font-family="system-ui, sans-serif" font-size="16" font-weight="700" text-anchor="middle">
            ${cleanTitle.length > 25 ? cleanTitle.substring(0, 22) + '...' : cleanTitle}
        </text>
        <text x="150" y="310" fill="#64748B" font-family="system-ui, sans-serif" font-size="12" font-weight="600" text-anchor="middle" letter-spacing="1">
            MOVIEMANIA
        </text>
    </svg>`;
    return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

/* ==========================================================================
   4. Mobile Navigation Drawer
   ========================================================================== */
function initMobileNav() {
    const toggleBtn = document.querySelector('.nav-toggle-btn');
    const navLinks = document.querySelector('.nav-links');
    if (toggleBtn && navLinks) {
        toggleBtn.addEventListener('click', () => {
            navLinks.classList.toggle('mobile-open');
        });
    }
}

/* ==========================================================================
   5. Alert Dismissal
   ========================================================================== */
function initAlertDismissal() {
    document.querySelectorAll('.alert-close').forEach(btn => {
        btn.addEventListener('click', () => {
            const alert = btn.closest('.alert');
            if (alert) alert.remove();
        });
    });
}

/* ==========================================================================
   6. Toast Notifications & Helpers
   ========================================================================== */
function showToast(message, type = 'info') {
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.cssText = `
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            pointer-events: none;
        `;
        document.body.appendChild(toastContainer);
    }

    const toast = document.createElement('div');
    const bgColor = type === 'success' ? '#10B981' : '#F59E0B';
    const textColor = type === 'success' ? '#FFFFFF' : '#0B0F17';
    toast.style.cssText = `
        background-color: ${bgColor};
        color: ${textColor};
        padding: 0.75rem 1.25rem;
        border-radius: 8px;
        font-size: 0.9rem;
        font-weight: 600;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        opacity: 0;
        transform: translateY(10px);
        transition: all 0.25s ease;
        pointer-events: auto;
    `;
    toast.textContent = message;
    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
    }, 10);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        setTimeout(() => toast.remove(), 250);
    }, 3200);
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
