"""Semana 9 - Limpieza del dataset de logística de entregas (Delivery_Logistics.csv).

Autora: Camila Alejandra Salas Gracia (casalas-2024a-cell)

Uso:
    python limpieza.py                      # lee data/Delivery_Logistics.csv
    python limpieza.py ruta/raw.csv ruta/salida_dir

Genera:
    data/Delivery_Logistics_clean.csv   dataset limpio
    reportes/antes_despues.json         métricas antes/después
    reportes/antes_despues.md           la misma evidencia en tabla

Principio de diseño: no se inventa ni se borra ningún dato. Lo que no se puede
corregir (valores topados, banderas inconsistentes) se MARCA o se documenta.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
COLS_TOPE = {"distance_km": "distancia_en_tope", "package_weight_kg": "peso_en_tope",
             "delivery_cost": "costo_en_tope"}
MIN_REPETICIONES_TOPE = 50   # un valor extremo repetido >=50 veces no es una medición: es un tope


def leer_crudo(ruta: Path) -> pd.DataFrame:
    """Lee todo como texto (así se ve cómo vino cada celda)."""
    return pd.read_csv(ruta, dtype=str, keep_default_na=False)


def _horas(serie: pd.Series) -> pd.Series:
    """Las horas vienen como fecha de 1970 con las horas en los nanosegundos."""
    ext = serie.str.extract(r"^1970-01-01 00:00:00\.(\d{9})$")[0]
    assert ext.notna().all(), "tiempo con formato inesperado"
    return ext.astype("int64")


def perfilar_antes(raw: pd.DataFrame) -> dict:
    ids = pd.to_numeric(raw["delivery_id"])
    costo = pd.to_numeric(raw["delivery_cost"])
    return {
        "etiqueta": "antes",
        "filas": int(len(raw)),
        "columnas": int(raw.shape[1]),
        "filas_duplicadas_exactas": int(raw.duplicated().sum()),
        "celdas_nulas": int((raw == "").sum().sum()),
        "delivery_id_repetidos": int(ids.duplicated().sum()),
        "delivery_id_distintos": int(ids.nunique()),
        "delivery_id_no_enteros": int((ids % 1 != 0).sum()),
        "columnas_de_tiempo_guardadas_como_fecha_1970": int(
            sum(raw[c].str.startswith("1970-01-01").all()
                for c in ("delivery_time_hours", "expected_time_hours"))),
        "valores_costo_con_mas_de_2_decimales": int((costo.round(2) != costo).sum()),
        "valores_topados": {c: int(pd.to_numeric(raw[c]).isin(
            [pd.to_numeric(raw[c]).min(), pd.to_numeric(raw[c]).max()]).sum()) for c in COLS_TOPE},
        "delayed_distintos": sorted(raw["delayed"].unique().tolist()),
    }


def limpiar(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()

    # 1) Texto: quitar bordes (en este archivo no hay, pero la regla queda)
    for c in ("delivery_partner", "package_type", "vehicle_type", "delivery_mode", "region",
              "weather_condition", "delivery_status", "delayed"):
        df[c] = df[c].str.strip().str.lower()

    # 2) Tiempos: de «1970-01-01 00:00:00.000000008» a 8 (horas, entero)
    df["delivery_time_hours"] = _horas(df["delivery_time_hours"])
    df["expected_time_hours"] = _horas(df["expected_time_hours"])

    # 3) Numéricos y booleano
    for c in ("distance_km", "package_weight_kg", "delivery_cost"):
        df[c] = pd.to_numeric(df[c]).astype("float64")
    df["delivery_rating"] = pd.to_numeric(df["delivery_rating"]).astype("int64")
    df["delayed"] = df["delayed"].map({"yes": True, "no": False}).astype(bool)

    # 4) Identificador: el archivo trae el ID recortado (250 primeras filas = 250.99,
    #    250 últimas = 24750.01, como si se hubiera aplicado un tope al percentil 1 y 99).
    #    En las 24 500 filas intactas el ID coincide con la posición de la fila (1..25000),
    #    así que se reconstruye con la posición y se deja una marca.
    ids = pd.to_numeric(df["delivery_id"])
    posicion = pd.Series(np.arange(1, len(df) + 1), index=df.index)
    intacto = ids % 1 == 0
    assert (ids[intacto] == posicion[intacto]).all(), "el ID no coincide con la posición"
    df["id_reconstruido"] = ~intacto
    df["delivery_id"] = posicion.astype("int64")

    # 5) Valores topados: se marcan, NO se corrigen (el valor real se perdió)
    for col, flag in COLS_TOPE.items():
        v = df[col]
        df[flag] = v.isin([v.min(), v.max()]) & v.map(v.value_counts()).ge(MIN_REPETICIONES_TOPE)

    # 6) Validaciones
    assert df["delivery_id"].is_unique
    assert df.isna().sum().sum() == 0
    assert (df["delivery_status"].isin(["delivered", "delayed", "failed"])).all()
    assert (df["delayed"] == (df["delivery_status"] != "delivered")).all(), \
        "la bandera delayed no coincide con delivery_status"
    assert df["delivery_rating"].between(1, 5).all()
    assert (df[["distance_km", "package_weight_kg", "delivery_cost"]] > 0).all().all()
    return df.reset_index(drop=True)


def inconsistencias(limpio: pd.DataFrame) -> dict:
    """Problemas que se DETECTAN pero no se corrigen (no hay fuente para saber la verdad)."""
    tarde_por_tiempo = limpio["delivery_time_hours"] > limpio["expected_time_hours"]
    return {
        "delayed_pero_dentro_del_plazo": int((limpio["delayed"] & ~tarde_por_tiempo).sum()),
        "fallidas_con_tiempo_de_entrega": int((limpio["delivery_status"] == "failed").sum()),
        "express_con_plazo_8h": int(((limpio["delivery_mode"] == "express")
                                     & (limpio["expected_time_hours"] == 8)).sum()),
        "entregadas_fuera_de_plazo": int(((limpio["delivery_status"] == "delivered")
                                          & tarde_por_tiempo).sum()),
    }


def perfilar_despues(limpio: pd.DataFrame) -> dict:
    return {
        "etiqueta": "después",
        "filas": int(len(limpio)),
        "columnas": int(limpio.shape[1]),
        "filas_duplicadas_exactas": int(limpio.duplicated().sum()),
        "celdas_nulas": int(limpio.isna().sum().sum()),
        "delivery_id_repetidos": int(limpio["delivery_id"].duplicated().sum()),
        "delivery_id_distintos": int(limpio["delivery_id"].nunique()),
        "delivery_id_no_enteros": 0,
        "id_reconstruido": int(limpio["id_reconstruido"].sum()),
        "marcados_en_tope": {f: int(limpio[f].sum()) for f in COLS_TOPE.values()},
        "tipos": {c: str(t) for c, t in limpio.dtypes.items()},
        "inconsistencias_detectadas_no_corregidas": inconsistencias(limpio),
    }


def tabla_md(a: dict, d: dict) -> str:
    filas = [
        ("Filas", a["filas"], d["filas"]),
        ("Columnas", a["columnas"], d["columnas"]),
        ("Filas duplicadas exactas", a["filas_duplicadas_exactas"], d["filas_duplicadas_exactas"]),
        ("Celdas nulas", a["celdas_nulas"], d["celdas_nulas"]),
        ("`delivery_id` repetidos", a["delivery_id_repetidos"], d["delivery_id_repetidos"]),
        ("`delivery_id` distintos (filas = 25 000)", a["delivery_id_distintos"], d["delivery_id_distintos"]),
        ("`delivery_id` no enteros (p. ej. `250.99`)", a["delivery_id_no_enteros"], d["delivery_id_no_enteros"]),
        ("Columnas de tiempo guardadas como fecha de 1970 (de 2)",
         a["columnas_de_tiempo_guardadas_como_fecha_1970"], 0),
    ]
    out = ["| Métrica | Antes | Después |", "|---|---:|---:|"]
    out += [f"| {m} | {x:,} | {y:,} |".replace(",", " ") for m, x, y in filas]
    out += ["", f"`delivery_id` reconstruido en {d['id_reconstruido']} filas (marcadas en `id_reconstruido`). "
            "Valores topados marcados (no corregidos): "
            + ", ".join(f"`{k}`={v}" for k, v in d["marcados_en_tope"].items()) + ".",
            "", "Inconsistencias detectadas y **no** corregidas: "
            + ", ".join(f"`{k}`={v}" for k, v in d["inconsistencias_detectadas_no_corregidas"].items()) + "."]
    return "\n".join(out)


def main(ruta: Path, salida: Path) -> pd.DataFrame:
    raw = leer_crudo(ruta)
    antes = perfilar_antes(raw)
    limpio = limpiar(raw)
    despues = perfilar_despues(limpio)

    (salida / "data").mkdir(parents=True, exist_ok=True)
    (salida / "reportes").mkdir(parents=True, exist_ok=True)
    limpio.to_csv(salida / "data" / "Delivery_Logistics_clean.csv", index=False)
    (salida / "reportes" / "antes_despues.json").write_text(
        json.dumps({"antes": antes, "despues": despues}, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8")
    (salida / "reportes" / "antes_despues.md").write_text(tabla_md(antes, despues) + "\n", encoding="utf-8")
    print(tabla_md(antes, despues))
    return limpio


if __name__ == "__main__":
    raw_p = Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI / "data" / "Delivery_Logistics.csv"
    out_d = Path(sys.argv[2]) if len(sys.argv) > 2 else AQUI
    main(raw_p, out_d)
