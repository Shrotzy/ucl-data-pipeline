"""
Step 3 of the pipeline: LOAD (teams, matches, standings).

Take the clean rows from transform.py and write them into PostgreSQL.
Safe to re-run: if a team or match already exists, we UPDATE it instead of
inserting a duplicate (this is called an "upsert").
"""

import json
import os

import psycopg2
from dotenv import load_dotenv

from transform import (extract_teams, flatten_match, flatten_standings,
                       latest_raw_file, snapshot_date_from_path)

load_dotenv()  # reads your DB_* settings from the .env file

UPSERT_TEAM = """
    INSERT INTO teams (team_id, name, short_name, tla)
    VALUES (%(team_id)s, %(name)s, %(short_name)s, %(tla)s)
    ON CONFLICT (team_id) DO UPDATE SET
        name = EXCLUDED.name,
        short_name = EXCLUDED.short_name,
        tla = EXCLUDED.tla;
"""

UPSERT_MATCH = """
    INSERT INTO matches (match_id, utc_date, status, stage, matchday,
                         home_team_id, away_team_id, home_goals, away_goals, winner)
    VALUES (%(match_id)s, %(utc_date)s, %(status)s, %(stage)s, %(matchday)s,
            %(home_team_id)s, %(away_team_id)s, %(home_goals)s, %(away_goals)s, %(winner)s)
    ON CONFLICT (match_id) DO UPDATE SET
        utc_date = EXCLUDED.utc_date,
        status = EXCLUDED.status,
        stage = EXCLUDED.stage,
        matchday = EXCLUDED.matchday,
        home_team_id = EXCLUDED.home_team_id,
        away_team_id = EXCLUDED.away_team_id,
        home_goals = EXCLUDED.home_goals,
        away_goals = EXCLUDED.away_goals,
        winner = EXCLUDED.winner;
"""

UPSERT_STANDING = """
    INSERT INTO standings (snapshot_date, team_id, position, played, won, draw, lost,
                           goals_for, goals_against, points)
    VALUES (%(snapshot_date)s, %(team_id)s, %(position)s, %(played)s, %(won)s, %(draw)s,
            %(lost)s, %(goals_for)s, %(goals_against)s, %(points)s)
    ON CONFLICT (snapshot_date, team_id) DO UPDATE SET
        position = EXCLUDED.position,
        played = EXCLUDED.played,
        won = EXCLUDED.won,
        draw = EXCLUDED.draw,
        lost = EXCLUDED.lost,
        goals_for = EXCLUDED.goals_for,
        goals_against = EXCLUDED.goals_against,
        points = EXCLUDED.points;
"""


def get_connection():
    """Open a connection to PostgreSQL using the settings in .env."""
    password = os.getenv("DB_PASSWORD")
    if not password:
        raise SystemExit("Missing DB_PASSWORD. Did you add the DB_* lines to your .env file?")
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "ucl_datapipeline"),
        user=os.getenv("DB_USER", "postgres"),
        password=password,
    )


def count_rows(cur, table: str) -> int:
    cur.execute(f"SELECT COUNT(*) FROM {table};")  # table names here are ours, not user input
    return cur.fetchone()[0]


def main() -> None:
    path = latest_raw_file("matches")
    print(f"Reading {path}")
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    matches = [flatten_match(m) for m in raw["matches"]]
    teams = list(extract_teams(raw["matches"]).values())

    standings_path = latest_raw_file("standings")
    print(f"Reading {standings_path}")
    with open(standings_path, encoding="utf-8") as f:
        raw_standings = json.load(f)
    standings = flatten_standings(raw_standings, snapshot_date_from_path(standings_path))

    conn = get_connection()
    try:
        # "with conn" = one transaction: everything saves together, or nothing does.
        with conn, conn.cursor() as cur:
            # Teams first, because matches point to them (foreign keys).
            cur.executemany(UPSERT_TEAM, teams)
            cur.executemany(UPSERT_MATCH, matches)
            cur.executemany(UPSERT_STANDING, standings)

            print(f"Sent {len(teams)} teams, {len(matches)} matches, "
                  f"{len(standings)} standings rows.")
            print(f"Rows now in the database: teams = {count_rows(cur, 'teams')}, "
                  f"matches = {count_rows(cur, 'matches')}, "
                  f"standings = {count_rows(cur, 'standings')}")
    finally:
        conn.close()

    print("Done.")


if __name__ == "__main__":
    main()