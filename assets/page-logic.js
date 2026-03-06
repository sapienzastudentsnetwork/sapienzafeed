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
                targetElement.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});

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