import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Courses that should NOT have an English version
EXCLUDED_EN_IDS = (33503, 33504)

THEME_VARS_CSS = """
:root {
    --bg-color: #ffffff;
    --text-color: #333333;
    --heading-color: #0056b3;
    --link-color: #007BFF;
    --toc-bg: #f8f9fa;
    --toc-border: #e9ecef;
    --border-color: #eee;
    --details-body-border: #f4f4f4;
    --table-header-bg: #f0f0f0;
    --table-header-text: #333333;
}

/* 1. Apply dark variables if system is dark AND user hasn't forced light */
@media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
        --bg-color: #1a1a1a;
        --text-color: #e0e0e0;
        --heading-color: #4da3ff;
        --link-color: #66b2ff;
        --toc-bg: #2d2d2d;
        --toc-border: #444;
        --border-color: #404040;
        --details-body-border: #333;
        --table-header-bg: #333333;
        --table-header-text: #ffffff;
    }
}

/* 2. Apply dark variables if user explicitly toggled dark mode */
[data-theme="dark"] {
    --bg-color: #1a1a1a;
    --text-color: #e0e0e0;
    --heading-color: #4da3ff;
    --link-color: #66b2ff;
    --toc-bg: #2d2d2d;
    --toc-border: #444;
    --border-color: #404040;
    --details-body-border: #333;
    --table-header-bg: #333333;
    --table-header-text: #ffffff;
}

body { 
    background-color: var(--bg-color); 
    color: var(--text-color); 
    transition: background 0.3s, color 0.3s; 
}

.table-responsive table thead th {
    background-color: var(--table-header-bg) !important;
    color: var(--table-header-text) !important;
}

.table-striped tbody tr:nth-of-type(odd) {
    background-color: rgba(255, 255, 255, 0.05);
}

h1, h2, h3, h4, h5, h6 { color: var(--heading-color) !important; }
a { color: var(--link-color); }

/* Hover anchors for direct linking */
.heading-anchor {
    opacity: 0;
    color: #ccc !important;
    font-size: 0.8em;
    text-decoration: none !important;
    margin-left: 8px;
    transition: opacity 0.2s ease-in-out;
    cursor: pointer;
    user-select: none;
}
h2:hover .heading-anchor, h3:hover .heading-anchor, 
h4:hover .heading-anchor, h5:hover .heading-anchor, h6:hover .heading-anchor {
    opacity: 1;
}
.heading-anchor:hover { color: var(--link-color) !important; }

.theme-bar { 
    display: flex; 
    justify-content: flex-end; 
    gap: 8px; 
    align-items: center; 
    padding: 10px 0; 
    margin-bottom: 20px; 
    border-bottom: 1px solid var(--border-color); 
    flex-wrap: wrap; /* Allows items to wrap nicely on small screens */
}

/* Unified button styles */
.theme-toggle, .original-link-btn, .lang-btn, .font-toggle-label { 
    display: inline-flex; 
    align-items: center; 
    justify-content: center;
    box-sizing: border-box;
    cursor: pointer; 
    background: var(--toc-bg); 
    color: var(--text-color) !important; 
    border: 1px solid var(--border-color); 
    padding: 6px 14px; 
    border-radius: 20px; 
    font-size: 0.85em; 
    transition: 0.2s; 
    text-decoration: none; 
    white-space: nowrap; /* Prevents text from breaking into two lines */
    margin: 0;
}
.theme-toggle:hover, .original-link-btn:hover, .lang-btn:hover, .font-toggle-label:hover { 
    filter: brightness(1.2); 
    text-decoration: none; 
}

.lang-btn { 
    font-size: 1.1em; 
    padding: 4px 10px;
}

/* OpenDyslexic Font Configuration */
@font-face {
    font-family: 'OpenDyslexic';
    src: url('opendyslexic/OpenDyslexic-Regular.woff2') format('woff2');
    font-weight: normal;
    font-style: normal;
}
@font-face {
    font-family: 'OpenDyslexic';
    src: url('opendyslexic/OpenDyslexic-Bold.woff2') format('woff2');
    font-weight: bold;
    font-style: normal;
}
@font-face {
    font-family: 'OpenDyslexic';
    src: url('opendyslexic/OpenDyslexic-Italic.woff2') format('woff2');
    font-weight: normal;
    font-style: italic;
}
@font-face {
    font-family: 'OpenDyslexic';
    src: url('opendyslexic/OpenDyslexic-Bold-Italic.woff2') format('woff2');
    font-weight: bold;
    font-style: italic;
}

/* Apply OpenDyslexic to all elements when html has .dyslexic class */
html.dyslexic, html.dyslexic * {
    font-family: 'OpenDyslexic' !important;
    font-size-adjust: 0.45;
}

/* Additional Styling for the DSA checkbox label */
.font-toggle-label { 
    gap: 6px; 
    user-select: none;
}
.font-toggle-label input[type="checkbox"] {
    margin: 0; /* Ensures checkbox doesn't alter the button height */
}

/* Mobile adjustments for theme bar */
@media (max-width: 600px) {
    .theme-bar { 
        justify-content: center; 
        gap: 6px; 
    }
    .theme-toggle, .original-link-btn, .font-toggle-label { 
        font-size: 0.75em; 
        padding: 5px 12px;
    }
    .lang-btn { 
        font-size: 1em; 
        padding: 4px 10px;
    }
}
"""

INDEX_CSS = """
body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 20px auto; padding: 20px; }
h1 { color: #333; }
a { text-decoration: none; color: #007BFF; }
a:hover { text-decoration: underline; }

/* List and category styles */
h2.category-title { 
    color: var(--heading-color, #0056b3); 
    margin-top: 30px; 
    margin-bottom: 15px; 
    border-bottom: 1px solid var(--border-color, #eee); 
    padding-bottom: 5px; 
    font-size: 1.4em; 
}

ul.category-list, ul.simple-list { 
    padding-left: 20px; 
    margin-top: 10px; 
}

ul.category-list li, ul.simple-list li { 
    margin-bottom: 12px; 
}

/* Collapsible Course Metadata specific styling for Index/Homepage */
.course-metadata-details {
    margin-top: 30px; /* Added top margin since it is now moved to the bottom */
    margin-bottom: 20px;
    padding: 10px; /* Reduced padding to make it smaller */
    border: 1px solid var(--toc-border, #e9ecef);
    border-radius: 8px;
    background-color: var(--toc-bg, #f8f9fa);
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    font-size: 0.9em; /* Reduced base font size for the block */
}
.course-metadata-details summary {
    font-weight: bold;
    color: var(--heading-color, #0056b3);
    font-size: 1.0em; /* Scaled down the title */
    margin-bottom: 0;
    cursor: pointer;
    list-style: none; /* Hide default arrow in some browsers */
    display: flex;
    align-items: center;
}
.course-metadata-details summary::-webkit-details-marker {
    display: none;
}
.course-metadata-details[open] summary {
    margin-bottom: 12px;
    border-bottom: 1px solid var(--border-color, #eee);
    padding-bottom: 8px;
}
.course-metadata-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 10px;
}
.course-metadata-list li {
    background: var(--bg-color, #ffffff);
    padding: 8px 12px;
    border-radius: 4px;
    border: 1px solid var(--border-color, #eee);
    font-size: 0.9em;
    display: flex;
    flex-direction: column;
}
.course-metadata-list li span {
    font-weight: bold;
    color: var(--heading-color, #0056b3);
    margin-top: 4px;
}
.course-metadata-video {
    margin-top: 15px;
    position: relative;
    padding-bottom: 56.25%; /* 16:9 Aspect Ratio */
    height: 0;
    overflow: hidden;
    border-radius: 8px;
}
.course-metadata-video iframe {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
}
"""

