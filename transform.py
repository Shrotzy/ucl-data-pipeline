"""
Step 2 of the pipeline: TRANSFORM.

Read the newest raw files from data/raw/ and flatten the nested JSON into
simple rows that match our database tables (teams, matches, standings).
Run this file by itself to preview the rows. Nothing is saved to the
database here (that's load.py's job).
"""

import json
from datetime import date, datetime
from pathlib import Path

RAW_DIR = Path("data/raw")


def latest_raw_file(prefix: str) -> Path:
    """Find the newest raw file, e.g. prefix='matches' -> matches_2026....json"""
    files = sorted(RAW_DIR.glob(f"{prefix}_*.json"))
    if not files:
        raise SystemExit(f"No {prefix}_*.json file in {RAW_DIR}. Run ingest.py first.")
    return files[-1]  # timestamps in the names sort oldest -> newest


def snapshot_date_from_path(path: Path) -> date:
    """standings_20261118T213339Z.json -> 2026-11-18 (the day the data was pulled)."""
    stamp = path.stem.split("_")[-1]  # '20261118T213339Z'
    return datetime.strptime(stamp[:8], "%Y%m%d").date()


def flatten_match(match: dict) -> dict:
    """Turn one nested match into one flat row (the 'reach into the boxes' step)."""
    full_time = match["score"]["fullTime"]
    return {
        "match_id": match["id"],
        "utc_date": match["utcDate"],
        "status": match["status"],
        "stage": match["stage"],
        "matchday": match["matchday"],
        "home_team_id": match["homeTeam"]["id"],
        "away_team_id": match["awayTeam"]["id"],
        "home_goals": full_time["home"],  # None if the match hasn't been played yet
        "away_goals": full_time["away"],
        "winner": match["score"]["winner"],
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


def flatten_standings(raw: dict, snapshot_date: date) -> list:
    """Turn the standings response into one flat row per team.

    The API can return several tables (TOTAL, HOME, AWAY). We only keep TOTAL.
    """
    rows = []
    for block in raw["standings"]:
        if block.get("type") != "TOTAL":
            continue
        for entry in block["table"]:
            rows.append({
                "snapshot_date": snapshot_date,
                "team_id": entry["team"]["id"],
                "position": entry["position"],
                "played": entry["playedGames"],
                "won": entry["won"],
                "draw": entry["draw"],
                "lost": entry["lost"],
                "goals_for": entry["goalsFor"],
                "goals_against": entry["goalsAgainst"],
                "points": entry["points"],
            })
    return rows


def main() -> None:
    matches_path = latest_raw_file("matches")
    print(f"Reading {matches_path}")
    with open(matches_path, encoding="utf-8") as f:
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

    standings_path = latest_raw_file("standings")
    print(f"\nReading {standings_path}")
    with open(standings_path, encoding="utf-8") as f:
        raw_standings = json.load(f)
    standings = flatten_standings(raw_standings, snapshot_date_from_path(standings_path))
    print(f"{len(standings)} standings rows. First 3:")
    for row in standings[:3]:
        print(row)


if __name__ == "__main__":
    main()