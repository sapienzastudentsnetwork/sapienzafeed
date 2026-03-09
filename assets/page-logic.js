window.addEventListener('scroll', function() {
    var btn = document.getElementById('back-to-top');
    if (btn) {
        if (window.scrollY > 300) {
            btn.style.display = 'block';
        } else {
            btn.style.display = 'none';
        }
    }
});

document.addEventListener("DOMContentLoaded", function() {
    // Handle click on back to top buttons
    var btn = document.getElementById('back-to-top');
    if (btn) {
        btn.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // Handle click on heading anchors to copy URL to clipboard
    const anchors = document.querySelectorAll('.heading-anchor');
    anchors.forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            // Reconstruct full URL with the hash
            const url = window.location.origin + window.location.pathname + targetId;
            
            // Copy to clipboard
            navigator.clipboard.writeText(url).then(() => {
                const originalText = this.textContent;
                this.textContent = 'Copied!';
                setTimeout(() => { this.textContent = originalText; }, 1500);
            });
            
            // Update URL and smoothly scroll to element without jumping
            history.pushState(null, null, targetId);
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                // Open parent details if target is inside a collapsible
                let parentDetails = targetElement.closest('details');
                while (parentDetails) {
                    parentDetails.setAttribute('open', '');
                    parentDetails = parentDetails.parentElement ? parentDetails.parentElement.closest('details') : null;
                }
                
                // If the target itself is a details element, open it
                if (targetElement.tagName.toLowerCase() === 'details') {
                    targetElement.setAttribute('open', '');
                }

                targetElement.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});

/* =========================================
   AUTO-EXPAND COLLAPSIBLES ON HASH NAVIGATION
   ========================================= */
function expandTargetDetails() {
    if (window.location.hash) {
        try {
            // Remove the '#' to get the exact ID
            const targetId = window.location.hash.substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                // Open all parent details elements
                let parentDetails = targetElement.closest('details');
                while (parentDetails) {
                    parentDetails.setAttribute('open', '');
                    parentDetails = parentDetails.parentElement ? parentDetails.parentElement.closest('details') : null;
                }
                
                // If the target itself is a details element, open it
                if (targetElement.tagName.toLowerCase() === 'details') {
                    targetElement.setAttribute('open', '');
                }
                
                // Scroll into view
                targetElement.scrollIntoView({ behavior: 'smooth' });
            }
        } catch (e) {
            // Safely ignore invalid selectors
            console.error("Error expanding target details:", e);
        }
    }
}

// Run on page load
document.addEventListener('DOMContentLoaded', expandTargetDetails);

// Run on hash change (e.g., clicking anchor links pointing to the same page)
window.addEventListener('hashchange', expandTargetDetails);

/* =========================================
   PRINT OPTIMIZATION LOGIC
   ========================================= */

// Expand all dropdown menus (<details>) before opening the print prompt
window.addEventListener('beforeprint', () => {
    document.querySelectorAll('details').forEach(d => {
        if (!d.hasAttribute('open')) {
            d.setAttribute('data-print-opened', 'true');
            d.setAttribute('open', '');
        }
    });
});

// Close them after the print prompt is closed
window.addEventListener('afterprint', () => {
    document.querySelectorAll('details[data-print-opened="true"]').forEach(d => {
        d.removeAttribute('open');
        d.removeAttribute('data-print-opened');
    });
});

/* =========================================
   DYNAMIC NAVBAR WRAPPING LOGIC
   ========================================= */

document.addEventListener("DOMContentLoaded", () => {
    const navbar = document.querySelector('.top-navbar');
    const title = document.querySelector('.brand-title');
    const controls = document.querySelector('.controls-bar');

    if (navbar && title && controls) {
        let wrapBreakpoint = 0; // Stores the width where the layout breaks

        const checkWrap = () => {
            const isCurrentlyWrapped = navbar.classList.contains('is-wrapped');

            if (!isCurrentlyWrapped) {
                // 1. Temporarily force top alignment to accurately check offsets
                const oldAlign = navbar.style.alignItems;
                navbar.style.alignItems = 'flex-start';
                
                // 2. If controls are pushed below the title, they have wrapped
                const needsWrap = controls.offsetTop > title.offsetTop;
                
                // 3. Restore alignment
                navbar.style.alignItems = oldAlign;

                if (needsWrap) {
                    // Record the exact container width where the wrapping occurred
                    wrapBreakpoint = navbar.clientWidth;
                    navbar.classList.add('is-wrapped');
                }
            } else {
                // If it's already wrapped, only unwrap it if the container 
                // is safely wider than the breakpoint where it originally broke.
                // We add a 5px buffer to completely prevent edge-case flickering.
                if (navbar.clientWidth > wrapBreakpoint + 5) {
                    navbar.classList.remove('is-wrapped');
                    wrapBreakpoint = 0; // Reset the breakpoint
                }
            }
        };

        // Run the initial check
        checkWrap();

        // Use ResizeObserver to recalculate whenever the window or navbar changes size
        const resizeObserver = new ResizeObserver(checkWrap);
        resizeObserver.observe(navbar);
    }
});