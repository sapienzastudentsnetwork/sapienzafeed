import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Courses that should NOT have an English version
EXCLUDED_EN_IDS = (33503, 33504)

# Separate CSS content to avoid triggering HTML changes on styling updates
INDEX_CSS = """
body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 20px auto; padding: 20px; }
h1 { color: #333; }
a { display: inline-block; margin-top: 20px; text-decoration: none; color: #007BFF; }
"""

PAGE_CSS = """
body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 20px auto; padding: 20px; }
html { scroll-behavior: smooth; }
h1 { color: #333; }

/* Unified headings and summary styles for perfect visual parity */
h2, summary.level-h2 { color: #0056b3; font-size: 1.8em; font-weight: bold; margin-top: 40px; margin-bottom: 15px; border-bottom: 2px solid #eee; padding-bottom: 5px; }
h3, summary.level-h3 { color: #0056b3; font-size: 1.4em; font-weight: bold; margin-top: 30px; margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 5px; }
h4, summary.level-h4 { color: #004085; font-size: 1.15em; font-weight: bold; margin-top: 25px; margin-bottom: 10px; border-bottom: none; }
h5, summary.level-h5, h6, summary.level-h6 { color: #333; font-size: 1.05em; font-weight: bold; margin-top: 20px; font-style: italic; margin-bottom: 10px; }

summary.level-default { color: #0056b3; font-size: 1.2em; font-weight: bold; margin-top: 25px; margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 5px; }

h2:hover::after, h3:hover::after, h4:hover::after { content: ' #'; color: #ccc; font-size: 0.8em; }
a { text-decoration: none; color: #007BFF; }
a:hover { text-decoration: underline; }

/* Proper indentation for lists */
ul, ol { padding-left: 40px; margin-bottom: 15px; }

/* Table of Contents */
.toc { background: #f8f9fa; padding: 15px; border: 1px solid #e9ecef; border-radius: 8px; margin-bottom: 30px; }
.toc h2 { margin-top: 0; padding-bottom: 10px; font-size: 1.2em; color: #333; border-bottom: 2px solid #ddd; }
.toc ul { list-style-type: none; padding-left: 0; margin-bottom: 0; }
.toc li { margin-bottom: 8px; line-height: 1.3; }
.toc a { color: #0056b3; }

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

APPLY_SIDEBAR_CSS = """
.corso-home-menu--generale {
    margin-top: 50px;
    padding: 20px;
    background-color: #f9f9f9;
    border-top: 3px solid #0056b3;
}
.corso-home-menu--generale ul {
    list-style: none;
    padding: 0;
}
.corso-home-menu--generale li {
    margin-bottom: 10px;
}
"""

BACK_TO_TOP_JS = """
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
"""

def save_static_files(output_dir="corsidilaurea"):
    """Saves the separated CSS and JS files to prevent HTML changes on styling/logic updates."""
    os.makedirs(output_dir, exist_ok=True)

    # Save CSS
    with open(os.path.join(output_dir, "index-style.css"), "w", encoding="utf-8") as f:
        f.write(INDEX_CSS)
    with open(os.path.join(output_dir, "page-style.css"), "w", encoding="utf-8") as f:
        f.write(PAGE_CSS)
    with open(os.path.join(output_dir, "teachers-style.css"), "w", encoding="utf-8") as f:
        f.write(TEACHERS_CSS)
        
    # Save JS
    with open(os.path.join(output_dir, "back-to-top.js"), "w", encoding="utf-8") as f:
        f.write(BACK_TO_TOP_JS)

def get_relative_path(directory, filename):
    """Calculates the relative path to the root static files based on directory depth."""
    parts = os.path.normpath(directory).split(os.sep)
    depth = len(parts) - 1
    return ("../" * depth) + filename if depth > 0 else filename

def generate_index_html(directory, links, title, back_url="../index.html"):
    """Generates an index.html file with a list of links."""
    index_path = os.path.join(directory, "index.html")
    css_path = get_relative_path(directory, "index-style.css")

    back_html = f"<a href='{back_url}'>«</a> " if back_url else ""

    with open(index_path, "w", encoding="utf-8") as file:
        file.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="{css_path}">
</head>
<body>
    <h1>{back_html}{title}</h1>
    <ul>
""".format(back_html=back_html, title=title, css_path=css_path))

        for link_text, link_url in sorted(links):
            formatted_url = link_url
            if ".html" not in link_url and "#" not in link_url:
                formatted_url = link_url.rstrip("/") + "/index.html"

            file.write(f'        <li><a href="{formatted_url}">{link_text}</a></li>\n')

        file.write("""    </ul>
</body>
</html>""")


