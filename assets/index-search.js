/**
 * Filters the links dynamically in the index page based on user input.
 * Hides empty categories and toggles the Table of Contents visibility.
 * Expands a <details> block ONLY if its inner elements match the search.
 * Restores the collapsed state of auto-expanded <details> when the search is cleared.
 */
function filterLinks() {
    var input = document.getElementById('search-input');
    // Added trim() to prevent trailing spaces from breaking the stemming logic
    var filter = input.value.toUpperCase().trim();
    
    // Basic stemming: drop the last letter if it's a common singular/plural ending (O, A, E, I, S)
    // This allows "tirocinio" to match "tirocini" (stem: "tirocini") and vice versa (stem: "tirocin").
    var flexibleFilter = filter;
    if (filter.length > 3 && /[OAEIS]$/.test(filter)) {
        flexibleFilter = filter.slice(0, -1);
    }
    
    var lists = document.querySelectorAll('.category-list, .simple-list, .course-metadata-list');
    
    lists.forEach(function(ul) {
        var isCategoryMatch = false;
        var isDetailsMatch = false;
        
        // 1. Check if the parent category title (H2/H3) matches the search query
        var startElem = ul.closest('details') || ul;
        var elem = startElem.previousElementSibling;
        
        while (elem) {
            if (elem.tagName === 'H2' || elem.tagName === 'H3') {
                var headingText = elem.textContent || elem.innerText;
                if (filter !== '' && (headingText.toUpperCase().indexOf(filter) > -1 || headingText.toUpperCase().indexOf(flexibleFilter) > -1)) {
                    isCategoryMatch = true;
                }
                break;
            }
            elem = elem.previousElementSibling;
        }

        // 2. Check if the parent details summary matches the search query
        var parentDetails = ul.closest('details');
        if (parentDetails) {
            var summary = parentDetails.querySelector('summary');
            if (summary) {
                var summaryText = summary.textContent || summary.innerText;
                if (filter !== '' && (summaryText.toUpperCase().indexOf(filter) > -1 || summaryText.toUpperCase().indexOf(flexibleFilter) > -1)) {
                    isDetailsMatch = true;
                }
            }
        }
        
        var hasMatchingInnerItem = false;
        var hasVisibleItems = false;
        var lis = ul.getElementsByTagName('li');
        
        for (var i = 0; i < lis.length; i++) {
            var txtValue = lis[i].textContent || lis[i].innerText;
            
            // Extract the href attribute to allow searching by the LAST part of the URL
            var aTag = lis[i].querySelector('a');
            var hrefValue = aTag ? aTag.getAttribute('href') : '';
            var urlLastSegment = '';
            
            if (hrefValue) {
                // Remove query strings and anchors
                var cleanUrl = hrefValue.split('?')[0].split('#')[0];
                // Remove trailing slash if present
                if (cleanUrl.endsWith('/')) {
                    cleanUrl = cleanUrl.slice(0, -1);
                }
                // Extract only the last part of the path
                urlLastSegment = cleanUrl.substring(cleanUrl.lastIndexOf('/') + 1);
            }
            
            // Check if either the visible text or the LAST SEGMENT of the URL matches the search filter (or flexible filter)
            var isItemMatch = (filter !== '' && (
                txtValue.toUpperCase().indexOf(filter) > -1 || 
                urlLastSegment.toUpperCase().indexOf(filter) > -1 ||
                txtValue.toUpperCase().indexOf(flexibleFilter) > -1 || 
                urlLastSegment.toUpperCase().indexOf(flexibleFilter) > -1
            ));
            
            // Show the item if it matches the category, details, the item itself, or if the search is empty
            if (isCategoryMatch || isDetailsMatch || isItemMatch || filter === '') {
                lis[i].style.display = '';
                hasVisibleItems = true;
                // Keep track if there is AT LEAST one actual match on the inner items
                if (isItemMatch) {
                    hasMatchingInnerItem = true;
                }
            } else {
                lis[i].style.display = 'none';
            }
        }
        
        // Hide the entire ul if it has no visible items to prevent empty margins in layout
        if (filter !== '' && !hasVisibleItems) {
            ul.style.display = 'none';
        } else {
            ul.style.display = '';
        }
        
        // 3. Handle visibility and automatic expansion of <details>
        if (parentDetails) {
            var shouldShow = (isCategoryMatch || isDetailsMatch || hasMatchingInnerItem || filter === '');
            parentDetails.style.display = shouldShow ? '' : 'none';
            
            if (filter === '') {
                // If the search is cleared, close the details ONLY if we opened it previously
                if (parentDetails.getAttribute('data-search-opened') === 'true') {
                    parentDetails.open = false;
                    parentDetails.removeAttribute('data-search-opened');
                }
            } else {
                // Expand automatically ONLY if an inner item was found (not if it's just a summary match)
                if (hasMatchingInnerItem) {
                    // If it's not already open, open it and apply the flag
                    if (!parentDetails.open) {
                        parentDetails.open = true;
                        parentDetails.setAttribute('data-search-opened', 'true');
                    }
                }
            }
        }
    });
    
    // Independent handling of category titles (H2, H3)
    var headings = document.querySelectorAll('h2.category-title, h3.subcategory-title');
    headings.forEach(function(heading) {
        var headingText = heading.textContent || heading.innerText;
        var isCategoryMatch = (filter !== '' && (headingText.toUpperCase().indexOf(filter) > -1 || headingText.toUpperCase().indexOf(flexibleFilter) > -1));
        
        var hasVisibleContent = false;
        var sibling = heading.nextElementSibling;
        
        // Traverse subsequent nodes until the next title
        while (sibling && sibling.tagName !== 'H2' && sibling.tagName !== 'H3') {
            if (sibling.tagName === 'UL') {
                var visibleItems = Array.from(sibling.getElementsByTagName('li')).filter(function(li) {
                    return li.style.display !== 'none';
                });
                if (visibleItems.length > 0) {
                    hasVisibleContent = true;
                }
            } else if (sibling.tagName === 'DETAILS') {
                if (sibling.style.display !== 'none') {
                    hasVisibleContent = true;
                }
            }
            
            sibling = sibling.nextElementSibling;
        }
        
        heading.style.display = (isCategoryMatch || hasVisibleContent || filter === '') ? '' : 'none';
    });
    
    // Hide the Table of Contents (TOC) during the search
    var toc = document.querySelector('.toc');
    if (toc) {
        toc.style.display = filter === '' ? '' : 'none';
    }
}