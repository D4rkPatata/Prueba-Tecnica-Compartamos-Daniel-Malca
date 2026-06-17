-- =====================================================================
-- P3. Pedidos cuyo total_amount_usd supera 2 desviaciones estándar del
--     promedio (outliers por arriba).
--     Salida: order_id, customer_id, total_amount_usd, z_score.
-- =====================================================================

WITH stats AS (
    SELECT
        AVG(gross_amount_usd)    AS media,
        STDDEV(gross_amount_usd) AS desv          -- desviación estándar muestral
    FROM `prueba-tecnica-compartamos.analytics.fact_venta`
    WHERE gross_amount_usd IS NOT NULL
)
SELECT
    f.order_id,
    f.customer_id,
    f.gross_amount_usd AS total_amount_usd,
    ROUND((f.gross_amount_usd - s.media) / s.desv, 4) AS z_score
FROM `prueba-tecnica-compartamos.analytics.fact_venta` f
CROSS JOIN stats s
WHERE (f.gross_amount_usd - s.media) / s.desv > 2
ORDER BY z_score DESC;
