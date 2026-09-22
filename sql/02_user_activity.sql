-- 02_user_activity.sql
-- User activity analysis: DAU, WAU, MAU

-- 1. DAU — Daily Active Users
SELECT
    event_time::date AS activity_date,
    COUNT(DISTINCT user_id) AS dau
FROM events
GROUP BY activity_date
ORDER BY activity_date;


-- 2. WAU — Weekly Active Users
SELECT
    DATE_TRUNC('week', event_time)::date AS week,
    COUNT(DISTINCT user_id) AS wau
FROM events
GROUP BY week
ORDER BY week;


-- 3. MAU — Monthly Active Users
SELECT
    DATE_TRUNC('month', event_time)::date AS month,
    COUNT(DISTINCT user_id) AS mau
FROM events
GROUP BY month
ORDER BY month;


-- 4. DAU / MAU — approximate stickiness by month
WITH daily_activity AS (
    SELECT
        event_time::date AS activity_date,
        COUNT(DISTINCT user_id) AS dau
    FROM events
    GROUP BY activity_date
),
monthly_activity AS (
    SELECT
        DATE_TRUNC('month', event_time)::date AS month,
        COUNT(DISTINCT user_id) AS mau
    FROM events
    GROUP BY month
)
SELECT
    m.month,
    ROUND(
        AVG(d.dau) / m.mau * 100,
        2
    ) AS dau_mau_percent
FROM monthly_activity m
JOIN daily_activity d
    ON DATE_TRUNC('month', d.activity_date)::date = m.month
GROUP BY m.month, m.mau
ORDER BY m.month;
