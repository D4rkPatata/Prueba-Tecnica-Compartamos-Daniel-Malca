-- =====================================================================
-- VW_REPORTE_VENTAS   
-- Vista de looker con toda la información de ventas, clientes y productos.
-- =====================================================================
CREATE OR REPLACE VIEW `prueba-tecnica-compartamos.analytics.vw_reporte_ventas` AS
SELECT
    f.order_id,
    f.order_date,
    f.mes_fecha,                         -- primer día del mes (eje temporal)
    f.anio,
    f.mes,
    -- Producto
    f.product_id,
    pr.product_name,
    f.product_category,
    -- Cliente
    f.customer_id,
    c.nombre_completo,
    c.city,
    c.loyalty_tier,
    -- Métricas
    f.quantity,
    f.unit_price_usd,
    f.discount_pct,
    f.gross_amount_usd,                  -- monto bruto (qty * unit_price)
    f.net_amount_usd,                    -- ingreso neto (tras descuento) = "revenue"
    f.profit_usd,                        -- utilidad (neto - costo)
    -- Atributos de pedido
    f.status,
    f.payment_method
FROM `prueba-tecnica-compartamos.analytics.fact_venta`     f
LEFT JOIN `prueba-tecnica-compartamos.analytics.dim_producto` pr USING (product_id)
LEFT JOIN `prueba-tecnica-compartamos.analytics.dim_cliente`  c  USING (customer_id);
