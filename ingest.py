"""
Step 1 of the pipeline: INGEST.
 
Pull Champions League data from football-data.org and save the raw,
untouched responses to data/raw/. We don't clean anything here on purpose:
if we mess up the cleaning later, we can re-run it on these raw files
without calling the API again.
"""

import json
import os
import time
import requests
from datetime  import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
BASE_URL = "https://api.football-data.org/v4"
COMPETITION = "CL"  # Champions League
RAW_DIR = Path("data/raw")

SECONDS_BETWEEN_CALLS = 7
MAX_RETRIES = 3

ENDPOINTS = {
    "matches": f"/competitions/{COMPETITION}/matches",
    "standings": f"/competitions/{COMPETITION}/standings",
    "teams": f"/competitions/{COMPETITION}/teams",
}


def fetch(path: str) -> dict:
    """Call one API endpoint. Retries if it fails or if we hit the rate limit."""
    url = BASE_URL + path
    headers = {"X-Auth-Token": API_KEY}
 
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=headers, timeout=30)
 
            if response.status_code == 429:  # "too many requests"
                try:
                    wait = int(response.headers.get("Retry-After", 60))
                except ValueError:
                    wait = 60
                print(f"  Rate limited. Waiting {wait}s (attempt {attempt}/{MAX_RETRIES})...")
                time.sleep(wait)
                continue
 
            response.raise_for_status()  # raises an error for 4xx/5xx codes
            return response.json()
 
        except requests.RequestException as error:
            print(f"  Request failed: {error} (attempt {attempt}/{MAX_RETRIES})")
            time.sleep(SECONDS_BETWEEN_CALLS * attempt)
 
    raise RuntimeError(f"Gave up on {url} after {MAX_RETRIES} attempts")


def save_raw(name: str, data: dict) -> Path:
    """Save the raw response as a timestamped JSON file."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    file_path = RAW_DIR / f"{name}_{timestamp}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return file_path
 
 
def main() -> None:
    if not API_KEY:
        raise SystemExit("Missing FOOTBALL_DATA_API_KEY. Did you create your .env file?")
 
    for i, (name, path) in enumerate(ENDPOINTS.items()):
        if i > 0:
            time.sleep(SECONDS_BETWEEN_CALLS)  # stay under the rate limit
        print(f"Fetching {name}...")
        data = fetch(path)
        saved_to = save_raw(name, data)
        print(f"  Saved to {saved_to}")
 
    print("Done.")
 
 
if __name__ == "__main__":
    main()
