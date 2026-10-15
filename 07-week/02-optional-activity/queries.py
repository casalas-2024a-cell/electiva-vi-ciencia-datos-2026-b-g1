"""Semana 7 - Ejecuta las 3 consultas SQL y reproduce el WHERE y el GROUP BY en pandas.

Autora: Camila Alejandra Salas Gracia (casalas-2024a-cell)

Uso:
    python queries.py

Requiere la carpeta 06-week al lado de esta (usa su modelo y su CSV limpio).
Escribe resultados.md con las salidas.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
SEMANA6 = AQUI.parent / "06-week"
sys.path.insert(0, str(SEMANA6))
from build_db import construir_db, leer_limpio  # noqa: E402


def cargar_consultas(ruta: Path) -> dict[str, str]:
    """Separa queries.sql en {Q1: sql, Q2: sql, Q3: sql} usando los marcadores [Qn]."""
    texto = ruta.read_text(encoding="utf-8")
    partes = re.split(r"^-- \[(Q\d)\].*$", texto, flags=re.M)
    return {partes[i]: partes[i + 1].strip() for i in range(1, len(partes), 2)}


def tabla_md(df: pd.DataFrame) -> str:
    cab = "| " + " | ".join(df.columns) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    filas = ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join([cab, sep, *filas])


def main() -> None:
    csv = SEMANA6 / "data" / "Delivery_Logistics_clean.csv"
    con = construir_db(csv)               # base en memoria
    consultas = cargar_consultas(AQUI / "queries.sql")
    plano = leer_limpio(csv)              # versión plana para pandas

    sql = {k: pd.read_sql_query(q, con) for k, q in consultas.items()}

    # ---- Equivalente pandas de Q1 (WHERE) --------------------------------
    f = plano[(plano["delivery_status"] == "failed") & (plano["weather_condition"] == "stormy")
              & (plano["delivery_mode"] == "express") & (plano["delivery_cost"] > 1400)]
    p1 = (f[["delivery_id", "delivery_partner", "region", "vehicle_type", "delivery_rating", "delivery_cost"]]
          .rename(columns={"delivery_id": "entrega_id", "delivery_partner": "socio", "vehicle_type": "vehiculo",
                           "delivery_rating": "calificacion", "delivery_cost": "costo"})
          .sort_values(["costo", "entrega_id"], ascending=[False, True]).reset_index(drop=True))
    pd.testing.assert_frame_equal(sql["Q1"], p1, check_dtype=False)

    # ---- Equivalente pandas de Q3 (GROUP BY) -----------------------------
    g = plano.groupby("delivery_mode")
    p3 = pd.DataFrame({
        "entregas": g.size(),
        "pct_retrasadas": (100 * g["delayed"].mean()).round(1),
        "calificacion_promedio": g["delivery_rating"].mean().round(2),
        "costo_promedio": g["delivery_cost"].mean().round(1),
    }).reset_index().rename(columns={"delivery_mode": "modo"})
    p3 = p3.sort_values(["pct_retrasadas", "modo"], ascending=[False, True]).reset_index(drop=True)
    pd.testing.assert_frame_equal(sql["Q3"], p3, check_dtype=False)

    print(f"Q1: {len(sql['Q1'])} entregas express fallidas con tormenta y costo > 1400  (SQL == pandas)")
    print(sql["Q1"].to_string(index=False))
    print("Q2: top 10 por costo")
    print(sql["Q2"].to_string(index=False))
    print("Q3: por modo de entrega  (SQL == pandas)")
    print(sql["Q3"].to_string(index=False))

    explicacion = {
        "Q1": "Filtra con `WHERE` (cuatro condiciones) las entregas express fallidas con tormenta y costo mayor que 1 400, "
              "usando la vista plana `v_entrega`.",
        "Q2": "Une 5 tablas con `JOIN` para mostrar socio, región, vehículo y modo en lugar de llaves. "
              "Todas las filas del top 10 tienen el costo máximo del archivo (topado), así que el orden entre "
              "ellas es solo el desempate por `entrega_id`, no un ranking real.",
        "Q3": "Agrupa con `GROUP BY` por modo de entrega para comparar volumen, porcentaje retrasado, "
              "calificación y costo.",
    }
    md = ["# Resultados de la semana 7", "",
          "Generado por `queries.py`. Q1 y Q3 se verificaron contra su equivalente en pandas con "
          "`assert_frame_equal`.", ""]
    for k in ("Q1", "Q2", "Q3"):
        md += [f"## {k}", "", explicacion[k], "", "```sql", consultas[k], "```", "",
               f"Filas devueltas: {len(sql[k])}", "", tabla_md(sql[k]), ""]
    (AQUI / "resultados.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
