-- =====================================================================
-- P2. Revenue mensual por categoría de producto.
--     Salida: año, mes, categoria, revenue_total. Ordenado de mayor a menor.
-- =====================================================================
SELECT
    f.anio                          AS anio,
    f.mes                           AS mes,
    f.product_category              AS categoria,
    ROUND(SUM(f.net_amount_usd), 2) AS revenue_total
FROM `prueba-tecnica-compartamos.analytics.fact_venta` f
WHERE f.order_date IS NOT NULL
GROUP BY f.anio, f.mes, f.product_category
ORDER BY revenue_total DESC;
