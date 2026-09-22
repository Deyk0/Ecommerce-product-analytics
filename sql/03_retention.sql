-- 03_retention.sql
-- Retention and cohort analysis
-- Методология:
-- M0 = первые 30 дней после регистрации
-- M1 = 30-59 дней
-- M2 = 60-89 дней
-- M3 = 90-119 дней и т.д.


-- 1. Cohort sizes
-- Размер каждой регистрационной когорты

SELECT
    DATE_TRUNC('month', registration_date)::date AS cohort_month,
    COUNT(*) AS cohort_users
FROM users
GROUP BY cohort_month
ORDER BY cohort_month;


-- 2. Check for events before registration
-- Проверка качества данных:
-- события пользователя не должны происходить раньше регистрации

SELECT
    COUNT(*) AS events_before_registration
FROM events e
JOIN users u
    ON e.user_id = u.user_id
WHERE e.event_time::date < u.registration_date;


-- 3. Active users by cohort and retention month
-- Количество активных пользователей каждой когорты
-- в каждом 30-дневном периоде после регистрации

SELECT
    DATE_TRUNC('month', u.registration_date)::date AS cohort_month,

    FLOOR(
        (e.event_time::date - u.registration_date) / 30.0
    )::integer AS retention_month,

    COUNT(DISTINCT u.user_id) AS active_users

FROM users u
JOIN events e
    ON u.user_id = e.user_id

WHERE e.event_time::date >= u.registration_date

GROUP BY
    DATE_TRUNC('month', u.registration_date)::date,
    FLOOR(
        (e.event_time::date - u.registration_date) / 30.0
    )::integer

ORDER BY
    cohort_month,
    retention_month;


-- 4. Activity retention
-- Доля пользователей когорты,
-- которые были активны в каждом 30-дневном периоде
--
-- M0 = 0-29 дней
-- M1 = 30-59 дней
-- M2 = 60-89 дней
-- M3 = 90-119 дней и т.д.

WITH cohort_sizes AS (
    SELECT
        DATE_TRUNC('month', registration_date)::date AS cohort_month,
        COUNT(*) AS cohort_users
    FROM users
    GROUP BY
        DATE_TRUNC('month', registration_date)::date
),

cohort_activity AS (
    SELECT
        DATE_TRUNC('month', u.registration_date)::date AS cohort_month,

        FLOOR(
            (e.event_time::date - u.registration_date) / 30.0
        )::integer AS retention_month,

        COUNT(DISTINCT u.user_id) AS active_users

    FROM users u
    JOIN events e
        ON u.user_id = e.user_id

    WHERE e.event_time::date >= u.registration_date

    GROUP BY
        DATE_TRUNC('month', u.registration_date)::date,
        FLOOR(
            (e.event_time::date - u.registration_date) / 30.0
        )::integer
)

SELECT
    ca.cohort_month,
    ca.retention_month,
    ca.active_users,
    cs.cohort_users,

    ROUND(
        100.0 * ca.active_users / cs.cohort_users,
        2
    ) AS retention_percent

FROM cohort_activity ca

JOIN cohort_sizes cs
    ON ca.cohort_month = cs.cohort_month

ORDER BY
    ca.cohort_month,
    ca.retention_month;


-- 5. Purchase retention by cohort and 30-day period
-- Доля пользователей когорты,
-- совершивших покупку в каждом 30-дневном периоде
--
-- M0 = 0-29 дней
-- M1 = 30-59 дней
-- M2 = 60-89 дней и т.д.

WITH cohort_sizes AS (
    SELECT
        DATE_TRUNC('month', registration_date)::date AS cohort_month,
        COUNT(*) AS cohort_users
    FROM users
    GROUP BY
        DATE_TRUNC('month', registration_date)::date
),

cohort_purchases AS (
    SELECT
        DATE_TRUNC('month', u.registration_date)::date AS cohort_month,

        FLOOR(
            (o.order_time::date - u.registration_date) / 30.0
        )::integer AS retention_month,

        COUNT(DISTINCT o.user_id) AS purchasing_users

    FROM orders o

    JOIN users u
        ON o.user_id = u.user_id

    WHERE o.order_time::date >= u.registration_date

    GROUP BY
        DATE_TRUNC('month', u.registration_date)::date,
        FLOOR(
            (o.order_time::date - u.registration_date) / 30.0
        )::integer
)

SELECT
    cp.cohort_month,
    cp.retention_month,
    cp.purchasing_users,
    cs.cohort_users,

    ROUND(
        100.0 * cp.purchasing_users / cs.cohort_users,
        2
    ) AS purchase_retention_percent

FROM cohort_purchases cp

JOIN cohort_sizes cs
    ON cp.cohort_month = cs.cohort_month

ORDER BY
    cp.cohort_month,
    cp.retention_month;