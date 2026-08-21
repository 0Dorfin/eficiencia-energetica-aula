"""El checkpoint de `models/` tiene que cargar con la clase que sirve predicciones.

Si alguien cambia la arquitectura sin regenerar el `.pt` —o al revés—, estos tests
fallan. Sin ellos el síntoma es mucho peor: la app arranca, predice, y nadie sabe
que el modelo servido no es el documentado.
"""

import pytest
import torch

from derroche import RedDerrocheV2, cargar_bundle
from derroche.inferencia import MODELO_V2, SCALER_V2


def test_el_checkpoint_carga_con_la_clase_de_produccion(checkpoint):
    modelo = RedDerrocheV2(checkpoint["input_dim"], checkpoint["hidden_dim"])
    modelo.load_state_dict(checkpoint["model_state"])


def test_el_checkpoint_trae_los_metadatos_necesarios(checkpoint):
    for clave in ("model_state", "input_dim", "hidden_dim", "feature_cols", "best_threshold"):
        assert clave in checkpoint, f"al checkpoint le falta '{clave}'"


def test_el_umbral_es_una_probabilidad(checkpoint):
    assert 0.0 < checkpoint["best_threshold"] < 1.0


def test_el_escalador_espera_tantas_columnas_como_features(checkpoint):
    bundle = cargar_bundle(MODELO_V2, SCALER_V2)
    assert bundle.scaler.n_features_in_ == checkpoint["input_dim"]


def test_el_bundle_se_cachea_por_ruta():
    """El servicio en tiempo real llama a predict() cada 60 s; recargar sería absurdo."""
    primero = cargar_bundle(MODELO_V2, SCALER_V2)
    segundo = cargar_bundle(MODELO_V2, SCALER_V2)
    assert primero is segundo


def test_el_modelo_se_carga_en_modo_evaluacion():
    """En modo train, dropout y batchnorm harían la predicción no determinista."""
    assert not cargar_bundle(MODELO_V2, SCALER_V2).modelo.training


def test_un_checkpoint_inexistente_falla_con_claridad(tmp_path):
    with pytest.raises(FileNotFoundError):
        cargar_bundle(tmp_path / "no_existe.pt", SCALER_V2)
