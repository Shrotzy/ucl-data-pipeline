-- Queries for the Champions League pipeline (run in pgAdmin's Query Tool)

-- 1. Finished matches with team names (joins teams twice: home and away)
SELECT m.matchday,
       h.name AS home_team,
       m.home_goals,
       m.away_goals,
       a.name AS away_team
FROM matches m
JOIN teams h ON m.home_team_id = h.team_id
JOIN teams a ON m.away_team_id = a.team_id
WHERE m.status = 'FINISHED'
ORDER BY m.utc_date
LIMIT 10;

-- 2. Total goals scored and conceded per team (home and away combined)
SELECT t.name,
       COUNT(*)             AS games,
       SUM(g.goals_for)     AS goals_scored,
       SUM(g.goals_against) AS goals_conceded
FROM (
    SELECT home_team_id AS team_id, home_goals AS goals_for, away_goals AS goals_against
    FROM matches
    WHERE status = 'FINISHED'

    UNION ALL

    SELECT away_team_id, away_goals, home_goals
    FROM matches
    WHERE status = 'FINISHED'
) g
JOIN teams t ON g.team_id = t.team_id
GROUP BY t.name
ORDER BY goals_scored DESC;

-- 3. Goal difference with ranking (window function: RANK)
SELECT t.name,
       COUNT(*)                                AS games,
       SUM(g.goals_for)                        AS goals_scored,
       SUM(g.goals_against)                    AS goals_conceded,
       SUM(g.goals_for) - SUM(g.goals_against) AS goal_diff,
       RANK() OVER (ORDER BY SUM(g.goals_for) - SUM(g.goals_against) DESC) AS gd_rank
FROM (
    SELECT home_team_id AS team_id, home_goals AS goals_for, away_goals AS goals_against
    FROM matches
    WHERE status = 'FINISHED'

    UNION ALL

    SELECT away_team_id, away_goals, home_goals
    FROM matches
    WHERE status = 'FINISHED'
) g
JOIN teams t ON g.team_id = t.team_id
GROUP BY t.name
ORDER BY gd_rank;

-- 4. Recent form: points from each team's last 3 finished matches
--    (window function: ROW_NUMBER numbers each team's matches, newest first)
WITH team_matches AS (
    SELECT utc_date,
           home_team_id AS team_id,
           CASE WHEN home_goals > away_goals THEN 3
                WHEN home_goals = away_goals THEN 1
                ELSE 0 END AS points
    FROM matches
    WHERE status = 'FINISHED'

    UNION ALL

    SELECT utc_date,
           away_team_id,
           CASE WHEN away_goals > home_goals THEN 3
                WHEN away_goals = home_goals THEN 1
                ELSE 0 END
    FROM matches
    WHERE status = 'FINISHED'
),
numbered AS (
    SELECT team_id, points,
           ROW_NUMBER() OVER (PARTITION BY team_id ORDER BY utc_date DESC) AS recency
    FROM team_matches
)
SELECT t.name,
       COUNT(*)         AS games_counted,
       SUM(n.points)    AS points_last_3
FROM numbered n
JOIN teams t ON n.team_id = t.team_id
WHERE n.recency <= 3
GROUP BY t.name
ORDER BY points_last_3 DESC, t.name;

-- 5. Data check: compare our numbers (from matches) with the API's own standings.
--    Returns a row for every team where they disagree. Zero rows = everything matches.
    WITH ours AS (
        SELECT team_id,
            COUNT(*)             AS played,
            SUM(goals_for)       AS gf,
            SUM(goals_against)   AS ga
        FROM (
            SELECT home_team_id AS team_id, home_goals AS goals_for, away_goals AS goals_against
            FROM matches
            WHERE status = 'FINISHED'

            UNION ALL

            SELECT away_team_id, away_goals, home_goals
            FROM matches
            WHERE status = 'FINISHED'
        ) g
        GROUP BY team_id
    )
    SELECT t.name,
        o.played AS our_played, s.played        AS api_played,
        o.gf     AS our_gf,     s.goals_for     AS api_gf,
        o.ga     AS our_ga,     s.goals_against AS api_ga
    FROM ours o
    JOIN standings s ON s.team_id = o.team_id
                    AND s.snapshot_date = (SELECT MAX(snapshot_date) FROM standings)
    JOIN teams t ON t.team_id = o.team_id
    WHERE o.played <> s.played OR o.gf <> s.goals_for OR o.ga <> s.goals_against;