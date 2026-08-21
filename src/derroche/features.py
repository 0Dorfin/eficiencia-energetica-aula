"""Construcción de las features del modelo de derroche.

Este módulo es la **única** definición de qué features usa el modelo y de cómo se
calculan. Lo importan los notebooks de entrenamiento, la app de predicción y el
servicio de inferencia en tiempo real.

Hay dos caminos de entrada con formas distintas:

- **Entrenamiento** — un `DataFrame` ordenado por tiempo, donde los lags salen de las
  filas anteriores (`shift`).
- **Inferencia** — una lectura suelta más, opcionalmente, las de las 3 horas previas.

Para que no puedan divergir, ambos delegan el cálculo en `_derivadas()`. Las
operaciones que usa (`np.sin`, restas, productos) se comportan igual sobre escalares
que sobre `Series`, así que la fórmula de cada feature está escrita una sola vez.
"""

from __future__ import annotations

import numpy as np

#: Las 13 columnas que produce el pipeline de datos (`data/gold/dataset_entrenamiento.csv`).
COLUMNAS_BASE = [
    "hora_del_dia",
    "dia_de_la_semana",
    "mes_del_ano",
    "temp_aula",
    "hum_aula",
    "pres_aula",
    "temp_exterior",
    "nubosidad",
    "hum_exterior",
    "vel_viento",
    "elevacion_sol",
    "acimut_sol",
    "calefaccion_encendida",
]

COLUMNA_TARGET = "derroche_siguiente_hora"

#: Las 31 features que consume la red, **en el orden en que se le pasan**.
#: El checkpoint guarda su propia copia en `feature_cols`; `tests/test_features.py`
#: comprueba que ambas coinciden.
FEATURE_COLS = [
    # Calendario en codificación cíclica
    "hora_sin", "hora_cos",
    "dia_sin", "dia_cos",
    "mes_sin", "mes_cos",
    # Ambiente interior
    "temp_aula", "hum_aula", "pres_aula",
    # Ambiente exterior
    "temp_exterior", "nubosidad", "hum_exterior", "vel_viento",
    # Sol
    "elevacion_sol", "acimut_sol",
    # Calefacción
    "calefaccion_encendida",
    # Lags de 1 a 3 horas
    "temp_aula_lag1", "temp_aula_lag2", "temp_aula_lag3",
    "temp_exterior_lag1", "temp_exterior_lag2", "temp_exterior_lag3",
    "calefaccion_lag1", "calefaccion_lag2", "calefaccion_lag3",
    # Variaciones
    "delta_temp_aula_1h", "delta_temp_aula_2h", "delta_temp_exterior_1h",
    # Interacciones
    "diff_temp", "calef_x_diff", "calef_x_viento",
]

#: Periodo de cada variable de calendario, para la codificación cíclica.
_PERIODOS = {"hora": 24, "dia": 7, "mes": 12}

_LAGS = [1, 2, 3]


def _ciclica(valor, periodo):
    """Codifica una variable circular en (sin, cos).

    La hora 23 y la hora 0 son adyacentes; codificadas como enteros distarían 23
    unidades. Vale igual para escalares y para `Series`.
    """
    angulo = 2 * np.pi * valor / periodo
    return np.sin(angulo), np.cos(angulo)


