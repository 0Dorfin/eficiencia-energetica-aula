# Arquitectura

Descripción de la infraestructura IoT, el stack tecnológico y la arquitectura de datos
por capas (medallion) sobre la que se apoya el proyecto.

- [1. Contexto](#1-contexto)
- [2. Stack tecnológico](#2-stack-tecnológico)
- [3. Sensores del aula](#3-sensores-del-aula)
- [4. Integraciones externas](#4-integraciones-externas)
- [5. Base de datos](#5-base-de-datos)
- [6. Arquitectura medallion](#6-arquitectura-medallion)
- [7. Servicios y puertos](#7-servicios-y-puertos)

---

## 1. Contexto

El objetivo es detectar y **predecir derroche energético** en un aula del centro.
Se define *derroche* como la situación en la que la calefacción está encendida mientras
puertas o ventanas permanecen abiertas durante un tiempo significativo.

El aula dispone de una infraestructura IoT con sensores Zigbee y un sistema domótico
basado en **Home Assistant**, que persiste el histórico en TimescaleDB.

Esa infraestructura la opera el CIPFP Mislata: el proyecto **no accede a Home Assistant ni a
Zigbee2MQTT**, sino que parte de un **export de la tabla `ltss`** entregado por el centro. Para
poder demostrar el comportamiento en directo sin acceso a la red del aula, se añadió un
simulador que reproduce el stream de sensores sobre una base local — ver
[tiempo-real.md](tiempo-real.md).

## 2. Stack tecnológico

| Componente | Tecnología | Función |
|---|---|---|
| Servidor domótico | Home Assistant | Integración de sensores y fuentes externas |
| Broker MQTT | Mosquitto | Mensajería entre dispositivos |
| Pasarela Zigbee | Zigbee2MQTT + SLZB-06 | Comunicación con sensores Zigbee |
| Base de datos | TimescaleDB (PostgreSQL 15) | Almacenamiento de series temporales |
| Dashboard | Grafana | Visualización histórica y en tiempo real |
| Lenguaje | Python 3.12 | Análisis, modelado e interfaz |
| ML / IA | scikit-learn, PyTorch | Regresión lineal y red neuronal |
| App de predicción | Streamlit + Plotly | Interfaz de usuario |
| Contenedores | Docker Compose | Orquestación de servicios |

## 3. Sensores del aula

| Sensor | Modelo | Magnitudes |
|---|---|---|
| Temperatura/Humedad/Presión (×4) | Aqara WSDCGQ11LM | Temperatura (°C), humedad (%), presión (hPa) |
| Puerta (×1) | Aqara MCCGQ11LM | Abierto / cerrado |
| Ventanas (×12) | Aqara MCCGQ11LM | Abierto / cerrado |
| Consumo eléctrico | Shelly Pro EM-50 | Consumo (W) |

En total 17 dispositivos Zigbee. El consumo del Shelly no llegó a usarse como feature: queda
como vía de mejora (ver [README](../README.md#resultados)).

## 4. Integraciones externas

| Integración | Datos |
|---|---|
| Met.no (Mislata) | Temperatura exterior, nubosidad, humedad, viento |
| Sun | Elevación solar, acimut solar |

## 5. Base de datos

La tabla principal es `public.ltss`, el histórico que escribe Home Assistant y que el centro
entregó como volcado SQL (`infra/init-scripts/01_creacion.sql`):

```sql
CREATE TABLE public.ltss (
  "time"      timestamptz NOT NULL,
  entity_id   varchar     NOT NULL,
  state       varchar     NULL,
  attributes  jsonb       NULL
);
```

El stack en tiempo real añade la tabla `predicciones_derroche`
(`sql/06_predicciones_live.sql`), donde el servicio de inferencia escribe una fila por hora.

## 6. Arquitectura medallion

Capas materializadas como vistas SQL en TimescaleDB. Detalle completo en [datos.md](datos.md).

```
  ltss (crudo)
      │
      ▼
  bronze_sensores        sql/01_bronze_extract.sql
  filtra las entidades relevantes
      │
      ▼
  silver_sensores        sql/02_silver_clean.sql
  state (texto) → numérico, on/off → 1/0, inHg → hPa, descarta unavailable
      │
      ▼
  gold_features_horaria  sql/03_gold_features_hourly.sql
  agregación horaria + minutos de apertura + meteorología + sol
      │
      ├──► gold_correlaciones   sql/04_gold_correlaciones.sql   (análisis de redundancia)
      ├──► notebooks/           (datasets CSV en data/gold/)
      └──► predicciones_derroche  sql/06_predicciones_live.sql  (inferencia en vivo)
```

## 7. Servicios y puertos

| Stack | Servicio | Puerto | Contenido |
|---|---|---|---|
| Histórico (`docker-compose.yml`) | TimescaleDB | 5432 | Volcado completo de `ltss` |
| Histórico | Grafana | 3000 | Dashboard histórico |
| Tiempo real (`docker-compose.live.yml`) | TimescaleDB | 5433 | Base vacía alimentada por el simulador |
| Tiempo real | Grafana | 3001 | Dashboard en directo |
| Tiempo real (perfil `simulate`) | simulate-ltss | — | Inserta lecturas simuladas |
| Tiempo real (perfil `simulate`) | predict-derroche | — | Escribe predicciones cada 60 s |

Los puertos y credenciales se configuran vía `.env` (ver `.env.example`).
