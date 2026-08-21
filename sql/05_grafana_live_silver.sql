SELECT
    "time" AS "time",
    entity_id AS metric,
    state_numeric AS value
FROM silver_sensores
WHERE $__timeFilter("time")
  AND state_numeric IS NOT NULL
ORDER BY "time";
