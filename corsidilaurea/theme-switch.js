
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
    // If no saved theme, CSS media queries will handle the system default
})();

// Sync across tabs
window.addEventListener('storage', (event) => {
    if (event.key === 'theme') {
        applyTheme(event.newValue);
    }
});
