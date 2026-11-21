"""Semana 11 - Análisis temporal y series de tiempo.

Autora: Camila Alejandra Salas Gracia (casalas-2024a-cell)

El dataset de logística (semanas 6 a 10) NO trae fechas. La guía permite usar una serie real o
simulada, así que aquí se le asigna a cada entrega una FECHA SIMULADA (semilla fija) con una
tendencia suave y una temporada alta en nov-dic. Todo lo demás (retrasos, costos, clima...) es el
dato real del archivo. Por eso se mira el volumen mensual (que sí depende del calendario simulado)
y el % de entregas con retraso (que, en estos datos, no debería depender de la fecha).

Pasos: 1 cargar y poner la fecha como índice · 2 resample mensual · 3 media móvil (rolling) ·
4 gráfica · 5 interpretación (se escribe en salidas/interpretacion.txt y en el README).

Uso:  python serie_temporal.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
CSV = AQUI.parent.parent / "10-week" / "02-optional-activity" / "salidas" / "Delivery_Logistics_clean.csv"
SALIDAS = AQUI / "salidas"
SEMILLA = 11
TEAL, NARANJA, GRIS = "#0b6e75", "#c4650a", "#9aa5ad"
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

# 1. CARGAR: datos reales + fecha simulada como índice ------------------------------------------
df = pd.read_csv(CSV)
df["tarde"] = df["delivery_status"] != "delivered"          # retrasada o fallida (igual que semana 10)

dias = pd.date_range("2024-01-01", "2025-12-31", freq="D")
t = np.arange(len(dias))
peso = (1 + 0.0007 * t                                     # tendencia suave al alza
        + np.where(dias.month.isin([11, 12]), 0.35, 0)     # temporada alta
        + np.where(dias.month.isin([1, 2]), -0.15, 0)      # temporada baja
        - np.where(dias.dayofweek == 6, 0.5, 0))           # menos entregas los domingos
rng = np.random.default_rng(SEMILLA)
df["fecha"] = rng.choice(dias, size=len(df), p=peso / peso.sum())
df = df.set_index("fecha").sort_index()
print(f"Entregas: {len(df):,} | {df.index.min().date()} a {df.index.max().date()}")

# 2. AGREGAR POR MES con resample ----------------------------------------------------------------
mensual = df.resample("MS").agg(entregas=("delivery_id", "size"), tardias=("tarde", "sum"),
                                costo_total=("delivery_cost", "sum"))
mensual["pct_tardias"] = 100 * mensual["tardias"] / mensual["entregas"]

# 3. MEDIA MÓVIL de 3 meses con rolling ----------------------------------------------------------
mensual["entregas_mm3"] = mensual["entregas"].rolling(3).mean()
mensual["pct_tardias_mm3"] = mensual["pct_tardias"].rolling(3).mean()
SALIDAS.mkdir(exist_ok=True)
mensual.round(2).to_csv(SALIDAS / "serie_mensual.csv")

# 5. Cifras para la interpretación -------------------------------------------------------------
x = np.arange(len(mensual))
pend = np.polyfit(x, mensual["entregas"], 1)[0]
alto = mensual["entregas"].nlargest(3).index
bajo = mensual["entregas"].nsmallest(3).index
prom_nd = mensual[mensual.index.month.isin([11, 12])]["entregas"].mean()
prom_resto = mensual[~mensual.index.month.isin([11, 12])]["entregas"].mean()
r = mensual["pct_tardias"]
m = lambda ts: ", ".join(f"{MESES[i.month-1]}-{i.year}" for i in sorted(ts))
fmt = lambda v, d=1: f"{v:.{d}f}".replace(".", ",")
texto = (
    f"El volumen mensual sube en promedio {fmt(pend)} entregas por mes (tendencia al alza) y tiene una temporada alta clara: "
    f"nov-dic promedian {fmt(prom_nd, 0)} entregas frente a {fmt(prom_resto, 0)} en el resto del año; los tres meses más altos son {m(alto)} y los más bajos {m(bajo)}. "
    f"El % de entregas tardías casi no se mueve (entre {fmt(r.min())} % y {fmt(r.max())} %, media {fmt(r.mean())} %): no hay estacionalidad en el retraso. "
    "Ojo: las fechas son simuladas, así que la tendencia y la temporada son las que se pusieron a propósito; lo que se demuestra es el método."
)
(SALIDAS / "interpretacion.txt").write_text(texto + "\n", encoding="utf-8")
print(texto)

# 4. GRÁFICA: serie + media móvil ---------------------------------------------------------------
fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True, gridspec_kw={"height_ratios": [1.6, 1]})
a1.plot(mensual.index, mensual["entregas"], marker="o", color=GRIS, lw=1.6, label="Entregas por mes")
a1.plot(mensual.index, mensual["entregas_mm3"], color=TEAL, lw=3, label="Media móvil de 3 meses")
for ts in mensual.index[mensual.index.month.isin([11, 12])]:
    a1.axvspan(ts, ts + pd.offsets.MonthEnd(0), color=NARANJA, alpha=0.12, lw=0)
a1.set_ylabel("Entregas"); a1.set_ylim(0, mensual["entregas"].max() * 1.2)
a1.set_title("El volumen de entregas sube con el tiempo y se dispara en nov-dic (fechas simuladas)", loc="left", fontweight="bold", fontsize=12)
a1.legend(frameon=False, loc="upper left", ncol=2)
a2.plot(mensual.index, mensual["pct_tardias"], marker="o", color=GRIS, lw=1.6, label="% tardías por mes")
a2.plot(mensual.index, mensual["pct_tardias_mm3"], color=NARANJA, lw=3, label="Media móvil de 3 meses")
a2.set_ylim(0, 50); a2.set_ylabel("% retrasadas o fallidas")
a2.set_title(f"El % de entregas tardías se mantiene cerca de {fmt(r.mean(), 0)} % todo el periodo", loc="left", fontweight="bold", fontsize=12)
a2.legend(frameon=False, loc="lower left", ncol=2)
a2.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
a2.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{MESES[mdates.num2date(v).month-1]}\n{mdates.num2date(v).year}"))
for a in (a1, a2):
    a.spines[["top", "right"]].set_visible(False); a.grid(axis="y", alpha=0.25)
fig.text(0.01, 0.005, "Fuente: Delivery_Logistics limpio (25 000 entregas); calendario 2024-2025 simulado, semilla 11.", fontsize=8, color="#555")
fig.tight_layout(rect=(0, 0.02, 1, 1))
fig.savefig(AQUI / "serie_temporal.png", dpi=150)
print("Gráfica: serie_temporal.png")
