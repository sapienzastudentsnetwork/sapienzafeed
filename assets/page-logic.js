/* =========================================
   DYNAMIC NAVBAR ADJUSTMENT (STACK & CENTER)
   ========================================= */
function adjustNavbarLayout() {
    const navbar = document.querySelector('.top-navbar');
    const title = document.querySelector('.brand-title');
    const controls = document.querySelector('.controls-bar');
    
    if (!navbar || !title || !controls) return;

    // Remove stacked class to measure natural width first
    navbar.classList.remove('is-stacked');
    
    // Check if the combined width of title and buttons exceeds the navbar container
    // We add a 40px buffer to account for gaps and padding
    const availableWidth = navbar.offsetWidth;
    const itemsWidth = title.offsetWidth + controls.offsetWidth + 40;

    if (itemsWidth > availableWidth) {
        navbar.classList.add('is-stacked');
    }
}

// Global Resize Listener
window.addEventListener('resize', adjustNavbarLayout);

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
    // Initial check for navbar layout
    adjustNavbarLayout();

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
   EXCLUSIVE ACCORDION FOR CATEGORY DETAILS
   ========================================= */
document.addEventListener("DOMContentLoaded", function() {
    // Select all details elements with the class 'category-details'
    const categoryDetails = document.querySelectorAll('details.category-details');
    // Reference the search input
    const searchInput = document.getElementById('search-input');

    categoryDetails.forEach(details => {
        details.addEventListener('toggle', function() {
            // EXCEPTION: If the user is actively searching, do not close other details.
            // This allows the search script to expand multiple matching categories.
            if (searchInput && searchInput.value.trim() !== '') {
                return;
            }

            // Normal behavior: if the current details element is opening, close the others
            if (this.open) {
                categoryDetails.forEach(otherDetails => {
                    if (otherDetails !== this && otherDetails.open) {
                        otherDetails.removeAttribute('open');
                    }
                });
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

/* ====================================================
   PILL NAVIGATION SYSTEM
   ==================================================== */
function openTab(evt, tabId) {
    // 1. Hide all tab contents
    var tabContents = document.getElementsByClassName("tab-content");
    for (var i = 0; i < tabContents.length; i++) {
        tabContents[i].style.display = "none";
    }

    // 2. Remove "active" class from all buttons
    var tabButtons = document.getElementsByClassName("pill-button");
    for (var i = 0; i < tabButtons.length; i++) {
        tabButtons[i].classList.remove("active");
    }

    // 3. Show current tab and add "active" to the corresponding button
    document.getElementById(tabId).style.display = "block";
    if (evt && evt.currentTarget) {
        evt.currentTarget.classList.add("active");
    }

    // 4. Sync the mobile dropdown
    var selectElem = document.getElementById("category-select");
    if (selectElem && selectElem.value !== tabId) {
        selectElem.value = tabId;
    }
}

function openTabFromSelect(evt) {
    var tabId = evt.target.value;

    // Find the corresponding pill button to simulate the click state
    var tabButtons = document.getElementsByClassName("pill-button");
    var targetBtn = null;
    for (var i = 0; i < tabButtons.length; i++) {
        if (tabButtons[i].getAttribute("onclick").includes(tabId)) {
            targetBtn = tabButtons[i];
            break;
        }
    }

    openTab({ currentTarget: targetBtn }, tabId);
}