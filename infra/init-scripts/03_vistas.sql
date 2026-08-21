CREATE OR REPLACE VIEW bronze_sensores AS
SELECT
    "time",
    entity_id,
    state,
    attributes
FROM ltss
WHERE entity_id IN (
    'sensor.sensor_temperatura_1_temperature',
    'sensor.sensor_temperatura_2_temperature',
    'sensor.sensor_temperatura_3_temperature',
    'sensor.sensor_temperatura_4_temperature',
    'sensor.sensor_temperatura_1_humidity',
    'sensor.sensor_temperatura_2_humidity',
    'sensor.sensor_temperatura_3_humidity',
    'sensor.sensor_temperatura_4_humidity',
    'sensor.sensor_temperatura_1_pressure',
    'sensor.sensor_temperatura_2_pressure',
    'sensor.sensor_temperatura_3_pressure',
    'sensor.sensor_temperatura_4_pressure',
    'binary_sensor.sensor_puerta_1_contact',
    'binary_sensor.sensor_ventana_1_contact',
    'binary_sensor.sensor_ventana_2_contact',
    'binary_sensor.sensor_ventana_3_contact',
    'binary_sensor.sensor_ventana_4_contact',
    'binary_sensor.sensor_ventana_5_contact',
    'binary_sensor.sensor_ventana_6_contact',
    'binary_sensor.sensor_ventana_7_contact',
    'binary_sensor.sensor_ventana_8_contact',
    'binary_sensor.sensor_ventana_9_contact',
    'binary_sensor.sensor_ventana_10_contact',
    'binary_sensor.sensor_ventana_11_contact',
    'binary_sensor.sensor_ventana_12_contact',
    'sensor.mislata_temperatura',
    'sensor.mislata_nubosidad',
    'sensor.mislata_humedad',
    'sensor.mislata_viento',
    'sensor.sun_solar_elevation',
    'sensor.sun_solar_azimuth'
);

CREATE OR REPLACE VIEW silver_sensores AS
SELECT
    "time",
    entity_id,
    CASE
        WHEN entity_id LIKE 'binary_sensor.%' THEN
            CASE WHEN state = 'on' THEN 1.0 WHEN state = 'off' THEN 0.0 END
        WHEN entity_id = 'sensor.sensor_temperatura_1_pressure'
            AND state ~ '^-?[0-9]+\.?[0-9]*$'
        THEN CAST(state AS DOUBLE PRECISION) * 33.8639
        WHEN state ~ '^-?[0-9]+\.?[0-9]*$'
        THEN CAST(state AS DOUBLE PRECISION)
    END AS state_numeric
FROM bronze_sensores
WHERE state IS NOT NULL
  AND state NOT IN ('unavailable', 'unknown', '');

CREATE OR REPLACE VIEW gold_features_horaria AS
SELECT
    hora AS fecha_hora_utc,
    temp_aula_1, temp_aula_2, temp_aula_3, temp_aula_4,
    COALESCE(temp_aula_1 + temp_aula_2 + temp_aula_3 + temp_aula_4, NULL)
        / NULLIF(
            (CASE WHEN temp_aula_1 IS NOT NULL THEN 1 ELSE 0 END) +
            (CASE WHEN temp_aula_2 IS NOT NULL THEN 1 ELSE 0 END) +
            (CASE WHEN temp_aula_3 IS NOT NULL THEN 1 ELSE 0 END) +
            (CASE WHEN temp_aula_4 IS NOT NULL THEN 1 ELSE 0 END), 0)
        AS temp_aula,
    hum_aula_1, hum_aula_2, hum_aula_3, hum_aula_4,
    COALESCE(hum_aula_1 + hum_aula_2 + hum_aula_3 + hum_aula_4, NULL)
        / NULLIF(
            (CASE WHEN hum_aula_1 IS NOT NULL THEN 1 ELSE 0 END) +
            (CASE WHEN hum_aula_2 IS NOT NULL THEN 1 ELSE 0 END) +
            (CASE WHEN hum_aula_3 IS NOT NULL THEN 1 ELSE 0 END) +
            (CASE WHEN hum_aula_4 IS NOT NULL THEN 1 ELSE 0 END), 0)
        AS hum_aula,
    pres_aula_1, pres_aula_2, pres_aula_3, pres_aula_4,
    COALESCE(pres_aula_1 + pres_aula_2 + pres_aula_3 + pres_aula_4, NULL)
        / NULLIF(
            (CASE WHEN pres_aula_1 IS NOT NULL THEN 1 ELSE 0 END) +
            (CASE WHEN pres_aula_2 IS NOT NULL THEN 1 ELSE 0 END) +
            (CASE WHEN pres_aula_3 IS NOT NULL THEN 1 ELSE 0 END) +
            (CASE WHEN pres_aula_4 IS NOT NULL THEN 1 ELSE 0 END), 0)
        AS pres_aula,
    min_puerta_1,
    min_ventana_1, min_ventana_2, min_ventana_3, min_ventana_4,
    min_ventana_5, min_ventana_6, min_ventana_7, min_ventana_8,
    min_ventana_9, min_ventana_10, min_ventana_11, min_ventana_12,
    temp_exterior, nubosidad, hum_exterior, vel_viento,
    elevacion_sol, acimut_sol
