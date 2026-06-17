# Prueba Técnica — Data Engineer (Lakehouse)

Pipeline ETL completo sobre **Google Cloud Platform**: ingesta de 3 CSV a GCS +
BigQuery, limpieza a una capa STAGE, modelado analítico (DIM/FACT) y un reporte
en Looker Studio.

**Flujo de capas:**

```
CSV  ──>  GCS + RAW  ──>  STAGE  ──>  ANALYTICS  ──>  Looker Studio
        (ingest.py)    (stage.py)   (SQL)          (vista)
```

---

## 1. Instalación y configuración

### 1.1 Entorno virtual e instalación de dependencias

```powershell
# Crear y activar el entorno virtual (uv)
uv venv
.venv\Scripts\activate

# Instalar dependencias
uv pip install -r requirements.txt
```

### 1.2 Configurar el `.env`

Copia la plantilla y completa tus valores:

```powershell
Copy-Item .env.example .env
```

```bash
GCP_PROJECT_ID=tu-project-id
GCS_BUCKET=tu-bucket
BQ_DATASET_RAW=raw
BQ_DATASET_STAGE=stage
BQ_DATASET_ANALYTICS=analytics
DATA_DIR=data_raw
```

> Las **credenciales** de GCP no van en el `.env` (ver 1.4).

### 1.3 Crear el bucket y los datasets en GCP

```bash
# Autenticarse y fijar el proyecto
gcloud auth login
gcloud config set project tu-project-id

# Bucket de GCS
gcloud storage buckets create gs://tu-bucket --location=US

# Datasets de BigQuery
bq mk --location=US --dataset tu-project-id:raw
bq mk --location=US --dataset tu-project-id:stage
bq mk --location=US --dataset tu-project-id:analytics
```

### 1.4 Credenciales para los scripts de Python

```bash
gcloud auth application-default login
```

### 1.5 Ejecutar el pipeline completo

```powershell
uv run python main.py
```

`main.py` valida primero la conexión a GCP (preflight) y luego ejecuta en orden:
**ingesta → stage → analytics**. Si una etapa falla, corta con un mensaje claro.

---

## 2. Ingesta (`src/ingest.py`) — CSV → GCS + RAW

Con **Python (pandas)** se leen los 3 CSV de `data_raw/` y, por cada uno:

1. **Se sube el archivo a un bucket de GCS**, en una ruta versionada por fecha:
   `gs://<bucket>/raw/<tabla>/<tabla>_<timestamp>.csv` (queda el histórico de cargas).
2. **El último CSV ingestado se carga al dataset `raw`** de BigQuery en
   `raw.<tabla>_raw` (modo `WRITE_TRUNCATE`).

La capa RAW se carga **todo como STRING** (sin transformar), para que la limpieza
se haga después de forma controlada en STAGE.

---

## 3. Limpieza / Transformación

Se siguieron las indicaciones de calidad de la prueba y las indicaciones
adicionales (país único, dedup por registro más antiguo, recálculo de cantidades,
integridad referencial, etc.).

- **Exploración previa:** [`notebooks/cleaning.ipynb`](notebooks/cleaning.ipynb)
  se usó para **explorar los datos, detectar los problemas y validar** la lógica de
  limpieza antes de llevarla a producción (evidencia de cada problema + verificación
  de cada regla).
- **Producción:** [`src/stage.py`](src/stage.py) aplica esa limpieza ya validada y
  **sube las tablas limpias al dataset `stage`** (`stage.<tabla>_stage`).

La carga a STAGE es **re-procesable**: cada tabla se carga a una temporal y se hace
**MERGE por clave primaria** contra la tabla final (upsert idempotente, una fila por
PK, soporta ingesta de registros nuevos). Se añade `stage_updated_at` como columna
de auditoría.

---

## 4. Analytics (STAGE → ANALYTICS)

El paso STAGE → ANALYTICS se resolvió **principalmente en SQL**: no hace falta la
complejidad de Python porque solo son **agregaciones y joins**. Los scripts viven en
[`sql/analytics/`](sql/analytics/) y los orquesta [`src/analytics.py`](src/analytics.py):

| Tabla | Descripción |
|---|---|
| `dim_cliente` | Dimensión de cliente (con PII protegida, ver §7). |
| `dim_producto` | Dimensión de producto (incluye margen). |
| `fact_venta` | Tablón de hechos de ventas (grano = pedido). Reemplaza a fact_cliente/fact_producto. |

Las tablas se crean con `CREATE OR REPLACE`, así que el proceso es idempotente.

---

## 5. Reportería — Looker Studio

El reporte se hizo en **Looker Studio**. Como Looker Studio no tiene un modelo de
datos propio, se creó una **vista** en BigQuery de la que se alimenta el dashboard:
[`sql/analytics/vw_reporte_ventas.sql`](sql/analytics/vw_reporte_ventas.sql). Es una
vista denormalizada (fact + dimensiones) al grano de pedido, de modo que Looker hace
toda la agregación.

Responde las preguntas de negocio: top 5 productos por ingresos, evolución mensual de
ventas, ticket promedio por categoría y % de pedidos por estado.

![Dashboard](docs/dashboard.png)
<!-- (captura del dashboard creado en Looker Studio) -->

---

## 6. Examen SQL / Python

Resuelto en la carpeta [`preguntas_sql/`](preguntas_sql/). Cada archivo contiene la
query de una pregunta, referenciando las tablas del dataset `analytics`:

| Archivo | Pregunta |
|---|---|
| [`p1.sql`](preguntas_sql/p1.sql) | Top 3 clientes por pedidos en el último trimestre. |
| [`p2.sql`](preguntas_sql/p2.sql) | Revenue mensual por categoría de producto. |
| [`p3.sql`](preguntas_sql/p3.sql) | Pedidos con `total_amount_usd` > 2σ (con z-score). |

---

## 7. Seguridad de la Información (PII)

La protección de datos sensibles se aplica en la query que pasa de **STAGE → ANALYTICS**
([`dim_cliente.sql`](sql/analytics/dim_cliente.sql)):

- **Teléfono:** se **enmascara** mostrando solo los últimos 4 dígitos (`****XXXX`).
- **Email:** se **hashea con SHA-256** (irreversible), columna `email_hash`.

El resto de los datos se mantienen para análisis (nombre, ciudad, etc.).

| Columna | Clasificación | Técnica |
|---|---|---|
| `email` | PII directo | Hash SHA-256 → `email_hash` |
| `phone` | PII directo | Enmascarado → `phone_masked` (`****XXXX`) |
| `nombre_completo` / `first_name` / `last_name` | PII directo | Se mantiene (requerido por el reporte) |

---

## Estructura del proyecto

```
.
├── main.py                      # pipeline completo (ingesta → stage → analytics)
├── requirements.txt
├── .env.example
├── data_raw/                    # CSV de entrada
├── notebooks/
│   └── cleaning.ipynb           # exploración y validación de la limpieza
├── src/
│   ├── config.py                # configuración desde .env
│   ├── bq.py                    # cliente BigQuery + preflight
│   ├── ingest.py                # CSV → GCS + RAW
│   ├── stage.py                 # RAW → STAGE (limpieza + MERGE)
│   └── analytics.py             # orquesta los SQL de analytics
├── sql/analytics/               # DDL de dim/fact + vista de reporte
└── preguntas_sql/               # examen SQL (p1, p2, p3)
```
