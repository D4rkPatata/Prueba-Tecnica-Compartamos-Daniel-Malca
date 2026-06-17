import pandas as pd
from google.cloud import bigquery, storage
from datetime import datetime
import os


PROJECT_ID  = "prueba-tecnica-compartamos"
BUCKET_NAME = "compartamos-bucket"
DATASET_RAW = "raw"
DATA_DIR    = "data_raw"

# Primary keys de cada tabla para el MERGE
PRIMARY_KEYS = {
    "customers": "customer_id",
    "products":  "product_id",
    "orders":    "order_id",
}

ARCHIVOS = {
    "customers": f"{DATA_DIR}/customers.csv",
    "products":  f"{DATA_DIR}/products.csv",
    "orders":    f"{DATA_DIR}/orders.csv",
}


def subir_a_gcs(bucket_name: str, origen: str, destino: str) -> None:
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(bucket_name)
    blob   = bucket.blob(destino)
    blob.upload_from_filename(origen)
    print(f"  [GCS] Subido: gs://{bucket_name}/{destino}")


def cargar_a_bigquery(df: pd.DataFrame, tabla: str) -> None:
    client     = bigquery.Client(project=PROJECT_ID)
    table_ref  = f"{PROJECT_ID}.{DATASET_RAW}.{tabla}_raw"
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=True,
    )
    job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    job.result()
    print(f"  [BQ]  Cargado: {table_ref}  ({len(df)} filas)")


def main():
    print(f"\n{'='*55}")
    print(f"  INGESTA RAW  —  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}\n")

    for nombre, ruta in ARCHIVOS.items():
        print(f"► {nombre}.csv")

        df = pd.read_csv(ruta, dtype=str)
        print(f"  [CSV] Leído: {df.shape[0]} filas x {df.shape[1]} columnas")

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        destino_gcs = f"raw/{nombre}/{nombre}_{ts}.csv"
        subir_a_gcs(BUCKET_NAME, ruta, destino_gcs)

        cargar_a_bigquery(df, nombre)
        print()

    print("✓ Ingesta completada.\n")

if __name__ == "__main__":
    main()