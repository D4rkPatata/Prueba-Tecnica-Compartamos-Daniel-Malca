-- =====================================================================
-- P1. Los 3 clientes con mayor número de pedidos en el ÚLTIMO TRIMESTRE
--     disponible en los datos.
--     Salida: customer_id, nombre_completo, cantidad_pedidos.
-- =====================================================================

SELECT
    f.customer_id,
    c.nombre_completo,
    COUNT(DISTINCT f.order_id) AS cantidad_pedidos
FROM `prueba-tecnica-compartamos.analytics.fact_venta` f
JOIN `prueba-tecnica-compartamos.analytics.dim_cliente` c ON f.customer_id = c.customer_id
WHERE f.order_date >= (
    SELECT DATE_TRUNC(MAX(order_date), QUARTER)
    FROM `prueba-tecnica-compartamos.analytics.fact_venta`
)
GROUP BY f.customer_id, c.nombre_completo
ORDER BY cantidad_pedidos DESC
LIMIT 3;
