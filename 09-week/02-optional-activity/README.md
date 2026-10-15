# Semana 9 · Limpieza del dataset de logística de entregas

```python
FULL_NAME   = "Camila Alejandra Salas Gracia"
GITHUB_USER = "casalas-2024a-cell"
```

Asignatura: Ciencia de Datos · Ingeniería Industrial · CORHUILA · 2026-B · Corte 2.
Guía de la actividad: *Semana 9 · Transformación y calidad de datos* (formativa, opcional).

## Qué se entrega

| Archivo | Contenido |
|---|---|
| [`limpieza.py`](limpieza.py) | Script de limpieza en pandas (función `limpiar`) y generador del reporte antes/después |
| [`data/Delivery_Logistics.csv`](data/Delivery_Logistics.csv) | Dataset **original** (25 000 filas × 15 columnas) |
| [`data/Delivery_Logistics_clean.csv`](data/Delivery_Logistics_clean.csv) | Dataset **limpio** (25 000 filas × 19 columnas: 15 originales + 4 marcas de calidad) |
| [`reportes/antes_despues.md`](reportes/antes_despues.md) y [`.json`](reportes/antes_despues.json) | Evidencia antes/después |

```bash
python limpieza.py     # lee data/Delivery_Logistics.csv y regenera data/ y reportes/
```

**Decisión de diseño:** no se inventa ni se borra ningún dato. Lo que no se puede corregir se **marca** o se documenta.

## 1. Evidencia antes/después

| Métrica | Antes | Después |
|---|---:|---:|
| Filas | 25 000 | 25 000 |
| Columnas | 15 | 19 |
| Filas duplicadas exactas | 0 | 0 |
| Celdas nulas | 0 | 0 |
| `delivery_id` repetidos | 498 | 0 |
| `delivery_id` distintos (de 25 000 filas) | 24 502 | 25 000 |
| `delivery_id` no enteros (p. ej. `250.99`) | 500 | 0 |
| Columnas de tiempo guardadas como fecha de 1970 (de 2) | 2 | 0 |

Esta vez el archivo no trae nulos ni duplicados exactos: el problema está en cómo se guardaron los datos, no en que falten.

## 2. Problemas encontrados y cómo los traté

| # | Problema | Cómo lo detecté | Tratamiento |
|---|---|---|---|
| 1 | **`delivery_id` recortado**: 250 filas iniciales con `250.99` y 250 finales con `24750.01` (498 repetidos) | Un ID debería ser entero y único; los valores coinciden con los percentiles 1 y 99 de 1..25 000, es decir, se aplicó un tope por error | En las 24 500 filas intactas el ID coincide con la posición de la fila (verificado con `assert`); reconstruyo el ID con la posición y marco las 500 filas en `id_reconstruido` |
| 2 | **Horas guardadas como fecha**: `1970-01-01 00:00:00.000000008` significa 8 horas (las horas están en los nanosegundos) | Todas las celdas de las dos columnas empiezan con `1970-01-01` | Extraigo el número con una expresión regular y lo guardo como entero (2 columnas) |
| 3 | **Booleano como texto**: `delayed` = `yes`/`no` | Dos valores distintos | Convertido a `bool` |
| 4 | **Valores topados** en `distance_km`, `package_weight_kg` y `delivery_cost`: el mínimo y el máximo se repiten cientos de veces (p. ej. el costo `1632.7206` aparece 250 veces y `95.6674`, 250) | Frecuencia de los extremos frente a la del resto (máx. ~19) | **No se corrigen** (el valor real se perdió); se marcan en `distancia_en_tope` (510), `peso_en_tope` (508) y `costo_en_tope` (500) |
| 5 | **Coherencia entre `delayed` y `delivery_status`** | Tabulación cruzada | Se verifica con `assert`: `delayed = (estado ≠ delivered)` en las 25 000 filas. Sin cambios |

### Inconsistencias que detecté y **no** corregí

| Hallazgo | Filas | Por qué no lo toqué |
|---|---:|---|
| `delayed = yes` pero el tiempo real **no** supera el plazo esperado | 1 203 | No hay fuente para saber cuál de los dos campos es el correcto |
| Entregas `failed` con un tiempo de entrega registrado | 1 328 | Una entrega fallida no debería tener tiempo de entrega; no se sabe qué mide |
| Entregas `delivered` fuera de plazo | 0 | Es coherente: ninguna lo está |
| *Express* con plazo de 8 h (el resto de *express* va de 2 a 7 h) | 8 | Posible error, pero son 8 filas |

## 3. Dos dimensiones de calidad que mejoré

Dimensiones de la sesión de clase: completitud, exactitud, consistencia, unicidad y vigencia (Wang y Strong, 1996; ISO/IEC, 2008).

### a) Unicidad: de 24 502 a 25 000 identificadores distintos

Había 498 filas con un ID que ya existía, así que no se podía identificar una entrega de forma única (un `JOIN` por ID las habría multiplicado). Tras la reconstrucción cada fila tiene su propio ID y esa fila queda marcada. **Ojo:** esto es una reconstrucción razonada (el ID coincide con la posición en las 24 500 filas intactas), no una recuperación del dato original.

### b) Consistencia: representación coherente de tiempos y banderas

Dos columnas de horas parecían fechas de 1970 y no se podían promediar ni comparar de forma natural; ahora son enteros (promedio real ≈ 6,2 h, plazo promedio ≈ 13,1 h), `delayed` es booleano y el estado, el ID y los tipos pasan validaciones automáticas.

### Bonus: exactitud, hecha visible

La exactitud **no se pudo mejorar**: los ~500 valores topados en cada una de tres columnas siguen siendo imprecisos. Lo que sí se logró es que ya no pasen desapercibidos: cualquier análisis puede excluirlos con `*_en_tope`. Ejemplo: en un «top de costos», 250 entregas empatan en el máximo.

## 4. Limitaciones

- El archivo no tiene fechas ni moneda.
- La reconstrucción del ID se apoya en que el orden del archivo se conserva; si alguien reordenó filas, el ID reconstruido sería arbitrario (el ID original ya estaba perdido en esas 500 filas).
- Los datos parecen sintéticos (distribuciones casi uniformes de distancia y peso; el costo depende casi exclusivamente de la distancia, con correlación 0,99).

## 5. Referencias

CORHUILA. (2026). *Ciencia de Datos · Semana 9 · Transformación y calidad de datos* [Material de clase]. Corporación Universitaria del Huila. https://code-corhuila.github.io/ova-web/2026-B/ciencia-datos/09-week/01-session/

International Organization for Standardization & International Electrotechnical Commission. (2008). *ISO/IEC 25012:2008 Software engineering — Software product Quality Requirements and Evaluation (SQuaRE) — Data quality model*.

McKinney, W. (2022). *Python for data analysis* (3.ª ed.). O'Reilly Media.

pandas. (s. f.). *Working with missing data*. https://pandas.pydata.org/docs/user_guide/missing_data.html

Python Software Foundation. (s. f.). *re — Regular expression operations*. https://docs.python.org/3/library/re.html

Rahm, E., y Do, H. H. (2000). Data cleaning: Problems and current approaches. *IEEE Data Engineering Bulletin, 23*(4), 3–13.

Wang, R. Y., y Strong, D. M. (1996). Beyond accuracy: What data quality means to data consumers. *Journal of Management Information Systems, 12*(4), 5–33.

Wickham, H. (2014). Tidy data. *Journal of Statistical Software, 59*(10), 1–23.
