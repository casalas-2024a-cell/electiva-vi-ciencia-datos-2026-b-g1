"""Semana 6 - Dibuja el ERD de logística de entregas (genera erd.png).

Autora: Camila Alejandra Salas Gracia (casalas-2024a-cell)
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

AQUI = Path(__file__).resolve().parent
H = 0.36
ENC, PK, FK = "#0b6e75", "#fff4c2", "#e2f1f3"

# nombre: (x, y_superior, ancho, [(clave, columna, tipo)])
def cat(pk, rot="TEXT UNIQUE"):
    return [("PK", pk, "INTEGER"), ("", "nombre", rot)]


TABLAS = {
    "socio_logistico": (0.4, 9.8, 3.4, cat("socio_id")),
    "socio_region": (0.4, 7.6, 3.4, [("PK,FK", "socio_id", "-> socio_logistico"),
                                      ("PK,FK", "region_id", "-> region")]),
    "region": (0.4, 5.4, 3.4, cat("region_id")),
    "entrega": (7.0, 9.8, 4.6, [
        ("PK", "entrega_id", "INTEGER"), ("FK", "socio_id", "-> socio_region"),
        ("FK", "region_id", "-> socio_region"), ("FK", "paquete_id", "-> tipo_paquete"),
        ("FK", "vehiculo_id", "-> tipo_vehiculo"), ("FK", "modo_id", "-> modo_entrega"),
        ("FK", "clima_id", "-> clima"), ("FK", "estado_id", "-> estado_entrega"),
        ("", "distancia_km", "REAL"), ("", "peso_kg", "REAL"), ("", "tiempo_entrega_h", "INTEGER"),
        ("", "tiempo_esperado_h", "INTEGER"), ("", "calificacion", "INTEGER 1-5"), ("", "costo", "REAL"),
        ("", "id_reconstruido", "0/1"), ("", "distancia_en_tope", "0/1"),
        ("", "peso_en_tope", "0/1"), ("", "costo_en_tope", "0/1")]),
    "tipo_paquete": (13.4, 9.8, 3.6, cat("paquete_id")),
    "tipo_vehiculo": (13.4, 8.3, 3.6, cat("vehiculo_id")),
    "modo_entrega": (13.4, 6.8, 3.6, cat("modo_id")),
    "clima": (13.4, 5.3, 3.6, cat("clima_id")),
    "estado_entrega": (13.4, 3.8, 3.6, cat("estado_id")),
}


def dibujar_tabla(ax, nombre, x, y, w, cols):
    alto = H * (len(cols) + 1)
    ax.add_patch(Rectangle((x, y - alto), w, alto, fc="white", ec="#333", lw=1.2, zorder=2))
    ax.add_patch(Rectangle((x, y - H), w, H, fc=ENC, ec="#333", lw=1.2, zorder=3))
    ax.text(x + w / 2, y - H / 2, nombre, color="white", ha="center", va="center",
            fontsize=10, fontweight="bold", zorder=4)
    for i, (clave, col, tipo) in enumerate(cols):
        yf = y - H * (i + 2)
        if clave:
            ax.add_patch(Rectangle((x, yf), w, H, fc=PK if "PK" in clave else FK, ec="none", zorder=3))
        ax.text(x + 0.08, yf + H / 2, clave, fontsize=7.5, va="center", color="#8a5a00",
                fontweight="bold", zorder=4)
        ax.text(x + 0.85, yf + H / 2, col, fontsize=8.5, va="center", zorder=4)
        ax.text(x + w - 0.08, yf + H / 2, tipo, fontsize=7, va="center", ha="right",
                color="#555", zorder=4)
    return {"x": x, "y": y, "w": w, "h": alto}


def main():
    fig, ax = plt.subplots(figsize=(17.4, 8.6))
    ax.set_xlim(0, 17.4)
    ax.set_ylim(2.0, 10.6)
    ax.axis("off")
    c = {n: dibujar_tabla(ax, n, *t) for n, t in TABLAS.items()}

    def pt(n, lado, f=0.5):
        b = c[n]
        return {"izq": (b["x"], b["y"] - b["h"] * f), "der": (b["x"] + b["w"], b["y"] - b["h"] * f),
                "arr": (b["x"] + b["w"] * f, b["y"]), "aba": (b["x"] + b["w"] * f, b["y"] - b["h"])}[lado]

    def unir(puntos, uno, muchos):
        """Línea por `puntos`; '1' junto al primer punto y 'N' junto al último."""
        ax.plot([p[0] for p in puntos], [p[1] for p in puntos], color="#333", lw=1.4, zorder=1)
        for (p, q, txt) in ((puntos[0], puntos[1], uno), (puntos[-1], puntos[-2], muchos)):
            dx, dy = q[0] - p[0], q[1] - p[1]
            n = max((dx ** 2 + dy ** 2) ** 0.5, 1e-9)
            ax.text(p[0] + dx / n * 0.28 - dy / n * 0.18, p[1] + dy / n * 0.28 + dx / n * 0.18, txt,
                    fontsize=10, fontweight="bold", color=ENC, ha="center", va="center")

    unir([pt("socio_logistico", "aba", 0.5), pt("socio_region", "arr", 0.5)], "1", "N")
    unir([pt("region", "arr", 0.5), pt("socio_region", "aba", 0.5)], "1", "N")
    unir([pt("socio_region", "der", 0.5), (5.4, pt("socio_region", "der", 0.5)[1]),
          (5.4, c["entrega"]["y"] - c["entrega"]["h"] * 0.17), pt("entrega", "izq", 0.17)], "1", "N")
    centros = {"tipo_paquete": 0.20, "tipo_vehiculo": 0.30, "modo_entrega": 0.40, "clima": 0.50,
               "estado_entrega": 0.60}
    for n, f in centros.items():
        unir([pt("entrega", "der", {"tipo_paquete": 0.19, "tipo_vehiculo": 0.30, "modo_entrega": 0.41,
                                    "clima": 0.52, "estado_entrega": 0.97}[n]), pt(n, "izq", 0.5)], "N", "1")
    ax.text(8.7, 10.45, "ERD · Logística de entregas (N:M socio ↔ región, resuelta con socio_region)",
            ha="center", fontsize=12, fontweight="bold")
    ax.text(8.7, 2.25, "PK = llave primaria   FK = llave foránea   1 → N = uno a muchos   "
            "entrega(socio_id, region_id) es una llave foránea compuesta hacia socio_region   "
            "Autora: Camila Alejandra Salas Gracia", ha="center", fontsize=8.2, color="#444")
    fig.savefig(AQUI / "erd.png", dpi=150, bbox_inches="tight", facecolor="white")
    print("erd.png generado")


if __name__ == "__main__":
    main()