def _derivadas(base, lags):
    """Calcula las 31 features a partir de los valores base y de los lags.

    `base` y `lags` son mapas de escalares (inferencia) o de `Series` (entrenamiento);
    el cálculo es idéntico en ambos casos.

    Args:
        base: valores de la hora actual, con las claves de `COLUMNAS_BASE`.
        lags: valores rezagados, con las claves `temp_aula_lag1`, `temp_exterior_lag1`,
            `calefaccion_lag1`, … hasta el lag 3.

    Returns:
        Un dict con las 31 claves de `FEATURE_COLS`.
    """
    temp_aula = base["temp_aula"]
    temp_ext = base["temp_exterior"]
    calefaccion = base["calefaccion_encendida"]
    viento = base["vel_viento"]

    hora_sin, hora_cos = _ciclica(base["hora_del_dia"], _PERIODOS["hora"])
    dia_sin, dia_cos = _ciclica(base["dia_de_la_semana"], _PERIODOS["dia"])
    mes_sin, mes_cos = _ciclica(base["mes_del_ano"], _PERIODOS["mes"])

    diff_temp = temp_aula - temp_ext

    features = {
        "hora_sin": hora_sin, "hora_cos": hora_cos,
        "dia_sin": dia_sin, "dia_cos": dia_cos,
        "mes_sin": mes_sin, "mes_cos": mes_cos,
        "temp_aula": temp_aula,
        "hum_aula": base["hum_aula"],
        "pres_aula": base["pres_aula"],
        "temp_exterior": temp_ext,
        "nubosidad": base["nubosidad"],
        "hum_exterior": base["hum_exterior"],
        "vel_viento": viento,
        "elevacion_sol": base["elevacion_sol"],
        "acimut_sol": base["acimut_sol"],
        "calefaccion_encendida": calefaccion,
        "delta_temp_aula_1h": temp_aula - lags["temp_aula_lag1"],
        "delta_temp_aula_2h": temp_aula - lags["temp_aula_lag2"],
        "delta_temp_exterior_1h": temp_ext - lags["temp_exterior_lag1"],
        "diff_temp": diff_temp,
        "calef_x_diff": calefaccion * diff_temp,
        "calef_x_viento": calefaccion * viento,
    }
    features.update(lags)
    return features


def build_frame(df):
    """Añade las 31 features a un `DataFrame` ordenado por tiempo.

    Los lags se toman de las filas anteriores, así que las 3 primeras filas quedan
    con nulos: el llamante decide si las descarta.

    Args:
        df: `DataFrame` indexado por tiempo y ordenado, con las `COLUMNAS_BASE`.

    Returns:
        Una copia de `df` con las columnas de `FEATURE_COLS` añadidas.
    """
    faltan = set(COLUMNAS_BASE) - set(df.columns)
    if faltan:
        raise ValueError(f"Faltan columnas base en el DataFrame: {sorted(faltan)}")

    df = df.copy()
    lags = {}
    for lag in _LAGS:
        lags[f"temp_aula_lag{lag}"] = df["temp_aula"].shift(lag)
        lags[f"temp_exterior_lag{lag}"] = df["temp_exterior"].shift(lag)
        lags[f"calefaccion_lag{lag}"] = df["calefaccion_encendida"].shift(lag)

    for nombre, valores in _derivadas(df, lags).items():
        df[nombre] = valores
    return df


def build_vector(lectura, previas=None):
    """Construye el vector de features de una lectura suelta.

    Cuando falta una lectura previa se usa la de la hora actual, lo que equivale a
    suponer que la variable no ha cambiado: el lag toma el valor actual y el delta
    correspondiente sale 0.

    Args:
        lectura: dict con las `COLUMNAS_BASE`.
        previas: dict opcional `{1: {...}, 2: {...}, 3: {...}}` con las lecturas de
            hace 1, 2 y 3 horas. Cada una puede traer solo algunas claves.

    Returns:
        `np.ndarray` de forma `(1, 31)` y dtype float32, con las columnas en el
        orden de `FEATURE_COLS`.
    """
    faltan = set(COLUMNAS_BASE) - set(lectura)
    if faltan:
        raise ValueError(f"Faltan claves en la lectura: {sorted(faltan)}")

    previas = previas or {}
    lags = {}
    for lag in _LAGS:
        previa = previas.get(lag) or {}
        lags[f"temp_aula_lag{lag}"] = previa.get("temp_aula", lectura["temp_aula"])
        lags[f"temp_exterior_lag{lag}"] = previa.get("temp_exterior", lectura["temp_exterior"])
        lags[f"calefaccion_lag{lag}"] = previa.get(
            "calefaccion_encendida", lectura["calefaccion_encendida"]
        )

    features = _derivadas(lectura, lags)
    return np.array([[features[col] for col in FEATURE_COLS]], dtype=np.float32)
