"""Export DuckDB mart tables to parquet files for Streamlit Cloud deployment."""
import os
import duckdb

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "ainara.duckdb")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "dashboard", "data")

TABLES = [
    "fct_ventas_diarias",
    "fct_pedidos",
    "dim_clientes",
    "rpt_productos_vendidos",
    "rpt_sabores",
    "rpt_pnl",
    "rpt_cash_flow",
    "rpt_egresos",
    "rpt_rfm",
    "rpt_margenes",
    "rpt_puntos",
    "rpt_zonas",
    "rpt_clientes_nuevos",
]

os.makedirs(OUT_DIR, exist_ok=True)

conn = duckdb.connect(DB_PATH, read_only=True)

for table in TABLES:
    try:
        df = conn.execute(f'SELECT * FROM main."{table}"').df()
        out = os.path.join(OUT_DIR, f"{table}.parquet")
        df.to_parquet(out, index=False)
        print(f"  {table}: {len(df)} rows -> {out}")
    except Exception as e:
        print(f"  {table}: ERROR - {e}")

conn.close()
print("\nDone!")
