-- Semana 7 - Consultas SQL sobre el modelo de logística de entregas
-- Autora: Camila Alejandra Salas Gracia (casalas-2024a-cell)
-- Base: SQLite, creada con 06-week/build_db.py a partir de Delivery_Logistics_clean.csv
-- El costo no tiene moneda declarada en el archivo.

-- [Q1] WHERE ---------------------------------------------------------------
-- Pregunta: ¿qué entregas express fallidas, en clima de tormenta, costaron más de 1 400?
SELECT entrega_id, socio, region, vehiculo, calificacion, costo
FROM v_entrega
WHERE estado = 'failed' AND clima = 'stormy' AND modo = 'express' AND costo > 1400
ORDER BY costo DESC, entrega_id;

-- [Q2] JOIN ----------------------------------------------------------------
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

-- [Q3] GROUP BY ------------------------------------------------------------
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
