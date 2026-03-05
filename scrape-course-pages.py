import os
import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def fetch_html(url, timeout=15):
    """
    Executes a safe HTTP GET request. 
    Returns the response object if successful, otherwise None.
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"Skipping {url} due to request error: {e}")
        return None

def add_heading_anchors(soup, content_block):
    """
    Finds headings in a block, generates an ID (if missing), 
    and injects a clickable anchor (#).
    """
    for h_tag in content_block.find_all(['h2', 'h3', 'h4', 'h5', 'h6']):
        # Skip headings inside collapsibles to avoid interfering with click events
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

def generate_theme_bar_html(language_key, flag_html="", original_url=None):
    """
    Generates the standard HTML for the top theme bar.
    """
    dsa_text = "OpenDyslexic"
    dsa_toggle_html = f'<label class="font-toggle-label"><input type="checkbox" id="font-dsa-toggle"> {dsa_text}</label>'
    
    original_btn_html = ""
    if original_url:
        original_btn_text = "🌐 Fonte" if language_key == "it" else "🌐 Source"
        original_btn_html = f'<a href="{original_url}" class="original-link-btn" target="_blank" rel="noopener noreferrer">{original_btn_text}</a>'

    theme_btn_text = "🌓 Tema" if language_key == "it" else "🌓 Theme"
    return f'<div class="theme-bar">{dsa_toggle_html}{flag_html}{original_btn_html}<button class="theme-toggle" onclick="toggleTheme()">{theme_btn_text}</button></div>'

def make_urls_absolute(soup, base_url):
    """
    Converts relative URLs in href (for <a>) and src (for <img>) attributes to absolute URLs.
    """
    for tag in soup.find_all(["a", "img"]):
        attr = "href" if tag.name == "a" else "src"
        if tag.has_attr(attr) and tag[attr].startswith("/"):
            tag[attr] = urljoin(base_url, tag[attr])

def extract_course_metadata(soup, language_key):
    """
    Extracts course metadata (e.g., degree class, faculty, language) from the homepage's 'corso-info' list
    and extracts the YouTube presentation video link.
    Returns a tuple containing the collapsible <details> HTML string and the YouTube URL.
    """
    metadata_html = ""
    youtube_url = None
    
    # 1. Extract the course information list
    target_ul = soup.find('ul', class_='corso-info')
            
    if target_ul:
        metadata_html += "<ul class='course-metadata-list'>\n"
        for li in target_ul.find_all('li', recursive=False):
            metadata_html += f"  <li>{li.decode_contents()}</li>\n"
        metadata_html += "</ul>\n"
        
    # 2. Extract YouTube presentation video link instead of iframe
    video_div = soup.find('div', class_='cdl-video-video')
    if video_div:
        iframe = video_div.find('iframe')
        if iframe and iframe.has_attr('src'):
            youtube_url = iframe['src']
    else:
        # Fallback
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src', '')
            if 'youtube.com' in src or 'youtu.be' in src:
                youtube_url = src
                break # Only take the first presentation video
            
    # 3. Wrap in a collapsible <details> tag if any data was found
    if metadata_html:
        summary_text = "Dettagli" if language_key == "it" else "Details"
        collapsible_block = (
            "<details class='course-metadata-details'>\n"
            f"  <summary>ℹ️ {summary_text}</summary>\n"
            f"  <div class='details-body'>\n{metadata_html}  </div>\n"
            "</details>\n"
        )
        return collapsible_block, youtube_url.replace("embed/", "watch?v=")
        
    return "", None

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

def get_assets_relative_path(directory, filename):
    """Calculates the relative path to the root static files based on directory depth."""
    parts = os.path.normpath(directory).split(os.sep)
    depth = len(parts)
    return ("../" * depth) + "assets/" + filename if depth > 0 else filename

def generate_index_html(directory, links=None, title="", back_url="../index.html", metadata_html="", original_url=None, language_key="en", categorized_links=None, flag_html="", info_category_name=None):
    """Generates an index.html file with a list of links (optionally grouped by category) and metadata."""
    index_path = os.path.join(directory, "index.html")
    theme_css_path = get_assets_relative_path(directory, "theme-style.css")
    css_path = get_assets_relative_path(directory, "index-style.css")
    js_theme_path = get_assets_relative_path(directory, "theme-switch.js")

    back_html = f"<a href='{back_url}'>«</a> " if back_url else ""

    # Generate theme bar using utility function
    theme_bar_html = generate_theme_bar_html(language_key, flag_html, original_url)

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
                # Skip empty categories unless it is the info category and we have metadata to show
                if not cat_links and not (category == info_category_name and metadata_html):
                    continue 
                    
                file.write(f'    <h2 class="category-title">{category}</h2>\n')
                
                # Render metadata at the top of the info category
                if category == info_category_name and metadata_html:
                    file.write(f'{metadata_html}\n')

                if cat_links:
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

        # Appending metadata_html at the bottom ONLY if it wasn't injected into categorized_links
        if not categorized_links and metadata_html:
            file.write(f"\n{metadata_html}\n")
            
        file.write("""</body>
</html>""")

def fix_contacts_collapsibles(soup):
    """
    Finds the specific structure of the 'contacts' page where an <a> tag 
    acting as a toggle is followed by a div containing the emails. 
    Converts them into functional HTML5 <details> elements.
    """
    toggles = soup.find_all('a', class_='accordion-card--contacts-toggle')
    
    for toggle in toggles:
        contacts_div = toggle.find_next_sibling('div', class_='accordion-card--contacts')
        
        if contacts_div:
            details = soup.new_tag('details')
            details['class'] = 'accordion-card--contacts-fixed'
            details['style'] = 'margin-top: 10px; cursor: pointer;'
            
            summary = soup.new_tag('summary')
            summary.string = toggle.get_text(strip=True)
            summary['style'] = 'font-weight: bold; color: var(--link-color);'
            details.append(summary)
            
            content_wrapper = soup.new_tag('div')
            content_wrapper['style'] = 'margin-top: 10px; padding-left: 15px;'
            for child in list(contacts_div.children):
                content_wrapper.append(child)
            
            details.append(content_wrapper)
            
            toggle.replace_with(details)
            contacts_div.decompose()

def clean_excessive_newlines(soup):
    """
    Removes excessive newlines and spaces from text nodes inside the HTML.
    Specifically targets issues in 'sapienza-for-you' pages.
    """
    for text_node in soup.find_all(string=True):
        if text_node.parent.name not in ['script', 'style', 'pre', 'code']:
            cleaned_text = re.sub(r'\s+', ' ', text_node)
            if cleaned_text != text_node:
                text_node.replace_with(cleaned_text)

def fetch_and_save_page(languages, pages, ids, excluded_en_ids, course_names, course_acronyms, output_dir="corsidilaurea", custom_links={}, file_to_cat={}, categories_dict={}):
    base_url = "https://corsidilaurea.uniroma1.it"
    url_pattern = base_url + "/{}/course/{}/{}"
    os.makedirs(output_dir, exist_ok=True)

    # Root index
    root_links = [(name, cid) for cid, name in course_names.items() if cid in ids]
    # No back button for the root directory
    generate_index_html(output_dir, links=root_links, title="Degree Courses", back_url=None)

    for course_id in ids:
        acronym = course_acronyms.get(course_id, course_id)
        course_prefix = f"[{acronym}] "

        course_dir = os.path.join(output_dir, course_id)
        os.makedirs(course_dir, exist_ok=True)

        # Calculate how many languages are actually generated for this course
        valid_langs = [l for l in languages if not (l == "en" and course_id in excluded_en_ids)]
        is_single_lang = len(valid_langs) == 1

        language_links = []
        for language_key in languages:
            # Skip English if course is in exclusion list
            if language_key == "en" and course_id in excluded_en_ids:
                continue

            language_dir = os.path.join(course_dir, language_key)
            os.makedirs(language_dir, exist_ok=True)

            homepage_url = f"{base_url}/{language_key}/course/{course_id}"
            extracted_metadata = ""
            youtube_video_url = None
            
            hp_resp = fetch_html(homepage_url)
            if hp_resp:
                hp_soup = BeautifulSoup(hp_resp.text, 'html.parser')
                extracted_metadata, youtube_video_url = extract_course_metadata(hp_soup, language_key)

            page_links = []

            for language_page in pages:
                url = url_pattern.format(language_key, course_id, language_page)

                response = fetch_html(url)
                if not response:
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Fix contacts collapsibles before links are modified
                fix_contacts_collapsibles(soup)
                
                # Clean up excessive newlines
                clean_excessive_newlines(soup)
                
                # Fix links to be absolute using utility function
                make_urls_absolute(soup, base_url)

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
                            
                            # FIX: Unwrap any <p> or <div> tags inside headings that would break inline anchors
                            for block_tag in h_tag.find_all(['p', 'div']):
                                block_tag.unwrap()
                                
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

                        # Phase 2.2: Add physical anchors using utility function
                        add_heading_anchors(soup, process_block)

                        combined_content += '\n'.join([line for line in str(process_block).splitlines() if line.strip()]).replace(" ", " ") + "\n"

                    # Calculate relative path depth
                    page_depth = language_page.count('/')
                    
                    # Path to go up from page to language folder (e.g. it/ or en/)
                    up_to_lang = "../" * (page_depth + 1)
                    
                    # Path to go up to the root 'corsidilaurea' where static assets live
                    # Since pages are in course_id/lang_key/page.html, we need (page_depth + 2)
                    rel_to_static_root = "../" * (page_depth + 3) + "assets/"
                    
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
                    if course_id not in excluded_en_ids:
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
                    
                    # Generate theme bar using utility function
                    theme_bar_html = generate_theme_bar_html(language_key, flag_html, url)

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
                cats = categories_dict.get(language_key, categories_dict["en"])

                # Pre-initialize categorized map to maintain section order
                categorized_links = {
                    cats["info"]: [],
                    cats["opp"]: [],
                    cats["freq"]: [],
                    cats["ext"]: []
                }
                
                # Append YouTube link if extracted
                if youtube_video_url:
                    yt_text = "Video presentazione (#IoScelgoSapienza)" if language_key == "it" else "Video presentation (#IoScelgoSapienza)"
                    categorized_links[cats["info"]].append((yt_text, youtube_video_url))

                for link_text, filename in page_links:
                    cat_key = file_to_cat.get(filename, "info") # Fallback to info
                    categorized_links[cats[cat_key]].append((link_text, filename))
                
                # Append shared custom links (key "all")
                if "all" in custom_links and language_key in custom_links["all"]:
                    for link_text, link_url in custom_links["all"][language_key]:
                        categorized_links[cats["ext"]].append((link_text, link_url))

                # Append course-specific custom links
                if course_id in custom_links and language_key in custom_links[course_id]:
                    for link_text, link_url in custom_links[course_id][language_key]:
                        categorized_links[cats["ext"]].append((link_text, link_url))

                # Filter out empty categories, but keep info category if it has metadata
                categorized_links = {k: v for k, v in categorized_links.items() if v or (k == cats["info"] and extracted_metadata)}

                # Build language toggle for the index page
                index_flag_html = ""
                if course_id not in excluded_en_ids:
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
                    flag_html=index_flag_html,
                    info_category_name=cats["info"]
                )
                language_links.append((language_key.replace("en","English").replace("it","Italian"), f"{language_key}/index.html"))

        if language_links:
            # Default to English if available, otherwise use the first available language
            default_lang_path = "en/index.html" if "en" in valid_langs else language_links[0][1]
            with open(os.path.join(course_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(f'<html><head><meta http-equiv="refresh" content="0;url={default_lang_path}"></head></html>')

def fetch_and_save_teachers(languages, ids, excluded_en_ids, course_acronyms, output_dir="corsidilaurea"):
    base_url = "https://corsidilaurea.uniroma1.it"
    os.makedirs(output_dir, exist_ok=True)

    for course_id in ids:
        acronym = course_acronyms.get(course_id, course_id)
        course_prefix = f"[{acronym}] "
        course_dir = os.path.join(output_dir, course_id)
        
        for language_key in languages:
            if language_key == "en" and course_id in excluded_en_ids:
                continue
                
            language_dir = os.path.join(course_dir, language_key)
            os.makedirs(language_dir, exist_ok=True)
            
            url = f"{base_url}/{language_key}/course/{course_id}/teachers"
            
            response = fetch_html(url)
            if not response:
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Fix absolute links using utility function
            make_urls_absolute(soup, base_url)
                    
            teachers_container = soup.find("div", class_="docente-cerca-results")
            
            if teachers_container:
                # Generate IDs and anchors using utility function
                add_heading_anchors(soup, teachers_container)

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
                if course_id not in excluded_en_ids:
                    other_lang = "en" if language_key == "it" else "it"
                    flag = "🇮🇹" if language_key == "it" else "🇬🇧"
                    flag_html = f'<a href="../{other_lang}/teachers.html" class="lang-btn" title="Switch language">{flag}</a>'
                
                back_to_top_text = "Torna sù" if language_key == "it" else "Back to top"
                
                # Generate theme bar using utility function
                theme_bar_html = generate_theme_bar_html(language_key, flag_html, url)

                # Calculate relative paths
                theme_css_path = get_assets_relative_path(language_dir, "theme-style.css")
                css_path = get_assets_relative_path(language_dir, "teachers-style.css")
                js_path = get_assets_relative_path(language_dir, "page-logic.js")
                js_theme_path = get_assets_relative_path(language_dir, "theme-switch.js")

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

def fetch_and_save_apply(languages, ids, excluded_en_ids, course_names, course_acronyms, output_dir="corsidilaurea"):
    """
    Scrapes the 'apply' (iscrizione) page for each course, including the general sidebar.
    """
    base_url = "https://corsidilaurea.uniroma1.it"
    url_pattern = base_url + "/{}/course/{}/apply"
    
    for course_id in ids:
        acronym = course_acronyms.get(course_id, course_id)
        course_prefix = f"[{acronym}] "
        course_dir = os.path.join(output_dir, course_id)

        for language_key in languages:
            # Skip English if course is in exclusion list
            if language_key == "en" and course_id in excluded_en_ids:
                continue
                
            url = url_pattern.format(language_key, course_id)
            lang_dir = os.path.join(course_dir, language_key)
            os.makedirs(lang_dir, exist_ok=True)
            
            response = fetch_html(url)
            if not response:
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Absolute URL conversion for links and images using utility function
            make_urls_absolute(soup, base_url)

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
                    
                    # Generate IDs and insert clickable anchors using utility function
                    add_heading_anchors(soup, block)

                    combined_content += block.prettify()

                # RELATIVE PATH CALCULATIONS
                # Since apply.html is at lang_dir level (e.g. it/apply.html), depth is 0
                page_depth = 0
                
                # Path to go up from page to language folder
                up_to_lang = "../" * (page_depth + 1)
                
                # Path to go up to the root 'corsidilaurea' where static assets live
                # From it/apply.html we need to go up 2 levels (lang_dir -> course_id -> root)
                rel_to_static_root = "../" * (page_depth + 3) + "assets/"
                
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
                if course_id not in excluded_en_ids:
                    other_lang = "en" if language_key == "it" else "it"
                    flag = "🇮🇹" if language_key == "it" else "🇬🇧"
                    # Path: Up to course root -> other lang folder -> same filename
                    lang_link = f"{up_to_lang}{other_lang}/apply.html"
                    flag_html = f'<a href="{lang_link}" class="lang-btn" title="Switch language">{flag}</a>'

                back_to_top_text = "Torna sù" if language_key == "it" else "Back to top"
                
                # Generate theme bar using utility function
                theme_bar_html = generate_theme_bar_html(language_key, flag_html, url)

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
    # Load configuration from JSON file
    json_path = "scrape-course-pages_config.json"
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            CONFIG = json.load(f)
    else:
        print(f"Warning: {json_path} not found. Proceeding with empty dicts.")
        CONFIG = {}
    
    COURSE_IDS = CONFIG.get("course_ids", {})
    EXCLUDED_EN_IDS = CONFIG.get("excluded_en_ids", {})
    COURSE_NAMES = CONFIG.get("course_names", {})
    COURSE_ACRONYMS = CONFIG.get("course_acronyms", {})
    CUSTOM_LINKS = CONFIG.get("custom_links", {})
    FILE_TO_CAT = CONFIG.get("file_to_cat", {})
    CATEGORIES_DICT = CONFIG.get("categories_dict", {})

    LANGUAGES = ["it", "en"]
    PAGES = CONFIG.get("pages", [])
    
    OUTPUT_DIRECTORY = "corsidilaurea"

    # Run scraping
    fetch_and_save_apply(LANGUAGES, COURSE_IDS, EXCLUDED_EN_IDS, COURSE_NAMES, COURSE_ACRONYMS, OUTPUT_DIRECTORY)
    fetch_and_save_teachers(LANGUAGES, COURSE_IDS, EXCLUDED_EN_IDS, COURSE_ACRONYMS, OUTPUT_DIRECTORY)
    fetch_and_save_page(LANGUAGES, PAGES, COURSE_IDS, EXCLUDED_EN_IDS, COURSE_NAMES, COURSE_ACRONYMS, OUTPUT_DIRECTORY, custom_links=CUSTOM_LINKS, file_to_cat=FILE_TO_CAT, categories_dict=CATEGORIES_DICT)