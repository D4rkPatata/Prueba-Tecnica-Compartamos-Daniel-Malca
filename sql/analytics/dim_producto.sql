-- =====================================================================
-- DIM_PRODUCTO   (analytics.dim_producto)
-- Dimensión de producto. Grano: 1 fila por product_id.
-- Fuente: stage.products_stage
--
-- Columna               Tipo       Descripción
-- --------------------  ---------  --------------------------------------------
-- product_id            INT64      PK. Identificador único del producto.
-- product_name          STRING     Nombre del producto.
-- category              STRING     Categoría.
-- supplier              STRING     Proveedor (formato 'PROVEEDOR [LETRA]').
-- price_usd             FLOAT64    Precio de venta (inválido -> 0).
-- cost_usd              FLOAT64    Costo (inválido -> 0).
-- margin_usd            FLOAT64    Margen unitario = price_usd - cost_usd.
-- margin_pct            FLOAT64    Margen % = margin_usd / price_usd (NULL si precio 0).
-- stock_units           INT64      Unidades en stock (inválido -> 0).
-- active                BOOL       Si el producto está activo.
-- analytics_updated_at  TIMESTAMP  Marca de tiempo de la carga analytics.
-- =====================================================================
CREATE OR REPLACE TABLE `prueba-tecnica-compartamos.analytics.dim_producto` AS
SELECT
    product_id,
    product_name,
    category,
    supplier,
    price_usd,
    cost_usd,
    ROUND(price_usd - cost_usd, 2)                                    AS margin_usd,
    ROUND(SAFE_DIVIDE(price_usd - cost_usd, NULLIF(price_usd, 0)), 4) AS margin_pct,
    stock_units,
    active,
    CURRENT_TIMESTAMP() AS analytics_updated_at
FROM `prueba-tecnica-compartamos.stage.products_stage`;
