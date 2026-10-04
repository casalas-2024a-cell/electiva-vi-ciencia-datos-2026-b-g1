-- Modelo relacional derivado del ERD (SQLite).
-- Seis tablas de catálogo (lado "1") y una tabla de hechos DELIVERY (lado "N").

PRAGMA foreign_keys = ON;

CREATE TABLE delivery_partner (
    partner_id   INTEGER PRIMARY KEY,
    partner_name TEXT NOT NULL UNIQUE
);

CREATE TABLE vehicle_type (
    vehicle_type_id INTEGER PRIMARY KEY,
    vehicle_name    TEXT NOT NULL UNIQUE
);

CREATE TABLE package_type (
    package_type_id INTEGER PRIMARY KEY,
    package_name    TEXT NOT NULL UNIQUE
);

CREATE TABLE delivery_mode (
    mode_id   INTEGER PRIMARY KEY,
    mode_name TEXT NOT NULL UNIQUE
);

CREATE TABLE region (
    region_id   INTEGER PRIMARY KEY,
    region_name TEXT NOT NULL UNIQUE
);

CREATE TABLE weather_condition (
    weather_id     INTEGER PRIMARY KEY,
    condition_name TEXT NOT NULL UNIQUE
);

CREATE TABLE delivery (
    delivery_id         INTEGER PRIMARY KEY,
    partner_id          INTEGER NOT NULL REFERENCES delivery_partner(partner_id),
    vehicle_type_id     INTEGER NOT NULL REFERENCES vehicle_type(vehicle_type_id),
    package_type_id     INTEGER NOT NULL REFERENCES package_type(package_type_id),
    mode_id             INTEGER NOT NULL REFERENCES delivery_mode(mode_id),
    region_id           INTEGER NOT NULL REFERENCES region(region_id),
    weather_id          INTEGER NOT NULL REFERENCES weather_condition(weather_id),
    distance_km         REAL    NOT NULL CHECK (distance_km > 0),
    package_weight_kg   REAL    NOT NULL CHECK (package_weight_kg > 0),
    delivery_time_hours INTEGER NOT NULL CHECK (delivery_time_hours >= 0),
    expected_time_hours INTEGER NOT NULL CHECK (expected_time_hours > 0),
    is_delayed          INTEGER NOT NULL CHECK (is_delayed IN (0, 1)),
    delivery_status     TEXT    NOT NULL CHECK (delivery_status IN ('delivered', 'delayed', 'failed')),
    delivery_rating     INTEGER NOT NULL CHECK (delivery_rating BETWEEN 1 AND 5),
    delivery_cost       REAL    NOT NULL CHECK (delivery_cost >= 0)
);

CREATE INDEX idx_delivery_weather ON delivery(weather_id);
CREATE INDEX idx_delivery_partner ON delivery(partner_id);
