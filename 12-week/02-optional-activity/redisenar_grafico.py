"""Semana 12 - Rediseña un gráfico.

Autora: Camila Alejandra Salas Gracia (casalas-2024a-cell)

Se toma el resultado del análisis 1 de la semana 10 (% de entregas retrasadas por clima, solo modo
«same day») y se dibuja primero como un gráfico MAL HECHO (antes) y luego rediseñado (después).
Los números son los mismos en los dos gráficos y se calculan aquí desde el CSV limpio.

Uso:  python redisenar_grafico.py     # necesita la carpeta 10-week al lado
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

AQUI = Path(__file__).resolve().parent
CSV = AQUI.parent.parent / "10-week" / "02-optional-activity" / "salidas" / "Delivery_Logistics_clean.csv"
NARANJA, GRIS, OSCURO = "#c4650a", "#aab4bb", "#1f2d36"
ES = {"stormy": "Tormenta", "rainy": "Lluvia", "foggy": "Niebla", "clear": "Despejado", "hot": "Calor", "cold": "Frío"}
fmt = lambda v, d=1: f"{v:.{d}f}".replace(".", ",")

df = pd.read_csv(CSV)
sd = df[df["delivery_mode"] == "same day"]                       # mismo plazo prometido (8 h) para todos
pct = (100 * (sd["delivery_status"] != "delivered").groupby(sd["weather_condition"]).mean())
n = sd.groupby("weather_condition").size()
print(pct.round(1).sort_values(ascending=False).to_dict(), "| entregas same day:", len(sd))

# ---------------------------------------------------------------- ANTES: gráfico deficiente
orden_malo = ["clear", "cold", "foggy", "hot", "rainy", "stormy"]    # orden arbitrario (alfabético)
vals = [pct[c] for c in orden_malo]
fig, ax = plt.subplots(figsize=(7, 5.2))
ax.pie(vals, labels=[f"{ES[c]} {fmt(v)}" for c, v in zip(orden_malo, vals)],
       colors=["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff"],
       explode=[0.08] * 6, shadow=True, textprops={"fontsize": 10}, startangle=30)
fig.tight_layout()
fig.savefig(AQUI / "grafico_antes.png", dpi=150)
plt.close(fig)

# ---------------------------------------------------------------- DESPUÉS: rediseño
d = pct.sort_values()                                               # ordenado: se lee el ranking
adverso = d.index.isin(["stormy", "rainy", "foggy"])
fig, ax = plt.subplots(figsize=(8.2, 5.2))
bars = ax.barh([ES[c] for c in d.index], d.values, color=[NARANJA if a else GRIS for a in adverso], height=0.65)
for b, v in zip(bars, d.values):
    ax.text(v + 1, b.get_y() + b.get_height() / 2, f"{fmt(v)} %", va="center", fontsize=11, fontweight="bold", color=OSCURO)
ax.set_xlim(0, 80)                                                   # escala honesta: empieza en cero
ax.set_xlabel("Entregas «same day» retrasadas o fallidas (%)")
ax.spines[["top", "right"]].set_visible(False)
ax.tick_params(axis="y", length=0, labelsize=11)
fig.suptitle(f"Con tormenta, {fmt(pct['stormy'], 0)} % de las entregas del mismo día llegan tarde: {fmt(pct['stormy'] / pct['cold'], 0)} veces más que con frío",
             x=0.01, ha="left", fontsize=12, fontweight="bold", color=OSCURO)
miles = lambda v: f"{v:,}".replace(",", " ")
fig.text(0.01, 0.01, f"Clima adverso (naranja): tormenta, lluvia y niebla. Fuente: Delivery_Logistics limpio, solo modo same day ({miles(int(n.sum()))} entregas, "
         f"{miles(int(n.min()))} a {miles(int(n.max()))} por clima).", fontsize=8, color="#555")
fig.tight_layout(rect=(0, 0.04, 1, 0.94))
fig.savefig(AQUI / "grafico_despues.png", dpi=150)
print("Listo: grafico_antes.png y grafico_despues.png")
