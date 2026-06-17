"""
Pipeline ETL completo  —  punto de entrada único.

Ejecuta en orden:
    1. Ingesta   : CSV  -> RAW    (src/ingest.py)
    2. Stage     : RAW  -> STAGE  (src/stage.py)
    3. Analytics : STAGE-> ANALYTICS + vista de reporte (src/analytics.py)

Uso:
    uv run python main.py

Requiere credenciales de GCP (Application Default Credentials):
    gcloud auth application-default login
"""

import sys
import time
from pathlib import Path

# Permite importar los módulos que viven en src/
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import bq
import config
import ingest
import stage
import analytics


ETAPAS = [
    ("INGESTA   (CSV -> RAW)",        ingest.main),
    ("STAGE     (RAW -> STAGE)",      stage.main),
    ("ANALYTICS (STAGE -> ANALYTICS)", analytics.main),
]


def main() -> int:
    print("\n" + "#" * 60)
    print("#  PIPELINE ETL  —  Prueba Técnica Compartamos")
    print("#" * 60)

    # Preflight: valida credenciales y proyecto ANTES de empezar.
    # Si falla, corta acá con un mensaje claro (no a mitad del pipeline).
    print("\n>>> Verificando conexión a GCP...")
    bq.get_client()
    print(f"    OK: proyecto '{config.PROJECT_ID}' accesible")

    inicio = time.time()
    for nombre, etapa in ETAPAS:
        print(f"\n>>> {nombre}")
        try:
            etapa()
        except Exception as e:
            print(f"\n✗ El pipeline falló en la etapa '{nombre}':\n  {e}\n")
            return 1

    print("#" * 60)
    print(f"#  PIPELINE COMPLETADO en {time.time() - inicio:.1f}s")
    print("#" * 60 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
