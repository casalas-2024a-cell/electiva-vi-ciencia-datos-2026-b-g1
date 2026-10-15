"""Semana 8 - Dibuja el pipeline ETL de logística de entregas (genera pipeline_etl.png).

Autora: Camila Alejandra Salas Gracia (casalas-2024a-cell)
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch

AQUI = Path(__file__).resolve().parent
BATCH = "#0b6e75"
STREAM = "#c4650a"
GRIS = "#444444"

COLUMNAS = ["1. FUENTES", "2. EXTRAER", "3. TRANSFORMAR", "4. CARGAR", "5. BI"]
X = [0.3, 3.9, 7.5, 11.1, 14.7]
ANCHO, ALTO = 3.1, 1.5
# filas: (titulo, color, [texto por columna])
FILAS = [
    ("STREAMING (propuesto)", STREAM, 7.6, [
        "Rastreo GPS del vehículo\neventos de posición\ncada pocos segundos",
        "Apache Kafka\ntópico\n«eventos_ruta»",
        "Python (consumidor)\nalerta: tiempo en ruta\nsupera el plazo prometido",
        "PostgreSQL\ntabla «alertas»",
    ]),
    ("BATCH (implementado)", BATCH, 5.5, [
        "Registro de entregas\nCSV (Delivery_Logistics)\n25 000 filas",
        "Python: pandas.read_csv\ncarga del archivo\ncerrado (diaria)",
        "pandas (limpieza.py)\nID, tiempos, tipos,\nmarcas de valores topados",
        "SQLite (clase)\n→ PostgreSQL (producción)\nmodelo normalizado",
    ]),
    ("BATCH (opcional)", BATCH, 3.4, [
        "API Frankfurter\ntipo de cambio\nUSD → INR (JSON)",
        "Python: requests\nconsulta diaria",
        "pandas / dbt\nconvertir el costo\na dólares",
        "Misma base SQL\ntabla «tipo_cambio»",
    ]),
]


def caja(ax, x, y, texto, color, ancho=ANCHO, alto=ALTO, rell="white"):
    ax.add_patch(FancyBboxPatch((x, y), ancho, alto, boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc=rell, ec=color, lw=2, zorder=2))
    ax.text(x + ancho / 2, y + alto / 2, texto, ha="center", va="center",
            fontsize=8.6, color="#111", zorder=3, linespacing=1.35)


def flecha(ax, x0, y0, x1, y1, color=GRIS):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=14,
                                 lw=1.8, color=color, zorder=1))


def main():
    fig, ax = plt.subplots(figsize=(18.8, 8.6))
    ax.set_xlim(0, 18.8)
    ax.set_ylim(1.0, 10.3)
    ax.axis("off")

    for x, c in zip(X, COLUMNAS):
        ax.text(x + ANCHO / 2, 9.75, c, ha="center", fontsize=11, fontweight="bold", color=GRIS)

    for titulo, color, y, textos in FILAS:
        ax.text(0.05, y + ALTO + 0.18, titulo, fontsize=8.5, fontweight="bold", color=color)
        for i, t in enumerate(textos):
            caja(ax, X[i], y, t, color)
            if i < len(textos) - 1:
                flecha(ax, X[i] + ANCHO, y + ALTO / 2, X[i + 1], y + ALTO / 2, color)

    # Caja de BI: una sola, recibe las tres filas
    caja(ax, X[4], 3.4, "Tablero BI\n(Power BI / Metabase)\n\n• Alertas en línea\n• % retrasadas por modo\n"
         "• Retrasos por clima\n• Costo por socio", GRIS, alto=5.7, rell="#f4f8f8")
    for _, color, y, _t in FILAS:
        flecha(ax, X[3] + ANCHO, y + ALTO / 2, X[4], y + ALTO / 2, color)

    # Orquestación
    ax.add_patch(FancyBboxPatch((0.3, 1.45), 17.5, 1.05, boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc="#eef3f3", ec=GRIS, lw=1.6, ls="--", zorder=1))
    ax.text(9.05, 1.97, "ORQUESTACIÓN Y MONITOREO · Apache Airflow: programa la carga diaria, "
            "reintenta si falla y avisa; el flujo en tiempo real corre continuo con Kafka",
            ha="center", va="center", fontsize=9.6, fontweight="bold", color=GRIS)

    ax.legend(handles=[Patch(fc="white", ec=BATCH, lw=2, label="Batch (por lotes)"),
                       Patch(fc="white", ec=STREAM, lw=2, label="Streaming (tiempo real)")],
              loc="lower left", bbox_to_anchor=(0.0, 0.2), ncol=2, frameon=False, fontsize=9)
    ax.text(9.4, 10.2, "Pipeline ETL · Logística de entregas · Camila Alejandra Salas Gracia",
            ha="center", fontsize=12.5, fontweight="bold")
    fig.savefig(AQUI / "pipeline_etl.png", dpi=140, bbox_inches="tight", facecolor="white")
    print("pipeline_etl.png generado")


if __name__ == "__main__":
    main()
