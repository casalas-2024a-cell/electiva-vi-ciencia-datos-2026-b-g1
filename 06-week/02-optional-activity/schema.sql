-- Semana 6 - Modelo relacional de la logística de entregas
-- Autora: Camila Alejandra Salas Gracia (casalas-2024a-cell)
-- Motor: SQLite 3 (las llaves foráneas se activan con PRAGMA foreign_keys = ON)

PRAGMA foreign_keys = ON;

-- Catálogos: cada nombre se guarda una sola vez -------------------------------
CREATE TABLE socio_logistico (socio_id   INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE);
CREATE TABLE tipo_paquete    (paquete_id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE);
CREATE TABLE tipo_vehiculo   (vehiculo_id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE);
CREATE TABLE modo_entrega    (modo_id    INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE);
CREATE TABLE region          (region_id  INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE);
CREATE TABLE clima           (clima_id   INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE);
-- delivered / delayed / failed
CREATE TABLE estado_entrega  (estado_id  INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE);

-- N:M socio <-> región: en qué regiones opera cada socio (cobertura).
-- Un socio cubre muchas regiones y una región la cubren muchos socios.
CREATE TABLE socio_region (
    socio_id   INTEGER NOT NULL REFERENCES socio_logistico(socio_id),
    region_id  INTEGER NOT NULL REFERENCES region(region_id),
    PRIMARY KEY (socio_id, region_id)
);

-- Entidad principal: una entrega -------------------------------------------------
CREATE TABLE entrega (
    entrega_id        INTEGER PRIMARY KEY,
    socio_id          INTEGER NOT NULL,
    region_id         INTEGER NOT NULL,
    paquete_id        INTEGER NOT NULL REFERENCES tipo_paquete(paquete_id),
    vehiculo_id       INTEGER NOT NULL REFERENCES tipo_vehiculo(vehiculo_id),
    modo_id           INTEGER NOT NULL REFERENCES modo_entrega(modo_id),
    clima_id          INTEGER NOT NULL REFERENCES clima(clima_id),
    estado_id         INTEGER NOT NULL REFERENCES estado_entrega(estado_id),
    distancia_km      REAL    NOT NULL CHECK (distancia_km > 0),
    peso_kg           REAL    NOT NULL CHECK (peso_kg > 0),
    tiempo_entrega_h  INTEGER NOT NULL CHECK (tiempo_entrega_h >= 0),
    tiempo_esperado_h INTEGER NOT NULL CHECK (tiempo_esperado_h > 0),
    calificacion      INTEGER NOT NULL CHECK (calificacion BETWEEN 1 AND 5),
    costo             REAL    NOT NULL CHECK (costo > 0),
    -- marcas de calidad que dejó la semana 9 (el valor real se perdió o se reconstruyó)
    id_reconstruido   INTEGER NOT NULL CHECK (id_reconstruido IN (0, 1)),
    distancia_en_tope INTEGER NOT NULL CHECK (distancia_en_tope IN (0, 1)),
    peso_en_tope      INTEGER NOT NULL CHECK (peso_en_tope IN (0, 1)),
    costo_en_tope     INTEGER NOT NULL CHECK (costo_en_tope IN (0, 1)),
    -- la entrega solo puede ocurrir donde el socio tiene cobertura
    FOREIGN KEY (socio_id, region_id) REFERENCES socio_region(socio_id, region_id)
);

CREATE INDEX idx_entrega_socio  ON entrega(socio_id);
CREATE INDEX idx_entrega_modo   ON entrega(modo_id);
CREATE INDEX idx_entrega_clima  ON entrega(clima_id);

-- Vista plana: lo que era el CSV. «retrasada» se deriva del estado (3FN: no se guarda dos veces).
CREATE VIEW v_entrega AS
SELECT e.entrega_id,
       s.nombre AS socio, r.nombre AS region, p.nombre AS paquete, v.nombre AS vehiculo,
       m.nombre AS modo, c.nombre AS clima, es.nombre AS estado,
       (es.nombre <> 'delivered') AS retrasada,
       e.distancia_km, e.peso_kg, e.tiempo_entrega_h, e.tiempo_esperado_h, e.calificacion, e.costo
FROM entrega e
JOIN socio_logistico s ON s.socio_id = e.socio_id
JOIN region          r ON r.region_id = e.region_id
JOIN tipo_paquete    p ON p.paquete_id = e.paquete_id
JOIN tipo_vehiculo   v ON v.vehiculo_id = e.vehiculo_id
JOIN modo_entrega    m ON m.modo_id = e.modo_id
JOIN clima           c ON c.clima_id = e.clima_id
JOIN estado_entrega es ON es.estado_id = e.estado_id;
