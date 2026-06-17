-- =====================================================================
-- DIM_CLIENTE   (analytics.dim_cliente)
-- Dimensión de cliente. Grano: 1 fila por customer_id.
-- Fuente: stage.customers_stage
--
-- PII: el email se hashea (SHA-256, irreversible) y el teléfono se enmascara
-- (solo últimos 4 dígitos). El nombre se conserva porque el reporte/P1 lo requiere.
--
-- Columna               Tipo       Descripción
-- --------------------  ---------  --------------------------------------------
-- customer_id           INT64      PK. Identificador único del cliente.
-- nombre_completo       STRING     first_name + last_name (PII, requerido por el reporte).
-- first_name            STRING     Nombre (PII).
-- last_name             STRING     Apellido (PII).
-- email_hash            STRING     Email hasheado con SHA-256 (hex). PII protegido.
-- phone_masked          STRING     Teléfono enmascarado: ****XXXX (últimos 4 dígitos).
-- city                  STRING     Ciudad.
-- country               STRING     País (normalizado a COLOMBIA).
-- age                   INT64      Edad (NULL si era imposible: <0 o >120).
-- loyalty_tier          STRING     BRONZE / SILVER / GOLD / NO DETERMINADO.
-- registration_date     DATE       Fecha de registro del cliente.
-- analytics_updated_at  TIMESTAMP  Marca de tiempo de la carga analytics.
-- =====================================================================
CREATE OR REPLACE TABLE `analytics.dim_cliente` AS
SELECT
    customer_id,
    TRIM(CONCAT(COALESCE(first_name, ''), ' ', COALESCE(last_name, ''))) AS nombre_completo,
    first_name,
    last_name,
    -- PII: email hasheado (normalizado a minúsculas antes del hash)
    TO_HEX(SHA256(LOWER(TRIM(email)))) AS email_hash,
    -- PII: teléfono enmascarado, solo últimos 4 dígitos
    CASE
        WHEN phone IS NULL THEN NULL
        ELSE CONCAT('****', SUBSTR(REGEXP_REPLACE(phone, r'\D', ''), -4))
    END AS phone_masked,
    city,
    country,
    age,
    loyalty_tier,
    registration_date,
    CURRENT_TIMESTAMP() AS analytics_updated_at
FROM `stage.customers_stage`;
