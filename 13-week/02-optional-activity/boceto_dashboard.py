"""Semana 13 - Diseña un dashboard (boceto).

Autora: Camila Alejandra Salas Gracia (casalas-2024a-cell)

Proceso elegido: entregas de última milla (dataset de logística de las semanas 6 a 10).
El boceto dibuja el tablero con gráficos pequeños calculados con los datos reales, para que cada
KPI tenga su gráfico acompañante, y muestra el panel de filtros a la izquierda.

Uso:  python boceto_dashboard.py     # necesita la carpeta 10-week al lado
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import pandas as pd

AQUI = Path(__file__).resolve().parent
CSV = AQUI.parent.parent / "10-week" / "02-optional-activity" / "salidas" / "Delivery_Logistics_clean.csv"
TEAL, NARANJA, GRIS, OSCURO = "#0b6e75", "#c4650a", "#aab4bb", "#1f2d36"
ES_CLIMA = {"stormy": "Tormenta", "rainy": "Lluvia", "foggy": "Niebla", "clear": "Despejado", "hot": "Calor", "cold": "Frío"}
ES_MODO = {"express": "Express", "same day": "Same day", "two day": "Two day", "standard": "Standard"}
fmt = lambda v, d=1: f"{v:.{d}f}".replace(".", ",")

d = pd.read_csv(CSV)
d["tarde"] = d["delivery_status"] != "delivered"
d["fallida"] = d["delivery_status"] == "failed"
KPI = {"a_tiempo": 100 * (1 - d["tarde"].mean()), "calif": d["delivery_rating"].mean(), "fallidas": 100 * d["fallida"].mean()}
print({k: round(v, 2) for k, v in KPI.items()})

fig = plt.figure(figsize=(16, 9), facecolor="white")
gs = fig.add_gridspec(3, 4, width_ratios=[0.8, 1.4, 1.4, 1.4], height_ratios=[0.55, 2.4, 0.15], hspace=0.45, wspace=0.35,
                      left=0.02, right=0.985, top=0.9, bottom=0.07)
fig.text(0.02, 0.955, "BOCETO · Tablero de entregas de última milla", fontsize=17, fontweight="bold", color=OSCURO)
fig.text(0.02, 0.925, "Camila Alejandra Salas Gracia · datos de ejemplo: Delivery_Logistics (25 000 entregas)", fontsize=10, color="#555")

# --- Panel de filtros (izquierda) ---
ax = fig.add_subplot(gs[:, 0]); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.03", fc="#f3f6f7", ec=GRIS))
ax.text(0.08, 0.95, "FILTROS", fontsize=12, fontweight="bold", color=OSCURO)
for i, (nombre, ej) in enumerate([("Región", "todas (5)"), ("Socio logístico", "todos (9)"), ("Modo de entrega", "todos (4)"),
                                  ("Clima", "todos (6)"), ("Tipo de vehículo", "todos (6)"), ("Tipo de paquete", "todos (9)")]):
    y = 0.84 - i * 0.135
    ax.text(0.08, y, nombre, fontsize=10, color=OSCURO)
    ax.add_patch(FancyBboxPatch((0.08, y - 0.07), 0.84, 0.05, boxstyle="round,pad=0,rounding_size=0.01", fc="white", ec=GRIS))
    ax.text(0.12, y - 0.055, ej + "  ▾", fontsize=9, color="#555")
ax.text(0.08, 0.02, "Fecha: solo si el dato la trae", fontsize=8, color="#555")

# --- Fila de KPI (arriba) ---
tarjetas = [("1  ENTREGAS A TIEMPO", f"{fmt(KPI['a_tiempo'])} %", "Objetivo: ≥ 85 %", NARANJA),
            ("2  CALIFICACIÓN PROMEDIO", f"{fmt(KPI['calif'], 2)} / 5", "Objetivo: ≥ 4,0", NARANJA),
            ("3  ENTREGAS FALLIDAS", f"{fmt(KPI['fallidas'])} %", "Objetivo: ≤ 3 %", NARANJA)]
for j, (t, v, o, c) in enumerate(tarjetas):
    ax = fig.add_subplot(gs[0, j + 1]); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.05", fc="#f3f6f7", ec=GRIS))
    ax.text(0.05, 0.74, t, fontsize=10, color="#4a5a66"); ax.text(0.05, 0.2, v, fontsize=24, fontweight="bold", color=c)
    ax.text(0.95, 0.24, o, fontsize=10, color="#4a5a66", ha="right")

# --- Gráfico del KPI 1: mapa de calor modo x clima ---
ax = fig.add_subplot(gs[1, 1])
orden_modo = ["express", "same day", "two day", "standard"]; orden_clima = ["stormy", "rainy", "foggy", "clear", "hot", "cold"]
m = (100 * d.pivot_table(index="delivery_mode", columns="weather_condition", values="tarde", aggfunc="mean")).loc[orden_modo, orden_clima]
im = ax.imshow(m.values, cmap="Oranges", vmin=0, vmax=100, aspect="auto")
ax.set_xticks(range(6), [ES_CLIMA[c] for c in orden_clima], fontsize=8, rotation=35); ax.set_yticks(range(4), [ES_MODO[c] for c in orden_modo], fontsize=9)
for (i, j), v in __import__("numpy").ndenumerate(m.values):
    ax.text(j, i, fmt(v, 0), ha="center", va="center", fontsize=9, color="white" if v > 60 else OSCURO)
ax.set_title("1 · Los retrasos se concentran en\nexpress y same day con clima adverso", loc="left", fontsize=10.5, fontweight="bold", color=OSCURO)
ax.set_xlabel("% de entregas retrasadas o fallidas", fontsize=8)

# --- Gráfico del KPI 2: calificación por clima ---
ax = fig.add_subplot(gs[1, 2])
r = d.groupby("weather_condition")["delivery_rating"].mean().loc[orden_clima[::-1]]
ax.barh([ES_CLIMA[c] for c in r.index], r.values, color=[NARANJA if c in ("stormy", "rainy", "foggy") else GRIS for c in r.index])
for i, v in enumerate(r.values): ax.text(v - 0.08, i, fmt(v, 2), va="center", ha="right", fontsize=9, color="white")
ax.set_xlim(0, 5); ax.axvline(4, color=OSCURO, ls="--", lw=1); ax.text(4.05, 5.45, "obj. 4,0", fontsize=8)
ax.set_title("2 · La calificación cae con\ntormenta y lluvia", loc="left", fontsize=10.5, fontweight="bold", color=OSCURO)
ax.spines[["top", "right"]].set_visible(False)

# --- Gráfico del KPI 3: % fallidas por clima ---
ax = fig.add_subplot(gs[1, 3])
f = (100 * d.groupby("weather_condition")["fallida"].mean()).loc[orden_clima[::-1]]
ax.barh([ES_CLIMA[c] for c in f.index], f.values, color=[NARANJA if c in ("stormy", "rainy", "foggy") else GRIS for c in f.index])
for i, v in enumerate(f.values): ax.text(v + 0.1, i, fmt(v) + " %", va="center", fontsize=8)
ax.set_xlim(0, 11); ax.axvline(3, color=OSCURO, ls="--", lw=1); ax.text(3.1, 5.45, "obj. 3 %", fontsize=8)
ax.set_title("3 · Con tormenta se pierde casi\nel triple de entregas", loc="left", fontsize=10.5, fontweight="bold", color=OSCURO)
ax.spines[["top", "right"]].set_visible(False)

fig.text(0.215, 0.025, "Lectura: KPI arriba (qué tan bien vamos) → gráfico debajo de cada KPI (dónde está el problema) → filtros a la izquierda para segmentar.", fontsize=9, color="#555")
fig.savefig(AQUI / "boceto_dashboard.png", dpi=130)
print("Listo: boceto_dashboard.png")
