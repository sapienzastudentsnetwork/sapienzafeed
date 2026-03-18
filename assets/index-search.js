/**
 * Filters the links dynamically in the index page based on user input.
 * Integrates with the tab (pill) system by hiding the navigation pills
 * and displaying all matching tab contents in an "open accordion" stacked layout
 * during a search. Restores the tabbed layout when the search is cleared.
 */
function filterLinks() {
    var input = document.getElementById('search-input');
    if (!input) return; // Failsafe if input doesn't exist

    var filter = input.value.toUpperCase().trim();

    // 1. HIDE TOC AND ANNOUNCEMENTS DURING SEARCH
    var toc = document.querySelector('.toc');
    if (toc) {
        toc.style.setProperty('display', filter === '' ? '' : 'none', 'important');
    }

    var announcementSections = document.querySelectorAll('.announcements-section');
    announcementSections.forEach(function(section) {
        section.style.setProperty('display', filter === '' ? '' : 'none', 'important');
    });

    // 2. STEMMING LOGIC
    // Drop the last letter if it's a common singular/plural ending
    var flexibleFilter = filter;
    if (filter.length > 3 && /[OAEIS]$/.test(filter)) {
        flexibleFilter = filter.slice(0, -1);
    }

    // 3. TAB / PILL NAVIGATION HANDLING
    var navControls = document.querySelector('.nav-controls-container');
    if (navControls) {
        // Hide navigation controls during search to show stacked results
        navControls.style.display = filter === '' ? 'block' : 'none';
    }

    // 4. FILTERING TAB CONTENTS
    var tabContents = document.querySelectorAll('.tab-content');

    if (tabContents.length > 0) {
        tabContents.forEach(function(tabContent) {
            // Find the corresponding pill button to extract the category name
            var categoryName = "";
            var relatedBtn = document.querySelector('.pill-button[onclick*="' + tabContent.id + '"]');
            if (relatedBtn) {
                categoryName = (relatedBtn.textContent || relatedBtn.innerText).toUpperCase();
            }

            var isCategoryMatch = (filter !== '' && (categoryName.indexOf(filter) > -1 || categoryName.indexOf(flexibleFilter) > -1));
            var hasVisibleItems = false;
            var lists = tabContent.querySelectorAll('ul');

            lists.forEach(function(ul) {
                var listItems = ul.children;
                for (var i = 0; i < listItems.length; i++) {
                    var li = listItems[i];
                    var txtValue = li.textContent || li.innerText;

                    var aTag = li.querySelector('a');
                    var hrefValue = aTag ? aTag.getAttribute('href') : '';
                    var urlLastSegment = '';

                    if (hrefValue) {
                        var cleanUrl = hrefValue.split('?')[0].split('#')[0];
                        if (cleanUrl.endsWith('/')) cleanUrl = cleanUrl.slice(0, -1);
                        urlLastSegment = cleanUrl.substring(cleanUrl.lastIndexOf('/') + 1).toUpperCase();
                    }

                    txtValue = txtValue.toUpperCase();

                    var isItemMatch = (filter !== '' && (
                        txtValue.indexOf(filter) > -1 ||
                        urlLastSegment.indexOf(filter) > -1 ||
                        txtValue.indexOf(flexibleFilter) > -1 ||
                        urlLastSegment.indexOf(flexibleFilter) > -1
                    ));

                    if (isCategoryMatch || isItemMatch || filter === '') {
                        li.style.display = '';
                        hasVisibleItems = true;
                    } else {
                        li.style.display = 'none';
                    }

                    // Handle nested <details> blocks (like Metadata or Timetables)
                    var detailsElem = li.querySelector('details');
                    if (detailsElem) {
                        if (filter !== '' && isItemMatch) {
                            if (!detailsElem.open) {
                                detailsElem.open = true;
                                detailsElem.setAttribute('data-search-opened', 'true');
                            }
                        } else if (filter === '') {
                            if (detailsElem.getAttribute('data-search-opened') === 'true') {
                                detailsElem.open = false;
                                detailsElem.removeAttribute('data-search-opened');
                            }
                        }
                    }
                }
            });

            // Display logic for the tab content container
            if (filter === '') {
                // Restore original tab state (show only the active tab)
                if (relatedBtn && relatedBtn.classList.contains('active')) {
                    tabContent.style.display = 'block';
                } else {
                    tabContent.style.display = 'none';
                }

                // Remove the dynamically injected heading
                var dynamicHeading = tabContent.querySelector('.search-category-heading');
                if (dynamicHeading) dynamicHeading.style.display = 'none';

            } else {
                // Search mode: show if it has matches
                if (hasVisibleItems || isCategoryMatch) {
                    tabContent.style.display = 'block';

                    // Inject a temporary heading to simulate the "open accordion" look
                    var heading = tabContent.querySelector('.search-category-heading');
                    if (!heading) {
                        heading = document.createElement('h2');
                        heading.className = 'search-category-heading category-title';
                        heading.textContent = relatedBtn ? (relatedBtn.textContent || relatedBtn.innerText) : '';
                        heading.style.marginTop = '10px';
                        heading.style.marginBottom = '10px';
                        tabContent.insertBefore(heading, tabContent.firstChild);
                    }
                    heading.style.display = 'block';
                } else {
                    tabContent.style.display = 'none';
                }
            }
        });

    } else {
        // 5. FALLBACK FOR SIMPLE LISTS (e.g. Root Index)
        var simpleLists = document.querySelectorAll('.simple-list');
        simpleLists.forEach(function(ul) {
            var hasVisibleItems = false;
            var listItems = ul.children;

            for (var i = 0; i < listItems.length; i++) {
                var li = listItems[i];
                var txtValue = li.textContent || li.innerText;

                var aTag = li.querySelector('a');
                var hrefValue = aTag ? aTag.getAttribute('href') : '';
                var urlLastSegment = '';

                if (hrefValue) {
                    var cleanUrl = hrefValue.split('?')[0].split('#')[0];
                    if (cleanUrl.endsWith('/')) cleanUrl = cleanUrl.slice(0, -1);
                    urlLastSegment = cleanUrl.substring(cleanUrl.lastIndexOf('/') + 1).toUpperCase();
                }

                txtValue = txtValue.toUpperCase();

                var isItemMatch = (filter !== '' && (
                    txtValue.indexOf(filter) > -1 ||
                    urlLastSegment.indexOf(filter) > -1 ||
                    txtValue.indexOf(flexibleFilter) > -1 ||
                    urlLastSegment.indexOf(flexibleFilter) > -1
                ));

                if (isItemMatch || filter === '') {
                    li.style.display = '';
                    hasVisibleItems = true;
                } else {
                    li.style.display = 'none';
                }
            }

            ul.style.display = (filter !== '' && !hasVisibleItems) ? 'none' : '';
        });
    }
}