FROM (
    SELECT
        date_trunc('hour', "time") AS hora,
        AVG(CASE WHEN entity_id = 'sensor.sensor_temperatura_1_temperature' THEN state_numeric END) AS temp_aula_1,
        AVG(CASE WHEN entity_id = 'sensor.sensor_temperatura_2_temperature' THEN state_numeric END) AS temp_aula_2,
        AVG(CASE WHEN entity_id = 'sensor.sensor_temperatura_3_temperature' THEN state_numeric END) AS temp_aula_3,
        AVG(CASE WHEN entity_id = 'sensor.sensor_temperatura_4_temperature' THEN state_numeric END) AS temp_aula_4,
        AVG(CASE WHEN entity_id = 'sensor.sensor_temperatura_1_humidity' THEN state_numeric END) AS hum_aula_1,
        AVG(CASE WHEN entity_id = 'sensor.sensor_temperatura_2_humidity' THEN state_numeric END) AS hum_aula_2,
        AVG(CASE WHEN entity_id = 'sensor.sensor_temperatura_3_humidity' THEN state_numeric END) AS hum_aula_3,
        AVG(CASE WHEN entity_id = 'sensor.sensor_temperatura_4_humidity' THEN state_numeric END) AS hum_aula_4,
        AVG(CASE WHEN entity_id = 'sensor.sensor_temperatura_1_pressure' THEN state_numeric END) AS pres_aula_1,
        AVG(CASE WHEN entity_id = 'sensor.sensor_temperatura_2_pressure' THEN state_numeric END) AS pres_aula_2,
        AVG(CASE WHEN entity_id = 'sensor.sensor_temperatura_3_pressure' THEN state_numeric END) AS pres_aula_3,
        AVG(CASE WHEN entity_id = 'sensor.sensor_temperatura_4_pressure' THEN state_numeric END) AS pres_aula_4,
        ROUND((AVG(CASE WHEN entity_id = 'binary_sensor.sensor_puerta_1_contact' THEN state_numeric END) * 60)::numeric, 1) AS min_puerta_1,
        ROUND((AVG(CASE WHEN entity_id = 'binary_sensor.sensor_ventana_1_contact' THEN state_numeric END) * 60)::numeric, 1) AS min_ventana_1,
        ROUND((AVG(CASE WHEN entity_id = 'binary_sensor.sensor_ventana_2_contact' THEN state_numeric END) * 60)::numeric, 1) AS min_ventana_2,
        ROUND((AVG(CASE WHEN entity_id = 'binary_sensor.sensor_ventana_3_contact' THEN state_numeric END) * 60)::numeric, 1) AS min_ventana_3,
        ROUND((AVG(CASE WHEN entity_id = 'binary_sensor.sensor_ventana_4_contact' THEN state_numeric END) * 60)::numeric, 1) AS min_ventana_4,
        ROUND((AVG(CASE WHEN entity_id = 'binary_sensor.sensor_ventana_5_contact' THEN state_numeric END) * 60)::numeric, 1) AS min_ventana_5,
        ROUND((AVG(CASE WHEN entity_id = 'binary_sensor.sensor_ventana_6_contact' THEN state_numeric END) * 60)::numeric, 1) AS min_ventana_6,
        ROUND((AVG(CASE WHEN entity_id = 'binary_sensor.sensor_ventana_7_contact' THEN state_numeric END) * 60)::numeric, 1) AS min_ventana_7,
        ROUND((AVG(CASE WHEN entity_id = 'binary_sensor.sensor_ventana_8_contact' THEN state_numeric END) * 60)::numeric, 1) AS min_ventana_8,
        ROUND((AVG(CASE WHEN entity_id = 'binary_sensor.sensor_ventana_9_contact' THEN state_numeric END) * 60)::numeric, 1) AS min_ventana_9,
        ROUND((AVG(CASE WHEN entity_id = 'binary_sensor.sensor_ventana_10_contact' THEN state_numeric END) * 60)::numeric, 1) AS min_ventana_10,
        ROUND((AVG(CASE WHEN entity_id = 'binary_sensor.sensor_ventana_11_contact' THEN state_numeric END) * 60)::numeric, 1) AS min_ventana_11,
        ROUND((AVG(CASE WHEN entity_id = 'binary_sensor.sensor_ventana_12_contact' THEN state_numeric END) * 60)::numeric, 1) AS min_ventana_12,
        AVG(CASE WHEN entity_id = 'sensor.mislata_temperatura' THEN state_numeric END) AS temp_exterior,
        AVG(CASE WHEN entity_id = 'sensor.mislata_nubosidad' THEN state_numeric END) AS nubosidad,
        AVG(CASE WHEN entity_id = 'sensor.mislata_humedad' THEN state_numeric END) AS hum_exterior,
        AVG(CASE WHEN entity_id = 'sensor.mislata_viento' THEN state_numeric END) AS vel_viento,
        AVG(CASE WHEN entity_id = 'sensor.sun_solar_elevation' THEN state_numeric END) AS elevacion_sol,
        AVG(CASE WHEN entity_id = 'sensor.sun_solar_azimuth' THEN state_numeric END) AS acimut_sol
    FROM silver_sensores
    WHERE state_numeric IS NOT NULL
    GROUP BY date_trunc('hour', "time")
) sub
ORDER BY hora;

CREATE TABLE IF NOT EXISTS predicciones_derroche (
    hora        timestamptz PRIMARY KEY,
    probabilidad double precision NOT NULL,
    prediccion  integer NOT NULL,
    metodo      varchar NOT NULL DEFAULT 'heuristic'
);
