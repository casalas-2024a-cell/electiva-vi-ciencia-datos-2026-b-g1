# Semana 7 · Consultas SQL y pandas

```python
FULL_NAME   = "Camila Alejandra Salas Gracia"
GITHUB_USER = "casalas-2024a-cell"
```

Asignatura: Ciencia de Datos · Ingeniería Industrial · CORHUILA · 2026-B · Corte 2.
Guía de la actividad: *Semana 7 · Herramientas y lenguajes (SQL, NoSQL, Python)* (formativa, opcional).

## Qué se entrega

| Archivo | Contenido |
|---|---|
| [`queries.sql`](queries.sql) | 3 consultas SQL: `WHERE`, `JOIN` y `GROUP BY`, cada una con su pregunta |
| [`queries.py`](queries.py) | Ejecuta las consultas sobre SQLite y reproduce en pandas el `GROUP BY` (y también el `WHERE`) |
| [`resultados.md`](resultados.md) | Salida completa de las tres consultas |

Las consultas se ejecutan sobre el modelo de la [semana 6](../06-week/README.md), con las 25 000 entregas del CSV limpio.

```bash
python queries.py    # necesita la carpeta 06-week al lado de esta
```

El script **falla si SQL y pandas no coinciden** (`assert_frame_equal`); con los datos entregados pasa sin diferencias.

## Qué responde cada consulta

### Q1 · `WHERE`: entregas express fallidas, con tormenta y costo alto

```sql
SELECT entrega_id, socio, region, vehiculo, calificacion, costo
FROM v_entrega
WHERE estado = 'failed' AND clima = 'stormy' AND modo = 'express' AND costo > 1400
ORDER BY costo DESC, entrega_id;
```

Devuelve **23 entregas**. Usa la vista `v_entrega` (el CSV plano reconstruido a partir de las tablas) para no repetir los `JOIN`. Casi todas tienen calificación 1 o 2, que es coherente con una entrega fallida.

### Q2 · `JOIN`: las 10 entregas más costosas

```sql
SELECT e.entrega_id, s.nombre AS socio, r.nombre AS region, v.nombre AS vehiculo,
       m.nombre AS modo, e.distancia_km, e.costo, e.costo_en_tope
FROM entrega AS e
JOIN socio_logistico AS s ON s.socio_id    = e.socio_id
JOIN region          AS r ON r.region_id   = e.region_id
JOIN tipo_vehiculo   AS v ON v.vehiculo_id = e.vehiculo_id
JOIN modo_entrega    AS m ON m.modo_id     = e.modo_id
ORDER BY e.costo DESC, e.entrega_id
LIMIT 10;
```

Une cinco tablas para ver nombres en lugar de llaves.

> **Ojo con este resultado:** las 10 filas cuestan exactamente **1 632,7206**. Ese valor aparece 250 veces: el archivo trae el costo **topado** en su máximo (y en 95,6674 en el mínimo). No es un ranking real: son entregas cuyo costo verdadero (probablemente mayor) se perdió; el desempate por `entrega_id` solo hace la salida reproducible. Por eso el modelo guarda `costo_en_tope`.

### Q3 · `GROUP BY`: volumen, retraso, calificación y costo por modo de entrega

```sql
SELECT m.nombre AS modo, COUNT(*) AS entregas,
       ROUND(100.0 * SUM(es.nombre <> 'delivered') / COUNT(*), 1) AS pct_retrasadas,
       ROUND(AVG(e.calificacion), 2) AS calificacion_promedio,
       ROUND(AVG(e.costo), 1) AS costo_promedio
FROM entrega AS e
JOIN modo_entrega   AS m  ON m.modo_id    = e.modo_id
JOIN estado_entrega AS es ON es.estado_id = e.estado_id
GROUP BY m.modo_id, m.nombre
ORDER BY pct_retrasadas DESC, m.nombre;
```

| modo | entregas | % retrasadas | calificación prom. | costo prom. |
|---|---:|---:|---:|---:|
| express | 6 233 | 73,8 | 2,72 | 880,4 |
| same day | 6 279 | 32,5 | 3,54 | 929,9 |
| two day | 6 302 | 0,4 | 4,18 | 829,7 |
| standard | 6 186 | 0,0 | 4,22 | 819,3 |

«Retrasada» incluye las entregas con estado `delayed` **y** `failed` (6 669 de 25 000).

**Cómo leerlo (importante):** el tiempo real de entrega es prácticamente el mismo en los cuatro modos (promedio de 6,2 a 6,3 horas). Lo que cambia es el **plazo prometido**: 8 h en *same day*, 16 h en *two day*, 24 h en *standard* y apenas 2 a 7 h en *express*. Por eso *express* parece muy retrasado y *standard* casi nunca: no es que *express* se mueva más lento, sino que promete menos tiempo del que la operación suele necesitar. El resultado describe cómo están definidos los plazos, no la calidad de cada servicio.

## Equivalente en pandas

```python
g = plano.groupby("delivery_mode")
p3 = pd.DataFrame({
    "entregas": g.size(),
    "pct_retrasadas": (100 * g["delayed"].mean()).round(1),
    "calificacion_promedio": g["delivery_rating"].mean().round(2),
    "costo_promedio": g["delivery_cost"].mean().round(1),
})
```

Es la misma agrupación sobre la tabla plana: `size()` equivale a `COUNT(*)` y la media de una columna booleana equivale a `SUM(condición) / COUNT(*)`.

## Limitaciones

- Una consulta compara promedios sin prueba de significancia; las diferencias grandes (como la de retraso por modo) no necesitan una, las pequeñas sí (ver semana 10).
- El costo no tiene moneda declarada.
- Los datos parecen sintéticos (distribuciones casi uniformes): describen el archivo, no una operación real.

## Referencias

CORHUILA. (2026). *Ciencia de Datos · Semana 7 · Herramientas y lenguajes (SQL, NoSQL, Python)* [Material de clase]. Corporación Universitaria del Huila. https://code-corhuila.github.io/ova-web/2026-B/ciencia-datos/07-week/01-session/

Elmasri, R., y Navathe, S. B. (2016). *Fundamentals of database systems* (7.ª ed.). Pearson.

McKinney, W. (2022). *Python for data analysis* (3.ª ed.). O'Reilly Media.

pandas. (s. f.). *Comparison with SQL*. https://pandas.pydata.org/docs/getting_started/comparison/comparison_with_sql.html

pandas. (s. f.). *Group by: split-apply-combine*. https://pandas.pydata.org/docs/user_guide/groupby.html

Python Software Foundation. (s. f.). *sqlite3 — DB-API 2.0 interface for SQLite databases*. https://docs.python.org/3/library/sqlite3.html

SQLite. (s. f.). *SQL as understood by SQLite*. https://www.sqlite.org/lang.html