def fetch_and_save_page(languages, pages, ids, course_names, course_acronyms, output_dir="corsidilaurea"):
    base_url = "https://corsidilaurea.uniroma1.it"
    url_pattern = base_url + "/{}/course/{}/{}"
    os.makedirs(output_dir, exist_ok=True)

    root_links = [(name, str(cid)) for cid, name in course_names.items() if cid in ids]
    # No back button for the root directory
    generate_index_html(output_dir, root_links, "Degree Courses", back_url=None)

    for course_id in ids:
        acronym = course_acronyms.get(course_id, str(course_id))
        course_prefix = f"[{acronym}] "

        course_dir = os.path.join(output_dir, str(course_id))
        os.makedirs(course_dir, exist_ok=True)

        language_links = []
        
        # Calculate how many languages are actually generated for this course
        valid_langs = [l for l in languages if not (l == "en" and course_id in EXCLUDED_EN_IDS)]
        is_single_lang = len(valid_langs) == 1

        for language_key in languages:
            # Skip English scraping for specific course IDs
            if language_key == "en" and course_id in EXCLUDED_EN_IDS:
                continue

            language_dir = os.path.join(course_dir, language_key)
            os.makedirs(language_dir, exist_ok=True)

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

                    for a_tag in soup.find_all("a", href=True):
                        if a_tag["href"].startswith("/"):
                            a_tag["href"] = urljoin(base_url, a_tag["href"])

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
                        
                        # PRE-PASS: Count wrap candidates to avoid wrapping single-chapter pages
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

                        for i, block in enumerate(content_blocks):
                            field_item_div = block.find("div", class_="field-item")
                            process_block = field_item_div if field_item_div else block

                            manifesto_div = process_block.find("div", class_="manifesto")
                            if manifesto_div:
                                manifesto_div.decompose()

                            for script in process_block.find_all("script"):
                                script.decompose()
                            optional_group_popup = process_block.find("div", id="optional-group-popup-div")
                            if optional_group_popup:
                                optional_group_popup.decompose()

                            # FEATURE 1: Add IDs to headers and collect them for TOC
                            for h_tag in process_block.find_all(['h2', 'h3', 'h4', 'h5', 'h6']):
                                raw_text = h_tag.get_text(strip=True)
                                if not raw_text:
                                    continue
                                    
                                if not h_tag.has_attr('id'):
                                    h_id = re.sub(r'[^a-z0-9]+', '-', raw_text.lower()).strip('-')
                                    h_tag['id'] = h_id
                                else:
                                    h_id = h_tag['id']
                                
                                header_level = int(h_tag.name[1]) 
                                toc_items.append((header_level, raw_text, h_id))

                            # FEATURE 2: Wrap large sections in <details> tags (ONLY IF MULTIPLE SECTIONS)
                            if should_wrap:
                                # 1. Handle explicit accordions securely
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
                                                    
                                                summary_tag.string = title_div.get_text(separator=" ", strip=True)
                                                title_div.decompose()
                                            else:
                                                summary_tag.string = "Dettagli" if language_key == "it" else "Details"
                                                
                                            summary_tag['class'] = level_class
                                            details_tag.append(summary_tag)
                                            
                                            # Wrap content in a body div for safe CSS styling
                                            body_div = soup.new_tag("div")
                                            body_div['class'] = "details-body"
                                            for child in list(content_div.children):
                                                body_div.append(child)
                                                
                                            details_tag.append(body_div)
                                            acc_item.insert_after(details_tag)
                                            acc_item.decompose()

                                # 2. Handle large plain divs (not accordions)
                                for child_elem in list(process_block.children):
                                    if child_elem.name == "div" and "cdl-accordion" not in child_elem.get("class", []) and "accordion-item" not in child_elem.get("class", []):
                                        if child_elem.get("id") in ["cdl-course-home-text", "cdl-course-attendance-text"]:
                                            continue
                                            
                                        char_len = len(child_elem.get_text(strip=True))
                                        vertical_items = len(child_elem.find_all(['tr', 'li', 'br']))
                                        
                                        if char_len > 1200 or vertical_items > 10:
                                            details_tag = soup.new_tag("details")
                                            summary_tag = soup.new_tag("summary")
                                            level_class = "level-default"
                                            
                                            first_tag = child_elem.find(['h2', 'h3', 'h4', 'h5', 'strong'])
                                            if first_tag and len(first_tag.get_text(strip=True)) < 100:
                                                if first_tag.name in ['h2', 'h3', 'h4', 'h5', 'h6']:
                                                    level_class = f"level-{first_tag.name}"
                                                elif first_tag.name == 'strong':
                                                    level_class = "level-h4"
                                                    
                                                summary_tag.string = first_tag.get_text(separator=" ", strip=True)
                                                first_tag.decompose()
                                            else:
                                                th_tag = child_elem.select_one("thead tr th")
                                                if th_tag and len(th_tag.get_text(strip=True)) < 150:
                                                    summary_tag.string = th_tag.get_text(separator=" ", strip=True)
                                                    level_class = "level-h4"
                                                    # Not using .decompose() to preserve table structure
                                                else:
                                                    summary_tag.string = "Approfondimento" if language_key == "it" else "More details"
                                                
                                            summary_tag['class'] = level_class
                                            details_tag.append(summary_tag)
                                            
                                            # Wrap content in a body div for safe CSS styling
                                            body_div = soup.new_tag("div")
                                            body_div['class'] = "details-body"
                                            
                                            child_elem.insert_after(details_tag)
                                            body_div.append(child_elem)
                                            details_tag.append(body_div)

                            # Extract the main heading only from the first block
                            if i == 0:
                                h3_tag = process_block.find("h3")
                                if h3_tag:
                                    h3_id = h3_tag.get('id')
                                    if h3_id:
                                        toc_items = [item for item in toc_items if item[2] != h3_id]
                                    
                                    page_heading = f"{course_prefix}{h3_tag.get_text(strip=True)}"
                                    h3_tag.decompose() 
                                else:
                                    page_title = " ".join(
                                        [word.capitalize() if word not in ["di", "del", "della", "delle"] else word for word in
                                         language_page.replace("-", " ").split()]).replace("Desame","d'Esame")
                                    page_heading = f"{course_prefix}{page_title}"

                            combined_content += '\n'.join([line for line in str(process_block).splitlines() if line.strip()]).replace(" ", " ") + "\n"

                        filename = f"{language_page}.html"
                        
                        # Generate language toggle only if English is allowed for this course
                        flag_html = ""
                        if course_id not in EXCLUDED_EN_IDS:
                            other_lang = "en" if language_key == "it" else "it"
                            flag = "🇮🇹" if language_key == "it" else "🇬🇧"
                            flag_html = f" [<a href='../{other_lang}/{filename}' title='Switch language' style='text-decoration: none;'>{flag}</a>]"

                        # BUILD TABLE OF CONTENTS HTML
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
                        
                        # Use dynamic relative path for page-style.css
                        # Calculate relative paths
                        css_path = get_relative_path(language_dir, "page-style.css")
                        js_path = get_relative_path(language_dir, "back-to-top.js")

                        # Update the content formatting
                        content = """<!DOCTYPE html>
                        <html lang="{lang}">
                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>{title}</title>
                            <link rel="stylesheet" href="{css_path}">
                        </head>
                        <body>
                        <h1><a href='index.html'>«</a> {heading} <a href='{url}' target='_blank' rel='noopener noreferrer'>(🌐)</a>{flag_html}</h1>
                        {toc}
                        {content}

                        <button id="back-to-top" title="{btn_text}" onclick="window.scrollTo({{top: 0, behavior: 'smooth'}})">▲ {btn_text}</button>
                        <script src="{js_path}"></script>
                        </body>
                        </html>""".format(
                            lang=language_key, 
                            title=page_heading, 
                            heading=page_heading,
                            flag_html=flag_html,
                            url=url,
                            toc=toc_html,
                            content=combined_content,
                            btn_text=back_to_top_text,
                            css_path=css_path,
                            js_path=js_path # <-- Add this parameter
                        )

                        output_path = os.path.join(language_dir, filename)
                        with open(output_path, "w", encoding="utf-8") as file:
                            file.write(content)

                        clean_link_title = page_heading.replace(course_prefix, "")
                        page_links.append((clean_link_title, filename))
                        print(f"Saved: {output_path}")
                    else:
                        print(f"No useful content found for {course_id}/{language_key}/{language_page}")

            page_links.append(("Teachers" if language_key == "en" else "Docenti", "teachers.html"))

            if page_links:
                # Set dynamic back_url based on whether it's a single language course or not
                lang_back_url = "../../index.html" if is_single_lang else "../index.html"
                generate_index_html(language_dir, page_links, course_names.get(course_id, course_prefix), back_url=lang_back_url)
                language_links.append((language_key.replace("en","English").replace("it","Italian"), f"{language_key}/index.html"))

        if language_links:
            if is_single_lang:
                course_index = os.path.join(course_dir, "index.html")
                lang_path = language_links[0][1]
                with open(course_index, "w", encoding="utf-8") as f:
                    f.write(f'<html><head><meta http-equiv="refresh" content="0;url={lang_path}"></head></html>')
            else:
                generate_index_html(course_dir, language_links, course_prefix+"Choose Language", back_url="../index.html")


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
                    
                    if h3_tag:
                        page_heading = f"{course_prefix}{h3_tag.get_text(strip=True)}"
                    else:
                        fallback_title = "Teachers" if language_key == "en" else "Docenti"
                        page_heading = f"{course_prefix}{fallback_title}"

                    flag_html = ""
                    if course_id not in EXCLUDED_EN_IDS:
                        other_lang = "en" if language_key == "it" else "it"
                        flag = "🇮🇹" if language_key == "it" else "🇬🇧"
                        flag_html = f" [<a href='../{other_lang}/teachers.html' title='Switch language' style='text-decoration: none;'>{flag}</a>]"
                    
                    back_to_top_text = "Torna su" if language_key == "it" else "Back to top"
                    
                    # Calculate relative paths
                    css_path = get_relative_path(language_dir, "teachers-style.css")
                    js_path = get_relative_path(language_dir, "back-to-top.js")

                    # Update the content formatting
                    content = """<!DOCTYPE html>
                    <html lang="{lang}">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>{title}</title>
                        <link rel="stylesheet" href="{css_path}">
                    </head>
                    <body>
                    <h1><a href='index.html'>«</a> {heading} <a href='{url}' target='_blank' rel='noopener noreferrer'>(🌐)</a>{flag_html}</h1>
                    {content}

                    <button id="back-to-top" title="{btn_text}" onclick="window.scrollTo({{top: 0, behavior: 'smooth'}})">▲ {btn_text}</button>
                    <script src="{js_path}"></script>
                    </body>
                    </html>""".format(
                        lang=language_key,
                        title=page_heading,
                        heading=page_heading,
                        url=url,
                        flag_html=flag_html,
                        content=teachers_container.prettify() if teachers_container else "",
                        btn_text=back_to_top_text,
                        css_path=css_path,
                        js_path=js_path
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
            
            for a_tag in soup.find_all("a", href=True):
                if a_tag["href"].startswith("/"):
                    a_tag["href"] = urljoin(base_url, a_tag["href"])

            for img_tag in soup.find_all("img", src=True):
                if img_tag["src"].startswith("/"):
                    img_tag["src"] = urljoin(base_url, img_tag["src"])

            content_blocks = []

            mt_divs = soup.find_all("div", class_=re.compile(r'^mt-\d+$'))
            for mt_div in mt_divs:
                col_div = mt_div.find("div", class_=re.compile(r'^col-md-\d+$'))
                if col_div:
                    content_blocks.append(col_div)

            # 2. Sidebar: 'corso-home-menu--generale'
            # We look for the sidebar to place it at the bottom
            sidebar = soup.find("div", class_="corso-home-menu--generale")
            if sidebar:
                content_blocks.append(sidebar)

            if content_blocks:
                combined_content = ""
                for block in content_blocks:
                    # Clean up unwanted elements like scripts
                    for script in block.find_all("script"):
                        script.decompose()
                    
                    combined_content += block.prettify()

                css_path = get_relative_path(lang_dir, "page-style.css")
                js_path = get_relative_path(lang_dir, "back-to-top.js")
                
                main_section = soup.find("section", id="block-system-main")
                h3_tag = main_section.find("h4") if main_section else None
                
                if h3_tag:
                    page_heading = f"{course_prefix}{h3_tag.get_text(strip=True)}"
                else:
                    fallback_title = "Come e quando iscriversi" if language_key == "en" else "How and When to Enroll"
                    page_heading = f"{course_prefix}{fallback_title}"

                flag_html = ""
                if course_id not in EXCLUDED_EN_IDS:
                    other_lang = "en" if language_key == "it" else "it"
                    flag = "🇮🇹" if language_key == "it" else "🇬🇧"
                    flag_html = f" [<a href='../{other_lang}/apply.html' title='Switch language' style='text-decoration: none;'>{flag}</a>]"

                back_to_top_text = "Torna su" if language_key == "it" else "Back to top"

                html_content = f"""<!DOCTYPE html>
<html lang="{language_key}">
<head>
    <meta charset="UTF-8">
    <title>{page_heading}</title>
    <link rel="stylesheet" href="{css_path}">
    <style>{APPLY_SIDEBAR_CSS}</style>
</head>
<body>
    <h1><a href='index.html'>«</a> {page_heading} <a href='{url}' target='_blank' rel='noopener noreferrer'>(🌐)</a>{flag_html}</h1>
    <div class="content-wrapper">
        {combined_content}
    </div>
    <button id="back-to-top" title="{back_to_top_text}">{back_to_top_text}</button>
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

    LANGUAGES = ["it", "en"]
    PAGES = [
        "presentation",
        "objectives",
        "professional-opportunities",
        "choice-orientation",
        "international-experiences",
        "organization",
        "quality"
    ]
    IDS = [33502, 33508, 33516, 33519, 33503, 33504]
    OUTPUT_DIRECTORY = "corsidilaurea"

    save_static_files(output_dir="corsidilaurea")

    # Run scraping
    fetch_and_save_apply(LANGUAGES, IDS, COURSE_NAMES, COURSE_ACRONYMS, OUTPUT_DIRECTORY)
    fetch_and_save_teachers(LANGUAGES, IDS, COURSE_ACRONYMS, OUTPUT_DIRECTORY)
    fetch_and_save_page(LANGUAGES, PAGES, IDS, COURSE_NAMES, COURSE_ACRONYMS, OUTPUT_DIRECTORY)