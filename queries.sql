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