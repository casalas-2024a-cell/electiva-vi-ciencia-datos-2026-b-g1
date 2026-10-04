#!/usr/bin/env python3
"""
Ciencia de Datos · Corte 2 · Semana 9
Modelo, consulta y limpieza de datos — Logística de última milla.

Qué hace este script (de punta a punta, reproducible):
  1. Carga data/Delivery_Logistics.csv (dataset crudo, 25 000 entregas).
  2. Perfila el dataset ANTES de limpiar (nulos, duplicados, tipos, formatos).
  3. Limpia: nulos, duplicados, IDs, tipos, formatos y valores en los extremos.
  4. Perfila el dataset DESPUÉS y escribe reports/before_after.md.
  5. Guarda data/Delivery_Logistics_clean.csv.
  6. Carga el dato limpio en SQLite con el modelo de schema.sql (el ERD).
  7. Responde 2 preguntas con SQL y con pandas, verifica que coincidan y
     escribe reports/query_results.md.

Uso:  python limpieza_y_consultas.py
Requiere: pandas (y scipy opcional para la prueba chi-cuadrado).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
RAW_CSV = BASE / "data" / "Delivery_Logistics.csv"
CLEAN_CSV = BASE / "data" / "Delivery_Logistics_clean.csv"
SCHEMA_SQL = BASE / "schema.sql"
REPORTS = BASE / "reports"
REPORTS.mkdir(exist_ok=True)

CAT_COLS = [
    "delivery_partner", "package_type", "vehicle_type",
    "delivery_mode", "region", "weather_condition", "delivery_status",
]
NUM_COLS = ["distance_km", "package_weight_kg", "delivery_cost"]
TIME_COLS = ["delivery_time_hours", "expected_time_hours"]
# Un valor que aparece >= este número de veces exactamente en el mínimo o el
# máximo de la columna se considera "amontonado" en el extremo (ver paso 7).
PILEUP_MIN_COUNT = 200


# --------------------------------------------------------------------------
# Perfilado (se usa antes y después para poder comparar)
# --------------------------------------------------------------------------
def profile(df: pd.DataFrame) -> dict:
    """Métricas de calidad comparables antes/después."""
    id_num = pd.to_numeric(df["delivery_id"], errors="coerce")
    non_integer_ids = int((id_num.notna() & (id_num % 1 != 0)).sum())
    cat_formats_bad = 0
    for c in CAT_COLS:
        s = df[c].astype("string")
        cat_formats_bad += int((s.str.contains(" ", na=False) | (s != s.str.strip().str.lower())).sum())
    time_as_datetime = [c for c in TIME_COLS if df[c].astype(str).str.startswith("1970").any()]
    return {
        "filas": len(df),
        "columnas": df.shape[1],
        "nulos_totales": int(df.isna().sum().sum()),
        "filas_duplicadas_exactas": int(df.duplicated().sum()),
        "filas_duplicadas_sin_id": int(df.drop(columns="delivery_id").duplicated().sum()),
        "delivery_id_valores_repetidos": int(len(df) - df["delivery_id"].nunique()),
        "delivery_id_no_enteros": non_integer_ids,
        "columnas_tiempo_como_fecha_1970": ", ".join(time_as_datetime) or "ninguna",
        "celdas_categoricas_sin_normalizar": cat_formats_bad,
        "delayed_tipo": str(df["delayed"].dtype),
        "decimales_maximos_delivery_cost": int(
            df["delivery_cost"].astype(str).str.split(".").str[1].str.len().fillna(0).max()
        ),
        "memoria_MB": round(df.memory_usage(deep=True).sum() / 1e6, 2),
    }


# --------------------------------------------------------------------------
# Limpieza
# --------------------------------------------------------------------------
def clean(raw: pd.DataFrame, log: list[str]) -> pd.DataFrame:
    df = raw.copy()

    # 1) Formatos de texto: quitar espacios, minúsculas, snake_case ------------
    for c in CAT_COLS + ["delayed"]:
        df[c] = (
            df[c].astype("string").str.strip().str.lower()
            .str.replace(r"\s+", "_", regex=True)
        )
    log.append("Texto normalizado: strip + minúsculas + snake_case "
               "(p. ej. 'blue dart' -> 'blue_dart', 'ev van' -> 'ev_van').")

    # 2) Nulos: contar, luego imputar o eliminar según el tipo de columna -----
    nulls_before = df.isna().sum()
    # Regla: si falta la etiqueta de retraso o el estado, la fila no sirve
    # para el análisis -> se elimina. Numéricas -> mediana. Categóricas -> 'unknown'.
    must_have = ["delayed", "delivery_status", "delivery_time_hours", "expected_time_hours"]
    dropped_null_rows = int(df[must_have].isna().any(axis=1).sum())
    df = df.dropna(subset=must_have)
    for c in NUM_COLS:
        n = int(df[c].isna().sum())
        if n:
            df[c] = df[c].fillna(df[c].median())
    for c in CAT_COLS:
        n = int(df[c].isna().sum())
        if n:
            df[c] = df[c].fillna("unknown")
    log.append(f"Nulos antes: {int(nulls_before.sum())} en total. Filas eliminadas por "
               f"nulos en columnas clave: {dropped_null_rows}. Regla de imputación "
               "(mediana en numéricas, 'unknown' en categóricas) implementada; "
               "se aplica solo si hay nulos.")

    # 3) Duplicados -------------------------------------------------------------
    before = len(df)
    df = df.drop_duplicates(subset=[c for c in df.columns if c != "delivery_id"])
    log.append(f"Duplicados eliminados (ignorando delivery_id): {before - len(df)}.")

    # 4) delivery_id corrupto -> reconstruir -----------------------------------
    # En el CSV, las primeras 250 filas traen 250.99 y las últimas 250 traen
    # 24750.01 (valores no enteros repetidos). Las 24 500 filas del medio son
    # 251, 252, ..., 24750 y cuadran exactamente con (posición + 1), así que el
    # ID original es recuperable por posición.
    ids = pd.to_numeric(raw["delivery_id"])
    good = ids[(ids % 1 == 0)]
    assert (good.values == (good.index.values + 1)).all(), "IDs buenos no siguen la posición"
    bad_ids = int((ids % 1 != 0).sum())
    df = df.reset_index(drop=True)
    df["delivery_id"] = np.arange(1, len(df) + 1, dtype="int32")
    log.append(f"delivery_id: {bad_ids} filas con ID no entero/repetido (250.99 y 24750.01); "
               "reconstruido como 1..N según el orden del archivo "
               "(verificado: los IDs sanos coinciden con posición+1).")

    # 5) Tipos: tiempos guardados como fecha 1970-01-01 00:00:00.00000000N -----
    # El valor real (horas) quedó como nanosegundos desde 1970 (N). Se recupera
    # convirtiendo a datetime y tomando el entero de nanosegundos.
    for c in TIME_COLS:
        df[c] = pd.to_datetime(df[c]).astype("datetime64[ns]").astype("int64").astype("int16")
    log.append("Tiempos (delivery_time_hours, expected_time_hours): venían como fecha "
               "'1970-01-01 00:00:00.00000000N'; el N son las horas -> convertidos a entero.")

    df["is_delayed"] = df["delayed"].map({"yes": True, "no": False}).astype(bool)
    df = df.drop(columns="delayed")
    df["delivery_rating"] = df["delivery_rating"].astype("int8")
    for c in CAT_COLS:
        df[c] = df[c].astype("category")
    log.append("Tipos: delayed yes/no -> bool (is_delayed); rating -> int8; "
               "categóricas -> category; delivery_id -> int32.")

    # 6) Formato numérico ------------------------------------------------------
    df["delivery_cost"] = df["delivery_cost"].round(2)
    df["distance_km"] = df["distance_km"].round(1)
    df["package_weight_kg"] = df["package_weight_kg"].round(2)
    log.append("Redondeo: delivery_cost a 2 decimales (había hasta 4), distance_km a 1, "
               "package_weight_kg a 2.")

    # 7) Valores amontonados en el mínimo/máximo (posible tope/winsorización) --
    # delivery_cost = 95.6674 y 1632.7206 aparecen exactamente 250 veces cada uno
    # (1 % de 25 000) y con 4 decimales, mientras el resto tiene 2: parece que se
    # topó el 1 % inferior y superior. No se eliminan (no son errores de captura
    # demostrables); se marcan para poder excluirlos en un análisis de sensibilidad.
    flag = pd.Series(False, index=df.index)
    for c in NUM_COLS:
        lo, hi = df[c].min(), df[c].max()
        for edge in (lo, hi):
            if (df[c] == edge).sum() >= PILEUP_MIN_COUNT:
                flag |= df[c] == edge
    df["boundary_value_flag"] = flag
    log.append(f"Valores amontonados en el mínimo/máximo de distancia, peso o costo: "
               f"{int(flag.sum())} filas marcadas en boundary_value_flag (no eliminadas).")

    # 8) Columna derivada útil y control de consistencia -----------------------
    df["delay_hours"] = (df["delivery_time_hours"] - df["expected_time_hours"]).astype("int16")
    inconsistent = int(((df["delivery_status"] == "delayed") & (df["delay_hours"] <= 0)).sum())
    log.append(f"Consistencia: {inconsistent} entregas con estado 'delayed' pero tiempo real "
               "<= esperado (se conservan; el estado del dataset es la etiqueta oficial). "
               "Además is_delayed=True incluye las entregas 'failed'.")

    # Validaciones finales (la limpieza falla ruidosamente si algo quedó mal)
    assert df["delivery_id"].is_unique
    assert df.isna().sum().sum() == 0
    assert (df["distance_km"] > 0).all() and (df["delivery_cost"] > 0).all()
    assert df["delivery_rating"].between(1, 5).all()
    return df


# --------------------------------------------------------------------------
# SQLite: carga el modelo del ERD (schema.sql) y devuelve la conexión
# --------------------------------------------------------------------------
def build_database(df: pd.DataFrame) -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.executescript(SCHEMA_SQL.read_text(encoding="utf-8"))
    lookups = {
        "delivery_partner": ("partner_id", "partner_name", "delivery_partner"),
        "vehicle_type": ("vehicle_type_id", "vehicle_name", "vehicle_type"),
        "package_type": ("package_type_id", "package_name", "package_type"),
        "delivery_mode": ("mode_id", "mode_name", "delivery_mode"),
        "region": ("region_id", "region_name", "region"),
        "weather_condition": ("weather_id", "condition_name", "weather_condition"),
    }
    fact = pd.DataFrame({"delivery_id": df["delivery_id"].astype(int)})
    for table, (pk, name_col, src) in lookups.items():
        names = sorted(df[src].astype(str).unique())
        ids = {n: i for i, n in enumerate(names, start=1)}
        con.executemany(f"INSERT INTO {table} VALUES (?, ?)", [(i, n) for n, i in ids.items()])
        fact[pk] = df[src].astype(str).map(ids).values
    for c in ["distance_km", "package_weight_kg", "delivery_time_hours", "expected_time_hours",
              "delivery_status", "delivery_rating", "delivery_cost"]:
        fact[c] = df[c].astype(str).values if c == "delivery_status" else df[c].values
    fact["is_delayed"] = df["is_delayed"].astype(int).values
    cols = ["delivery_id", "partner_id", "vehicle_type_id", "package_type_id", "mode_id",
            "region_id", "weather_id", "distance_km", "package_weight_kg", "delivery_time_hours",
            "expected_time_hours", "is_delayed", "delivery_status", "delivery_rating",
            "delivery_cost"]
    fact[cols].to_sql("delivery", con, if_exists="append", index=False)
    con.commit()
    return con


# --------------------------------------------------------------------------
# Consultas
# --------------------------------------------------------------------------
Q1_SQL = """
SELECT w.condition_name                       AS weather,
       COUNT(*)                               AS deliveries,
       SUM(d.is_delayed)                      AS delayed,
       ROUND(100.0 * AVG(d.is_delayed), 1)    AS delay_rate_pct
