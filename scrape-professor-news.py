import os
import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# File paths
JSON_FILE = "professors.json"  # JSON file containing professor data
REPO_PATH = "./lecturers"      # Directory to store the news and index files

LANGUAGES = ["it", "en"]
DEFAULT_PIC = "https://corsidilaurea.uniroma1.it/sites/all/modules/custom/cdl_professors/images/user_picture.png"
NULL_UUID = "00000000-0000-0000-0000-000000000000"

def load_professors():
    """
    Load the list of professors from a JSON file.
    """
    if not os.path.exists(JSON_FILE):
        print(f"Error: {JSON_FILE} not found.")
        return {}
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def is_external_url(url):
    """
    Checks if a URL points to an external domain.
    """
    if not url: return False
    return url.startswith("http")

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

def make_urls_absolute(soup, base_url):
    """
    Converts relative URLs in href (for <a>) and src (for <img>) attributes to absolute URLs.
    Cleans existing Drupal external link indicators and appends a standardized external link icon.
    """
    for ext in soup.find_all("span", class_="ext"):
        ext.decompose()
    for invisible in soup.find_all("span", class_="element-invisible", string=re.compile(r"link is external", re.I)):
        invisible.decompose()
    for icon in soup.find_all(["i", "svg"], class_=re.compile(r"(fa-)?external-link")):
        icon.decompose()

    for tag in soup.find_all(["a", "img"]):
        attr = "href" if tag.name == "a" else "src"
        if tag.has_attr(attr):
            url = tag[attr]
            if url.startswith("/"):
                tag[attr] = urljoin(base_url, url)
            
            if tag.name == "a":
                href = tag.get("href", "")
                if is_external_url(href):
                    if not tag.find("img") and tag.get_text(strip=True):
                        if not tag.find("span", class_="external-icon"):
                            for t in tag.find_all(string=re.compile(r"↗")):
                                t.replace_with(t.replace("↗", "").strip())
                                
                            icon_span = soup.new_tag("span", attrs={"class": "external-icon"})
                            icon_span.string = "↗"

                            inner_h = tag.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                            if inner_h:
                                inner_h.append(soup.new_string(" "))
                                inner_h.append(icon_span)
                            else:
                                tag.append(soup.new_string(" "))
                                tag.append(icon_span)

def add_heading_anchors(soup, content_block):
    """
    Finds headings in a block, generates an ID (if missing), 
    and injects a clickable anchor (#).
    """
    for h_tag in content_block.find_all(['h2', 'h3', 'h4', 'h5', 'h6']):
        if h_tag.find_parent('summary') or h_tag.find_parent('details'):
            continue
        if h_tag.find_parent('a'):
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

def generate_top_bars_html(language_key, flag_html="", original_url=None, back_url=None, is_index_page=False):
    """
    Generates the standard HTML for the two top bars exactly like the course pages script.
    Bar 1: Controls (Language, Font, Theme).
    Bar 2: Navigation (Source, Back, Print).
    """
    # Bar 1: Controls (Font, Language, Theme)
    dsa_text = "OpenDyslexic"
    dsa_toggle_html = f'<label class="font-toggle-label"><input type="checkbox" id="font-dsa-toggle"> {dsa_text}</label>'
    
    theme_btn_text = "🌓 Tema" if language_key == "it" else "🌓 Theme"
    theme_btn_html = f'<button class="theme-toggle" onclick="toggleTheme()">{theme_btn_text}</button>'
    
    controls_bar_html = f'<div class="controls-bar">{dsa_toggle_html}{flag_html}{theme_btn_html}</div>'

    # Bar 2: Navigation (Back, Print, Source)
    back_btn_html = ""
    if back_url:
        if is_index_page:
            back_text = "🏠 sapienzafeed"
        else:
            back_text = "◀️ Docenti" if language_key == "it" else "◀️ Lecturers"
            
        back_btn_html = f'<a href="{back_url}" class="back-link-btn">{back_text}</a>'

    print_btn_html = ""
    if not is_index_page:
        print_btn_text = "🖨️ Salva come PDF" if language_key == "it" else "🖨️ Save as PDF"
        print_btn_html = f'<button class="print-btn" onclick="window.print()">{print_btn_text}</button>'

    original_btn_html = ""
    if original_url:
        original_btn_text = "🌐 Fonte" if language_key == "it" else "🌐 Source"
        original_btn_html = f'<a href="{original_url}" class="original-link-btn" target="_blank" rel="noopener noreferrer">{original_btn_text}</a>'

    nav_bar_html = ""
    if back_btn_html or print_btn_html or original_btn_html:
        nav_bar_html = f'<div class="navigation-bar">{back_btn_html}{print_btn_html}{original_btn_html}</div>'

    return f'{controls_bar_html}\n{nav_bar_html}'

