-- 01_funnel.sql
-- Анализ воронки от визита до покупки

-- 1. Количество уникальных пользователей на каждом этапе
SELECT
    COUNT(DISTINCT user_id) FILTER (
        WHERE event_name = 'visit'
    ) AS visit_users,

    COUNT(DISTINCT user_id) FILTER (
        WHERE event_name = 'view_product'
    ) AS view_users,

    COUNT(DISTINCT user_id) FILTER (
        WHERE event_name = 'add_to_cart'
    ) AS cart_users,

    COUNT(DISTINCT user_id) FILTER (
        WHERE event_name = 'checkout'
    ) AS checkout_users,

    COUNT(DISTINCT user_id) FILTER (
        WHERE event_name = 'purchase'
    ) AS purchase_users
FROM events;


-- 2. Конверсия между этапами
WITH funnel AS (
    SELECT
        COUNT(DISTINCT user_id) FILTER (
            WHERE event_name = 'visit'
        ) AS visit_users,

        COUNT(DISTINCT user_id) FILTER (
            WHERE event_name = 'view_product'
        ) AS view_users,

        COUNT(DISTINCT user_id) FILTER (
            WHERE event_name = 'add_to_cart'
        ) AS cart_users,

        COUNT(DISTINCT user_id) FILTER (
            WHERE event_name = 'checkout'
        ) AS checkout_users,

        COUNT(DISTINCT user_id) FILTER (
            WHERE event_name = 'purchase'
        ) AS purchase_users
    FROM events
)
SELECT
    visit_users,
    view_users,
    cart_users,
    checkout_users,
    purchase_users,

    ROUND(100.0 * view_users / visit_users, 2)
        AS visit_to_view_percent,

    ROUND(100.0 * cart_users / view_users, 2)
        AS view_to_cart_percent,

    ROUND(100.0 * checkout_users / cart_users, 2)
        AS cart_to_checkout_percent,

    ROUND(100.0 * purchase_users / checkout_users, 2)
        AS checkout_to_purchase_percent,

    ROUND(100.0 * purchase_users / visit_users, 2)
        AS visit_to_purchase_percent
FROM funnel;


-- 3. Воронка по месяцам
SELECT
    DATE_TRUNC('month', event_time)::date AS month,

    COUNT(DISTINCT user_id) FILTER (
        WHERE event_name = 'visit'
    ) AS visit_users,

    COUNT(DISTINCT user_id) FILTER (
        WHERE event_name = 'view_product'
    ) AS view_users,

    COUNT(DISTINCT user_id) FILTER (
        WHERE event_name = 'add_to_cart'
    ) AS cart_users,

    COUNT(DISTINCT user_id) FILTER (
        WHERE event_name = 'checkout'
    ) AS checkout_users,

    COUNT(DISTINCT user_id) FILTER (
        WHERE event_name = 'purchase'
    ) AS purchase_users

FROM events
GROUP BY month
ORDER BY month;