# Eficiencia Energética del Aula

Sistema de detección y predicción de **derroche energético** en un aula con instrumentación IoT.
Una red neuronal predice, a partir de las lecturas de la hora actual, si en la hora siguiente
habrá calefacción encendida con puertas o ventanas abiertas.

## Índice

- [Pipeline](#pipeline)
- [Requisitos](#requisitos)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Puesta en marcha](#puesta-en-marcha)
- [Comandos útiles](#comandos-útiles)
- [Stack tecnológico](#stack-tecnológico)
- [Servicios y puertos](#servicios-y-puertos)
- [Variables de entorno](#variables-de-entorno)
- [Resultados](#resultados)
- [Documentación](#documentación)

## Pipeline

```
  Sensores Zigbee (17 dispositivos)          Met.no + Sun
  temperatura · humedad · presión            meteorología · posición solar
  puerta · 12 ventanas · consumo
            │                                        │
            └────────────► Home Assistant ◄──────────┘
                                 │
                                 ▼
                        TimescaleDB · tabla ltss
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
   bronze_sensores  ──►  silver_sensores  ──►  gold_features_horaria
   filtra entidades      texto → numérico      agregación horaria
        │                                              │
        │                        ┌─────────────────────┴─────────────────────┐
        │                        ▼                                           ▼
        │              Regresión lineal                              Dataset horario
        │              temperatura calefacción                       3.924 muestras
        │                        │                                           │
        │                        ▼                                           │
        │              calefaccion_encendida ──────► derroche_actual ────────┤
        │                                            (min. ponderados > 12)  │
        │                                                                    ▼
        │                                                    derroche_siguiente_hora
        │                                                            TARGET
        │                                                              │
        │                                                              ▼
        │                                                       RedDerrocheV2
        │                                                    31 features · PyTorch
        │                                                              │
        ▼                                     ┌────────────────────────┼────────────────┐
   Grafana :3000                              ▼                        ▼                │
   dashboard histórico              App Streamlit :8501     predicciones_derroche       │
                                    predicción manual       Grafana :3001 en directo ◄──┘
```

## Requisitos

- Docker + Docker Compose
- Python 3.12 (para notebooks y app)

## Estructura del repositorio

```
proyecto_domotica_3/
├── README.md
├── requirements.txt
├── .env.example                      # Plantilla de credenciales y puertos
│
├── src/derroche/                     # Paquete: definición única del modelo
│   ├── features.py                   # Las 31 features (entrenamiento e inferencia)
│   ├── modelo.py                     # Arquitecturas RedDerroche y RedDerrocheV2
│   └── inferencia.py                 # Carga cacheada de artefactos y predict()
│
├── tests/                            # Suite de pytest
│   ├── test_features.py              # Paridad entrenamiento/inferencia
│   ├── test_artefactos.py            # El .pt carga con la clase de producción
│   └── test_prediccion.py            # Regla de negocio y métricas documentadas
│
├── app/                              # App de predicción
│   └── main.py                       # Interfaz Streamlit
│
├── scripts/                          # Pipeline en tiempo real y entrenamiento
│   ├── simular_sensores.py           # Simulador del stream de sensores
│   ├── predecir_derroche.py          # Servicio de inferencia continua
│   ├── estado_calefaccion.py         # Algoritmo de termostato (módulo compartido)
│   ├── entrenar_calefaccion.py       # Reentrena la regresión lineal
│   └── rellenar_huecos.py            # Relleno de huecos en ltss
│
├── notebooks/                        # Análisis y modelado
│   ├── 01_eda.ipynb                  # Correlaciones entre sensores
│   ├── 02_dataset_gold.ipynb         # Construcción del dataset y del target
│   ├── 03_regresion_calefaccion.ipynb # Modelo lineal de calefacción
│   ├── 04_red_neuronal_v1.ipynb      # Red neuronal V1 (13 features)
│   ├── 05_red_neuronal_v2.ipynb      # Red neuronal V2 — modelo final (31 features)
│   └── 06_evaluacion.ipynb           # Verifica que models/ reproduce las métricas
├── sql/                              # Vistas de la arquitectura medallion
│   ├── 01_bronze_extract.sql
│   ├── 02_silver_clean.sql
│   ├── 03_gold_features_hourly.sql
│   ├── 04_gold_correlaciones.sql
│   ├── 05_grafana_live_silver.sql
│   └── 06_predicciones_live.sql
│
├── models/                           # Artefactos entrenados
│   ├── model_derroche_v2.pt          # Modelo en producción
│   ├── model_derroche_v2_best.pt     # Mejor checkpoint de validación
│   ├── scaler_derroche_v2.joblib
│   ├── scaler_derroche.joblib
│   └── calefaccion_linear.joblib
│
├── data/                             # Arquitectura medallion en CSV
│   ├── bronze/historico_calefaccion.csv
│   ├── silver/dataset_horario.csv
│   └── gold/dataset_calefaccion..9_final.csv
│
├── infra/                            # Orquestación
│   ├── docker-compose.yml            # Stack histórico  (5432 / 3000)
│   ├── docker-compose.live.yml       # Stack en directo (5433 / 3001)
│   ├── init-scripts/                 # Creación de tablas y vistas
│   ├── grafana/                      # Provisioning + dashboard histórico
│   └── grafana-live/                 # Provisioning + dashboard en directo
│
├── docs/                             # Documentación técnica
├── slides/                           # Presentación del proyecto
└── assets/                           # Recursos visuales
```

## Puesta en marcha

```bash
cp .env.example .env        # define POSTGRES_PASSWORD antes de continuar
pip install -e .            # instala el paquete `derroche` en modo editable
```

El paquete `src/derroche/` es la definición única de las features, la arquitectura y
la inferencia. Los notebooks, la app y el servicio en tiempo real lo importan, de modo
que no pueden desincronizarse entre sí.

**Stack histórico** — base de datos con el volcado completo y dashboard histórico:

```bash
cd infra
docker compose --env-file ../.env up -d
```

- Grafana: http://localhost:3000 (`admin` / `GRAFANA_ADMIN_PASSWORD`)
- TimescaleDB: `localhost:5432`

> `--env-file ../.env` es necesario porque Docker Compose busca el `.env` junto al fichero
> compose, no en la raíz del repositorio.

> El volcado `infra/init-scripts/02_datos.sql` (222 MB) no está versionado por superar el
> límite de GitHub. Sin él la tabla `ltss` arranca vacía — ver
> [docs/datos.md § Regenerar los datos](docs/datos.md#7-regenerar-los-datos).

> Si los puertos 5432/5433/3000/3001 están ocupados, cámbialos en `.env`
> (`POSTGRES_PORT`, `POSTGRES_LIVE_PORT`, `GRAFANA_PORT`, `GRAFANA_LIVE_PORT`).

**Stack en tiempo real** — simulador de sensores + inferencia continua:

```bash
cd infra
docker compose --env-file ../.env -f docker-compose.live.yml --profile simulate up -d
```

- Grafana: http://localhost:3001
- TimescaleDB: `localhost:5433`

**App de predicción:**

```bash
pip install -r requirements.txt
streamlit run app/main.py       # http://localhost:8501
```

## Comandos útiles

```bash
# Logs del predictor en tiempo real
cd infra && docker compose --env-file ../.env -f docker-compose.live.yml logs -f predict-derroche

# Parar y limpiar volúmenes del stack en directo
cd infra && docker compose --env-file ../.env -f docker-compose.live.yml --profile simulate down -v

# Una única predicción contra la base en directo
PGPASSWORD=... python scripts/predecir_derroche.py --host localhost --port 5433 --once

# Reentrenar la regresión lineal de calefacción
python scripts/entrenar_calefaccion.py

# Abrir los notebooks
jupyter lab notebooks/

# Ejecutar los tests
pytest
```

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Captación IoT | Home Assistant, Mosquitto (MQTT), Zigbee2MQTT + SLZB-06 |
| Almacenamiento | TimescaleDB (PostgreSQL 15) |
| Transformación | SQL (vistas medallion), pandas |
| ML / IA | scikit-learn (regresión lineal), PyTorch (red neuronal) |
| Visualización | Grafana, Plotly |
| Interfaz | Streamlit |
| Orquestación | Docker Compose |

## Servicios y puertos

| Stack | Servicio | Puerto | Función |
|---|---|---|---|
| Histórico | `timescaledb` | 5432 | Volcado completo de `ltss` |
| Histórico | `grafana` | 3000 | Dashboard histórico |
| Tiempo real | `timescaledb_live` | 5433 | Base alimentada por el simulador |
| Tiempo real | `grafana_live` | 3001 | Dashboard en directo |
| Tiempo real | `simulate-ltss` | — | Inserta lecturas simuladas cada 5 s |
| Tiempo real | `predict-derroche` | — | Escribe predicciones cada 60 s |
| App | `streamlit` | 8501 | Predicción manual |

## Variables de entorno

Definidas en `.env` (plantilla en `.env.example`). `.env` está en `.gitignore`.

| Variable | Por defecto | Descripción |
|---|---|---|
| `POSTGRES_USER` | `postgres` | Usuario de TimescaleDB |
| `POSTGRES_PASSWORD` | — (**obligatoria**) | Contraseña de TimescaleDB |
| `POSTGRES_DB` | `postgres` | Base de datos |
| `POSTGRES_PORT` | `5432` | Puerto del stack histórico |
| `POSTGRES_LIVE_PORT` | `5433` | Puerto del stack en tiempo real |
| `GRAFANA_ADMIN_PASSWORD` | `admin` | Contraseña de admin de Grafana |
| `GRAFANA_PORT` | `3000` | Grafana histórico |
| `GRAFANA_LIVE_PORT` | `3001` | Grafana en directo |

Los scripts de `scripts/` leen además `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER` y `PGPASSWORD`.

## Resultados

| Componente | Resultado |
|---|---|
| Correlación entre sensores | Redundancia > 0.95 entre los 4 sensores del aula: basta con el sensor 2 |
| Regresión lineal (calefacción) | R² = 0.56 en test para inferir la temperatura del sensor de calefacción |
| Red neuronal (derroche) | F1 = 0.84 · ROC-AUC = 0.97 · Recall clase derroche = 0.90 |
| Dataset final | 3.924 muestras horarias, 26,96 % positivos |
| App de predicción | Predicción manual con lecturas actuales y de las 3 horas previas |
| Dashboards | Histórico (:3000) y tiempo real con predicción en vivo (:3001) |

**Conclusiones y limitaciones**

- Los 4 sensores del aula son redundantes; 3 de ellos podrían retirarse sin pérdida apreciable.
- El estado de la calefacción no se mide directamente: se infiere con un modelo lineal cuyo
  R² de 0.56 en test es el eslabón más débil de la cadena, ya que el target del clasificador
  depende de él.
- Se prioriza el recall de la clase derroche: un falso positivo (alerta innecesaria) cuesta
  menos que un derroche no detectado.

**Próximos pasos**

1. Alertas automáticas (email o notificación push) cuando el modelo prediga derroche.
2. Reentrenamiento periódico para adaptarse a cambios estacionales.
3. Incorporar el consumo eléctrico del Shelly Pro EM-50 como feature.
4. Explorar LSTM o Transformer para capturar dependencias temporales más largas.

## Documentación

| Documento | Contenido |
|---|---|
| [docs/arquitectura.md](docs/arquitectura.md) | Infraestructura IoT, stack, sensores, arquitectura medallion, puertos |
| [docs/datos.md](docs/datos.md) | Capas bronze/silver/gold, correlaciones, construcción del target, dataset final |
| [docs/modelo-ml.md](docs/modelo-ml.md) | Regresión lineal, redes V1 y V2, features, métricas, artefactos |
| [docs/app.md](docs/app.md) | App Streamlit: interfaz, pipeline de inferencia, ejecución |
| [docs/grafana.md](docs/grafana.md) | Dashboards histórico y en directo, provisioning |
| [docs/tiempo-real.md](docs/tiempo-real.md) | Simulador, servicio de inferencia continua, tabla de predicciones |
