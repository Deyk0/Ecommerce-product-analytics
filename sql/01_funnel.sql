-- 01_funnel.sql
-- Последовательный анализ воронки:
-- Visit → View Product → Add to Cart → Checkout → Purchase


-- =========================================================
-- 1. Последовательная воронка
-- =========================================================

WITH user_events AS (

    SELECT
        user_id,

        MIN(event_time) FILTER (
            WHERE event_name = 'visit'
        ) AS visit_time,

        MIN(event_time) FILTER (
            WHERE event_name = 'view_product'
        ) AS first_view_time,

        MIN(event_time) FILTER (
            WHERE event_name = 'add_to_cart'
        ) AS first_cart_time,

        MIN(event_time) FILTER (
            WHERE event_name = 'checkout'
        ) AS first_checkout_time,

        MIN(event_time) FILTER (
            WHERE event_name = 'purchase'
        ) AS first_purchase_time

    FROM events
    GROUP BY user_id
),

sequential_funnel AS (

    SELECT
        user_id,
        visit_time,

        CASE
            WHEN visit_time IS NOT NULL
                 AND first_view_time > visit_time
            THEN first_view_time
        END AS view_time,

        CASE
            WHEN visit_time IS NOT NULL
                 AND first_view_time > visit_time
                 AND first_cart_time > first_view_time
            THEN first_cart_time
        END AS cart_time,

        CASE
            WHEN visit_time IS NOT NULL
                 AND first_view_time > visit_time
                 AND first_cart_time > first_view_time
                 AND first_checkout_time > first_cart_time
            THEN first_checkout_time
        END AS checkout_time,

        CASE
            WHEN visit_time IS NOT NULL
                 AND first_view_time > visit_time
                 AND first_cart_time > first_view_time
                 AND first_checkout_time > first_cart_time
                 AND first_purchase_time > first_checkout_time
            THEN first_purchase_time
        END AS purchase_time

    FROM user_events
)

SELECT
    COUNT(*) FILTER (
        WHERE visit_time IS NOT NULL
    ) AS visit_users,

    COUNT(*) FILTER (
        WHERE view_time IS NOT NULL
    ) AS view_users,

    COUNT(*) FILTER (
        WHERE cart_time IS NOT NULL
    ) AS cart_users,

    COUNT(*) FILTER (
        WHERE checkout_time IS NOT NULL
    ) AS checkout_users,

    COUNT(*) FILTER (
        WHERE purchase_time IS NOT NULL
    ) AS purchase_users

FROM sequential_funnel;


-- =========================================================
-- 2. Конверсия между последовательными этапами
-- =========================================================

WITH user_events AS (

    SELECT
        user_id,

        MIN(event_time) FILTER (
            WHERE event_name = 'visit'
        ) AS visit_time,

        MIN(event_time) FILTER (
            WHERE event_name = 'view_product'
        ) AS first_view_time,

        MIN(event_time) FILTER (
            WHERE event_name = 'add_to_cart'
        ) AS first_cart_time,

        MIN(event_time) FILTER (
            WHERE event_name = 'checkout'
        ) AS first_checkout_time,

        MIN(event_time) FILTER (
            WHERE event_name = 'purchase'
        ) AS first_purchase_time

    FROM events
    GROUP BY user_id
),

sequential_funnel AS (

    SELECT
        user_id,

        visit_time,

        CASE
            WHEN visit_time IS NOT NULL
                 AND first_view_time > visit_time
            THEN first_view_time
        END AS view_time,

        CASE
            WHEN visit_time IS NOT NULL
                 AND first_view_time > visit_time
                 AND first_cart_time > first_view_time
            THEN first_cart_time
        END AS cart_time,

        CASE
            WHEN visit_time IS NOT NULL
                 AND first_view_time > visit_time
                 AND first_cart_time > first_view_time
                 AND first_checkout_time > first_cart_time
            THEN first_checkout_time
        END AS checkout_time,

        CASE
            WHEN visit_time IS NOT NULL
                 AND first_view_time > visit_time
                 AND first_cart_time > first_view_time
                 AND first_checkout_time > first_cart_time
                 AND first_purchase_time > first_checkout_time
            THEN first_purchase_time
        END AS purchase_time

    FROM user_events
),

