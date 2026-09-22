-- 04_revenue.sql
-- Revenue and monetization analysis


-- 1. Overall revenue metrics
-- Общая выручка, количество заказов и средний чек

SELECT
    SUM(revenue) AS total_revenue,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(
        SUM(revenue) / COUNT(DISTINCT order_id),
        2
    ) AS aov
FROM public.orders;


-- 2. Monthly revenue dynamics
-- Динамика выручки, заказов и среднего чека по месяцам

SELECT
    DATE_TRUNC('month', order_time)::date AS month,
    SUM(revenue) AS revenue,
    COUNT(DISTINCT order_id) AS orders,
    ROUND(
        SUM(revenue) / COUNT(DISTINCT order_id),
        2
    ) AS aov
FROM public.orders
GROUP BY month
ORDER BY month;


-- 3. Revenue by product category
-- Выручка, количество заказов и средний чек по категориям

SELECT
    p.category,
    SUM(o.revenue) AS revenue,
    COUNT(DISTINCT o.order_id) AS orders,
    ROUND(
        SUM(o.revenue) / COUNT(DISTINCT o.order_id),
        2
    ) AS aov
FROM public.orders o
JOIN public.products p
    ON o.product_id = p.product_id
GROUP BY p.category
ORDER BY revenue DESC;


-- 4. Revenue share by category
-- Доля каждой категории в общей выручке

SELECT
    p.category,
    SUM(o.revenue) AS revenue,
    ROUND(
        100.0 * SUM(o.revenue)
        / SUM(SUM(o.revenue)) OVER (),
        2
    ) AS revenue_share_percent
FROM public.orders o
JOIN public.products p
    ON o.product_id = p.product_id
GROUP BY p.category
ORDER BY revenue DESC;


-- 5. Category revenue summary
-- Итоговая таблица по категориям

SELECT
    p.category,
    COUNT(DISTINCT o.order_id) AS orders,
    SUM(o.revenue) AS revenue,
    ROUND(
        SUM(o.revenue) / COUNT(DISTINCT o.order_id),
        2
    ) AS aov,
    ROUND(
        100.0 * SUM(o.revenue)
        / SUM(SUM(o.revenue)) OVER (),
        2
    ) AS revenue_share_percent
FROM public.orders o
JOIN public.products p
    ON o.product_id = p.product_id
GROUP BY p.category
ORDER BY revenue DESC;


-- 6. ARPPU
-- Средняя выручка на одного платящего пользователя

SELECT
    COUNT(DISTINCT user_id) AS paying_users,
    SUM(revenue) AS total_revenue,
    ROUND(
        SUM(revenue) / COUNT(DISTINCT user_id),
        2
    ) AS arppu,
    ROUND(
        COUNT(DISTINCT order_id)::numeric
        / COUNT(DISTINCT user_id),
        2
    ) AS orders_per_user
FROM public.orders;


-- 7. Number of purchases per user
-- Распределение пользователей по количеству заказов

SELECT
    purchase_count,
    COUNT(*) AS users
FROM (
    SELECT
        user_id,
        COUNT(DISTINCT order_id) AS purchase_count
    FROM public.orders
    GROUP BY user_id
) user_purchases
GROUP BY purchase_count
ORDER BY purchase_count;


-- 8. LTV among paying users
-- Фактическая выручка на одного платящего пользователя
-- за наблюдаемый период

SELECT
    ROUND(AVG(user_revenue), 2) AS average_ltv,
    ROUND(MIN(user_revenue), 2) AS min_ltv,
    ROUND(MAX(user_revenue), 2) AS max_ltv
FROM (
    SELECT
        user_id,
        SUM(revenue) AS user_revenue
    FROM public.orders
    GROUP BY user_id
) user_revenue;


-- 9. LTV distribution
-- Распределение платящих пользователей
-- по диапазонам фактического LTV

SELECT
    ltv_segment,
    COUNT(*) AS users,
    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (),
        2
    ) AS user_share_percent,
    ROUND(SUM(user_revenue), 2) AS revenue
FROM (
    SELECT
        CASE
            WHEN user_revenue < 10000 THEN '< 10k'
            WHEN user_revenue < 25000 THEN '10k-25k'
            WHEN user_revenue < 50000 THEN '25k-50k'
            WHEN user_revenue < 100000 THEN '50k-100k'
            WHEN user_revenue < 250000 THEN '100k-250k'
            ELSE '250k+'
        END AS ltv_segment,
        user_revenue
    FROM (
        SELECT
            user_id,
            SUM(revenue) AS user_revenue
        FROM public.orders
        GROUP BY user_id
    ) user_revenue
) segments
GROUP BY ltv_segment
ORDER BY
    CASE ltv_segment
        WHEN '< 10k' THEN 1
        WHEN '10k-25k' THEN 2
        WHEN '25k-50k' THEN 3
        WHEN '50k-100k' THEN 4
        WHEN '100k-250k' THEN 5
        WHEN '250k+' THEN 6
    END;