FROM delivery d
JOIN weather_condition w ON w.weather_id = d.weather_id
JOIN delivery_mode m     ON m.mode_id    = d.mode_id
WHERE m.mode_name IN ('express', 'same_day')          -- filtro: modos con plazo corto
GROUP BY w.condition_name                             -- agregación
ORDER BY delay_rate_pct DESC;
"""

Q2_SQL = """
SELECT p.partner_name                         AS carrier,
       COUNT(*)                               AS deliveries,
       SUM(d.is_delayed)                      AS delayed,
       ROUND(100.0 * AVG(d.is_delayed), 1)    AS delay_rate_pct
FROM delivery d
JOIN delivery_partner p  ON p.partner_id = d.partner_id
JOIN delivery_mode m     ON m.mode_id    = d.mode_id
JOIN weather_condition w ON w.weather_id = d.weather_id
WHERE m.mode_name IN ('express', 'same_day')          -- filtro 1: plazo corto
  AND w.condition_name IN ('rainy', 'stormy')         -- filtro 2: clima adverso
GROUP BY p.partner_name                               -- agregación
ORDER BY delay_rate_pct DESC;
"""


def q1_pandas(df: pd.DataFrame) -> pd.DataFrame:
    sub = df[df["delivery_mode"].isin(["express", "same_day"])]
    out = (sub.groupby("weather_condition", observed=True)["is_delayed"]
           .agg(deliveries="size", delayed="sum", delay_rate_pct=lambda s: round(100 * s.mean(), 1))
           .reset_index().rename(columns={"weather_condition": "weather"}))
    return out.sort_values("delay_rate_pct", ascending=False, kind="stable").reset_index(drop=True)


def q2_pandas(df: pd.DataFrame) -> pd.DataFrame:
    sub = df[df["delivery_mode"].isin(["express", "same_day"])
             & df["weather_condition"].isin(["rainy", "stormy"])]
    out = (sub.groupby("delivery_partner", observed=True)["is_delayed"]
           .agg(deliveries="size", delayed="sum", delay_rate_pct=lambda s: round(100 * s.mean(), 1))
           .reset_index().rename(columns={"delivery_partner": "carrier"}))
    return out.sort_values("delay_rate_pct", ascending=False, kind="stable").reset_index(drop=True)


def chi2_p(table: pd.DataFrame) -> float | None:
    try:
        from scipy.stats import chi2_contingency
    except ImportError:
        return None
    obs = np.c_[table["delayed"], table["deliveries"] - table["delayed"]]
    return float(chi2_contingency(obs)[1])


def fmt_p(p: float) -> str:
    return "< 0.001" if p < 0.001 else f"= {p:.3f}"


def same_result(a: pd.DataFrame, b: pd.DataFrame, key: str) -> bool:
    a = a.sort_values(key).reset_index(drop=True)
    b = b.sort_values(key).reset_index(drop=True)
    return (a[key].tolist() == b[key].tolist()
            and (a["deliveries"].values == b["deliveries"].values).all()
            and (a["delayed"].values == b["delayed"].values).all()
            and np.allclose(a["delay_rate_pct"], b["delay_rate_pct"]))


# --------------------------------------------------------------------------
def md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(lines)


def main() -> None:
    raw = pd.read_csv(RAW_CSV)
    before = profile(raw)

    log: list[str] = []
    df = clean(raw, log)
    after = profile(df.assign(delayed=df["is_delayed"]))
    after["columnas"] = df.shape[1]  # el assign de arriba solo sirve para perfilar "delayed"
    df.to_csv(CLEAN_CSV, index=False)

    # ---- reporte antes/después ----
    cmp = pd.DataFrame({"antes": before, "después": after}).rename_axis("métrica").reset_index()
    dtypes = pd.DataFrame({
        "columna": raw.columns.tolist() + ["delay_hours", "boundary_value_flag"],
        "tipo_antes": [str(t) for t in raw.dtypes] + ["—", "—"],
    })
    dtypes["tipo_después"] = dtypes["columna"].map(
        lambda c: str(df[c].dtype) if c in df.columns else "(reemplazada por is_delayed: bool)")
    report = ["# Reporte de limpieza — antes / después\n",
              "## Métricas de calidad\n", md_table(cmp), "\n",
              "## Tipos de dato por columna\n", md_table(dtypes), "\n",
              "## Pasos aplicados\n", "\n".join(f"{i}. {m}" for i, m in enumerate(log, 1)), "\n"]
    (REPORTS / "before_after.md").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))

    # ---- SQL + pandas ----
    con = build_database(df)
    q1_sql = pd.read_sql_query(Q1_SQL, con)
    q2_sql = pd.read_sql_query(Q2_SQL, con)
    q1_pd, q2_pd = q1_pandas(df), q2_pandas(df)
    ok1, ok2 = same_result(q1_sql, q1_pd, "weather"), same_result(q2_sql, q2_pd, "carrier")
    assert ok1 and ok2, "SQL y pandas no coinciden"

    p1, p2 = chi2_p(q1_pd), chi2_p(q2_pd)
    out = ["# Resultados de las consultas\n",
           "## Q1 — Tasa de retraso por clima (solo express y same_day)\n", md_table(q1_sql),
           f"\nChi-cuadrado entre climas: p {fmt_p(p1)}\n" if p1 is not None else "",
           "## Q2 — Tasa de retraso por transportista (express/same_day con lluvia o tormenta)\n",
           md_table(q2_sql),
           f"\nChi-cuadrado entre transportistas: p {fmt_p(p2)}\n" if p2 is not None else "",
           f"\nVerificación SQL == pandas: Q1 {ok1}, Q2 {ok2}\n"]
    (REPORTS / "query_results.md").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))
    print(f"\nListo. Dataset limpio -> {CLEAN_CSV.relative_to(BASE)}")


if __name__ == "__main__":
    main()
