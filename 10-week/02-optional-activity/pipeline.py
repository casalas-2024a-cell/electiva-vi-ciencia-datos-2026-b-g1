"""Semana 10 - Mini-proyecto de datos (cierre del Corte 2).

Autora: Camila Alejandra Salas Gracia (casalas-2024a-cell)

Integra lo del corte en un solo flujo:
    EXTRAER (CSV crudo)  ->  LIMPIAR (pandas, semana 9)
    ->  CARGAR en el modelo relacional (semana 6)
    ->  ANALIZAR con 2 consultas (SQL y pandas, semana 7)

Uso:
    python pipeline.py

Necesita las carpetas 06-week y 09-week al lado de esta (reutiliza su código).
Escribe todo en salidas/.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "09-week"))
sys.path.insert(0, str(AQUI.parent / "06-week"))
from limpieza import leer_crudo, limpiar, perfilar_antes, perfilar_despues  # noqa: E402  (semana 9)
from build_db import conteos, construir_db, leer_limpio  # noqa: E402  (semana 6)

SALIDAS = AQUI / "salidas"
TEAL = "#0b6e75"
NARANJA = "#c4650a"

# --- Análisis 1: SQL = filtro (WHERE) + agregación (GROUP BY) ---------------
# Se compara el clima solo dentro del modo «same day»: así el plazo prometido es el mismo (8 h).
SQL_ANALISIS_1 = """
SELECT c.nombre                                                    AS clima,
       COUNT(*)                                                    AS entregas,
       ROUND(100.0 * SUM(es.nombre <> 'delivered') / COUNT(*), 1)  AS pct_retrasadas,
       ROUND(AVG(e.calificacion), 2)                               AS calificacion_promedio
FROM entrega AS e
JOIN clima          AS c  ON c.clima_id   = e.clima_id
JOIN modo_entrega   AS m  ON m.modo_id    = e.modo_id
JOIN estado_entrega AS es ON es.estado_id = e.estado_id
WHERE m.nombre = 'same day'
GROUP BY c.clima_id, c.nombre
ORDER BY pct_retrasadas DESC, c.nombre;
"""


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalo de confianza de Wilson para una proporción."""
    p = k / n
    den = 1 + z ** 2 / n
    centro = (p + z ** 2 / (2 * n)) / den
    mitad = z * math.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / den
    return centro - mitad, centro + mitad


def extraer(ruta: Path) -> pd.DataFrame:
    """E: lee el CSV tal cual (todo como texto, sin interpretar nada)."""
    df = leer_crudo(ruta)
    print(f"[extraer] {len(df)} filas x {df.shape[1]} columnas desde {ruta.name}")
    return df


def limpiar_datos(raw: pd.DataFrame):
    """T: aplica la limpieza de la semana 9 y mide antes/después."""
    antes = perfilar_antes(raw)
    limpio = limpiar(raw)
    despues = perfilar_despues(limpio)
    print(f"[limpiar] filas {antes['filas']} -> {despues['filas']} | "
          f"ID repetidos {antes['delivery_id_repetidos']} -> {despues['delivery_id_repetidos']} | "
          f"ID reconstruidos {despues['id_reconstruido']} | "
          f"columnas {antes['columnas']} -> {despues['columnas']}")
    return limpio, antes, despues


def cargar(limpio: pd.DataFrame):
    """L: guarda el CSV limpio y lo carga en el modelo relacional normalizado."""
    SALIDAS.mkdir(exist_ok=True)
    csv = SALIDAS / "Delivery_Logistics_clean.csv"
    limpio.to_csv(csv, index=False)
    con = construir_db(csv, SALIDAS / "logistica.db")
    assert con.execute("PRAGMA foreign_key_check").fetchall() == [], "llaves foráneas rotas"
    print(f"[cargar] {conteos(con)}")
    return con, csv