def scrape_professor_data(uuid):
    """
    Scrape IT and EN pages for a professor.
    Extracts profile info, localized activities, and prepares common sections for single-file deduplication.
    """
    base_domain = "https://corsidilaurea.uniroma1.it/"
    it_url = f"{base_domain}it/lecturer/{uuid}"
    en_url = f"{base_domain}en/lecturer/{uuid}"
    
    it_resp = fetch_html(it_url)
    en_resp = fetch_html(en_url)
    
    if not it_resp:
        return None
        
    it_soup = BeautifulSoup(it_resp.text, 'html.parser')
    en_soup = BeautifulSoup(en_resp.text, 'html.parser') if en_resp else None
    
    make_urls_absolute(it_soup, base_domain)
    if en_soup:
        make_urls_absolute(en_soup, base_domain)
    
    data = {
        "picture": DEFAULT_PIC,
        "email": "",
        "it_structure": "",
        "en_structure": "",
        "ssd": "",
        "common_sections": {}, # sec_id -> content_html
        "it_titles": {}, # sec_id -> IT title
        "en_titles": {}, # sec_id -> EN title
        "it_activities": "",
        "en_activities": ""
    }
    
    # Extract Base Metadata from IT
    pic_div = it_soup.find('div', class_='docente-picture')
    if pic_div and pic_div.find('img'):
        src = pic_div.find('img').get('src', '')
        if src: data["picture"] = src

    email_div = it_soup.find('div', class_='field email')
    if email_div and email_div.find('a'):
        data["email"] = email_div.find('a').get_text(strip=True)

    ssd_div = it_soup.find('div', class_='field ssd')
    if ssd_div:
        divs = ssd_div.find_all('div')
        if len(divs) > 1: data["ssd"] = divs[-1].get_text(strip=True)

    # Extract IT Structure
    structure_div = it_soup.find('div', class_='field structure')
    if structure_div:
        divs = structure_div.find_all('div')
        if len(divs) > 1: data["it_structure"] = divs[-1].get_text(strip=True)
            
    # Extract EN Structure (fallback to IT if EN missing)
    if en_soup:
        en_structure_div = en_soup.find('div', class_='field structure')
        if en_structure_div:
            divs = en_structure_div.find_all('div')
            if len(divs) > 1: data["en_structure"] = divs[-1].get_text(strip=True)
        else: data["en_structure"] = data["it_structure"]
    else: data["en_structure"] = data["it_structure"]

    # Helper function to extract clean title text without the '#' anchor
    def get_clean_title(tag_or_div):
        if not tag_or_div: return ""
        # Clone to avoid modifying the main soup object
        temp_soup = BeautifulSoup(str(tag_or_div), 'html.parser')
        # Remove any anchor injected by add_heading_anchors
        for a in temp_soup.find_all("a", class_="heading-anchor"):
            a.decompose()
        return temp_soup.get_text(strip=True)

    # Process IT sections
    it_info = it_soup.find('div', class_='docente-info')
    if it_info:
        add_heading_anchors(it_soup, it_info)
        for item in it_info.find_all('div', class_='accordion-item'):
            title_div = item.find('div', class_='accordion-title')
            content_div = item.find('div', class_='accordion-content')
            if not title_div or not content_div: continue
            
            sec_id = title_div.get('id', '')
            if not sec_id:
                h_tag = title_div.find(['h2', 'h3', 'h4', 'h5', 'h6'])
                text = get_clean_title(h_tag) if h_tag else get_clean_title(title_div)
                sec_id = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
                
            h_tag = title_div.find(['h2', 'h3', 'h4', 'h5', 'h6'])
            # Extract clean title to ensure no '#' appears in collapsable summary labels
            title = get_clean_title(h_tag) if h_tag else get_clean_title(title_div)
            
            # Recursively remove trailing empty tags or whitespace-only strings
            def clean_trailing_empty(container):
                while container.contents:
                    last = container.contents[-1]
                    if isinstance(last, str):
                        if not last.strip().replace('\xa0', ''):
                            last.extract()
                            continue
                    elif last.name in ['p', 'div', 'br', 'span']:
                        # If the tag has children, try to clean them first
                        if hasattr(last, 'contents') and last.contents:
                            clean_trailing_empty(last)
                        
                        # After potential internal cleaning, check if tag is now empty
                        if not last.get_text(strip=True).replace('\xa0', ''):
                            last.decompose()
                            continue
                    break

            clean_trailing_empty(content_div)

            content_html = "".join(str(child) for child in content_div.children)
                
            if sec_id == 'lecturer-activities':
                data['it_activities'] = content_html
            else:
                data['common_sections'][sec_id] = content_html
                
            data['it_titles'][sec_id] = title
                
    # Process EN sections
    if en_soup:
        en_info = en_soup.find('div', class_='docente-info')
        if en_info:
            add_heading_anchors(en_soup, en_info)
            for item in en_info.find_all('div', class_='accordion-item'):
                title_div = item.find('div', class_='accordion-title')
                content_div = item.find('div', class_='accordion-content')
                if not title_div or not content_div: continue
                
                sec_id = title_div.get('id', '')
                if not sec_id:
                    h_tag = title_div.find(['h2', 'h3', 'h4', 'h5', 'h6'])
                    text = get_clean_title(h_tag) if h_tag else get_clean_title(title_div)
                    sec_id = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
                    
                h_tag = title_div.find(['h2', 'h3', 'h4', 'h5', 'h6'])
                # Extract clean title to ensure no '#' appears in collapsable summary labels
                title = get_clean_title(h_tag) if h_tag else get_clean_title(title_div)
                
                if sec_id == 'lecturer-activities':
                    clean_trailing_empty(content_div)
                    content_html = "".join(str(child) for child in content_div.children)
                    data['en_activities'] = content_html
                    
                data['en_titles'][sec_id] = title

    return data

