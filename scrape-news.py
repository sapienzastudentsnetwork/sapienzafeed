import requests
from bs4 import BeautifulSoup
import os
import hashlib
import re
import json

# File paths
JSON_FILE = "professors.json"         # JSON file containing professor data
REPO_PATH = "./professors"            # Directory to store the news files

def load_professors():
    """
    Load the list of professors from a JSON file.
    
    Returns:
        dict: A dictionary mapping professor names to their corresponding URLs.
    """
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def clean_html(html):
    """
    Clean the provided HTML by removing class attributes.
    
    Args:
        html (str): The HTML content to clean.
        
    Returns:
        str: The cleaned HTML with all class attributes removed.
    """
    return re.sub(r' class="[^"]*"', '', html)

def get_news(url):
    """
    Fetch and extract the news section from the provided URL.
    
    Args:
        url (str): The URL from which to fetch the news.
        
    Returns:
        str or None: The cleaned HTML of the news section if found, otherwise None.
    """
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error loading page {url}")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    # Find the div that contains news using its specific class name
    news_div = soup.find('div', class_='field-name-field-notizie')
    if not news_div:
        return None
    
    return clean_html(str(news_div))

def save_news(professor, news_html):
    """
    Save the news HTML for a given professor in a dedicated directory.
    This function creates the professor's directory (if it doesn't exist)
    and saves the news content to a file, only if the content has changed.
    
    Args:
        professor (str): The professor's name.
        news_html (str): The HTML content of the news.
    """
    # Create a directory for the professor, replacing spaces with underscores
    professor_dir = os.path.join(REPO_PATH, professor.replace(' ', '_'))
    os.makedirs(professor_dir, exist_ok=True)
    file_path = os.path.join(professor_dir, "news.html")
    
    # If the news file already exists, check whether the content has changed
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            old_content = f.read()
        # Compare MD5 hashes of the cleaned old and new content
        if hashlib.md5(clean_html(old_content).encode()).hexdigest() == hashlib.md5(news_html.encode()).hexdigest():
            print(f"No changes for {professor}, skipping save.")
            return
    
    # Write the new news content to the file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(news_html)
    print(f"News updated for {professor}.")

# Load the list of professors from the JSON file
professors = load_professors()

# Iterate over each professor and their associated URL to fetch and save news
for professor, url in professors.items():
    print(f"Fetching news for {professor}...")
    news = get_news(url)
    if news:
        save_news(professor, news)
    else:
        print(f"No news found for {professor}.")
