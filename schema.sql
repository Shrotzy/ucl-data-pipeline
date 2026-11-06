CREATE TABLE IF NOT EXISTS teams (
    team_id     INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    short_name  TEXT,
    tla         TEXT
);

CREATE TABLE IF NOT EXISTS matches (
    match_id      INTEGER PRIMARY KEY,
    utc_date      TIMESTAMPTZ NOT NULL,
    status        TEXT NOT NULL,
    stage         TEXT,
    matchday      INTEGER,
    home_team_id  INTEGER REFERENCES teams (team_id),
    away_team_id  INTEGER REFERENCES teams (team_id),
    home_goals    INTEGER,
    away_goals    INTEGER,
    winner        TEXT
);

CREATE TABLE IF NOT EXISTS standings (
    snapshot_date  DATE NOT NULL,
    team_id        INTEGER NOT NULL REFERENCES teams (team_id),
    position       INTEGER,
    played         INTEGER,
    won            INTEGER,
    draw           INTEGER,
    lost           INTEGER,
    goals_for      INTEGER,
    goals_against  INTEGER,
    points         INTEGER,
    PRIMARY KEY (snapshot_date, team_id)
);