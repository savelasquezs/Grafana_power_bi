CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS dwh;

CREATE TABLE IF NOT EXISTS dwh.dim_dispositivo (
    dispositivo_key integer PRIMARY KEY,
    nombre varchar(100) NOT NULL,
    tipo varchar(50) NOT NULL,
    potencia_nominal_kwp numeric(8, 2) NOT NULL CHECK (potencia_nominal_kwp > 0)
);

CREATE TABLE IF NOT EXISTS silver.lectura_5min (
    ts timestamp NOT NULL,
    dispositivo_key integer NOT NULL REFERENCES dwh.dim_dispositivo(dispositivo_key),
    p_ac_kw numeric(10, 3) NOT NULL CHECK (p_ac_kw BETWEEN 0 AND 5.5),
    irradiancia_wm2 numeric(10, 1) NOT NULL CHECK (irradiancia_wm2 BETWEEN 0 AND 1200),
    temp_modulo_c numeric(5, 1) NOT NULL CHECK (temp_modulo_c BETWEEN -20 AND 90),
    PRIMARY KEY (ts, dispositivo_key)
);

CREATE TABLE IF NOT EXISTS dwh.fact_energia_dia (
    fecha_key date NOT NULL,
    dispositivo_key integer NOT NULL REFERENCES dwh.dim_dispositivo(dispositivo_key),
    energia_kwh numeric(12, 3) NOT NULL CHECK (energia_kwh >= 0),
    pct_datos_validos numeric(5, 2) NOT NULL CHECK (pct_datos_validos BETWEEN 0 AND 100),
    lecturas_validas integer NOT NULL CHECK (lecturas_validas >= 0),
    lecturas_totales integer NOT NULL CHECK (lecturas_totales >= lecturas_validas),
    PRIMARY KEY (fecha_key, dispositivo_key)
);

