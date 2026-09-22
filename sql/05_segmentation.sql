-- 05_segmentation.sql
-- User and session segmentation analysis

-- 1. Conversion by device
SELECT
    u.device,
    COUNT(DISTINCT e.session_id) AS sessions,
    COUNT(DISTINCT e.session_id) FILTER (
        WHERE e.event_name = 'purchase'
    ) AS purchase_sessions,
    ROUND(
        100.0 * COUNT(DISTINCT e.session_id) FILTER (
            WHERE e.event_name = 'purchase'
        ) / COUNT(DISTINCT e.session_id),
        2
    ) AS purchase_conversion_percent
FROM events e
JOIN users u
    ON e.user_id = u.user_id
GROUP BY u.device
ORDER BY purchase_conversion_percent DESC;


-- 2. Conversion by traffic source
SELECT
    u.traffic_source,
    COUNT(DISTINCT e.session_id) AS sessions,
    COUNT(DISTINCT e.session_id) FILTER (
        WHERE e.event_name = 'purchase'
    ) AS purchase_sessions,
    ROUND(
        100.0 * COUNT(DISTINCT e.session_id) FILTER (
            WHERE e.event_name = 'purchase'
        ) / COUNT(DISTINCT e.session_id),
        2
    ) AS purchase_conversion_percent
FROM events e
JOIN users u
    ON e.user_id = u.user_id
GROUP BY u.traffic_source
ORDER BY purchase_conversion_percent DESC;


-- 3. Number of purchases per user
SELECT
    purchase_count,
    COUNT(*) AS users
FROM (
    SELECT
        user_id,
        COUNT(DISTINCT order_id) AS purchase_count
    FROM orders
    GROUP BY user_id
) user_purchases
GROUP BY purchase_count
ORDER BY purchase_count;


-- 4. Repeat buyers
SELECT
    COUNT(*) FILTER (WHERE purchase_count >= 2) AS repeat_buyers,
    COUNT(*) AS total_buyers,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE purchase_count >= 2)
        / COUNT(*),
        2
    ) AS repeat_buyer_share_percent
FROM (
    SELECT
        user_id,
        COUNT(DISTINCT order_id) AS purchase_count
    FROM orders
    GROUP BY user_id
) user_purchases;


-- 5. Time to second purchase
WITH user_orders AS (
    SELECT
        user_id,
        order_time,
        ROW_NUMBER() OVER (
            PARTITION BY user_id
            ORDER BY order_time
        ) AS purchase_number
    FROM orders
),
second_purchase AS (
    SELECT
        user_id,
        order_time AS second_purchase_time
    FROM user_orders
    WHERE purchase_number = 2
),
first_purchase AS (
    SELECT
        user_id,
        order_time AS first_purchase_time
    FROM user_orders
    WHERE purchase_number = 1
)
SELECT
    COUNT(*) AS repeat_users,
    ROUND(
        AVG(
            EXTRACT(
                EPOCH FROM (
                    s.second_purchase_time - f.first_purchase_time
                )
            ) / 86400
        ),
        2
    ) AS avg_days_to_second_purchase
FROM first_purchase f
JOIN second_purchase s
    ON f.user_id = s.user_id;
