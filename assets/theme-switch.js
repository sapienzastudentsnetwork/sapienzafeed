
function applyTheme(theme) {
    // Set attribute on <html> element to influence CSS variables immediately
    document.documentElement.setAttribute('data-theme', theme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    
    // Determine current effective theme
    let activeTheme = currentTheme;
    if (!activeTheme) {
        activeTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    
    const targetTheme = (activeTheme === 'dark') ? 'light' : 'dark';
    localStorage.setItem('theme', targetTheme);
    applyTheme(targetTheme);
}

// Immediate execution (run in <head> to prevent flash)
(function() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        applyTheme(savedTheme);
    }
    // Prevent font flickering by applying it instantly to the HTML element
    const isFontDSA = localStorage.getItem('isFontDSA');
    if (isFontDSA) {
        document.documentElement.classList.add('dyslexic');
    }
})();

// Settings and Preferences Listeners
document.addEventListener("DOMContentLoaded", () => { 
    // DSA Font Checkbox Initialization
    let fontElement = document.getElementById('font-dsa-toggle');
    if (fontElement) {
        let isFontDSA = localStorage.getItem("isFontDSA");
        if (isFontDSA) {
            fontElement.checked = true; 
        }

        fontElement.addEventListener('change', function(e) {
            if (this.checked) {
                document.documentElement.classList.add('dyslexic');
                localStorage.setItem("isFontDSA", "true");
            } else {
                document.documentElement.classList.remove('dyslexic');
                localStorage.removeItem("isFontDSA");
            }
        });
    }
});

// Sync across tabs
window.addEventListener('storage', (event) => {
    if (event.key === 'theme') {
        applyTheme(event.newValue);
    } else if (event.key === 'isFontDSA') {
        const isDSA = !!event.newValue;
        if (isDSA) document.documentElement.classList.add('dyslexic');
        else document.documentElement.classList.remove('dyslexic');
        const fontElement = document.getElementById('font-dsa-toggle');
        if (fontElement) fontElement.checked = isDSA;
    }
});
