"""Semana 6 - Carga el CSV limpio en el modelo relacional normalizado (SQLite).

Autora: Camila Alejandra Salas Gracia (casalas-2024a-cell)

Uso:
    python build_db.py                 # crea logistica.db junto a este archivo

Otras semanas importan `construir_db` para reutilizar el mismo modelo.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
TABLAS = ["socio_logistico", "tipo_paquete", "tipo_vehiculo", "modo_entrega", "region", "clima",
          "estado_entrega", "socio_region", "entrega"]
# columna del CSV -> (tabla, columna id)
CATALOGOS = {"delivery_partner": ("socio_logistico", "socio_id"),
             "package_type": ("tipo_paquete", "paquete_id"),
             "vehicle_type": ("tipo_vehiculo", "vehiculo_id"),
             "delivery_mode": ("modo_entrega", "modo_id"),
             "region": ("region", "region_id"),
             "weather_condition": ("clima", "clima_id"),
             "delivery_status": ("estado_entrega", "estado_id")}


def leer_limpio(csv: Path) -> pd.DataFrame:
    return pd.read_csv(csv)


def construir_db(csv_limpio: Path, db_path: Path | None = None) -> sqlite3.Connection:
    """Crea la base (en archivo, o en memoria si db_path es None) y la llena."""
    df = leer_limpio(csv_limpio)
    assert df["delivery_id"].is_unique

    if db_path is not None and Path(db_path).exists():
        Path(db_path).unlink()
    con = sqlite3.connect(":memory:" if db_path is None else str(db_path))
    con.executescript((AQUI / "schema.sql").read_text(encoding="utf-8"))

    ids: dict[str, dict[str, int]] = {}
    for col, (tabla, pk) in CATALOGOS.items():
        con.executemany(f"INSERT INTO {tabla}(nombre) VALUES (?)", [(n,) for n in sorted(df[col].unique())])
        ids[col] = dict(con.execute(f"SELECT nombre, {pk} FROM {tabla}"))

    cobertura = df[["delivery_partner", "region"]].drop_duplicates()
    con.executemany("INSERT INTO socio_region VALUES (?,?)",
                    [(ids["delivery_partner"][s], ids["region"][r]) for s, r in cobertura.itertuples(index=False)])

    filas = []
    for r in df.itertuples(index=False):
        filas.append((int(r.delivery_id), ids["delivery_partner"][r.delivery_partner], ids["region"][r.region],
                      ids["package_type"][r.package_type], ids["vehicle_type"][r.vehicle_type],
                      ids["delivery_mode"][r.delivery_mode], ids["weather_condition"][r.weather_condition],
                      ids["delivery_status"][r.delivery_status], float(r.distance_km), float(r.package_weight_kg),
                      int(r.delivery_time_hours), int(r.expected_time_hours), int(r.delivery_rating),
                      float(r.delivery_cost), int(r.id_reconstruido), int(r.distancia_en_tope),
                      int(r.peso_en_tope), int(r.costo_en_tope)))
    con.executemany("INSERT INTO entrega VALUES (" + ",".join("?" * 18) + ")", filas)
    con.commit()
    return con


def conteos(con: sqlite3.Connection) -> dict:
    return {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in TABLAS}


if __name__ == "__main__":
    csv = Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI / "data" / "Delivery_Logistics_clean.csv"
    con = construir_db(csv, AQUI / "logistica.db")
    print("Filas por tabla:", conteos(con))
    print("Violaciones de llave foránea:", len(con.execute("PRAGMA foreign_key_check").fetchall()))
