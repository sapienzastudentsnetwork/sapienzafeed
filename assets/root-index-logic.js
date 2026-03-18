(function() {
    const pageTitle = document.getElementById('page-title');
    if (!pageTitle) return;

    const titleText = pageTitle.textContent.trim();

    // Trigger translation only if the title matches the courses selection page
    if (titleText === 'Corsi di Laurea' || titleText === 'Degree Courses') {
        const userLang = navigator.language || navigator.userLanguage;
        const isItalian = userLang.toLowerCase().startsWith('it');

        document.documentElement.lang = isItalian ? 'it' : 'en';
        pageTitle.textContent = isItalian ? 'Corsi di Laurea' : 'Degree Courses';

        // Target the theme button by ID or fallback class
        const themeBtn = document.getElementById('themeBtn') || document.querySelector('.theme-toggle');
        if (themeBtn) {
            themeBtn.innerHTML = isItalian ? '🌓 Tema' : '🌓 Theme';
        }
    }
})();