PAGE_CSS = """
body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 20px auto; padding: 20px; }
html { scroll-behavior: smooth; }
h1 { color: #333; }

/* Unified headings and summary styles for perfect visual parity */
h2, summary.level-h2 { 
    color: var(--heading-color) !important;
    font-size: 1.8em; 
    font-weight: bold; 
    margin-top: 40px; 
    margin-bottom: 15px; 
    border-bottom: 2px solid var(--border-color); 
    padding-bottom: 5px; 
}

h3, summary.level-h3 { 
    color: var(--heading-color) !important; 
    font-size: 1.4em; 
    font-weight: bold; 
    margin-top: 30px; 
    margin-bottom: 15px; 
    border-bottom: 1px solid var(--border-color); 
    padding-bottom: 5px; 
}

h4, summary.level-h4 { 
    color: var(--heading-color) !important; 
    font-size: 1.15em; 
    font-weight: bold; 
    margin-top: 25px; 
    margin-bottom: 10px; 
}

h5, summary.level-h5, h6, summary.level-h6 { color: #333; font-size: 1.05em; font-weight: bold; margin-top: 20px; font-style: italic; margin-bottom: 10px; }

summary.level-default { color: #0056b3; font-size: 1.2em; font-weight: bold; margin-top: 25px; margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 5px; }

a { text-decoration: none; color: #007BFF; }
a:hover { text-decoration: underline; }

/* Proper indentation for lists */
ul, ol { padding-left: 40px; margin-bottom: 15px; }

/* Table of Contents */
.toc { 
    background: var(--toc-bg); 
    padding: 15px; 
    border: 1px solid var(--toc-border); 
    border-radius: 8px; 
    margin-bottom: 30px; 
}

.toc h2 { 
    margin-top: 0; 
    padding-bottom: 10px; 
    font-size: 1.2em; 
    color: var(--text-color);
    border-bottom: 2px solid var(--border-color); 
}

.toc ul { list-style-type: none; padding-left: 0; margin-bottom: 0; }
.toc li { margin-bottom: 8px; line-height: 1.3; }
.toc a { color: var(--link-color); }

/* Details and Accordion Specifics */
details { margin-bottom: 20px; }
summary { 
    display: list-item; 
    cursor: pointer; 
    outline: none; 
    transition: color 0.2s; 
    word-break: break-word;
}

summary:hover { color: #003d82; }
details[open] summary.level-h2, details[open] summary.level-h3, details[open] summary.level-default { border-bottom-color: #0056b3; }

.details-body { 
    padding-left: 15px; 
    border-left: 3px solid #f4f4f4; 
    margin-top: 10px;
}

/* Fallback for short un-wrapped accordions */
.accordion-item { margin-bottom: 20px; }
.accordion-title { font-weight: bold; color: #0056b3; font-size: 1.1em; margin-bottom: 5px; }
.accordion-content { padding-left: 10px; border-left: 3px solid #eee; }

/* Back to top button */
#back-to-top {
    display: none;
    position: fixed;
    bottom: 20px;
    right: 20px;
    background-color: #0056b3;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 10px 15px;
    font-size: 0.9em;
    cursor: pointer;
    box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    z-index: 1000;
}
#back-to-top:hover { background-color: #003d82; }
"""

TEACHERS_CSS = """
body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 20px auto; padding: 20px; }
html { scroll-behavior: smooth; }
h1 { color: #333; }
a { text-decoration: none; color: #007BFF; }
a:hover { text-decoration: underline; }
.docente-card { border: 1px solid #eee; padding: 15px; margin-bottom: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
.docente-card .content { display: flex; align-items: center; gap: 20px; }
.docente-picture img { width: 80px; height: 80px; object-fit: cover; border-radius: 50%; }
.docente-info { flex-grow: 1; }
.full-name { font-weight: bold; font-size: 1.2em; margin-bottom: 5px; }
.email, .structure { font-size: 0.9em; color: #555; margin-top: 3px; }

/* Back to top button */
#back-to-top {
    display: none;
    position: fixed;
    bottom: 20px;
    right: 20px;
    background-color: #0056b3;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 10px 15px;
    font-size: 0.9em;
    cursor: pointer;
    box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    z-index: 1000;
}
#back-to-top:hover { background-color: #003d82; }
"""

APPLY_CSS = """
.corso-home-menu--generale {
    margin-top: 50px;
    padding: 20px;
    background-color: var(--toc-bg); 
    border-top: 3px solid var(--heading-color);
    color: var(--text-color);
}
.corso-home-menu--generale ul {
    list-style: none;
    padding: 0;
}
.corso-home-menu--generale li {
    margin-bottom: 10px;
}
.corso-home-menu--generale a {
    color: var(--link-color);
}
"""

THEME_JS = """
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
"""

PAGE_LOGIC_JS = """
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
"""

def extract_course_metadata(soup, language_key):
    """
    Extracts course metadata (e.g., degree class, faculty, language) from the homepage's 'corso-info' list
    and the YouTube presentation video iframe located in 'cdl-video-video'.
    Returns them wrapped in a collapsible <details> HTML tag.
    """
    metadata_html = ""
    
    # 1. Extract the course information list
    target_ul = soup.find('ul', class_='corso-info')
            
    if target_ul:
        metadata_html += "<ul class='course-metadata-list'>\n"
        for li in target_ul.find_all('li', recursive=False):
            metadata_html += f"  <li>{li.decode_contents()}</li>\n"
        metadata_html += "</ul>\n"
        
    # 2. Extract YouTube presentation video
    video_div = soup.find('div', class_='cdl-video-video')
    if video_div:
        iframe = video_div.find('iframe')
        if iframe:
            metadata_html += f"<div class='course-metadata-video'>\n  {iframe}\n</div>\n"
    else:
        # Fallback
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src', '')
            if 'youtube.com' in src or 'youtu.be' in src:
                metadata_html += f"<div class='course-metadata-video'>\n  {iframe}\n</div>\n"
                break # Only take the first presentation video
            
    # 3. Wrap in a collapsible <details> tag if any data was found
    if metadata_html:
        # Shortened the summary title
        summary_text = "Dettagli & Video" if language_key == "it" else "Details & Video"
        collapsible_block = (
            "<details class='course-metadata-details'>\n"
            f"  <summary>ℹ️ {summary_text}</summary>\n"
            f"  <div class='details-body'>\n{metadata_html}  </div>\n"
            "</details>\n"
        )
        return collapsible_block
        
    return ""


