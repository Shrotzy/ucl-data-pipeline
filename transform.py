"""
Step 2 of the pipeline: TRANSFORM.
 
Read the newest raw matches file from data/raw/ and flatten the nested JSON
into simple rows that match our database tables (teams and matches).
Nothing is saved to a database yet. For now we just print what we built so
you can check it by eye.
"""

import json
from pathlib import Path

RAW_DIR = Path("data/raw")

def latest_raw_file(prefix: str) -> Path:
    """Find the newest raw file, e.g. prefix='matches' -> matches_2026....json"""
    files = sorted(RAW_DIR.glob(f"{prefix}_*.json"))
    if not files:
        raise SystemExit(f"No {prefix}_*.json file in {RAW_DIR}. Run ingest.py first.")
    return files[-1]

def flatten_match(match: dict) -> list[dict]:
    """Turn one nested match into one flat row (the 'reach into the boxes' step)."""
    full_time = match["score"]["fullTime"]
    return {
        "match_id": match["id"],
        "utc_date": match["utcDate"],
        "status": match["status"],
        "stage": match["stage"],
        "home_team_id": match["homeTeam"]["id"],
        "away_team_id": match["awayTeam"]["id"],
        "home_goals": full_time["home"],
        "away_goals": full_time["away"],
        "winner": match["score"]["winner"],
        "matchday": match["matchday"],
    }

def extract_teams(matches: list) -> dict:
    """Collect each team once, using the homeTeam/awayTeam boxes inside matches."""
    teams = {}
    for match in matches:
        for side in ("homeTeam", "awayTeam"):
            team = match[side]
            if team["id"] is not None:  # knockout matches can have teams still TBD
                teams[team["id"]] = {
                    "team_id": team["id"],
                    "name": team["name"],
                    "short_name": team["shortName"],
                    "tla": team["tla"],
                }
    return teams

def main() -> None:
    path = latest_raw_file("matches")
    print(f"Reading {path}")
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
 
    matches = [flatten_match(m) for m in raw["matches"]]
    teams = extract_teams(raw["matches"])
 
    print(f"{len(matches)} matches, {len(teams)} teams\n")
    print("First 3 match rows:")
    for row in matches[:3]:
        print(row)
 
    # A tiny data check: a finished match should always have goals.
    bad = [m for m in matches if m["status"] == "FINISHED" and m["home_goals"] is None]
    print(f"\nCheck: finished matches missing a score = {len(bad)}")
 
 
if __name__ == "__main__":
    main()