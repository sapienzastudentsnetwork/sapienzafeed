import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def generate_index_html(directory, links, title):
    """Generates an index.html file with a list of links."""
    index_path = os.path.join(directory, "index.html")
    with open(index_path, "w", encoding="utf-8") as file:
        file.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 20px auto; padding: 20px; }}
        h1 {{ color: #333; }}
        a {{ display: inline-block; margin-top: 20px; text-decoration: none; color: #007BFF; }}
    </style>
</head>
<body>
    <h1><a href='../'>«</a> {title}</h1>
    <ul>
""".format(title=title))

        for link_text, link_url in sorted(links):
            file.write(f'        <li><a href="{link_url}">{link_text}</a></li>\n')

        file.write("""    </ul>
</body>
</html>""")


def fetch_and_save_page(languages, year, ids):
    base_url = "https://corsidilaurea.uniroma1.it"
    url_pattern = base_url + "/{}/corso/{}/{}/programmazione#bootstrap-fieldgroup-nav-item-{}"
    output_dir = "frequentare"
    os.makedirs(output_dir, exist_ok=True)

    course_names = {
        "30786": "ACSAI (30786)",
        "29932": "Computer Science (29932)",
        "29389": "Cybersecurity (29389)",
        "29923": "Informatica (29923)",
        "29400": "Informatica - erogato a distanza (29400)"
    }

    generate_index_html(output_dir, list({v: k for k, v in course_names.items()}.items()), "Degree Courses")

    for course_id in ids:
        course_prefix = f"[{course_id}] "
        #course_prefix = "[" + course_names[str(course_id)]+"] "

        course_dir = os.path.join(output_dir, str(course_id))
        os.makedirs(course_dir, exist_ok=True)

        language_links = []

        for language_key, language_pages in languages.items():
            if language_key == "en" and course_id == 29923:
                continue

            language_dir = os.path.join(course_dir, language_key)
            os.makedirs(language_dir, exist_ok=True)

            page_links = []

            for language_page in language_pages:
                url = url_pattern.format(language_key, year, course_id, language_page)
                response = requests.get(url)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    for a_tag in soup.find_all("a", href=True):
                        if a_tag["href"].startswith("/"):
                            a_tag["href"] = urljoin(base_url, a_tag["href"])

                    field_item_div = soup.find("div", id=f"bootstrap-fieldgroup-nav-item-{language_page}")

                    if field_item_div:
                        field_item_div = field_item_div.find("div", class_="field-item")

                        manifesto_div = field_item_div.find("div", class_="manifesto")
                        if manifesto_div:
                            manifesto_div.decompose()

                        for script in field_item_div.find_all("script"):
                            script.decompose()
                        optional_group_popup = field_item_div.find("div", id="optional-group-popup-div")
                        if optional_group_popup:
                            optional_group_popup.decompose()

                        page_title = " ".join(
                            [word.capitalize() if word not in ["di", "del", "della", "delle"] else word for word in
                             language_page.replace("-", " ").split()]).replace("Desame","d'Esame")

                        content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 20px auto; padding: 20px; }}
        h1 {{ color: #333; }}
        a {{ display: inline-block; margin-top: 20px; text-decoration: none; color: #007BFF; }}
        ul {{ padding-left: 20px; }}
    </style>
</head>
<body>
<h1><a href='.'>«</a> {title} <a href='{url}' target='_blank' rel='noopener noreferrer'>(🌐)</a></h1>
{content}
</body>
</html>""".format(title=course_prefix+page_title, url=url, content='\n'.join([line for line in str(field_item_div).splitlines() if line.strip()]).replace(" ", " "))

                        output_path = os.path.join(language_dir, f"{language_page}.html")
                        with open(output_path, "w", encoding="utf-8") as file:
                            file.write(content)

                        page_links.append((page_title, f"{language_page}.html"))
                        print(f"Saved: {output_path}")
                    else:
                        print(f"No useful content found for {course_id}/{language_key}/{language_page}")
                else:
                    print(f"Error {response.status_code} loading page for ID {course_id}")

            if page_links:
                generate_index_html(language_dir, page_links, course_prefix+"Choose Section")
                language_links.append((language_key.replace("en","English").replace("it","Italian"), f"{language_key}/index.html"))

        if language_links:
            generate_index_html(course_dir, language_links, course_prefix+"Choose Language")


# Parameters
YEAR = 2024
LANGUAGES = {
    "it": [
        "frequentare",
        "orario-delle-lezioni",
        "calendario-delle-sessioni-desame",
        "compilazione-del-percorso-formativo",
        "percorsi-di-eccellenza",
        "prova-finale"
    ],
    "en": [
        "attendance",
        "lesson-times",
        "exam-session-calendar",
        "custom-tailoring-your-programme",
        "honours-programme",
        "final-test"
    ]
}
IDS = [29389, 29400, 29923, 29932, 30786]

# Run scraping
fetch_and_save_page(LANGUAGES, YEAR, IDS)