def get_fallback_title(soup):
    """
    Extracts the title from the last item of the breadcrumb list.
    Used when the main content doesn't provide a clear H3/H4 heading.
    """
    breadcrumb = soup.find("ol", class_="breadcrumb")
    if breadcrumb:
        items = breadcrumb.find_all("li")
        if items:
            return items[-1].get_text(strip=True)
    return None

def save_static_files(output_dir="corsidilaurea"):
    """Saves the separated CSS and JS files to prevent HTML changes on styling/logic updates."""
    os.makedirs(output_dir, exist_ok=True)

    # Save CSS
    with open(os.path.join(output_dir, "index-style.css"), "w", encoding="utf-8") as f:
        f.write(INDEX_CSS)
    with open(os.path.join(output_dir, "page-style.css"), "w", encoding="utf-8") as f:
        f.write(PAGE_CSS)
    with open(os.path.join(output_dir, "theme-style.css"), "w", encoding="utf-8") as f:
        f.write(THEME_VARS_CSS)
    with open(os.path.join(output_dir, "apply-style.css"), "w", encoding="utf-8") as f:
        f.write(APPLY_CSS)
    with open(os.path.join(output_dir, "teachers-style.css"), "w", encoding="utf-8") as f:
        f.write(TEACHERS_CSS)
        
    # Save JS
    with open(os.path.join(output_dir, "theme-switch.js"), "w", encoding="utf-8") as f:
        f.write(THEME_JS)

    with open(os.path.join(output_dir, "page-logic.js"), "w", encoding="utf-8") as f:
        f.write(PAGE_LOGIC_JS)

def get_relative_path(directory, filename):
    """Calculates the relative path to the root static files based on directory depth."""
    parts = os.path.normpath(directory).split(os.sep)
    depth = len(parts) - 1
    return ("../" * depth) + filename if depth > 0 else filename

def generate_index_html(directory, links=None, title="", back_url="../index.html", metadata_html="", original_url=None, language_key="en", categorized_links=None, flag_html=""):
    """Generates an index.html file with a list of links (optionally grouped by category) and metadata."""
    index_path = os.path.join(directory, "index.html")
    theme_css_path = get_relative_path(directory, "theme-style.css")
    css_path = get_relative_path(directory, "index-style.css")
    js_theme_path = get_relative_path(directory, "theme-switch.js")

    back_html = f"<a href='{back_url}'>«</a> " if back_url else ""

    original_btn_html = ""
    if original_url:
        original_btn_text = "🌐 Pagina Originale" if language_key == "it" else "🌐 Original Page"
        original_btn_html = f'<a href="{original_url}" class="original-link-btn" target="_blank" rel="noopener noreferrer">{original_btn_text}</a>'

    theme_btn_text = "🌓 Dark Mode"
    dsa_toggle_html = '<label class="font-toggle-label"><input type="checkbox" id="font-dsa-toggle"> Font DSA</label>'
    # Inserted flag_html here to display language switch button on course index page
    theme_bar_html = f'<div class="theme-bar">{dsa_toggle_html}{flag_html}{original_btn_html}<button class="theme-toggle" onclick="toggleTheme()">{theme_btn_text}</button></div>'

    with open(index_path, "w", encoding="utf-8") as file:
        file.write("""<!DOCTYPE html>
<html lang="{language_key}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="{theme_css_path}">
    <link rel="stylesheet" href="{css_path}">
    <script src="{js_theme_path}"></script>
</head>
<body>
    <h1 id="page-title">{back_html}{title}</h1>
    {theme_bar_html}

""".format(language_key=language_key, back_html=back_html, title=title, theme_bar_html=theme_bar_html, theme_css_path=theme_css_path, css_path=css_path, js_theme_path=js_theme_path))

        # Render dynamically categorized links if provided
        if categorized_links:
            for category, cat_links in categorized_links.items():
                if not cat_links:
                    continue # Skip empty categories
                file.write(f'    <h2 class="category-title">{category}</h2>\n')
                file.write('    <ul class="category-list">\n')
                for link_text, link_url in sorted(cat_links):
                    formatted_url = link_url
                    if not link_url.startswith("http") and ".html" not in link_url and "#" not in link_url:
                        formatted_url = link_url.rstrip("/") + "/index.html"
                    file.write(f'        <li><a href="{formatted_url}">{link_text}</a></li>\n')
                file.write('    </ul>\n')
        
        # Render generic flat links (used for Root and Choose Language selection)
        elif links:
            file.write('    <ul class="simple-list">\n')
            for link_text, link_url in sorted(links):
                formatted_url = link_url
                if not link_url.startswith("http") and ".html" not in link_url and "#" not in link_url:
                    formatted_url = link_url.rstrip("/") + "/index.html"
                file.write(f'        <li><a href="{formatted_url}">{link_text}</a></li>\n')
            file.write('    </ul>\n')

        # Appending metadata_html after the list to display it at the bottom of the page
        file.write(f"""
{metadata_html}
</body>
</html>""")


