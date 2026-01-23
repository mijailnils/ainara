#!/usr/bin/env python3
"""
Script para cargar datos de MySQL dump a DuckDB
Uso: python scripts/load_data.py path/to/dump.sql
"""

import duckdb
import re
import sys
from pathlib import Path

TABLES_TO_LOAD = [
    'administradores', 'clientes', 'clientes_direcciones', 'configuracion',
    'delivery', 'horarios', 'pedidos', 'pedidos_productos',
    'pedidos_productos_sabores', 'pedidos_temp', 'permisos', 'productos',
    'productos_categorias', 'promos', 'sabores', 'sabores_categorias', 'zonas',
]

def extract_create_table(sql_content, table_name):
    pattern = rf"CREATE TABLE `{table_name}` \((.*?)\) ENGINE="
    match = re.search(pattern, sql_content, re.DOTALL | re.IGNORECASE)
    return match.group(1) if match else None

def parse_column_def(col_def):
    col_def = col_def.strip()
    if col_def.upper().startswith(('PRIMARY KEY', 'KEY ', 'UNIQUE KEY', 'CONSTRAINT', 'INDEX', 'FULLTEXT')):
        return None
    col_match = re.match(r'`(\w+)`\s+(.+)', col_def)
    if not col_match:
        return None
    col_name = col_match.group(1)
    col_type_def = col_match.group(2)
    duckdb_type = convert_mysql_type(col_type_def)
    return f'"{col_name}" {duckdb_type}'

def convert_mysql_type(mysql_type):
    t = mysql_type.upper().strip()
    if re.match(r'(TINY|SMALL|MEDIUM|BIG)?INT\s*\(\d+\)', t) or 'INT' in t:
        return 'BIGINT' if 'BIG' in t else 'INTEGER'
    if 'DECIMAL' in t:
        m = re.search(r'DECIMAL\s*\((\d+),\s*(\d+)\)', t)
        return f'DECIMAL({m.group(1)},{m.group(2)})' if m else 'DECIMAL(10,2)'
    if 'FLOAT' in t or 'DOUBLE' in t:
        return 'DOUBLE'
    if any(x in t for x in ['VARCHAR', 'CHAR(', 'TEXT', 'ENUM']):
        return 'VARCHAR'
    if 'BLOB' in t:
        return 'BLOB'
    if 'DATETIME' in t or 'TIMESTAMP' in t:
        return 'TIMESTAMP'
    if 'DATE' in t:
        return 'DATE'
    if 'TIME' in t:
        return 'TIME'
    return 'VARCHAR'

def create_duckdb_table(conn, table_name, columns_sql):
    columns = []
    current_col = ""
    paren_depth = 0
    for char in columns_sql:
        if char == '(':
            paren_depth += 1
        elif char == ')':
            paren_depth -= 1
        if char == ',' and paren_depth == 0:
            col = parse_column_def(current_col)
            if col:
                columns.append(col)
            current_col = ""
        else:
            current_col += char
    if current_col.strip():
        col = parse_column_def(current_col)
        if col:
            columns.append(col)
    if not columns:
        return False
    create_sql = f'CREATE TABLE raw."{table_name}" (\n  ' + ',\n  '.join(columns) + '\n)'
    try:
        conn.execute(f'DROP TABLE IF EXISTS raw."{table_name}"')
        conn.execute(create_sql)
        return True
    except Exception as e:
        print(f"    ❌ Error SQL: {e}")
        return False

def load_inserts(conn, sql_content, table_name):
    pattern = rf"INSERT INTO `{table_name}` \(([^)]+)\) VALUES\s*(.*?);"
    rows_loaded = 0
    for match in re.finditer(pattern, sql_content, re.DOTALL | re.IGNORECASE):
        columns = match.group(1).replace('`', '"')
        values_block = match.group(2)
        insert_sql = f'INSERT INTO raw."{table_name}" ({columns}) VALUES {values_block}'
        try:
            conn.execute(insert_sql)
            rows_loaded += values_block.count('),(') + 1
        except Exception as e:
            if rows_loaded == 0:
                print(f"    ⚠️  Error en INSERT: {str(e)[:80]}")
    return rows_loaded

def load_table(conn, sql_content, table_name):
    print(f"  Cargando {table_name}...")
    columns_sql = extract_create_table(sql_content, table_name)
    if not columns_sql:
        print(f"    ⚠️  No se encontró CREATE TABLE")
        return False
    if not create_duckdb_table(conn, table_name, columns_sql):
        return False
    load_inserts(conn, sql_content, table_name)
    actual_rows = conn.execute(f'SELECT COUNT(*) FROM raw."{table_name}"').fetchone()[0]
    print(f"    ✅ {actual_rows:,} filas" if actual_rows > 0 else "    ⚠️  Sin datos")
    return True

def main():
    if len(sys.argv) < 2:
        print("Uso: python load_data.py <dump.sql>")
        sys.exit(1)
    dump_path = Path(sys.argv[1])
    if not dump_path.exists():
        print(f"Error: No existe {dump_path}")
        sys.exit(1)
    print(f"📂 Leyendo: {dump_path}")
    with open(dump_path, 'r', encoding='latin1', errors='ignore') as f:
        sql_content = f.read()
    print(f"📊 Tamaño: {len(sql_content)/1024/1024:.1f} MB")
    db_path = Path(__file__).parent.parent / 'ainara.duckdb'
    print(f"🦆 DuckDB: {db_path}")
    conn = duckdb.connect(str(db_path))
    conn.execute("CREATE SCHEMA IF NOT EXISTS raw")
    print("\n🔄 Cargando...")
    loaded = sum(1 for t in TABLES_TO_LOAD if load_table(conn, sql_content, t))
    print(f"\n✅ {loaded}/{len(TABLES_TO_LOAD)} tablas")
    print("\n📋 Resumen:")
    for (t,) in conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='raw'").fetchall():
        c = conn.execute(f'SELECT COUNT(*) FROM raw."{t}"').fetchone()[0]
        print(f"   {t}: {c:,}")
    conn.close()
    print("\n🎉 Listo! Corré: dbt run")

if __name__ == "__main__":
    main()