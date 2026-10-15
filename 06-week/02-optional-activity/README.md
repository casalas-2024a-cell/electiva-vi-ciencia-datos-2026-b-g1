# Semana 6 · ERD de mi caso: logística de entregas

```python
FULL_NAME   = "Camila Alejandra Salas Gracia"
GITHUB_USER = "casalas-2024a-cell"
```

Asignatura: Ciencia de Datos · Ingeniería Industrial · Corporación Universitaria del Huila (CORHUILA) · 2026-B · Corte 2.
Guía de la actividad: *Semana 6 · ERD de tu caso* (formativa, opcional).

## 1. Caso y datos

El caso es una **operación de logística de última milla**: cada fila de `Delivery_Logistics.csv` es una entrega con su socio logístico (9, como DHL, FedEx o Delhivery), tipo de paquete (9), vehículo (6), modo de entrega (4: *same day*, *express*, *two day*, *standard*), región (5), clima (6), distancia, peso, horas reales y esperadas, estado (*delivered*, *delayed*, *failed*), calificación del cliente y costo.

Son **25 000 entregas**. El archivo no trae fechas ni moneda. Los datos de partida los limpia la semana 9 (`../09-week/limpieza.py`); aquí se usa el resultado, `data/Delivery_Logistics_clean.csv`.

## 2. ERD

![ERD de logística de entregas](erd.png)

La versión en Mermaid está en [`erd.md`](erd.md) y el DDL en [`schema.sql`](schema.sql).

| Entidad | PK | FK | Qué guarda |
|---|---|---|---|
| `entrega` | `entrega_id` | `socio_id` + `region_id` (compuesta hacia `socio_region`), `paquete_id`, `vehiculo_id`, `modo_id`, `clima_id`, `estado_id` | El hecho: medidas de la entrega y marcas de calidad |
| `socio_logistico` | `socio_id` | – | Catálogo de socios |
| `region` | `region_id` | – | Catálogo de regiones |
| `socio_region` | (`socio_id`, `region_id`) | ambas | **Tabla intermedia N:M**: dónde opera cada socio |
| `tipo_paquete`, `tipo_vehiculo`, `modo_entrega`, `clima`, `estado_entrega` | `*_id` | – | Catálogos (un nombre, una fila) |

### Relaciones

- `socio_logistico` N:M `region`, resuelta con `socio_region`: un socio opera en muchas regiones y una región la atienden muchos socios.
- `socio_region` 1:N `entrega` mediante la **llave foránea compuesta** (`socio_id`, `region_id`): una entrega solo puede existir donde el socio tiene cobertura. Así la tabla intermedia no es decorativa: hace cumplir una regla.
- Cada catálogo 1:N `entrega`.

> **Aclaración honesta:** la cobertura (`socio_region`) no venía en el archivo; la **derivé de las entregas observadas** (los 9 socios × 5 regiones = 45 pares, todos presentes). Hoy no restringe nada porque todos los pares ocurren; solo empezaría a hacerlo si el negocio define una cobertura más estrecha.

## 3. ¿Relacional o NoSQL?

**Elegí el enfoque relacional (SQL).**

1. **Datos tabulares y de esquema fijo:** las 15 columnas originales son las mismas en las 25 000 filas.
2. **Consultas que cruzan dimensiones** (retrasos por socio, modo y clima) son `JOIN` + `GROUP BY`, el caso natural de SQL (Codd, 1970; Elmasri y Navathe, 2016).
3. **Integridad:** no puede haber una entrega con un estado, socio o región inexistentes, ni de un socio sin cobertura en la región.
4. **Volumen moderado** (25 000 filas): no hay problema de escala que justifique un motor de documentos.

**Cuándo cambiaría:** si se registraran eventos de seguimiento (GPS cada pocos segundos, por entrega), esa telemetría encajaría mejor en un almacén de series de tiempo o de documentos (MongoDB, s. f.), dejando las entregas y catálogos en SQL.

## 4. Normalización

El CSV es una tabla plana: el nombre del socio, región, vehículo… se repite en las 25 000 filas.

| Forma normal | Qué apliqué | Redundancia evitada |
|---|---|---|
| **1FN** | Una celda, un valor; las horas son enteros (no fechas de 1970) y `delayed` es 0/1. | Valores compuestos o mal tipados. |
| **2FN** | Cada atributo del catálogo depende solo de su código (`socio_id`, etc.), no de la entrega. | Repetir nombres 25 000 veces; 9 socios en vez de 25 000 textos. |
| **3FN** | `delayed` se puede deducir del estado (`delayed = estado ≠ delivered`, verificado en las 25 000 filas): **no se guarda**; vive en la vista `v_entrega`. | Una columna que podría contradecir al estado. |

**Una dependencia que no normalicé:** `tiempo_esperado_h` casi depende solo del modo (*same day* = 8 h, *two day* = 16 h, *standard* = 24 h), pero *express* toma valores de 2 a 7 h (y 8 filas con 8 h). Como no es una dependencia exacta, lo dejé en `entrega`.

## 5. Cómo reproducirlo

```bash
python build_db.py        # crea logistica.db y verifica las llaves foráneas
python dibujar_erd.py     # regenera erd.png
```

Resultado de la carga: `socio_logistico` 9 · `tipo_paquete` 9 · `tipo_vehiculo` 6 · `modo_entrega` 4 · `region` 5 · `clima` 6 · `estado_entrega` 3 · `socio_region` 45 · `entrega` 25 000, con **0 violaciones de llave foránea**.

## 6. Limitaciones

- El archivo no tiene fechas, por lo que no se puede modelar el tiempo (ni hacer series).
- La moneda del costo no está declarada.
- El `delivery_id` original estaba recortado en 500 filas; lo reconstruí con la posición de la fila y lo marqué (`id_reconstruido`). Ver semana 9.
- 510, 508 y 500 valores de distancia, peso y costo están **topados** (repetidos en el mínimo y el máximo); se marcan en `*_en_tope` y no se corrigen.
- Los datos parecen sintéticos (distribuciones casi uniformes), así que describen este archivo y no una operación real.

## 7. Referencias

Chen, P. P. (1976). The entity-relationship model—Toward a unified view of data. *ACM Transactions on Database Systems, 1*(1), 9–36.

CORHUILA. (2026). *Ciencia de Datos · Semana 6 · Modelamiento de datos* [Material de clase]. Corporación Universitaria del Huila. https://code-corhuila.github.io/ova-web/2026-B/ciencia-datos/06-week/01-session/

Codd, E. F. (1970). A relational model of data for large shared data banks. *Communications of the ACM, 13*(6), 377–387.

Date, C. J. (2019). *Database design and relational theory: Normal forms and all that jazz* (2.ª ed.). Apress.

Elmasri, R., y Navathe, S. B. (2016). *Fundamentals of database systems* (7.ª ed.). Pearson.

Mermaid. (s. f.). *Entity relationship diagrams*. https://mermaid.js.org/syntax/entityRelationshipDiagram.html

MongoDB. (s. f.). *Data modeling*. https://www.mongodb.com/docs/manual/data-modeling/

SQLite. (s. f.). *SQLite foreign key support*. https://www.sqlite.org/foreignkeys.html
