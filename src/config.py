"""
Configuración central del pipeline.

Lee las variables de entorno desde el archivo .env de la raíz del proyecto y
las expone como constantes para que ingest/stage/analytics no repitan valores.
Si una variable no está definida, se usa un valor por defecto razonable.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Carga el .env de la raíz (un nivel arriba de src/)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


#por defecto pongo mi configuracion, editar en .env para que corra en otro proyecto
PROJECT_ID        = os.environ.get("GCP_PROJECT_ID", "prueba-tecnica-compartamos")
BUCKET_NAME       = os.environ.get("GCS_BUCKET", "compartamos-bucket")
DATASET_RAW       = os.environ.get("BQ_DATASET_RAW", "raw")
DATASET_STAGE     = os.environ.get("BQ_DATASET_STAGE", "stage")
DATASET_ANALYTICS = os.environ.get("BQ_DATASET_ANALYTICS", "analytics")
DATA_DIR          = os.environ.get("DATA_DIR", "data_raw")
