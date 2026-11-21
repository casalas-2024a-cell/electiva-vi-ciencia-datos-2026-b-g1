"""Semana 15 - Storytelling del proyecto final.

Autora: Camila Alejandra Salas Gracia (casalas-2024a-cell)

Genera las vistas del tablero con títulos que expresan una conclusión y la captura del gráfico clave.
Proyecto final: análisis de las entregas de última milla (pipeline de la semana 10).

Uso:  python vistas_storytelling.py     # necesita la carpeta 10-week al lado
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
CSV = AQUI.parent.parent / "10-week" / "02-optional-activity" / "salidas" / "Delivery_Logistics_clean.csv"
NARANJA, GRIS, OSCURO = "#c4650a", "#aab4bb", "#1f2d36"
ES_CLIMA = {"stormy": "Tormenta", "rainy": "Lluvia", "foggy": "Niebla", "clear": "Despejado", "hot": "Calor", "cold": "Frío"}
ES_MODO = {"express": "Express", "same day": "Same day", "two day": "Two day", "standard": "Standard"}
ADV = ("stormy", "rainy", "foggy")
fmt = lambda v, d=1: f"{v:.{d}f}".replace(".", ",")
miles = lambda v: f"{int(v):,}".replace(",", " ")

d = pd.read_csv(CSV)
d["tarde"] = d["delivery_status"] != "delivered"
d["fallida"] = d["delivery_status"] == "failed"
rapido = d["delivery_mode"].isin(["express", "same day"])
adverso = d["weather_condition"].isin(ADV)
R = {"tarde_total": 100 * d["tarde"].mean(), "tarde_rapido": 100 * d.loc[rapido, "tarde"].mean(),
     "tarde_rapido_adv": 100 * d.loc[rapido & adverso, "tarde"].mean(), "n_rapido_adv": int((rapido & adverso).sum()),
     "tarde_lentos": 100 * d.loc[~rapido, "tarde"].mean(), "tarde_exp_adv": 100 * d.loc[(d.delivery_mode == "express") & adverso, "tarde"].mean(),
     "tarde_sd_adv": 100 * d.loc[(d.delivery_mode == "same day") & adverso, "tarde"].mean(),
     "tarde_rapido_noadv": 100 * d.loc[rapido & ~adverso, "tarde"].mean(),
     "calif": d["delivery_rating"].mean(), "calif_a_tiempo": d.loc[~d["tarde"], "delivery_rating"].mean(), "calif_tarde": d.loc[d["tarde"], "delivery_rating"].mean(),
     "fallidas": 100 * d["fallida"].mean()}
print({k: round(float(v), 2) for k, v in R.items()})
orden_modo = ["express", "same day", "two day", "standard"]; orden_clima = ["stormy", "rainy", "foggy", "clear", "hot", "cold"]

# ---- Vista 1: KPI -------------------------------------------------------------------------------
fig, axs = plt.subplots(1, 3, figsize=(13, 3.6))
fig.suptitle(f"Una de cada {fmt(100 / R['tarde_total'], 0)} entregas llega tarde o falla, y los clientes lo castigan: {fmt(R['calif_tarde'], 1)} frente a {fmt(R['calif_a_tiempo'], 1)} estrellas",
             x=0.01, ha="left", fontsize=12.5, fontweight="bold", color=OSCURO)
for ax, (t, v, s) in zip(axs, [("Entregas retrasadas o fallidas", f"{fmt(R['tarde_total'])} %", "de 25 000 entregas"),
                               ("Calificación promedio", f"{fmt(R['calif'], 2)} / 5", f"a tiempo {fmt(R['calif_a_tiempo'], 2)} · tarde {fmt(R['calif_tarde'], 2)}"),
                               ("Entregas fallidas", f"{fmt(R['fallidas'])} %", "estado «failed»")]):
    ax.axis("off"); ax.add_patch(plt.Rectangle((0, 0), 1, 1, fc="#f3f6f7", ec=GRIS, transform=ax.transAxes))
    ax.text(0.07, 0.72, t, fontsize=11, color="#4a5a66", transform=ax.transAxes)
    ax.text(0.07, 0.35, v, fontsize=28, fontweight="bold", color=NARANJA, transform=ax.transAxes)
    ax.text(0.07, 0.12, s, fontsize=10, color="#4a5a66", transform=ax.transAxes)
fig.tight_layout(rect=(0, 0, 1, 0.85)); fig.savefig(AQUI / "vista_1_kpis.png", dpi=150); plt.close(fig)

# ---- Vista 2 = gráfico clave: mapa de calor modo x clima --------------------------------------------
m = (100 * d.pivot_table(index="delivery_mode", columns="weather_condition", values="tarde", aggfunc="mean")).loc[orden_modo, orden_clima]
fig, ax = plt.subplots(figsize=(9.5, 5))
ax.imshow(m.values, cmap="Oranges", vmin=0, vmax=100, aspect="auto")
ax.set_xticks(range(6), [ES_CLIMA[c] for c in orden_clima], fontsize=11); ax.set_yticks(range(4), [ES_MODO[c] for c in orden_modo], fontsize=11)
for (i, j), v in np.ndenumerate(m.values):
    ax.text(j, i, f"{fmt(v, 0)} %", ha="center", va="center", fontsize=11, fontweight="bold", color="white" if v > 60 else OSCURO)
ax.set_xlabel("Clima de la entrega", fontsize=10); ax.tick_params(length=0)
for s in ax.spines.values(): s.set_visible(False)
fig.suptitle(f"Con lluvia, tormenta o niebla, {fmt(R['tarde_exp_adv'], 0)} % de las entregas express llegan tarde y {fmt(R['tarde_sd_adv'], 0)} % de las same day",
             x=0.01, ha="left", fontsize=12.5, fontweight="bold", color=OSCURO)
fig.text(0.01, 0.01, "% de entregas retrasadas o fallidas por modo de entrega y clima. Fuente: Delivery_Logistics limpio (25 000 entregas).", fontsize=8, color="#555")
fig.tight_layout(rect=(0, 0.03, 1, 0.93)); fig.savefig(AQUI / "captura_grafico_clave.png", dpi=150); plt.close(fig)

# ---- Vista 3: calificación y fallidas por clima -------------------------------------------------------
cal = d.groupby("weather_condition")["delivery_rating"].mean().loc[orden_clima[::-1]]
fal = (100 * d.groupby("weather_condition")["fallida"].mean()).loc[orden_clima[::-1]]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.6))
for ax, serie, lim, txt in ((a1, cal, 5, lambda v: fmt(v, 2)), (a2, fal, 11, lambda v: fmt(v) + " %")):
    ax.barh([ES_CLIMA[c] for c in serie.index], serie.values, color=[NARANJA if c in ADV else GRIS for c in serie.index], height=0.65)
    for i, v in enumerate(serie.values): ax.text(v + lim * 0.015, i, txt(v), va="center", fontsize=9)
    ax.set_xlim(0, lim); ax.spines[["top", "right"]].set_visible(False)
a1.set_title(f"La calificación cae a {fmt(cal['stormy'], 2)} con tormenta", loc="left", fontsize=11.5, fontweight="bold", color=OSCURO)
a2.set_title(f"Con tormenta fallan {fmt(fal['stormy'], 1)} % de las entregas, casi el triple que sin clima adverso", loc="left", fontsize=11.5, fontweight="bold", color=OSCURO, wrap=True)
fig.tight_layout(); fig.savefig(AQUI / "vista_3_calificacion_fallidas.png", dpi=150); plt.close(fig)
print("Listo: vista_1_kpis.png, captura_grafico_clave.png, vista_3_calificacion_fallidas.png")
