import hashlib
import os
import re
import sys
import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load variables from .env file into os.environ
load_dotenv()

# ==========================================
# CONFIGURATION
# ==========================================
CONFLUENCE_DOMAIN = "cpibrock.atlassian.net"
SPACE_KEY = "COCWR"

CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")

URLS_FILE = "urls.txt"
CACHE_DIR = ".html_cache"  # Local folder to store content hashes

if not CONFLUENCE_EMAIL or not CONFLUENCE_API_TOKEN:
    print("\n[!] ERROR: Missing credentials in environment variables.")
    print("Please export CONFLUENCE_EMAIL and CONFLUENCE_API_TOKEN before running.\n")
    sys.exit(1)

# Confluence REST API Setup
AUTH = HTTPBasicAuth(CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN)
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}
BASE_API_URL = f"https://{CONFLUENCE_DOMAIN}/wiki/rest/api/content"

# Ensure local cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def get_url_cache_path(url):
    """Generates a unique cache file path based on SHA-256 of the URL."""
    url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, f"{url_hash}.hash")


def extract_clean_title(soup):
    """Extracts page title from <title> tag and strips site brand suffix."""
    title_tag = soup.find("title")
    if not title_tag:
        return "Untitled Page"

    raw_title = title_tag.get_text(strip=True)
    
    cleaned_title = re.sub(
        r'\s*(?:&#8211;|[–\-])\s*Centre for Pedagogical Innovation.*$',  # Might need to add more variations of the site suffix as we expand
        '', 
        raw_title, 
        flags=re.IGNORECASE
    ).strip()
    
    return cleaned_title or raw_title


def process_url(target_url):
    """Fetches WP page, parses HTML, checks local content hash, and syncs to Confluence."""
    print(f"\n--- Processing: {target_url} ---")
    
    # 1. Fetch HTML page
    res = requests.get(target_url)
    res.raise_for_status()

    # 2. Extract & clean main HTML content
    soup = BeautifulSoup(res.text, "html.parser")
    page_title = extract_clean_title(soup)
    print(f"Extracted Title: '{page_title}'")

    content_area = soup.find("article") or soup.find("main") or soup.find(class_="entry-content")
    if not content_area:
        content_area = soup.find("body")

    # Strip scripts, styles, navigation, and images/figures
    for element in content_area(["script", "style", "nav", "img", "figure", "picture"]):
        element.decompose()

    # 3. Build Final Storage HTML
    # Add a banner at the top linking to the original article as a confluence info panel
    banner_html = (
        f'<ac:structured-macro ac:name="info" ac:schema-version="1">'
        f'<ac:rich-text-body>'
        f'<p><em>The full version of this article is available on the CPI website: '
        f'<a href="{target_url}">{page_title}</a>.</em></p>'
        f'</ac:rich-text-body>'
        f'</ac:structured-macro><br/>'
    )
    final_storage_html = banner_html + str(content_area)

    # 4. Local Content Hash Comparison
    current_content_hash = hashlib.sha256(final_storage_html.encode("utf-8")).hexdigest()
    cache_path = get_url_cache_path(target_url)

    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            cached_hash = f.read().strip()
        
        if cached_hash == current_content_hash:
            print("[Skipping] Content has not changed since last import.")
            return

    # 5. Search for existing Confluence Page
    search_params = {
        "spaceKey": SPACE_KEY,
        "title": page_title,
        "expand": "version"
    }
    search_res = requests.get(BASE_API_URL, auth=AUTH, headers=HEADERS, params=search_params)
    search_res.raise_for_status()
    search_data = search_res.json()

    existing_pages = search_data.get("results", [])

    # 6. Create or Update Page in Confluence
    if existing_pages:
        page_id = existing_pages[0]["id"]
        current_version = existing_pages[0]["version"]["number"]
        print(f"Content changed. Updating Confluence Page ID: {page_id} (v{current_version} -> v{current_version + 1})...")

        update_payload = {
            "version": {"number": current_version + 1},
            "title": page_title,
            "type": "page",
            "body": {
                "storage": {
                    "value": final_storage_html,
                    "representation": "storage"
                }
            }
        }
        res = requests.put(f"{BASE_API_URL}/{page_id}", auth=AUTH, headers=HEADERS, json=update_payload)
        res.raise_for_status()
    else:
        print("Page does not exist in Confluence. Creating new page...")
        create_payload = {
            "type": "page",
            "title": page_title,
            "space": {"key": SPACE_KEY},
            "body": {
                "storage": {
                    "value": final_storage_html,
                    "representation": "storage"
                }
            }
        }
        res = requests.post(BASE_API_URL, auth=AUTH, headers=HEADERS, json=create_payload)
        res.raise_for_status()

    # 7. Update Local Cache Hash after successful push
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(current_content_hash)

    result_data = res.json()
    webui_path = result_data["_links"]["webui"]
    print(f"Success! Link: https://{CONFLUENCE_DOMAIN}/wiki{webui_path}")


# ==========================================
# MAIN EXECUTION
# ==========================================
if not os.path.exists(URLS_FILE):
    print(f"[!] Error: File '{URLS_FILE}' not found. Please create it and add URLs (one per line).")
    sys.exit(1)

with open(URLS_FILE, "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

print(f"Loaded {len(urls)} URLs from '{URLS_FILE}'. Checking local content hashes...")

for url in urls:
    try:
        process_url(url)
    except Exception as e:
        print(f"[X] Failed to process {url}. Error: {e}")

print("\n--- All URLs processed. ---")