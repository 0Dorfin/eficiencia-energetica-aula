"""Comportamiento de `predict()` y métricas del modelo sobre el conjunto de test.

El test de métricas es de regresión: fija los valores que documenta
`docs/modelo-ml.md`, de modo que reentrenar y publicar un modelo distinto sin
actualizar la documentación deje de pasar desapercibido.
"""

import numpy as np
import pytest
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split

from derroche import FEATURE_COLS, build_frame, cargar_bundle, predict
from derroche.inferencia import MODELO_V2, SCALER_V2
import torch

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

#: Valores publicados en docs/modelo-ml.md § Métricas en test.
METRICAS_DOCUMENTADAS = {"accuracy": 0.9083, "f1": 0.8402, "roc_auc": 0.9660}
TOLERANCIA = 0.005


def test_sin_calefaccion_no_hay_derroche():
    """Regla de negocio: sin calefacción encendida el derroche es imposible."""
    pred, prob = predict({**LECTURA, "calefaccion_encendida": 0.0})
    assert (pred, prob) == (0, 0.0)


def test_la_regla_de_negocio_no_invoca_la_red(monkeypatch):
    """Debe cortocircuitar antes de cargar nada."""
    def explota(*args, **kwargs):
        raise AssertionError("no debería cargarse el modelo")

    monkeypatch.setattr("derroche.inferencia.cargar_bundle", explota)
    assert predict({**LECTURA, "calefaccion_encendida": 0.0}) == (0, 0.0)


def test_predict_devuelve_una_probabilidad_y_una_clase():
    pred, prob = predict(LECTURA)
    assert pred in (0, 1)
    assert 0.0 <= prob <= 1.0


def test_la_clase_es_coherente_con_el_umbral():
    pred, prob = predict(LECTURA)
    umbral = cargar_bundle(MODELO_V2, SCALER_V2).umbral
    assert pred == (1 if prob >= umbral else 0)


def test_predict_es_determinista():
    assert predict(LECTURA) == predict(LECTURA)


def test_las_lecturas_previas_cambian_la_prediccion():
    """Si los lags no influyeran, las 9 features de histórico sobrarían."""
    sin_previas = predict(LECTURA)[1]
    con_previas = predict({
        **LECTURA,
        "prev_1h": {"temp_aula": 19.0, "temp_exterior": 4.0, "calefaccion_encendida": 0.0},
        "prev_2h": {"temp_aula": 18.5, "temp_exterior": 3.5, "calefaccion_encendida": 0.0},
        "prev_3h": {"temp_aula": 18.0, "temp_exterior": 3.0, "calefaccion_encendida": 0.0},
    })[1]
    assert sin_previas != pytest.approx(con_previas, abs=1e-6)


def test_las_metricas_en_test_siguen_siendo_las_documentadas(dataset, checkpoint):
    frame = build_frame(dataset).dropna()
    X = frame[FEATURE_COLS].values.astype(np.float32)
    y = frame["derroche_siguiente_hora"].values.astype(np.int64)

    bundle = cargar_bundle(MODELO_V2, SCALER_V2)
    X = bundle.scaler.transform(X)

    idx = np.arange(len(X))
    _, resto = train_test_split(idx, test_size=0.3, shuffle=False)
    _, test = train_test_split(resto, test_size=0.5, shuffle=False)

    with torch.no_grad():
        prob = torch.sigmoid(bundle.modelo(torch.tensor(X[test]))).numpy().ravel()
    pred = (prob >= bundle.umbral).astype(int)

    obtenidas = {
        "accuracy": accuracy_score(y[test], pred),
        "f1": f1_score(y[test], pred, zero_division=0),
        "roc_auc": roc_auc_score(y[test], prob),
    }
    for nombre, esperada in METRICAS_DOCUMENTADAS.items():
        assert obtenidas[nombre] == pytest.approx(esperada, abs=TOLERANCIA), (
            f"{nombre}: {obtenidas[nombre]:.4f} frente a {esperada:.4f} en docs/modelo-ml.md. "
            "Si el cambio es intencionado, actualiza la documentación y este test."
        )
