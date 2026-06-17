"""
Helper de conexión a BigQuery.

get_client() crea el cliente y hace un chequeo previo (preflight) de
credenciales y proyecto: si algo falla, corta con un mensaje accionable en
vez de un traceback a mitad del pipeline.
"""

from google.cloud import bigquery
from google.auth.exceptions import DefaultCredentialsError
from google.api_core.exceptions import Forbidden, NotFound

from config import PROJECT_ID


def get_client() -> bigquery.Client:
    """Devuelve un cliente de BigQuery ya validado.
    Lanza SystemExit con un mensaje claro si no hay credenciales o el
    proyecto no es accesible."""
    try:
        client = bigquery.Client(project=PROJECT_ID)
        # Llamada barata que obliga a autenticar y resolver el proyecto
        client.list_datasets(max_results=1)
        return client
    except DefaultCredentialsError:
        raise SystemExit(
            "✗ Sin credenciales de GCP.\n"
            "  Ejecuta: gcloud auth application-default login"
        )
    except (Forbidden, NotFound) as e:
        raise SystemExit(
            f"✗ El proyecto '{PROJECT_ID}' no existe o no tienes acceso.\n"
            f"  Revisa GCP_PROJECT_ID en .env y tus permisos.\n  Detalle: {e}"
        )
    except Exception as e:
        raise SystemExit(f"✗ No se pudo conectar a BigQuery ({PROJECT_ID}): {e}")