def analizar(con, limpio: pd.DataFrame):
    # ---- Análisis 1 (SQL): retraso por clima, solo modo «same day»
    a1 = pd.read_sql_query(SQL_ANALISIS_1, con)

    # ---- Análisis 2 (pandas): retraso por socio logístico, con intervalo de confianza
    # Filtro: sin costos topados (no cambian el retraso, pero mantienen el costo promedio interpretable)
    base = limpio[~limpio["costo_en_tope"]]
    por_socio = (base.groupby("delivery_partner")
                 .agg(entregas=("delayed", "size"), retrasadas=("delayed", "sum"),
                      costo_promedio=("delivery_cost", "mean"))
                 .reset_index())
    ic = por_socio.apply(lambda r: wilson(int(r["retrasadas"]), int(r["entregas"])), axis=1)
    por_socio["pct_retrasadas"] = (100 * por_socio["retrasadas"] / por_socio["entregas"]).round(1)
    por_socio["ic95_inf"] = [round(100 * a, 1) for a, _ in ic]
    por_socio["ic95_sup"] = [round(100 * b, 1) for _, b in ic]
    por_socio["costo_promedio"] = por_socio["costo_promedio"].round(1)
    a2 = (por_socio.rename(columns={"delivery_partner": "socio"}).drop(columns="retrasadas")
          .sort_values(["pct_retrasadas", "socio"], ascending=[False, True]).reset_index(drop=True))

    # Verificación cruzada: el análisis 1 en pandas debe dar lo mismo que en SQL
    sd = limpio[limpio["delivery_mode"] == "same day"]
    chk = sd.groupby("weather_condition").agg(n=("delayed", "size"), p=("delayed", "mean"))
    chk["p"] = (100 * chk["p"]).round(1)
    s = a1.set_index("clima")
    assert (chk["n"].sort_index().values == s["entregas"].sort_index().values).all()
    assert (chk["p"].sort_index().values == s["pct_retrasadas"].sort_index().values).all()

    a1.to_csv(SALIDAS / "analisis1_retraso_por_clima.csv", index=False)
    a2.to_csv(SALIDAS / "analisis2_retraso_por_socio.csv", index=False)
    print("[analizar] análisis 1 (SQL) y 2 (pandas) listos; verificación cruzada OK")
    return a1, a2


def graficar(a1: pd.DataFrame, a2: pd.DataFrame) -> None:
    fig, ejes = plt.subplots(1, 2, figsize=(14.5, 5.4))
    d1 = a1.sort_values("pct_retrasadas")
    ejes[0].barh(d1["clima"], d1["pct_retrasadas"], color=TEAL)
    ejes[0].set_xlabel("% de entregas retrasadas o fallidas")
    ejes[0].set_title("Análisis 1 · Retraso por clima\n(solo modo «same day», plazo de 8 h)", fontsize=11)
    for i, (p, n) in enumerate(zip(d1["pct_retrasadas"], d1["entregas"])):
        ejes[0].text(p + 0.8, i, f"{p:.1f} %  (n={n})", va="center", fontsize=8.5)
    ejes[0].set_xlim(0, d1["pct_retrasadas"].max() * 1.3)

    d2 = a2.sort_values("pct_retrasadas")
    y = range(len(d2))
    ejes[1].errorbar(d2["pct_retrasadas"], list(y),
                     xerr=[d2["pct_retrasadas"] - d2["ic95_inf"], d2["ic95_sup"] - d2["pct_retrasadas"]],
                     fmt="o", color=NARANJA, ecolor=NARANJA, capsize=3)
    ejes[1].set_yticks(list(y))
    ejes[1].set_yticklabels(d2["socio"])
    ejes[1].set_xlabel("% retrasadas o fallidas (con intervalo de confianza del 95 %)")
    ejes[1].set_title(f"Análisis 2 · Retraso por socio logístico\n(rango estrecho: {d2['pct_retrasadas'].min():.1f} % a "
                      f"{d2['pct_retrasadas'].max():.1f} %)", fontsize=11)
    ejes[1].set_xlim(20, 33)
    for ax in ejes:
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Mini-proyecto · Logística de entregas · Camila Alejandra Salas Gracia",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(SALIDAS / "analisis.png", dpi=140, facecolor="white")


def main() -> None:
    raw = extraer(AQUI / "data" / "Delivery_Logistics.csv")
    limpio, antes, despues = limpiar_datos(raw)
    con, _ = cargar(limpio)
    a1, a2 = analizar(con, limpio)
    graficar(a1, a2)
    print("\nAnálisis 1 (SQL):\n" + a1.to_string(index=False))
    print("\nAnálisis 2 (pandas):\n" + a2.to_string(index=False))


if __name__ == "__main__":
    main()
