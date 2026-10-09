SELECT
    ts AS "time",
    p_ac_kw AS "Potencia (kW)",
    irradiancia_wm2 AS "Irradiancia (W/m2)"
FROM silver.lectura_5min
WHERE $__timeFilter(ts)
  AND dispositivo_key = ${dispositivo:raw}
ORDER BY ts;

SELECT ROUND(
    100.0 * SUM(lecturas_validas) / NULLIF(SUM(lecturas_totales), 0),
    2
) AS "Datos válidos (%)"
FROM dwh.fact_energia_dia
WHERE $__timeFilter(fecha_key::timestamp)
  AND dispositivo_key = ${dispositivo:raw};

