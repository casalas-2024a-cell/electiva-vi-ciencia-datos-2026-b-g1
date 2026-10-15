| Métrica | Antes | Después |
|---|---:|---:|
| Filas | 25 000 | 25 000 |
| Columnas | 15 | 19 |
| Filas duplicadas exactas | 0 | 0 |
| Celdas nulas | 0 | 0 |
| `delivery_id` repetidos | 498 | 0 |
| `delivery_id` distintos (filas = 25 000) | 24 502 | 25 000 |
| `delivery_id` no enteros (p. ej. `250.99`) | 500 | 0 |
| Columnas de tiempo guardadas como fecha de 1970 (de 2) | 2 | 0 |

`delivery_id` reconstruido en 500 filas (marcadas en `id_reconstruido`). Valores topados marcados (no corregidos): `distancia_en_tope`=510, `peso_en_tope`=508, `costo_en_tope`=500.

Inconsistencias detectadas y **no** corregidas: `delayed_pero_dentro_del_plazo`=1203, `fallidas_con_tiempo_de_entrega`=1328, `express_con_plazo_8h`=8, `entregadas_fuera_de_plazo`=0.
