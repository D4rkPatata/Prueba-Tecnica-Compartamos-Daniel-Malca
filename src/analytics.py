"""
STAGE -> ANALYTICS  (BigQuery)

Construye la capa analítica (DIM_* y FACT_*) a partir de las tablas limpias
de STAGE. La transformación vive en archivos .sql (patrón ELT): este script
solo orquesta — lee cada .sql y lo ejecuta en BigQuery.

Las tablas se crean con CREATE OR REPLACE, así que el proceso es idempotente:
correrlo N veces deja siempre el mismo resultado (full-refresh de la capa).
"""

from pathlib import Path
from google.cloud import bigquery
from datetime import datetime


from config import PROJECT_ID, DATASET_ANALYTICS

SQL_DIR = Path(__file__).resolve().parent.parent / "sql" / "analytics"

# Orden de ejecución: dimensiones primero, luego el tablón de hechos
# (fact_venta hace JOIN con products, así que las dims van antes).
SCRIPTS = [
    "dim_cliente.sql",
    "dim_producto.sql",
    "fact_venta.sql",
]


def ejecutar_sql(client: bigquery.Client, ruta: Path) -> None:
    sql = ruta.read_text(encoding="utf-8")
    client.query(sql).result()
    print(f"  [OK] {ruta.name}")


def main():
    print(f"\n{'='*55}")
    print(f"  STAGE -> ANALYTICS  —  {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"{'='*55}\n")

    client = bigquery.Client(project=PROJECT_ID)
    client.create_dataset(f"{PROJECT_ID}.{DATASET_ANALYTICS}", exists_ok=True)

    for nombre in SCRIPTS:
        print(f"► {nombre}")
        ejecutar_sql(client, SQL_DIR / nombre)
        print()

    print("✓ ANALYTICS completado.\n")


if __name__ == "__main__":
    main()
