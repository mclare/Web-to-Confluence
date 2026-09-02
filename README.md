# CPI Web-to-Confluence Content Mirror

A lightweight Python automation tool developed for Brock University's Centre for Pedagogical Innovation (CPI). This script fetches public WordPress-based web pages, strips layout clutter, and mirrors the core article content into Atlassian Confluence Cloud Space.

By mirroring public web articles into a dedicated Confluence Space, Jira Service Management (JSM) customer support portals can index public pages, enabling automated "Related Articles" suggestions and search features directly inside support tickets.

## Key Features

* Content Cleaning: Parses live HTML using BeautifulSoup to strip site header/footer clutter, scripts, navigation, and broken image containers.
* Smart Delta Sync (Local Hashing): Generates a SHA-256 hash of the cleaned HTML content (.html_cache/) and compares it before calling Atlassian APIs. If page content hasn't changed, the update is skipped to prevent Confluence page version bloat and save API quota.
*  Native Confluence Components: Automatically prepends a native Confluence Info Panel macro linking back to the canonical public source page on the CPI website.
*  REST API Powered: Operates directly against Confluence Cloud's REST API without requiring third-party plugins or site administrator permissions.

## Setup & Installation

1. Prerequisites
  * Python 3.9+ installed.
  * An Atlassian account with edit permissions in the target Confluence Space (COCWR).
  * A standard Atlassian API Token generated at id.atlassian.com/manage-profile/security/api-tokens.

2. Environment Setup

  Clone the repository, create a virtual environment, and install dependencies:
```
Bash

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

3. Configure URLs

  Create or edit urls.txt in the root directory and add the full target URLs you wish to mirror (one per line):

```
Plaintext

https://brocku.ca/pedagogical-innovation/syllabus-template/
https://brocku.ca/pedagogical-innovation/course-design-overview/
```

## Usage
```
Bash

export CONFLUENCE_EMAIL="your-email@brocku.ca"
export CONFLUENCE_API_TOKEN="your_atlassian_api_token"

python content_mirror.py
```

### Automation via Cron

  To run this script automatically on a daily schedule (e.g., every midnight at 00:00), add an entry to your server's crontab:
```
Bash

0 0 * * * cd /path/to/repo && .venv/bin/python content_mirror.py >> mirror.log 2>&1
```
  (Note: Ensure CONFLUENCE_EMAIL and CONFLUENCE_API_TOKEN are defined in your user's crontab environment or loaded from a secured .env file.)

