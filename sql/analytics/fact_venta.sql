-- =====================================================================
-- FACT_VENTA   (analytics.fact_venta)
-- Tablón de hechos de ventas. Grano: 1 fila por línea de pedido (order_id).
-- Fuentes: stage.orders_stage  +  stage.products_stage (para costo/categoría).
--
-- Reemplaza a FACT_CLIENTE y FACT_PRODUCTO (indicación adicional): un único
-- hecho de ventas desde el cual se derivan las métricas de cliente y producto.
-- NO se filtra por status: se conservan todos los pedidos (completed, pending,
-- cancelled, returned) para poder reportar la distribución por estado.
--
-- Nota de negocio: total_amount_usd = quantity * unit_price_usd (bruto, sin
-- descuento). El descuento (discount_pct, 0-20%) se aplica aquí para obtener
-- el monto neto.
--
-- Columna               Tipo       Descripción
-- --------------------  ---------  --------------------------------------------
-- order_id              INT64      PK (degenerada). Identificador del pedido.
-- customer_id           INT64      FK -> dim_cliente.
-- product_id            INT64      FK -> dim_producto.
-- product_category      STRING     Categoría del producto (denormalizada para reporte).
-- order_date            DATE       Fecha del pedido.
-- ship_date             DATE       Fecha de envío (NULL si era anterior a order_date).
-- anio                  INT64      Año del pedido (para series mensuales).
-- mes                   INT64      Mes del pedido (1-12).
-- mes_fecha             DATE       Primer día del mes del pedido (para ordenar/graficar).
-- quantity              INT64      Unidades vendidas.
-- unit_price_usd        FLOAT64    Precio unitario.
-- discount_pct          FLOAT64    Descuento aplicado en % (0-20).
-- gross_amount_usd      FLOAT64    Monto bruto = quantity * unit_price_usd.
-- discount_amount_usd   FLOAT64    Monto del descuento = gross * discount_pct/100.
-- net_amount_usd        FLOAT64    Ingreso neto = gross - descuento.
-- unit_cost_usd         FLOAT64    Costo unitario (desde dim/producto).
-- cost_total_usd        FLOAT64    Costo total = quantity * unit_cost_usd.
-- profit_usd            FLOAT64    Utilidad = net_amount_usd - cost_total_usd.
-- status                STRING     Estado estandarizado del pedido.
-- payment_method        STRING     Método de pago estandarizado.
-- analytics_updated_at  TIMESTAMP  Marca de tiempo de la carga analytics.
-- =====================================================================
CREATE OR REPLACE TABLE `prueba-tecnica-compartamos.analytics.fact_venta` AS
SELECT
    o.order_id,
    o.customer_id,
    o.product_id,
    p.category AS product_category,
    o.order_date,
    o.ship_date,
    EXTRACT(YEAR  FROM o.order_date) AS anio,
    EXTRACT(MONTH FROM o.order_date) AS mes,
    DATE_TRUNC(o.order_date, MONTH)  AS mes_fecha,
    o.quantity,
    o.unit_price_usd,
    o.discount_pct,
    o.total_amount_usd AS gross_amount_usd,
    ROUND(o.total_amount_usd * COALESCE(o.discount_pct, 0) / 100, 2)        AS discount_amount_usd,
    ROUND(o.total_amount_usd * (1 - COALESCE(o.discount_pct, 0) / 100), 2)  AS net_amount_usd,
    p.cost_usd AS unit_cost_usd,
    ROUND(o.quantity * p.cost_usd, 2)                                       AS cost_total_usd,
    ROUND(o.total_amount_usd * (1 - COALESCE(o.discount_pct, 0) / 100)
          - o.quantity * p.cost_usd, 2)                                     AS profit_usd,
    o.status,
    o.payment_method,
    CURRENT_TIMESTAMP() AS analytics_updated_at
FROM `prueba-tecnica-compartamos.stage.orders_stage`   o
LEFT JOIN `prueba-tecnica-compartamos.stage.products_stage` p USING (product_id);
