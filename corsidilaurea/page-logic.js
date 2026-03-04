
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

// Handle click on heading anchors to copy URL to clipboard
document.addEventListener("DOMContentLoaded", function() {
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