def generate_common_html(uuid, data):
    """
    Generates a single common.html containing blocks that will be shared among languages.
    This allows manual edits in one place.
    """
    prof_dir = os.path.join(REPO_PATH, uuid)
    os.makedirs(prof_dir, exist_ok=True)
    file_path = os.path.join(prof_dir, "common.html")
    
    html = '<div class="common-sections-container">\n'
    for sec_id, content in data['common_sections'].items():
        html += f'  <div id="common-{sec_id}">\n{content}\n  </div>\n'
    html += '</div>\n'
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)

def generate_individual_page(uuid, lang, prof_name, data):
    """
    Generate the individual localized index.html page for a specific professor.
    Injects common.html content into localized details structures via Javascript.
    """
    prof_dir = os.path.join(REPO_PATH, uuid, lang)
    os.makedirs(prof_dir, exist_ok=True)
    file_path = os.path.join(prof_dir, "index.html")
    
    is_it = lang == "it"
    structure_label = "Struttura" if is_it else "Structure"
    structure_val = data['it_structure'] if is_it else data['en_structure']
    activities_val = data['it_activities'] if is_it else data['en_activities']
    titles = data['it_titles'] if is_it else data['en_titles']
    original_url = f"https://corsidilaurea.uniroma1.it/{lang}/lecturer/{uuid}"
    back_url = f"../../{lang}/index.html"
    
    other_lang = "en" if is_it else "it"
    flag = "🇮🇹 Lingua" if is_it else "🇬🇧 Language"
    flag_html = f'<a href="../{other_lang}/index.html" class="lang-btn" title="Switch language">{flag}</a>'
    
    top_bars_html = generate_top_bars_html(lang, flag_html=flag_html, original_url=original_url, back_url=back_url, is_index_page=False)
    
    # Generate mailto link for email
    email_html = f'<a href="mailto:{data["email"]}">{data["email"]}</a>' if data["email"] else "N/A"

    # Localization for Back to Top
    btt_text = "Torna sù" if is_it else "Back to top"

    html_content = f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{prof_name}</title>
    <link rel="stylesheet" href="../../../assets/theme-style.css">
    <link rel="stylesheet" href="../../../assets/page-style.css">
    <script src="../../../assets/theme-switch.js"></script>
    <script src="../../../assets/page-logic.js" defer></script>
</head>
<body>
    <div class="header-dashboard">
        <h1 id="page-title">{prof_name}</h1>
        <div class="header-actions">
            {top_bars_html}
        </div>
    </div>
    
    <div class="docente-profile" style="display: flex; gap: 20px; align-items: center; margin-bottom: 30px;">
        <div class="docente-picture">
            <img src="{data['picture']}" alt="" style="width: 120px; height: 120px; object-fit: cover; border-radius: 50%;">
        </div>
        <div class="docente-info">
            <p style="margin: 5px 0;"><strong>Email:</strong> {email_html}</p>
            <p style="margin: 5px 0;"><strong>{structure_label}:</strong> {structure_val}</p>
            <p style="margin: 5px 0;"><strong>SSD:</strong> {data['ssd']}</p>
        </div>
    </div>
    
    <div class="sections-content">
