-- =====================================================================
-- DIM_CLIENTE   (analytics.dim_cliente)
-- Dimensión de cliente. Grano: 1 fila por customer_id.
-- Fuente: stage.customers_stage
--
-- Columna               Tipo       Descripción
-- --------------------  ---------  --------------------------------------------
-- customer_id           INT64      PK. Identificador único del cliente.
-- nombre_completo       STRING     first_name + last_name.
-- first_name            STRING     Nombre.
-- last_name             STRING     Apellido.
-- email                 STRING     Correo electrónico.
-- phone                 STRING     Teléfono.
-- city                  STRING     Ciudad.
-- country               STRING     País (normalizado a COLOMBIA).
-- age                   INT64      Edad (NULL si era imposible: <0 o >120).
-- loyalty_tier          STRING     BRONZE / SILVER / GOLD / NO DETERMINADO.
-- registration_date     DATE       Fecha de registro del cliente.
-- analytics_updated_at  TIMESTAMP  Marca de tiempo de la carga analytics.
-- =====================================================================
CREATE OR REPLACE TABLE `prueba-tecnica-compartamos.analytics.dim_cliente` AS
SELECT
    customer_id,
    TRIM(CONCAT(COALESCE(first_name, ''), ' ', COALESCE(last_name, ''))) AS nombre_completo,
    first_name,
    last_name,
    email,
    phone,
    city,
    country,
    age,
    loyalty_tier,
    registration_date,
    CURRENT_TIMESTAMP() AS analytics_updated_at
FROM `prueba-tecnica-compartamos.stage.customers_stage`;