funnel AS (

    SELECT
        COUNT(*) FILTER (
            WHERE visit_time IS NOT NULL
        ) AS visit_users,

        COUNT(*) FILTER (
            WHERE view_time IS NOT NULL
        ) AS view_users,

        COUNT(*) FILTER (
            WHERE cart_time IS NOT NULL
        ) AS cart_users,

        COUNT(*) FILTER (
            WHERE checkout_time IS NOT NULL
        ) AS checkout_users,

        COUNT(*) FILTER (
            WHERE purchase_time IS NOT NULL
        ) AS purchase_users

    FROM sequential_funnel
)

SELECT
    visit_users,
    view_users,
    cart_users,
    checkout_users,
    purchase_users,

    ROUND(
        100.0 * view_users / NULLIF(visit_users, 0),
        2
    ) AS visit_to_view_percent,

    ROUND(
        100.0 * cart_users / NULLIF(view_users, 0),
        2
    ) AS view_to_cart_percent,

    ROUND(
        100.0 * checkout_users / NULLIF(cart_users, 0),
        2
    ) AS cart_to_checkout_percent,

    ROUND(
        100.0 * purchase_users / NULLIF(checkout_users, 0),
        2
    ) AS checkout_to_purchase_percent,

    ROUND(
        100.0 * purchase_users / NULLIF(visit_users, 0),
        2
    ) AS visit_to_purchase_percent

FROM funnel;


-- =========================================================
-- 3. Последовательная воронка по месяцам
-- =========================================================

WITH user_events AS (

    SELECT
        user_id,

        MIN(event_time) FILTER (
            WHERE event_name = 'visit'
        ) AS visit_time,

        MIN(event_time) FILTER (
            WHERE event_name = 'view_product'
        ) AS first_view_time,

        MIN(event_time) FILTER (
            WHERE event_name = 'add_to_cart'
        ) AS first_cart_time,

        MIN(event_time) FILTER (
            WHERE event_name = 'checkout'
        ) AS first_checkout_time,

        MIN(event_time) FILTER (
            WHERE event_name = 'purchase'
        ) AS first_purchase_time

    FROM events
    GROUP BY user_id
),

sequential_funnel AS (

    SELECT
        user_id,

        visit_time,

        CASE
            WHEN visit_time IS NOT NULL
                 AND first_view_time > visit_time
            THEN first_view_time
        END AS view_time,

        CASE
            WHEN visit_time IS NOT NULL
                 AND first_view_time > visit_time
                 AND first_cart_time > first_view_time
            THEN first_cart_time
        END AS cart_time,

        CASE
            WHEN visit_time IS NOT NULL
                 AND first_view_time > visit_time
                 AND first_cart_time > first_view_time
                 AND first_checkout_time > first_cart_time
            THEN first_checkout_time
        END AS checkout_time,

        CASE
            WHEN visit_time IS NOT NULL
                 AND first_view_time > visit_time
                 AND first_cart_time > first_view_time
                 AND first_checkout_time > first_cart_time
                 AND first_purchase_time > first_checkout_time
            THEN first_purchase_time
        END AS purchase_time

    FROM user_events
)

SELECT
    DATE_TRUNC('month', visit_time)::date AS month,

    COUNT(*) FILTER (
        WHERE visit_time IS NOT NULL
    ) AS visit_users,

    COUNT(*) FILTER (
        WHERE view_time IS NOT NULL
    ) AS view_users,

    COUNT(*) FILTER (
        WHERE cart_time IS NOT NULL
    ) AS cart_users,

    COUNT(*) FILTER (
        WHERE checkout_time IS NOT NULL
    ) AS checkout_users,

    COUNT(*) FILTER (
        WHERE purchase_time IS NOT NULL
    ) AS purchase_users

FROM sequential_funnel

WHERE visit_time IS NOT NULL

GROUP BY month
ORDER BY month;