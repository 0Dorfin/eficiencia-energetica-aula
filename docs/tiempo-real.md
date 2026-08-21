# Pipeline en tiempo real

Stack paralelo al histórico que simula el stream de sensores del aula y escribe
predicciones de derroche continuas, para alimentar el dashboard en directo.

- [1. Por qué un stack separado](#1-por-qué-un-stack-separado)
- [2. Flujo](#2-flujo)
- [3. Scripts](#3-scripts)
- [4. Puesta en marcha](#4-puesta-en-marcha)
- [5. Tabla de predicciones](#5-tabla-de-predicciones)

---

## 1. Por qué un stack separado

El aula real no es accesible desde fuera del centro, así que el stack en directo
(`infra/docker-compose.live.yml`) arranca una TimescaleDB vacía en el puerto **5433** y la
alimenta con un simulador. Así el dashboard en tiempo real puede demostrarse sin depender de
la red del centro, y sin contaminar el volcado histórico del puerto 5432.

## 2. Flujo

```
  datos_simulados.py            (cada 5 s)
      │  INSERT lecturas sintéticas de los 17 dispositivos
      ▼
  ltss  →  bronze_sensores  →  silver_sensores  →  gold_features_horaria
      │
      ▼
  predict_derroche.py           (cada 60 s)
      │  lee la ventana de 4 h, construye las 31 features, invoca RedDerrocheV2
      ▼
  predicciones_derroche  ──►  Grafana :3001
```

## 3. Scripts

| Script | Función |
|---|---|
| `scripts/datos_simulados.py` | Genera lecturas sintéticas con deriva realista para los 17 dispositivos y las inserta en `ltss`. Reintenta la conexión hasta 30 veces al arrancar. |
| `scripts/predict_derroche.py` | Cada `--interval` segundos lee `gold_features_horaria`, deriva features, invoca el modelo y hace `UPSERT` en `predicciones_derroche`. Al arrancar rellena las horas ya pasadas del día (`backfill_today`). |
| `scripts/estado_calefaccion.py` | Algoritmo de termostato + inferencia de `calefaccion_encendida` a partir de `models/calefaccion_linear.joblib`. Compartido por notebooks y pipeline. |
| `scripts/train_calefaccion.py` | Reentrena la regresión lineal de calefacción desde `data/silver/dataset_tarea3_limpio.csv`. |
| `scripts/relleno_datos.py` | Utilidad puntual: rellena huecos temporales de `ltss` copiando el mismo periodo de N años atrás, desplazado. |

Todos aceptan `--host`, `--port`, `--dbname`, `--user`, `--password`, con fallback a las
variables `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`.

**Flags útiles:**

```bash
python scripts/datos_simulados.py  --once             # una sola inserción
python scripts/datos_simulados.py  --seed 42          # simulación reproducible
python scripts/predict_derroche.py --once             # una predicción y salir
python scripts/predict_derroche.py --no-backfill      # no rellenar horas pasadas
python scripts/relleno_datos.py    --auto-gap --dry-run
```

## 4. Puesta en marcha

```bash
cp .env.example .env          # ajusta POSTGRES_PASSWORD
cd infra
docker compose -f docker-compose.live.yml --profile simulate up -d
```

Levanta cuatro contenedores: TimescaleDB (5433), Grafana (3001), el simulador y el predictor.
Sin `--profile simulate` arrancan solo la base de datos y Grafana.

El servicio `predict-derroche` instala PyTorch CPU en el primer arranque, así que tarda unos
minutos en emitir la primera predicción. Seguimiento:

```bash
docker compose -f docker-compose.live.yml logs -f predict-derroche
```

## 5. Tabla de predicciones

Definida en `sql/06_predicciones_live.sql` y ampliada por
`infra/init-scripts/04_predicciones_calefaccion_column.sql`:

```sql
CREATE TABLE IF NOT EXISTS predicciones_derroche (
    hora                  timestamptz PRIMARY KEY,
    probabilidad          double precision NOT NULL,
    prediccion            integer NOT NULL,
    metodo                varchar NOT NULL DEFAULT 'heuristic',
    calefaccion_encendida double precision
);
```

`hora` es clave primaria, de modo que el `UPSERT` recalcula la predicción de la hora en curso
a medida que llegan más lecturas, sin duplicar filas.
