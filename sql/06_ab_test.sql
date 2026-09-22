-- A/B test: View Product -> Add to Cart
-- Единица анализа: сессия

WITH session_funnel AS (
    SELECT
        u.experiment_group,
        e.session_id,

        MIN(
            CASE
                WHEN e.event_name = 'view_product'
                THEN e.event_time
            END
        ) AS view_time,

        MIN(
            CASE
                WHEN e.event_name = 'add_to_cart'
                THEN e.event_time
            END
        ) AS cart_time

    FROM events e
    JOIN users u
        ON e.user_id = u.user_id

    GROUP BY
        u.experiment_group,
        e.session_id
),

experiment_results AS (
    SELECT
        experiment_group,

        COUNT(*) FILTER (
            WHERE view_time IS NOT NULL
        ) AS sessions_viewed_product,

        COUNT(*) FILTER (
            WHERE view_time IS NOT NULL
              AND cart_time IS NOT NULL
              AND cart_time > view_time
        ) AS sessions_added_to_cart

    FROM session_funnel

    GROUP BY experiment_group
)

SELECT
    experiment_group,
    sessions_viewed_product,
    sessions_added_to_cart,

    ROUND(
        sessions_added_to_cart::NUMERIC
        / NULLIF(sessions_viewed_product, 0)
        * 100,
        2
    ) AS conversion_percent

FROM experiment_results

ORDER BY experiment_group;