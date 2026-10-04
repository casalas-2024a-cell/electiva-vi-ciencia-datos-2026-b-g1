# Reporte de limpieza — antes / después

## Métricas de calidad

| métrica | antes | después |
|---|---|---|
| filas | 25000 | 25000 |
| columnas | 15 | 17 |
| nulos_totales | 0 | 0 |
| filas_duplicadas_exactas | 0 | 0 |
| filas_duplicadas_sin_id | 0 | 0 |
| delivery_id_valores_repetidos | 498 | 0 |
| delivery_id_no_enteros | 500 | 0 |
| columnas_tiempo_como_fecha_1970 | delivery_time_hours, expected_time_hours | ninguna |
| celdas_categoricas_sin_normalizar | 34789 | 0 |
| delayed_tipo | str | bool |
| decimales_maximos_delivery_cost | 4 | 2 |
| memoria_MB | 16.0 | 1.13 |


## Tipos de dato por columna

| columna | tipo_antes | tipo_después |
|---|---|---|
| delivery_id | float64 | int32 |
| delivery_partner | str | category |
| package_type | str | category |
| vehicle_type | str | category |
| delivery_mode | str | category |
| region | str | category |
| weather_condition | str | category |
| distance_km | float64 | float64 |
| package_weight_kg | float64 | float64 |
| delivery_time_hours | str | int16 |
| expected_time_hours | str | int16 |
| delayed | str | (reemplazada por is_delayed: bool) |
| delivery_status | str | category |
| delivery_rating | int64 | int8 |
| delivery_cost | float64 | float64 |
| delay_hours | — | int16 |
| boundary_value_flag | — | bool |


## Pasos aplicados

1. Texto normalizado: strip + minúsculas + snake_case (p. ej. 'blue dart' -> 'blue_dart', 'ev van' -> 'ev_van').
2. Nulos antes: 0 en total. Filas eliminadas por nulos en columnas clave: 0. Regla de imputación (mediana en numéricas, 'unknown' en categóricas) implementada; se aplica solo si hay nulos.
3. Duplicados eliminados (ignorando delivery_id): 0.
4. delivery_id: 500 filas con ID no entero/repetido (250.99 y 24750.01); reconstruido como 1..N según el orden del archivo (verificado: los IDs sanos coinciden con posición+1).
5. Tiempos (delivery_time_hours, expected_time_hours): venían como fecha '1970-01-01 00:00:00.00000000N'; el N son las horas -> convertidos a entero.
6. Tipos: delayed yes/no -> bool (is_delayed); rating -> int8; categóricas -> category; delivery_id -> int32.
7. Redondeo: delivery_cost a 2 decimales (había hasta 4), distance_km a 1, package_weight_kg a 2.
8. Valores amontonados en el mínimo/máximo de distancia, peso o costo: 1370 filas marcadas en boundary_value_flag (no eliminadas).
9. Consistencia: 963 entregas con estado 'delayed' pero tiempo real <= esperado (se conservan; el estado del dataset es la etiqueta oficial). Además is_delayed=True incluye las entregas 'failed'.

