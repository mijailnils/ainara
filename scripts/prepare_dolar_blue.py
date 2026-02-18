"""
Convierte el CSV de Investing.com (formato europeo) a seed CSV para dbt.
Input:  raw_data/Datos históricos USD_ARSB.csv
Output: seeds/dolar_blue.csv
"""
import csv
import sys
import io
from pathlib import Path

# Paths
BASE = Path(__file__).parent.parent
RAW = BASE / "raw_data" / "Datos históricos USD_ARSB.csv"
OUT = BASE / "seeds" / "dolar_blue.csv"


def parse_euro_number(s: str) -> float:
    """'1.420,00' -> 1420.00 ; '208,00' -> 208.00"""
    s = s.strip().strip('"')
    s = s.replace(".", "")   # remove thousands separator
    s = s.replace(",", ".")  # decimal comma -> dot
    return float(s)


def parse_euro_date(s: str) -> str:
    """'09.02.2026' -> '2026-02-09'"""
    s = s.strip().strip('"')
    parts = s.split(".")
    return f"{parts[2]}-{parts[1]}-{parts[0]}"


def main():
    rows = []
    with open(RAW, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)  # Fecha, Último, Apertura, ...
        for row in reader:
            if not row or not row[0].strip():
                continue
            fecha = parse_euro_date(row[0])
            valor = parse_euro_number(row[1])
            rows.append((fecha, valor))

    # Sort ascending by date
    rows.sort(key=lambda x: x[0])

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["fecha", "valor_blue"])
        for fecha, valor in rows:
            writer.writerow([fecha, f"{valor:.2f}"])

    print(f"OK: {len(rows)} rows written to {OUT}")


if __name__ == "__main__":
    main()
