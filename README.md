# CPI Web-to-Confluence Content Mirror

This project mirrors public CPI web pages into a Confluence Cloud space. It fetches a page, strips out site-specific clutter, and creates or updates a matching page in Confluence while keeping a local hash cache to avoid unnecessary updates.

This is useful when public articles need to be searchable and referenced inside Confluence-based support workflows such as Jira Service Management.

## Features

- Pulls pages from a list of URLs in `urls.txt`
- Uses BeautifulSoup to remove navigation, scripts, styles, and non-content page elements
- Inserts a Confluence info panel that links back to the original source page
- Creates or updates Confluence pages using the Confluence REST API
- Stores a SHA-256 hash for each URL in `.html_cache/` to skip unchanged content

## Requirements

- Python 3.9+
- Access to the target Confluence Cloud space with permission to create and edit pages
- A Confluence Cloud account email and API token

## Setup

1. Clone the repository.
2. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install the dependencies:

```bash
pip install -r requirements.txt
```

4. Create or update `urls.txt` in the project root. Add one full URL per line:

```text
https://brocku.ca/pedagogical-innovation/syllabus-template/
https://brocku.ca/pedagogical-innovation/course-design-overview/
```

## Configuration

Set the required environment variables before running the script:

```bash
export CONFLUENCE_EMAIL="your-email@brocku.ca"
export CONFLUENCE_API_TOKEN="your_atlassian_api_token"
```

The script is configured for the Confluence domain `cpibrock.atlassian.net` and space key `COCWR`.

## Usage

Run the script from the repository root:

```bash
python content_mirror.py
```

If a page has changed, the script updates the matching Confluence page. If the cleaned content is unchanged, it skips the write and preserves version history.

## Scheduled automation

To run the script daily via cron:

```bash
0 0 * * * cd /path/to/repo && .venv/bin/python content_mirror.py >> mirror.log 2>&1
```

Make sure `CONFLUENCE_EMAIL` and `CONFLUENCE_API_TOKEN` are available in the cron environment or loaded from a secure secret source.

## Notes

- The script assumes the target page title matches the Confluence page title.
- The local cache is stored in `.html_cache/` and is not meant to be committed.
- If `urls.txt` is missing, the script exits with an error.

