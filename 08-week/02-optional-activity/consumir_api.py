"""Semana 8 - Consume una API pública con `requests` y muestra 3 registros.

Autora: Camila Alejandra Salas Gracia (casalas-2024a-cell)

API: Frankfurter (tipos de cambio del Banco Central Europeo, pública y sin llave).
Se pide USD -> INR de tres días hábiles. Es un ejemplo de enriquecimiento: el costo de
`Delivery_Logistics.csv` no declara moneda, y si fuera rupias (supuesto: varios socios
son operadores de India) este tipo de cambio permitiría expresarlo en dólares.

Uso:
    python consumir_api.py

Si no hay conexión (o la API falla), el script usa la muestra guardada en
api_sample.json y lo avisa; así la actividad es reproducible sin internet.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import requests

AQUI = Path(__file__).resolve().parent
URL = "https://api.frankfurter.app/{desde}..{hasta}"


def extraer(desde: str, hasta: str) -> tuple[dict, str]:
    """E de ETL: pide los datos. Devuelve (json, origen)."""
    try:
        resp = requests.get(URL.format(desde=desde, hasta=hasta),
                            params={"from": "USD", "to": "INR"}, timeout=10)
        resp.raise_for_status()
        return resp.json(), "API en vivo"
    except requests.RequestException as err:
        print(f"[aviso] no se pudo consultar la API ({type(err).__name__}); "
              "uso la muestra guardada (api_sample.json).")
        muestra = json.loads((AQUI / "api_sample.json").read_text(encoding="utf-8"))
        return muestra, "muestra guardada"


def transformar(datos: dict) -> pd.DataFrame:
    """T de ETL: de JSON anidado (fecha -> moneda -> tasa) a tabla."""
    filas = [{"fecha": f, "base": datos["base"], "INR_por_USD": r["INR"]}
             for f, r in sorted(datos["rates"].items())]
    return pd.DataFrame(filas)


def main() -> None:
    datos, origen = extraer("2026-10-12", "2026-10-14")
    tabla = transformar(datos)
    print(f"Origen: {origen} | base: {datos['base']} | registros: {len(tabla)}")
    print("3 registros:")
    print(tabla.head(3).to_string(index=False))
    # L de ETL: se guarda el resultado para usarlo después
    tabla.head(3).to_csv(AQUI / "muestra_api_3_registros.csv", index=False)


if __name__ == "__main__":
    main()
