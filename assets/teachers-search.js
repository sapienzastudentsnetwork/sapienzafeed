/**
 * Filters the teacher cards dynamically in the index page based on user input.
 * Searches through name, email, and structure text.
 * Supports matching words in any order (e.g., "Name Surname" matches "Surname Name").
 */
function filterTeachers() {
    var input = document.getElementById('search-input');
    var filterText = input.value.toUpperCase().trim();
    var searchTerms = filterText === '' ? [] : filterText.split(/\s+/);
    var cards = document.querySelectorAll('.docente-card');
    
    cards.forEach(function(card) {
        var nameElem = card.querySelector('.full-name');
        var emailElem = card.querySelector('.email');
        var structElem = card.querySelector('.structure');
        
        var nameTxt = nameElem ? nameElem.textContent || nameElem.innerText : '';
        var emailTxt = emailElem ? emailElem.textContent || emailElem.innerText : '';
        var structTxt = structElem ? structElem.textContent || structElem.innerText : '';
        
        var combinedText = (nameTxt + " " + emailTxt + " " + structTxt).toUpperCase();
        
        var isMatch = true;
        for (var i = 0; i < searchTerms.length; i++) {
            if (combinedText.indexOf(searchTerms[i]) === -1) {
                isMatch = false;
                break;
            }
        }
        
        card.style.display = isMatch ? '' : 'none';
    });
}