def fetch_and_save_page(languages, pages, ids, course_names, course_acronyms, output_dir="corsidilaurea", custom_links=None):
    if custom_links is None:
        custom_links = {}
        
    base_url = "https://corsidilaurea.uniroma1.it"
    url_pattern = base_url + "/{}/course/{}/{}"
    os.makedirs(output_dir, exist_ok=True)

    # Root index
    root_links = [(name, str(cid)) for cid, name in course_names.items() if cid in ids]
    # No back button for the root directory
    generate_index_html(output_dir, links=root_links, title="Degree Courses", back_url=None)

    for course_id in ids:
        acronym = course_acronyms.get(course_id, str(course_id))
        course_prefix = f"[{acronym}] "

        course_dir = os.path.join(output_dir, str(course_id))
        os.makedirs(course_dir, exist_ok=True)

        # Calculate how many languages are actually generated for this course
        valid_langs = [l for l in languages if not (l == "en" and course_id in EXCLUDED_EN_IDS)]
        is_single_lang = len(valid_langs) == 1

        language_links = []
        for language_key in languages:
            # Skip English if course is in exclusion list
            if language_key == "en" and course_id in EXCLUDED_EN_IDS:
                continue

            language_dir = os.path.join(course_dir, language_key)
            os.makedirs(language_dir, exist_ok=True)

            homepage_url = f"{base_url}/{language_key}/course/{course_id}"
            extracted_metadata = ""
            try:
                hp_resp = requests.get(homepage_url, timeout=15)
                if hp_resp.status_code == 200:
                    hp_soup = BeautifulSoup(hp_resp.text, 'html.parser')
                    extracted_metadata = extract_course_metadata(hp_soup, language_key)
            except requests.RequestException as e:
                print(f"Could not fetch homepage for metadata ({homepage_url}): {e}")

            page_links = []

            for language_page in pages:
                url = url_pattern.format(language_key, course_id, language_page)

                # Handle connection errors and invalid responses gracefully                
                try:
                    response = requests.get(url, timeout=15)
                    response.raise_for_status()
                except requests.RequestException as e:
                    print(f"Skipping {url} due to request error: {e}")
                    continue

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Fix links to be absolute
                    for a_tag in soup.find_all("a", href=True):
                        if a_tag["href"].startswith("/"):
                            a_tag["href"] = urljoin(base_url, a_tag["href"])

                    # Extract main content
                    content_blocks = []

                    main_div = soup.find("div", id="cdl-course-home-text")
                    if not main_div:
                        main_div = soup.find("div", id="cdl-course-attendance-text")

                    if main_div:
                        content_blocks.append(main_div)
                    else:
                        accordions = soup.find_all("div", class_="cdl-accordion")
                        if accordions:
                            for acc in accordions:
                                parent = acc.parent
                                if parent and parent not in content_blocks:
                                    content_blocks.append(parent)

                        if not content_blocks:
                            mt_divs = soup.find_all("div", class_=re.compile(r'^mt-\d+$'))
                            for mt_div in mt_divs:
                                col_div = mt_div.find("div", class_=re.compile(r'^col-md-\d+$'))
                                if col_div:
                                    content_blocks.append(col_div)
                                    break

                    if content_blocks:
                        combined_content = ""
                        page_heading = ""
                        toc_items = []
                        
                        # 1. Assessment phase: decide if we should wrap long blocks in <details>
                        wrap_candidates_count = 0
                        for block in content_blocks:
                            field_item_div = block.find("div", class_="field-item")
                            pb_count = field_item_div if field_item_div else block
                            
                            for acc_item in pb_count.find_all("div", class_="accordion-item"):
                                content_div = acc_item.find("div", class_="accordion-content")
                                if content_div:
                                    char_len = len(content_div.get_text(strip=True))
                                    vertical_items = len(content_div.find_all(['tr', 'li', 'br']))
                                    if char_len > 800 or vertical_items > 8:
                                        wrap_candidates_count += 1
                                    
                            for child_elem in pb_count.children:
                                if child_elem.name == "div" and "cdl-accordion" not in child_elem.get("class", []) and "accordion-item" not in child_elem.get("class", []):
                                    if child_elem.get("id") in ["cdl-course-home-text", "cdl-course-attendance-text"]:
                                        continue
                                    
                                    char_len = len(child_elem.get_text(strip=True))
                                    vertical_items = len(child_elem.find_all(['tr', 'li', 'br']))
                                    if char_len > 1200 or vertical_items > 10:
                                        wrap_candidates_count += 1
                        
                        # True only if there's more than one large section
                        should_wrap = wrap_candidates_count > 1

                        # 2. Processing phase
                        for i, block in enumerate(content_blocks):
                            field_item_div = block.find("div", class_="field-item")
                            process_block = field_item_div if field_item_div else block

                            # Clean up
                            for script in process_block.find_all(["script", "manifesto"]):
                                script.decompose()
                            
                            optional_group_popup = process_block.find("div", id="optional-group-popup-div")
                            if optional_group_popup:
                                optional_group_popup.decompose()

                            # Phase 2.1: Assign IDs to all headers before any wrapping occurs
                            for h_tag in process_block.find_all(['h2', 'h3', 'h4', 'h5', 'h6']):
                                raw_text = h_tag.get_text(strip=True)
                                if not raw_text: continue
                                    
                                if not h_tag.has_attr('id'):
                                    h_id = re.sub(r'[^a-z0-9]+', '-', raw_text.lower()).strip('-')
                                    if not h_id: h_id = f"header-{id(h_tag)}"
                                    h_tag['id'] = h_id
                                else:
                                    h_id = h_tag['id']
                                
                                header_level = int(h_tag.name[1]) 
                                toc_items.append((header_level, raw_text, h_id))

                            # Wrapping logic
                            if should_wrap:
                                # Wrap accordion-items
                                for acc_item in process_block.find_all("div", class_="accordion-item"):
                                    content_div = acc_item.find("div", class_="accordion-content")
                                    if content_div:
                                        char_len = len(content_div.get_text(strip=True))
                                        vertical_items = len(content_div.find_all(['tr', 'li', 'br']))
                                        
                                        if char_len > 800 or vertical_items > 8:
                                            details_tag = soup.new_tag("details")
                                            summary_tag = soup.new_tag("summary")
                                            level_class = "level-default"
                                            
                                            title_div = acc_item.find("div", class_="accordion-title")
                                            if title_div:
                                                h_tag = title_div.find(['h2', 'h3', 'h4', 'h5', 'h6'])
                                                if h_tag:
                                                    level_class = f"level-{h_tag.name}"
                                                    # Transfer ID to summary so anchor links scroll to it correctly
                                                    if h_tag.has_attr('id'):
                                                        summary_tag['id'] = h_tag['id']
                                                summary_tag.string = title_div.get_text(separator=" ", strip=True)
                                                title_div.decompose()
                                            else:
                                                summary_tag.string = "Dettagli" if language_key == "it" else "Details"
                                                
                                            summary_tag['class'] = level_class
                                            details_tag.append(summary_tag)
                                            body_div = soup.new_tag("div", attrs={"class": "details-body"})
                                            for child in list(content_div.children): body_div.append(child)
                                            details_tag.append(body_div)
                                            acc_item.insert_after(details_tag)
                                            acc_item.decompose()

                                # Wrap other large divs
                                for child_elem in list(process_block.children):
                                    if child_elem.name == "div" and "cdl-accordion" not in child_elem.get("class", []) and "accordion-item" not in child_elem.get("class", []):
                                        if child_elem.get("id") in ["cdl-course-home-text", "cdl-course-attendance-text"]: continue
                                            
                                        char_len = len(child_elem.get_text(strip=True))
                                        vertical_items = len(child_elem.find_all(['tr', 'li', 'br']))
                                        
                                        if char_len > 800 or vertical_items > 10:
                                            details_tag = soup.new_tag("details")
                                            summary_tag = soup.new_tag("summary")
                                            level_class = "level-default"
                                            
                                            first_tag = child_elem.find(['h2', 'h3', 'h4', 'h5', 'strong'])
                                            if first_tag and len(first_tag.get_text(strip=True)) < 100:
                                                if first_tag.name in ['h2', 'h3', 'h4', 'h5', 'h6']:
                                                    level_class = f"level-{first_tag.name}"
                                                    # Transfer ID
                                                    if first_tag.has_attr('id'):
                                                        summary_tag['id'] = first_tag['id']
                                                elif first_tag.name == 'strong':
                                                    level_class = "level-h4"
                                                    # Transfer ID
                                                    if first_tag.has_attr('id'):
                                                        summary_tag['id'] = first_tag['id']
                                                summary_tag.string = first_tag.get_text(separator=" ", strip=True)
                                                first_tag.decompose()
                                            else:
                                                th_tag = child_elem.select_one("thead tr th")
                                                if th_tag and len(th_tag.get_text(strip=True)) < 150:
                                                    summary_tag.string = th_tag.get_text(separator=" ", strip=True)
                                                    level_class = "level-h4"
                                                else:
                                                    summary_tag.string = "Approfondimento" if language_key == "it" else "More details"
                                                
                                            summary_tag['class'] = level_class
                                            details_tag.append(summary_tag)
                                            body_div = soup.new_tag("div", attrs={"class": "details-body"})
                                            child_elem.insert_after(details_tag)
                                            body_div.append(child_elem)
                                            details_tag.append(body_div)

                            # Handle heading and cleanup first block
                            if i == 0:
                                h3_tag = process_block.find("h3")
                                breadcrumb_title = get_fallback_title(soup) # Fallback to breadcrumb if h3 is missing

                                if h3_tag:
                                    h3_id = h3_tag.get('id')
                                    if h3_id: toc_items = [item for item in toc_items if item[2] != h3_id]
                                    page_heading = f"{course_prefix}{h3_tag.get_text(strip=True)}"
                                    h3_tag.decompose() 
                                elif breadcrumb_title:
                                    page_heading = f"{course_prefix}{breadcrumb_title}"
                                else:
                                    page_title = " ".join([word.capitalize() if word not in ["di", "del", "della", "delle"] else word for word in language_page.replace("-", " ").split()]).replace("Desame","d'Esame")
                                    page_heading = f"{course_prefix}{page_title}"

                            # Phase 2.2: Add physical anchors only to visible non-collapsible headings
                            for h_tag in process_block.find_all(['h2', 'h3', 'h4', 'h5', 'h6']):
                                # Skip headings inside collapsibles to avoid interfering with click events
                                if h_tag.find_parent('summary') or h_tag.find_parent('details'):
                                    continue

                                if h_tag.has_attr('id') and not h_tag.find("a", class_="heading-anchor"):
                                    h_id = h_tag['id']
                                    anchor = soup.new_tag("a", href=f"#{h_id}", attrs={"class": "heading-anchor", "title": "Copy direct link"})
                                    anchor.string = "#"
                                    h_tag.append(" ")
                                    h_tag.append(anchor)

                            combined_content += '\n'.join([line for line in str(process_block).splitlines() if line.strip()]).replace(" ", " ") + "\n"

                        # Calculate relative path depth
                        page_depth = language_page.count('/')
                        
                        # Path to go up from page to language folder (e.g. it/ or en/)
                        up_to_lang = "../" * (page_depth + 1)
                        
                        # Path to go up to the root 'corsidilaurea' where static assets live
                        # Since pages are in course_id/lang_key/page.html, we need (page_depth + 2)
                        rel_to_static_root = "../" * (page_depth + 2)
                        
                        # Back button: return to current course language index (e.g. it/index.html)
                        back_link = "index.html" if page_depth == 0 else "../index.html"
                        
                        filename = f"{language_page}.html"
                        output_path = os.path.join(language_dir, filename)
                        
                        # Create subdirectories automatically (e.g., 'attendance/')
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)

                        # Asset paths using rel_to_static_root
                        theme_css_path = f"{rel_to_static_root}theme-style.css"
                        css_path = f"{rel_to_static_root}page-style.css"
                        js_path = f"{rel_to_static_root}page-logic.js"
                        js_theme_path = f"{rel_to_static_root}theme-switch.js"

                        # Build language toggle with correct subdirectory jumping
                        flag_html = ""
                        if course_id not in EXCLUDED_EN_IDS:
                            other_lang = "en" if language_key == "it" else "it"
                            flag = "🇮🇹" if language_key == "it" else "🇬🇧"
                            # Path: Up to course root -> other lang folder -> same subpath/file
                            flag_url = f"{up_to_lang}{other_lang}/{filename}"
                            flag_html = f'<a href="{flag_url}" class="lang-btn" title="Switch language">{flag}</a>'

                        # Table of Contents HTML
                        toc_html = ""
                        if toc_items:
                            toc_title = "Indice" if language_key == "it" else "Table of Contents"
                            toc_html = f'<div class="toc">\n<h2>{toc_title}</h2>\n<ul>\n'

                            min_level = min(item[0] for item in toc_items)
                            
                            for level, text, link_id in toc_items:
                                margin_left = (level - min_level) * 20
                                toc_html += f'    <li style="margin-left: {margin_left}px;"><a href="#{link_id}">{text}</a></li>\n'
                            toc_html += '</ul>\n</div>\n'

                        back_to_top_text = "Torna sù" if language_key == "it" else "Back to top"
                        
                        # Theme bar with added DSA and Original Page links
                        dsa_text = "Font DSA" #if language_key == "it" else "DSA Font"
                        dsa_toggle_html = f'<label class="font-toggle-label"><input type="checkbox" id="font-dsa-toggle"> {dsa_text}</label>'
                        original_btn_text = "🌐 Pagina Originale" if language_key == "it" else "🌐 Original Page"
                        theme_bar_html = f'<div class="theme-bar">{dsa_toggle_html}{flag_html}<a href="{url}" class="original-link-btn" target="_blank" rel="noopener noreferrer">{original_btn_text}</a><button class="theme-toggle" onclick="toggleTheme()">🌓 Dark Mode</button></div>'

                        # Final HTML construction (H1 has no anchor)
                        content = f"""<!DOCTYPE html>
<html lang="{language_key}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_heading}</title>
    <link rel="stylesheet" href="{theme_css_path}">
    <link rel="stylesheet" href="{css_path}">
    <script src="{js_theme_path}"></script>
</head>
<body>
<h1 id="page-title"><a href='{back_link}'>«</a> {page_heading}</h1>
{theme_bar_html}
{toc_html}
<div class="content-wrapper">
{combined_content}
</div>
<button id="back-to-top" title="{back_to_top_text}" onclick="window.scrollTo({{top: 0, behavior: 'smooth'}})">▲ {back_to_top_text}</button>
<script src="{js_path}"></script>
</body>
</html>"""

                        with open(output_path, "w", encoding="utf-8") as file:
                            file.write(content)

                        clean_link_title = page_heading.replace(course_prefix, "")
                        page_links.append((clean_link_title, filename))
                        print(f"Saved: {output_path}")
                    else:
                        print(f"No useful content found for {course_id}/{language_key}/{language_page}")

            # Append manual links for apply and teachers
            page_links.append(("How and When to Enroll" if language_key == "en" else "Come e quando iscriversi", "apply.html"))
            page_links.append(("Teachers" if language_key == "en" else "Docenti", "teachers.html"))

            if page_links:
                # Always go back to global catalogue root since language selection page is removed
                lang_back_url = "../../index.html"

                # Define structural categories
                categories_dict = {
                    "it": {
                        "info": "Informazioni sul corso",
                        "opp": "Opportunità",
                        "freq": "Frequentare",
                        "ext": "Link esterni"
                    },
                    "en": {
                        "info": "Course Information",
                        "opp": "Opportunities",
                        "freq": "Attendance",
                        "ext": "External Links"
                    }
                }
                cats = categories_dict.get(language_key, categories_dict["en"])

                # Mapping scraped page filenames to their respective categories
                file_to_cat = {
                    "presentation.html": "info",
                    "objectives.html": "info",
                    "professional-opportunities.html": "info",
                    "choice-orientation.html": "info",
                    "quality.html": "info",
                    "international-experiences.html": "opp",
                    "attendance/instructions.html": "freq",
                    "organization.html": "freq",
                    "apply.html": "freq",
                    "teachers.html": "freq"
                }

                # Pre-initialize categorized map to maintain section order
                categorized_links = {
                    cats["info"]: [],
                    cats["opp"]: [],
                    cats["freq"]: [],
                    cats["ext"]: []
                }

                for link_text, filename in page_links:
                    cat_key = file_to_cat.get(filename, "info") # Fallback to info
                    categorized_links[cats[cat_key]].append((link_text, filename))
                
                # Appendi custom links condivisi (chiave "all")
                if "all" in custom_links and language_key in custom_links["all"]:
                    for link_text, link_url in custom_links["all"][language_key]:
                        categorized_links[cats["ext"]].append((link_text, link_url))

                # Appendi custom links specifici per il singolo corso
                if course_id in custom_links and language_key in custom_links[course_id]:
                    for link_text, link_url in custom_links[course_id][language_key]:
                        categorized_links[cats["ext"]].append((link_text, link_url))

                # Filter out empty categories
                categorized_links = {k: v for k, v in categorized_links.items() if v}

                # Build language toggle for the index page
                index_flag_html = ""
                if course_id not in EXCLUDED_EN_IDS:
                    other_lang = "en" if language_key == "it" else "it"
                    flag = "🇮🇹" if language_key == "it" else "🇬🇧"
                    index_flag_html = f'<a href="../{other_lang}/index.html" class="lang-btn" title="Switch language">{flag}</a>'

                generate_index_html(
                    directory=language_dir, 
                    title=course_names.get(course_id, course_prefix), 
                    back_url=lang_back_url, 
                    metadata_html=extracted_metadata,
                    original_url=homepage_url,
                    language_key=language_key,
                    categorized_links=categorized_links,
                    flag_html=index_flag_html
                )
                language_links.append((language_key.replace("en","English").replace("it","Italian"), f"{language_key}/index.html"))

        if language_links:
            # Default to English if available, otherwise use the first available language
            default_lang_path = "en/index.html" if "en" in valid_langs else language_links[0][1]
            with open(os.path.join(course_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(f'<html><head><meta http-equiv="refresh" content="0;url={default_lang_path}"></head></html>')

def fetch_and_save_teachers(languages, ids, course_acronyms, output_dir="corsidilaurea"):
    base_url = "https://corsidilaurea.uniroma1.it"
    os.makedirs(output_dir, exist_ok=True)

    for course_id in ids:
        acronym = course_acronyms.get(course_id, str(course_id))
        course_prefix = f"[{acronym}] "
        course_dir = os.path.join(output_dir, str(course_id))
        
        for language_key in languages:
            if language_key == "en" and course_id in EXCLUDED_EN_IDS:
                continue
                
            language_dir = os.path.join(course_dir, language_key)
            os.makedirs(language_dir, exist_ok=True)
            
            url = f"{base_url}/{language_key}/course/{course_id}/teachers"
            
            try:
                response = requests.get(url, timeout=15)
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"Skipping {url} due to request error: {e}")
                continue
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for a_tag in soup.find_all("a", href=True):
                    if a_tag["href"].startswith("/"):
                        a_tag["href"] = urljoin(base_url, a_tag["href"])
                
                for img_tag in soup.find_all("img", src=True):
                    if img_tag["src"].startswith("/"):
                        img_tag["src"] = urljoin(base_url, img_tag["src"])
                        
                teachers_container = soup.find("div", class_="docente-cerca-results")
                
                if teachers_container:
                    # Generate IDs and anchors for headings inside the container
                    for h_tag in teachers_container.find_all(['h2', 'h3', 'h4', 'h5', 'h6']):
                        # Skip headings inside collapsibles
                        if h_tag.find_parent('summary') or h_tag.find_parent('details'):
                            continue

                        raw_text = h_tag.get_text(strip=True)
                        if not raw_text: continue
                        
                        if not h_tag.has_attr('id'):
                            h_id = re.sub(r'[^a-z0-9]+', '-', raw_text.lower()).strip('-')
                            if not h_id: h_id = f"header-{id(h_tag)}"
                            h_tag['id'] = h_id
                        else:
                            h_id = h_tag['id']
                        
                        if not h_tag.find("a", class_="heading-anchor"):
                            anchor = soup.new_tag("a", href=f"#{h_id}", attrs={"class": "heading-anchor", "title": "Copy direct link"})
                            anchor.string = "#"
                            h_tag.append(" ")
                            h_tag.append(anchor)

                    teacher_cards = teachers_container.find_all("div", class_="docente-card")
                    
                    if teacher_cards:
                        def get_surname(card):
                            email_element = card.find("div", class_="email")
                            if email_element:
                                email_text = email_element.get_text(strip=True)
                                if "@" in email_text:
                                    local_part = email_text.split("@")[0]
                                    if "." in local_part:
                                        return local_part.split(".", 1)[1].lower()
                                    return local_part.lower()

                            name_element = card.find("div", class_="full-name")
                            if name_element:
                                full_name = name_element.get_text(strip=True)
                                parts = full_name.split()
                                return parts[-1].lower() if parts else ""
                            return ""

                        sorted_cards = sorted(teacher_cards, key=get_surname)
                        
                        teachers_container.clear()
                        for card in sorted_cards:
                            teachers_container.append(card)

                    main_section = soup.find("section", id="block-system-main")
                    h3_tag = main_section.find("h3") if main_section else None
                    breadcrumb_title = get_fallback_title(soup)

                    if h3_tag:
                        page_heading = f"{course_prefix}{h3_tag.get_text(strip=True)}"
                    elif breadcrumb_title:
                        page_heading = f"{course_prefix}{breadcrumb_title}"
                    else:
                        fallback_title = "Teachers" if language_key == "en" else "Docenti"
                        page_heading = f"{course_prefix}{fallback_title}"

                    flag_html = ""
                    if course_id not in EXCLUDED_EN_IDS:
                        other_lang = "en" if language_key == "it" else "it"
                        flag = "🇮🇹" if language_key == "it" else "🇬🇧"
                        flag_html = f'<a href="../{other_lang}/teachers.html" class="lang-btn" title="Switch language">{flag}</a>'
                    
                    back_to_top_text = "Torna sù" if language_key == "it" else "Back to top"
                    
                    # Theme bar with added DSA and Original Page links
                    theme_btn_text = "🌓 Dark Mode"
                    dsa_text = "Font DSA" #if language_key == "it" else "DSA Font"
                    dsa_toggle_html = f'<label class="font-toggle-label"><input type="checkbox" id="font-dsa-toggle"> {dsa_text}</label>'
                    original_btn_text = "🌐 Pagina Originale" if language_key == "it" else "🌐 Original Page"
                    theme_bar_html = f'<div class="theme-bar">{dsa_toggle_html}{flag_html}<a href="{url}" class="original-link-btn" target="_blank" rel="noopener noreferrer">{original_btn_text}</a><button class="theme-toggle" onclick="toggleTheme()">{theme_btn_text}</button></div>'

                    # Calculate relative paths
                    theme_css_path = get_relative_path(language_dir, "theme-style.css")
                    css_path = get_relative_path(language_dir, "teachers-style.css")
                    js_path = get_relative_path(language_dir, "page-logic.js")
                    js_theme_path = get_relative_path(language_dir, "theme-switch.js")

                    # Update the content formatting (H1 has no anchor)
                    content = """<!DOCTYPE html>
                    <html lang="{lang}">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>{title}</title>
                        <link rel="stylesheet" href="{theme_css_path}">
                        <link rel="stylesheet" href="{css_path}">
                        <script src="{js_theme_path}"></script>
                    </head>
                    <body>
                    <h1 id="page-title"><a href='index.html'>«</a> {heading}</h1>
                    {theme_bar_html}
                    {content}

                    <button id="back-to-top" title="{btn_text}" onclick="window.scrollTo({{top: 0, behavior: 'smooth'}})">▲ {btn_text}</button>
                    <script src="{js_path}"></script>
                    </body>
                    </html>""".format(
                        lang=language_key,
                        title=page_heading,
                        heading=page_heading,
                        theme_bar_html=theme_bar_html,
                        content=teachers_container.prettify() if teachers_container else "",
                        btn_text=back_to_top_text,
                        theme_css_path=theme_css_path,
                        css_path=css_path,
                        js_path=js_path,
                        js_theme_path=js_theme_path
                    )
                    
                    output_path = os.path.join(language_dir, "teachers.html")
                    with open(output_path, "w", encoding="utf-8") as file:
                        file.write(content)
                    print(f"Saved: {output_path}")

def fetch_and_save_apply(languages, ids, course_names, course_acronyms, output_dir="corsidilaurea"):
    """
    Scrapes the 'apply' (iscrizione) page for each course, including the general sidebar.
    """
    base_url = "https://corsidilaurea.uniroma1.it"
    url_pattern = base_url + "/{}/course/{}/apply"
    
    for course_id in ids:
        acronym = course_acronyms.get(course_id, str(course_id))
        course_prefix = f"[{acronym}] "
        course_dir = os.path.join(output_dir, str(course_id))

        for language_key in languages:
            # Skip English if course is in exclusion list
            if language_key == "en" and course_id in EXCLUDED_EN_IDS:
                continue
                
            url = url_pattern.format(language_key, course_id)
            lang_dir = os.path.join(course_dir, language_key)
            os.makedirs(lang_dir, exist_ok=True)
            
            try:
                response = requests.get(url, timeout=15)
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"Skipping apply page for {course_id} [{language_key}] due to error: {e}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Absolute URL conversion for links and images
            for tag in soup.find_all(["a", "img"]):
                attr = "href" if tag.name == "a" else "src"
                if tag.get(attr) and tag[attr].startswith("/"):
                    tag[attr] = urljoin(base_url, tag[attr])

            content_blocks = []

            mt_divs = soup.find_all("div", class_=re.compile(r'^mt-\d+$'))
            for mt_div in mt_divs:
                col_div = mt_div.find("div", class_=re.compile(r'^col-md-\d+$'))
                if col_div: content_blocks.append(col_div)

            sidebar = soup.find("div", class_="corso-home-menu--generale")
            if sidebar: content_blocks.append(sidebar)

            if content_blocks:
                combined_content = ""
                for block in content_blocks:
                    for script in block.find_all("script"): script.decompose()
                    
                    # Generate IDs and insert clickable anchors
                    for h_tag in block.find_all(['h2', 'h3', 'h4', 'h5', 'h6']):
                        # Skip headings inside collapsibles 
                        if h_tag.find_parent('summary') or h_tag.find_parent('details'):
                            continue

                        raw_text = h_tag.get_text(strip=True)
                        if not raw_text: continue
                        
                        if not h_tag.has_attr('id'):
                            h_id = re.sub(r'[^a-z0-9]+', '-', raw_text.lower()).strip('-')
                            if not h_id: h_id = f"header-{id(h_tag)}"
                            h_tag['id'] = h_id
                        else:
                            h_id = h_tag['id']
                            
                        if not h_tag.find("a", class_="heading-anchor"):
                            anchor = soup.new_tag("a", href=f"#{h_id}", attrs={"class": "heading-anchor", "title": "Copy direct link"})
                            anchor.string = "#"
                            h_tag.append(" ")
                            h_tag.append(anchor)

                    combined_content += block.prettify()

                # RELATIVE PATH CALCULATIONS
                # Since apply.html is at lang_dir level (e.g. it/apply.html), depth is 0
                page_depth = 0
                
                # Path to go up from page to language folder
                up_to_lang = "../" * (page_depth + 1)
                
                # Path to go up to the root 'corsidilaurea' where static assets live
                # From it/apply.html we need to go up 2 levels (lang_dir -> course_id -> root)
                rel_to_static_root = "../" * (page_depth + 2)
                
                # Back button: return to current course language index (it/index.html)
                back_link = "index.html"

                # Asset paths using rel_to_static_root
                theme_css_path = f"{rel_to_static_root}theme-style.css"
                css_path = f"{rel_to_static_root}page-style.css"
                apply_css_path = f"{rel_to_static_root}apply-style.css"
                js_path = f"{rel_to_static_root}page-logic.js"
                js_theme_path = f"{rel_to_static_root}theme-switch.js"
                
                # Handle heading with Breadcrumb fallback
                main_section = soup.find("section", id="block-system-main")
                h4_tag = main_section.find("h4") if main_section else None
                breadcrumb_title = get_fallback_title(soup)

                if h4_tag:
                    page_heading = f"{course_prefix}{h4_tag.get_text(strip=True)}"
                elif breadcrumb_title:
                    page_heading = f"{course_prefix}{breadcrumb_title}"
                else:
                    page_heading = f"{course_prefix}" + ("How and When to Enroll" if language_key == "en" else "Come e quando iscriversi")

                # Language Toggle with correct subdirectory jumping
                flag_html = ""
                if course_id not in EXCLUDED_EN_IDS:
                    other_lang = "en" if language_key == "it" else "it"
                    flag = "🇮🇹" if language_key == "it" else "🇬🇧"
                    # Path: Up to course root -> other lang folder -> same filename
                    lang_link = f"{up_to_lang}{other_lang}/apply.html"
                    flag_html = f'<a href="{lang_link}" class="lang-btn" title="Switch language">{flag}</a>'

                back_to_top_text = "Torna sù" if language_key == "it" else "Back to top"
                
                # Theme bar with added DSA and Original Page links
                dsa_text = "Font DSA" #if language_key == "it" else "DSA Font"
                dsa_toggle_html = f'<label class="font-toggle-label"><input type="checkbox" id="font-dsa-toggle"> {dsa_text}</label>'
                original_btn_text = "🌐 Pagina Originale" if language_key == "it" else "🌐 Original Page"
                theme_bar_html = f'<div class="theme-bar">{dsa_toggle_html}{flag_html}<a href="{url}" class="original-link-btn" target="_blank" rel="noopener noreferrer">{original_btn_text}</a><button class="theme-toggle" onclick="toggleTheme()">🌓 Dark Mode</button></div>'

                # Final HTML construction (H1 has no anchor)
                html_content = f"""<!DOCTYPE html>
<html lang="{language_key}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_heading}</title>
    <link rel="stylesheet" href="{theme_css_path}">
    <link rel="stylesheet" href="{css_path}">
    <link rel="stylesheet" href="{apply_css_path}">
    <script src="{js_theme_path}"></script>
</head>
<body>
    <h1 id="page-title"><a href='{back_link}'>«</a> {page_heading}</h1>
    {theme_bar_html}
    <div class="content-wrapper">
        {combined_content}
    </div>
    <button id="back-to-top" title="{back_to_top_text}" onclick="window.scrollTo({{top: 0, behavior: 'smooth'}})">▲ {back_to_top_text}</button>
    <script src="{js_path}"></script>
</body>
</html>"""

                output_path = os.path.join(lang_dir, "apply.html")
                with open(output_path, "w", encoding="utf-8") as file:
                    file.write(html_content)
                print(f"Saved: {output_path}")

if __name__ == "__main__":
    COURSE_NAMES = {
        33502: "ACSAI",
        33508: "Computer Science",
        33516: "Cybersecurity",
        33519: "Data Science",
        33503: "Informatica",
        33504: "Informatica - a distanza"
    }

    COURSE_ACRONYMS = {
        33502: "ACSAI",
        33508: "CS",
        33516: "CYBSEC",
        33519: "DS",
        33503: "INF",
        33504: "INF - A DIST."
    }

    # Custom links configuration mapping per course_id and language
    # Provide an ordered list of tuples (Link_Text, URL) that will be appended to the "External Links" section.
    # The "all" key applies links to EVERY course automatically.
    CUSTOM_LINKS = {
        "all": {
            "it": [
                ("Sito Web del Dipartimento (DI)", "https://www.di.uniroma1.it/it"),
                ("Sito Web della Facoltà (I3S)", "https://i3s.web.uniroma1.it/it")
            ],
            "en": [
                ("Department Website (DI)", "https://www.di.uniroma1.it/en"),
                ("Faculty Website (I3S)", "https://i3s.web.uniroma1.it/en")
            ]
        },
        33502: {
            "it": [
                ("Wiki del Corso su sapienzastudents.net", "https://sapienzastudents.net/acsai"),
                ("Gruppo Telegram del Corso di Laurea", "https://t.me/+0XvGe7P6Yb5hYTky")
            ],
            "en": [
                ("Course Wiki on sapienzastudents.net", "https://sapienzastudents.net/acsai"),
                ("Telegram Group for the Degree Course", "https://t.me/+0XvGe7P6Yb5hYTky")
            ]
        },
        33503: {
            "it": [
                ("Wiki del Corso su sapienzastudents.net", "https://sapienzastudents.net/it"),
                ("Gruppo Telegram del Corso di Laurea", "https://t.me/+o8wqkLM2NS1lMGI0")
            ],
            "en": [
                ("Course Wiki on sapienzastudents.net", "https://sapienzastudents.net/it"),
                ("Telegram Group for the Degree Course", "https://t.me/+o8wqkLM2NS1lMGI0")
            ]
        },
        33504: {
            "it": [
                ("Wiki del Corso su sapienzastudents.net", "https://sapienzastudents.net/it"),
                ("Gruppo Telegram del Corso di Laurea", "https://t.me/+JGzMbJh6QeFlYjlk")
            ],
            "en": [
                ("Course Wiki on sapienzastudents.net", "https://sapienzastudents.net/it"),
                ("Telegram Group for the Degree Course", "https://t.me/+JGzMbJh6QeFlYjlk")
            ]
        },
        33516: {
            "it": [
                ("Wiki del Corso su sapienzastudents.net", "https://sapienzastudents.net/it"),
                ("Gruppo Telegram del Corso di Laurea", "https://t.me/+MCDGWHGxGUg3ZTgy")
            ],
            "en": [
                ("Course Wiki on sapienzastudents.net", "https://sapienzastudents.net/it"),
                ("Telegram Group for the Degree Course", "https://t.me/+MCDGWHGxGUg3ZTgy")
            ]
        },
        33519: {
            "it": [
                ("Wiki del Corso su sapienzastudents.net", "https://sapienzastudents.net/it"),
                ("Gruppo Telegram del Corso di Laurea", "https://t.me/+kBVAbCt9WAw1ZDhk")
            ],
            "en": [
                ("Course Wiki on sapienzastudents.net", "https://sapienzastudents.net/it"),
                ("Telegram Group for the Degree Course", "https://t.me/+kBVAbCt9WAw1ZDhk")
            ]
        }
    }

    LANGUAGES = ["it", "en"]
    PAGES = [
        "presentation",
        "objectives",
        "professional-opportunities",
        "choice-orientation",
        "international-experiences",
        "organization",
        "quality",
        "attendance/instructions"
    ]
    IDS = [33502, 33508, 33516, 33519, 33503, 33504]
    OUTPUT_DIRECTORY = "corsidilaurea"

    save_static_files(output_dir="corsidilaurea")

    # Run scraping
    fetch_and_save_apply(LANGUAGES, IDS, COURSE_NAMES, COURSE_ACRONYMS, OUTPUT_DIRECTORY)
    fetch_and_save_teachers(LANGUAGES, IDS, COURSE_ACRONYMS, OUTPUT_DIRECTORY)
    fetch_and_save_page(LANGUAGES, PAGES, IDS, COURSE_NAMES, COURSE_ACRONYMS, OUTPUT_DIRECTORY, custom_links=CUSTOM_LINKS)