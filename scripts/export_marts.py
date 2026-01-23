#!/usr/bin/env python3
"""
Exporta marts de DuckDB a Excel
Uso: python scripts/export_marts.py
"""

import duckdb
import pandas as pd
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / 'ainara.duckdb'
OUTPUT_DIR = PROJECT_ROOT / 'marts_output'

def clean_dataframe(df):
    """Limpia el dataframe para que sea compatible con Excel"""
    for col in df.columns:
        # Convertir columnas datetime con timezone a sin timezone
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = pd.to_datetime(df[col]).dt.tz_localize(None)
    return df

def main():
    if not DB_PATH.exists():
        print(f"❌ No existe: {DB_PATH}")
        return
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    tables = conn.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'main'
        AND table_name NOT LIKE 'stg_%'
    """).fetchall()
    
    if not tables:
        print("⚠️  No hay marts. Corré: dbt run")
        return
    
    print(f"📊 Exportando {len(tables)} marts...\n")
    
    timestamp = datetime.now().strftime('%Y%m%d')
    
    for (table,) in tables:
        try:
            df = conn.execute(f'SELECT * FROM main."{table}"').df()
            df = clean_dataframe(df)
            filename = f"{table}_{timestamp}.xlsx"
            filepath = OUTPUT_DIR / filename
            df.to_excel(filepath, index=False)
            print(f"  ✅ {table}: {len(df):,} filas → {filename}")
        except Exception as e:
            print(f"  ❌ {table}: {e}")
    
    conn.close()
    print(f"\n📁 Archivos en: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()