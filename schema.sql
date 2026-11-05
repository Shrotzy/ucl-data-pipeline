-- Database schema for the Champions League pipeline (PostgreSQL).
-- Run this once to create the tables.
 
-- One row per team.
CREATE TABLE IF NOT EXISTS teams (
    team_id     INTEGER PRIMARY KEY,   -- the API's own ID for the team
    name        TEXT NOT NULL,
    short_name  TEXT,
    tla         TEXT                   -- 3-letter code, e.g. "RMA"
);


-- One row per match. Future matches are included, with NULL goals until played.

CREATE TABLE IF NOT EXISTS matches (
    match_id    INTEGER PRIMARY KEY,
    utc         TIMESTAMPTZ NOT NULL,
    status      TEXT NOT NULL,
    stage       TEXT,
    matchday    INTEGER
    home_team_id INTEGER REFERENCES teams(team_id),
    away_team_id INTEGER REFERENCES teams(team_id),
    home_goals   INTEGER,
    away_goals   INTEGER,
    winner       TEXT
or NULL
)

-- A snapshot of the league table taken each day we run the pipeline.
-- Keeping a snapshot per day lets us see how the table changes over time

CREATE TABLE IF NOT EXISTS standings (
    snapshot_date DATE NOT NULL,
    team_id       INTEGER REFERENCES teams(team_id),
    position      INTEGER,
    played        INTEGER,
    won           INTEGER,
    draw          INTEGER,
    lost          INTEGER,
    goals_for     INTEGER,
    goals_against INTEGER,
    points        INTEGER,
    PRIMARY KEY (snapshot_date, team_id)

)