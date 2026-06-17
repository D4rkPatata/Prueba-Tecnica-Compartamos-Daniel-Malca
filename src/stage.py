
import pandas as pd
import numpy as np
from google.cloud import bigquery
from datetime import datetime


from config import PROJECT_ID, DATASET_RAW, DATASET_STAGE

# Clave primaria de cada tabla -> usada por el MERGE para deduplicar/upsert
PRIMARY_KEYS = {
    "customers": "customer_id",
    "products":  "product_id",
    "orders":    "order_id",
}

# Esquemas explícitos de la capa STAGE (control total de tipos)
SF = bigquery.SchemaField
ESQUEMAS = {
    "customers": [
        SF("customer_id", "INTEGER"),       SF("first_name", "STRING"),
        SF("last_name", "STRING"),          SF("email", "STRING"),
        SF("phone", "STRING"),              SF("city", "STRING"),
        SF("country", "STRING"),            SF("age", "INTEGER"),
        SF("registration_date", "DATE"),    SF("loyalty_tier", "STRING"),
        SF("stage_updated_at", "TIMESTAMP"),
    ],
    "products": [
        SF("product_id", "INTEGER"),        SF("product_name", "STRING"),
        SF("category", "STRING"),           SF("price_usd", "FLOAT"),
        SF("cost_usd", "FLOAT"),            SF("stock_units", "INTEGER"),
        SF("supplier", "STRING"),           SF("active", "BOOLEAN"),
        SF("stage_updated_at", "TIMESTAMP"),
    ],
    "orders": [
        SF("order_id", "INTEGER"),          SF("customer_id", "INTEGER"),
        SF("product_id", "INTEGER"),        SF("quantity", "INTEGER"),
        SF("unit_price_usd", "FLOAT"),      SF("total_amount_usd", "FLOAT"),
        SF("order_date", "DATE"),           SF("ship_date", "DATE"),
        SF("status", "STRING"),             SF("payment_method", "STRING"),
        SF("discount_pct", "FLOAT"),        SF("credit_card_last4", "STRING"),
        SF("stage_updated_at", "TIMESTAMP"),
    ],
}




# Helpers
def _parse_fecha(serie: pd.Series) -> pd.Series:
    """Las fechas son YYYY?MM?DD y solo cambia el separador (-, ., /).
    Normalizo el separador a '-' y parseo con un único formato.
    Lo que no calza queda como NaT."""
    s = serie.astype(str).str.strip().str.replace(r"[./]", "-", regex=True)
    return pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")


def _a_entero(serie: pd.Series) -> pd.Series:
    """A entero nullable (Int64). Basura/nulos -> <NA>."""
    return pd.to_numeric(serie, errors="coerce").astype("Int64")

# Limpieza 

def limpiar_customers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates()          # filas idénticas: conservamos una
    df = df.dropna(how="all")          # registros 100% nulos no aportan

    # Sin customer_id no podemos identificar al cliente -> se descartan
    df = df.dropna(subset=["customer_id"])
    df["customer_id"] = _a_entero(df["customer_id"])
    df = df.dropna(subset=["customer_id"])

    # registration_date a DATE (necesaria ANTES del dedup para elegir la más antigua)
    df["registration_date"] = _parse_fecha(df["registration_date"])

    # Dedup por PK: en duplicados conservamos la fecha de registro MÁS ANTIGUA
    df = (df.sort_values("registration_date", na_position="last")
            .drop_duplicates(subset=["customer_id"], keep="first"))

    # Texto a mayúscula (requisito del examen)
    for col in ["first_name", "last_name", "city"]:
        df[col] = df[col].str.upper().str.strip()
    df["email"] = df["email"].str.strip()
    df["phone"] = df["phone"].str.strip()

    # País único -> COLOMBIA (todas las variantes apuntan al mismo país)
    df["country"] = "COLOMBIA"

    # age: edades imposibles (<0 o >120) -> NULL
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df.loc[(df["age"] < 0) | (df["age"] > 120), "age"] = np.nan
    df["age"] = df["age"].astype("Int64")

    # loyalty_tier: válidos {BRONZE, SILVER, GOLD}; inválido/nulo -> NO DETERMINADO
    tiers = {"BRONZE", "SILVER", "GOLD"}
    df["loyalty_tier"] = df["loyalty_tier"].str.upper().str.strip()
    df["loyalty_tier"] = df["loyalty_tier"].where(df["loyalty_tier"].isin(tiers), "NO DETERMINADO")

    return df


