# Resultados de la semana 7

Generado por `queries.py`. Q1 y Q3 se verificaron contra su equivalente en pandas con `assert_frame_equal`.

## Q1

Filtra con `WHERE` (cuatro condiciones) las entregas express fallidas con tormenta y costo mayor que 1 400, usando la vista plana `v_entrega`.

```sql
-- Pregunta: ¿qué entregas express fallidas, en clima de tormenta, costaron más de 1 400?
SELECT entrega_id, socio, region, vehiculo, calificacion, costo
FROM v_entrega
WHERE estado = 'failed' AND clima = 'stormy' AND modo = 'express' AND costo > 1400
ORDER BY costo DESC, entrega_id;
```

Filas devueltas: 23

| entrega_id | socio | region | vehiculo | calificacion | costo |
|---|---|---|---|---|---|
| 23267 | xpressbees | west | ev van | 1 | 1632.7206 |
| 15538 | ecom express | south | ev van | 2 | 1606.75 |
| 15302 | amazon logistics | east | truck | 1 | 1601.98 |
| 13584 | ekart | north | van | 1 | 1591.04 |
| 2962 | dhl | east | van | 2 | 1581.94 |
| 18898 | ekart | east | truck | 1 | 1575.18 |
| 12412 | xpressbees | north | bike | 1 | 1573.18 |
| 6150 | amazon logistics | north | truck | 1 | 1560.84 |
| 12294 | xpressbees | north | ev bike | 1 | 1553.89 |
| 23679 | xpressbees | east | van | 1 | 1529.41 |
| 1094 | dhl | central | van | 1 | 1517.19 |
| 3362 | xpressbees | central | ev van | 2 | 1489.94 |
| 14240 | shadowfax | south | ev bike | 1 | 1479.1 |
| 3300 | amazon logistics | west | scooter | 2 | 1470.28 |
| 12584 | ecom express | west | ev van | 1 | 1434.96 |
| 16036 | xpressbees | north | ev bike | 2 | 1428.86 |
| 115 | fedex | central | van | 1 | 1427.53 |
| 23477 | amazon logistics | west | truck | 1 | 1426.7 |
| 8537 | fedex | south | scooter | 1 | 1426.11 |
| 3379 | amazon logistics | west | ev bike | 1 | 1424.96 |
| 16013 | dhl | east | truck | 1 | 1416.33 |
| 23026 | shadowfax | central | truck | 1 | 1415.13 |
| 17417 | shadowfax | north | scooter | 1 | 1402.31 |

## Q2

Une 5 tablas con `JOIN` para mostrar socio, región, vehículo y modo en lugar de llaves. Todas las filas del top 10 tienen el costo máximo del archivo (topado), así que el orden entre ellas es solo el desempate por `entrega_id`, no un ranking real.

```sql
-- Pregunta: ¿cuáles son las 10 entregas más costosas y a qué socio, región,
-- vehículo y modo corresponden? Desempate por entrega_id: muchas entregas
-- comparten el costo máximo porque el archivo lo trae topado (costo_en_tope = 1).
SELECT e.entrega_id,
       s.nombre  AS socio,
       r.nombre  AS region,
       v.nombre  AS vehiculo,
       m.nombre  AS modo,
       e.distancia_km,
       e.costo,
       e.costo_en_tope
FROM entrega AS e
JOIN socio_logistico AS s ON s.socio_id    = e.socio_id
JOIN region          AS r ON r.region_id   = e.region_id
JOIN tipo_vehiculo   AS v ON v.vehiculo_id = e.vehiculo_id
JOIN modo_entrega    AS m ON m.modo_id     = e.modo_id
ORDER BY e.costo DESC, e.entrega_id
LIMIT 10;
```

Filas devueltas: 10

| entrega_id | socio | region | vehiculo | modo | distancia_km | costo | costo_en_tope |
|---|---|---|---|---|---|---|---|
| 1 | delhivery | west | bike | same day | 297.0 | 1632.7206 | 1 |
| 27 | dhl | east | ev bike | express | 293.8 | 1632.7206 | 1 |
| 106 | amazon logistics | south | truck | same day | 295.5 | 1632.7206 | 1 |
| 348 | ecom express | central | ev van | two day | 297.1 | 1632.7206 | 1 |
| 357 | blue dart | north | ev bike | express | 293.3 | 1632.7206 | 1 |
| 412 | ekart | east | bike | standard | 297.1 | 1632.7206 | 1 |
| 480 | delhivery | east | ev van | same day | 297.1 | 1632.7206 | 1 |
| 509 | ekart | east | scooter | same day | 283.3 | 1632.7206 | 1 |
| 658 | shadowfax | south | bike | same day | 289.1 | 1632.7206 | 1 |
| 705 | blue dart | west | truck | express | 295.2 | 1632.7206 | 1 |

## Q3

Agrupa con `GROUP BY` por modo de entrega para comparar volumen, porcentaje retrasado, calificación y costo.

```sql
-- Pregunta: por modo de entrega, ¿cuántas entregas hay, qué porcentaje se
-- retrasó, y cuáles son la calificación y el costo promedio?
SELECT m.nombre                                                  AS modo,
       COUNT(*)                                                  AS entregas,
       ROUND(100.0 * SUM(es.nombre <> 'delivered') / COUNT(*), 1) AS pct_retrasadas,
       ROUND(AVG(e.calificacion), 2)                             AS calificacion_promedio,
       ROUND(AVG(e.costo), 1)                                    AS costo_promedio
FROM entrega AS e
JOIN modo_entrega   AS m  ON m.modo_id    = e.modo_id
JOIN estado_entrega AS es ON es.estado_id = e.estado_id
GROUP BY m.modo_id, m.nombre
ORDER BY pct_retrasadas DESC, m.nombre;
```

Filas devueltas: 4

| modo | entregas | pct_retrasadas | calificacion_promedio | costo_promedio |
|---|---|---|---|---|
| express | 6233 | 73.8 | 2.72 | 880.4 |
| same day | 6279 | 32.5 | 3.54 | 929.9 |
| two day | 6302 | 0.4 | 4.18 | 829.7 |
| standard | 6186 | 0.0 | 4.22 | 819.3 |
