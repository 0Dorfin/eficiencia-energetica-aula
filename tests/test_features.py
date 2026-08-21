"""Las features del entrenamiento y las de la inferencia deben ser las mismas.

Cuando divergen se produce *train/serve skew*: el modelo recibe en producción
vectores construidos de otra forma que los de entrenamiento, y falla en silencio
—sin excepción, solo con peores predicciones—. Por eso se comprueba aquí.
"""

import numpy as np
import pytest

from derroche import FEATURE_COLS, build_frame, build_vector
from derroche.features import COLUMNAS_BASE

LECTURA = {
    "hora_del_dia": 12.0,
    "dia_de_la_semana": 3.0,
    "mes_del_ano": 1.0,
    "temp_aula": 21.5,
    "hum_aula": 48.0,
    "pres_aula": 1013.0,
    "temp_exterior": 6.0,
    "nubosidad": 7.0,
    "hum_exterior": 80.0,
    "vel_viento": 15.0,
    "elevacion_sol": 20.0,
    "acimut_sol": 140.0,
    "calefaccion_encendida": 1.0,
}


def test_el_orden_de_features_coincide_con_el_checkpoint(checkpoint):
    """El orden importa: el escalador y la red esperan las columnas en su posición."""
    assert list(checkpoint["feature_cols"]) == FEATURE_COLS


def test_el_checkpoint_espera_tantas_entradas_como_features(checkpoint):
    assert checkpoint["input_dim"] == len(FEATURE_COLS)


def test_build_vector_devuelve_la_forma_esperada():
    v = build_vector(LECTURA)
    assert v.shape == (1, len(FEATURE_COLS))
    assert v.dtype == np.float32


def test_build_vector_exige_las_columnas_base():
    incompleta = {k: v for k, v in LECTURA.items() if k != "temp_aula"}
    with pytest.raises(ValueError, match="temp_aula"):
        build_vector(incompleta)


def test_sin_lecturas_previas_los_deltas_son_cero():
    """Al faltar el histórico se asume que nada ha cambiado."""
    v = build_vector(LECTURA)[0]
    for col in ("delta_temp_aula_1h", "delta_temp_aula_2h", "delta_temp_exterior_1h"):
        assert v[FEATURE_COLS.index(col)] == 0.0


def test_la_codificacion_ciclica_hace_contiguas_las_horas_23_y_0():
    """El motivo de usar sin/cos: como enteros, 23 y 0 distarían 23 unidades."""
    def punto(hora):
        v = build_vector({**LECTURA, "hora_del_dia": hora})[0]
        return np.array([v[FEATURE_COLS.index("hora_sin")], v[FEATURE_COLS.index("hora_cos")]])

    d_23_0 = np.linalg.norm(punto(23) - punto(0))
    d_0_1 = np.linalg.norm(punto(0) - punto(1))
    assert d_23_0 == pytest.approx(d_0_1, abs=1e-6)


def test_entrenamiento_e_inferencia_producen_el_mismo_vector(dataset):
    """La garantía central: `build_frame` y `build_vector` no pueden divergir."""
    frame = build_frame(dataset).dropna()
    posiciones = {ts: i for i, ts in enumerate(dataset.index)}

    rng = np.random.default_rng(0)
    muestras = rng.choice(len(frame), size=min(100, len(frame)), replace=False)

    comparadas = 0
    for m in muestras:
        ts = frame.index[m]
        i = posiciones[ts]
        if i < 3:
            continue
        lectura = {c: float(dataset.iloc[i][c]) for c in COLUMNAS_BASE}
        previas = {
            lag: {
                "temp_aula": float(dataset.iloc[i - lag]["temp_aula"]),
                "temp_exterior": float(dataset.iloc[i - lag]["temp_exterior"]),
                "calefaccion_encendida": float(dataset.iloc[i - lag]["calefaccion_encendida"]),
            }
            for lag in (1, 2, 3)
        }
        esperado = frame.loc[ts, FEATURE_COLS].values.astype(np.float32)
        np.testing.assert_allclose(build_vector(lectura, previas)[0], esperado, rtol=1e-6, atol=1e-6)
        comparadas += 1

    assert comparadas > 50, "muestra insuficiente para que la comprobación valga"


def test_build_frame_exige_las_columnas_base(dataset):
    with pytest.raises(ValueError, match="temp_aula"):
        build_frame(dataset.drop(columns=["temp_aula"]))