def limpiar_products(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates()
    df = df.dropna(how="all")

    # product_id a entero + dedup por PK (eliminar uno)
    df["product_id"] = _a_entero(df["product_id"])
    df = df.dropna(subset=["product_id"])
    df = df.drop_duplicates(subset=["product_id"], keep="first")

    for col in ["product_name", "category"]:
        df[col] = df[col].str.upper().str.strip()

    # price/cost/stock: inválido (nulo o <= 0) -> 0
    for col, es_entero in [("price_usd", False), ("cost_usd", False), ("stock_units", True)]:
        v = pd.to_numeric(df[col], errors="coerce")
        v = v.where(v > 0, 0)
        df[col] = v.astype("Int64") if es_entero else v.round(2)

    # supplier -> formato 'PROVEEDOR [LETRA]'; sin letra reconocible -> NO DETERMINADO
    letra = df["supplier"].str.upper().str.extract(r"([A-Z])\s*$")[0]
    df["supplier"] = ("PROVEEDOR " + letra).where(letra.notna(), "NO DETERMINADO")

    # active -> booleano (solo 2 valores)
    truthy = {"1", "TRUE", "T", "YES", "SI"}
    df["active"] = df["active"].str.upper().str.strip().isin(truthy)

    return df


def limpiar_orders(df: pd.DataFrame, ids_clientes=None, ids_productos=None) -> pd.DataFrame:
    df = df.drop_duplicates()
    df = df.dropna(how="all")

    # order_id no nulo + identificadores a entero
    df = df.dropna(subset=["order_id"])
    for col in ["order_id", "customer_id", "product_id"]:
        df[col] = _a_entero(df[col])

    # Dedup por PK
    df = df.drop_duplicates(subset=["order_id"], keep="first")

    # Montos/descuento a numérico
    for col in ["unit_price_usd", "total_amount_usd", "discount_pct"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # quantity inválida (nula o <= 0) -> recalcular total/unit_price
    # (total = quantity * unit_price; el descuento no está incluido en total)
    q = pd.to_numeric(df["quantity"], errors="coerce")
    mask_q = q.isna() | (q <= 0)
    recalc = (df["total_amount_usd"] / df["unit_price_usd"]).round()
    df["quantity"] = q.where(~mask_q, recalc).astype("Int64")

    # Fechas a DATE; ship_date < order_date no tiene sentido -> NULL
    df["order_date"] = _parse_fecha(df["order_date"])
    df["ship_date"]  = _parse_fecha(df["ship_date"])
    df.loc[df["ship_date"] < df["order_date"], "ship_date"] = pd.NaT

    # status estandarizado; inválido -> NO DETERMINADO
    estados = {"COMPLETED", "PENDING", "CANCELLED", "RETURNED"}
    df["status"] = df["status"].str.upper().str.strip()
    df["status"] = df["status"].where(df["status"].isin(estados), "NO DETERMINADO")

    # payment_method estandarizado (espacios -> _); inválido -> NO DETERMINADO
    pagos = {"CREDIT_CARD", "DEBIT_CARD", "PAYPAL", "CASH"}
    df["payment_method"] = df["payment_method"].str.upper().str.strip().str.replace(" ", "_")
    df["payment_method"] = df["payment_method"].where(df["payment_method"].isin(pagos), "NO DETERMINADO")

    # credit_card_last4: PII, se conserva como string de 4 dígitos
    df["credit_card_last4"] = df["credit_card_last4"].str.strip()

    # Integridad referencial: cliente y producto deben existir en sus catálogos
    if ids_clientes is not None and ids_productos is not None:
        antes = len(df)
        df = df[df["customer_id"].isin(ids_clientes) & df["product_id"].isin(ids_productos)]
        print(f"  [STAGE] orders huérfanas eliminadas: {antes - len(df)}")

    return df

# Proceso en BigQuery

def leer_raw(client: bigquery.Client, tabla: str) -> pd.DataFrame:
    sql = f"SELECT * FROM `{PROJECT_ID}.{DATASET_RAW}.{tabla}_raw`"
    df = client.query(sql).to_dataframe()  # RAW viene todo como STRING
    print(f"  [RAW] {tabla}_raw -> {len(df)} filas leídas")
    return df


def cargar_stage(client: bigquery.Client, df: pd.DataFrame, tabla: str) -> None:
    """Carga el DataFrame limpio a una tabla temporal y hace MERGE por PK
    contra la tabla final (upsert re-procesable)."""
    schema = ESQUEMAS[tabla]
    cols   = [f.name for f in schema]
    pk     = PRIMARY_KEYS[tabla]

    # Columna de auditoría + ordenar/seleccionar según el esquema
    df = df.copy()
    df["stage_updated_at"] = pd.Timestamp.now()
    df = df.reindex(columns=cols)

    tmp_ref = f"{PROJECT_ID}.{DATASET_STAGE}.{tabla}_stage_tmp"
    tgt_ref = f"{PROJECT_ID}.{DATASET_STAGE}.{tabla}_stage"

    # 1) Tabla destino: la creamos si no existe (idempotente)
    client.create_table(bigquery.Table(tgt_ref, schema=schema), exists_ok=True)

    # 2) Cargar a temporal (siempre reemplaza)
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    client.load_table_from_dataframe(df, tmp_ref, job_config=job_config).result()

    # 3) MERGE: actualiza lo existente, inserta lo nuevo, una fila por PK
    set_clause = ", ".join(f"T.{c}=S.{c}" for c in cols if c != pk)
    ins_cols   = ", ".join(cols)
    ins_vals   = ", ".join(f"S.{c}" for c in cols)
    merge_sql = f"""
        MERGE `{tgt_ref}` T
        USING `{tmp_ref}` S
          ON T.{pk} = S.{pk}
        WHEN MATCHED THEN UPDATE SET {set_clause}
        WHEN NOT MATCHED THEN INSERT ({ins_cols}) VALUES ({ins_vals})
    """
    client.query(merge_sql).result()

    # 4) Limpiar la temporal
    client.delete_table(tmp_ref, not_found_ok=True)
    print(f"  [STAGE] MERGE -> {tgt_ref}  ({len(df)} filas procesadas)")


def main():
    print(f"\n{'='*55}")
    print(f"  RAW -> STAGE  —  {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"{'='*55}\n")

    client = bigquery.Client(project=PROJECT_ID)
    client.create_dataset(f"{PROJECT_ID}.{DATASET_STAGE}", exists_ok=True)

    # 1) Dimensiones primero (orders depende de sus IDs para integridad referencial)
    print("► customers")
    df_customers = limpiar_customers(leer_raw(client, "customers"))
    cargar_stage(client, df_customers, "customers")
    print()

    print("► products")
    df_products = limpiar_products(leer_raw(client, "products"))
    cargar_stage(client, df_products, "products")
    print()

    # 2) orders, validando que cliente y producto existan
    print("► orders")
    ids_clientes  = set(df_customers["customer_id"].dropna())
    ids_productos = set(df_products["product_id"].dropna())
    df_orders = limpiar_orders(leer_raw(client, "orders"), ids_clientes, ids_productos)
    cargar_stage(client, df_orders, "orders")
    print()

    print("✓ STAGE completado.\n")


if __name__ == "__main__":
    main()