'''

    # Build shared/common sections hooks
    for sec_id in data['common_sections'].keys():
        title = titles.get(sec_id) or data['it_titles'].get(sec_id, sec_id)
        
        html_content += f'''        <details id="details-{sec_id}" data-common-id="common-{sec_id}" style="display:none;">
            <summary class="level-h4" id="{sec_id}">{title}</summary>
            <div class="details-body" id="body-{sec_id}"></div>
        </details>\n'''
        
    # Build localized section (Insegnamenti / Course catalogue)
    act_id = "lecturer-activities"
    if activities_val:
        act_title = titles.get(act_id) or data['it_titles'].get(act_id, "Insegnamenti" if is_it else "Course catalogue")
        html_content += f'''        <details id="details-{act_id}">
            <summary class="level-h4" id="{act_id}">{act_title}</summary>
            <div class="details-body" id="body-{act_id}">
{activities_val}
            </div>
        </details>\n'''

    html_content += f'''    </div>

    <button id="back-to-top" title="{btt_text}">▲ {btt_text}</button>

    <script>
    fetch('../common.html')
        .then(response => response.text())
        .then(html => {{
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            document.querySelectorAll('details[data-common-id]').forEach(details => {{
                const commonId = details.getAttribute('data-common-id');
                const source = doc.getElementById(commonId);
                if (source && source.innerHTML.trim()) {{
                    details.querySelector('.details-body').innerHTML = source.innerHTML;
                    details.style.display = 'block'; // Make visible if content exists
                }}
            }});
        }})
        .catch(err => console.error('Error loading common content:', err));
    </script>
</body>
</html>'''

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

def generate_main_indexes(professors_data):
    """
    Generate the multilingual index.html containing the rich list of all lecturers.
    """
    for lang in LANGUAGES:
        lang_dir = os.path.join(REPO_PATH, lang)
        os.makedirs(lang_dir, exist_ok=True)
        index_path = os.path.join(lang_dir, "index.html")
        
        title = "Lecturers" if lang == "en" else "Docenti"
        back_url = "../../index.html"
        
        other_lang = "en" if lang == "it" else "it"
        flag = "🇮🇹 Lingua" if lang == "it" else "🇬🇧 Language"
        flag_html = f'<a href="../{other_lang}/index.html" class="lang-btn" title="Switch language">{flag}</a>'

        top_bars_html = generate_top_bars_html(lang, flag_html=flag_html, original_url=None, back_url=back_url, is_index_page=True)
        
        html = f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="../../assets/theme-style.css">
    <link rel="stylesheet" href="../../assets/teachers-style.css">
    <script src="../../assets/theme-switch.js"></script>
</head>
<body>
    <div class="header-dashboard">
        <h1 id="page-title">{title}</h1>
        <div class="header-actions">
            {top_bars_html}
        </div>
    </div>
    
    <div class="teachers-container">
'''
        
        sorted_professors = sorted(professors_data.items(), key=lambda item: item[1]['name'])
        structure_label = "Struttura" if lang == "it" else "Structure"
        
        for uuid, info in sorted_professors:
            if uuid == NULL_UUID:
                continue
                
            prof_name = info['name']
            prof_meta = info.get('metadata', {})
            
            picture = prof_meta.get('picture', DEFAULT_PIC)
            email = prof_meta.get('email', 'N/A')
            structure = prof_meta.get(f'{lang}_structure', 'N/A')
            
            # Generate mailto link for email in list view
            email_link_html = f'<a href="mailto:{email}">{email}</a>' if email != 'N/A' else 'N/A'
            
            html += f'''        <div class="docente-card">
            <div class="content">
                <div class="docente-picture">
                    <img src="{picture}" alt="">
                </div>
                <div class="docente-info">
                    <div class="full-name"><a href="../{uuid}/{lang}/index.html">{prof_name}</a></div>
                    <div class="email"><strong>Email:</strong> {email_link_html}</div>
                    <div class="structure"><strong>{structure_label}:</strong> {structure}</div>
                </div>
            </div>
        </div>\n'''

        html += '''    </div>
</body>
</html>'''

        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html)
    print("Unified multilingual lecturers indexes generated.")

def main():
    professors = load_professors()
    if not professors:
        return

    print(f"Loaded {len(professors)} professors. Starting scraping...")

    for uuid, info in professors.items():
        if uuid == NULL_UUID:
            continue
            
        url = info.get("url")
        if not url:
            continue
            
        print(f"Scraping: {info['name']} ({url})...")
        scraped_data = scrape_professor_data(uuid)
        
        if scraped_data:
            info['metadata'] = scraped_data
            
            # Step 1: Generate common deduplicated HTML core components
            generate_common_html(uuid, scraped_data)
            
            # Step 2: Generate specific language wrappers
            for lang in LANGUAGES:
                generate_individual_page(uuid, lang, info['name'], scraped_data)

    generate_main_indexes(professors)
    print("Scraping completed!")

if __name__ == "__main__":
    main()