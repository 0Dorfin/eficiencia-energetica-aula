"""Carga de artefactos y predicción de derroche.

Los artefactos se cachean por ruta: el servicio en tiempo real llama a `predict()`
cada 60 s de forma indefinida, y sin caché volvería a leer el modelo y el escalador
del disco en cada llamada.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import joblib
import torch

from .features import build_vector
from .modelo import RedDerroche, RedDerrocheV2

#: Directorio de artefactos, relativo a la raíz del repositorio.
MODELS_DIR = Path(__file__).resolve().parents[2] / "models"

MODELO_V2 = MODELS_DIR / "model_derroche_v2.pt"
SCALER_V2 = MODELS_DIR / "scaler_derroche_v2.joblib"


@dataclass(frozen=True)
class Bundle:
    """Modelo, escalador y metadatos de un checkpoint, listos para inferir."""

    modelo: torch.nn.Module
    scaler: object
    feature_cols: list
    umbral: float
    es_v2: bool


@lru_cache(maxsize=4)
def cargar_bundle(model_path=None, scaler_path=None) -> Bundle:
    """Carga un checkpoint y su escalador, cacheados por ruta.

    La caché guarda el modelo ya en modo `eval()`. Para recargar tras reentrenar,
    llama a `cargar_bundle.cache_clear()`.
    """
    model_path = Path(model_path or MODELO_V2)
    scaler_path = Path(scaler_path or SCALER_V2)

    checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)
    scaler = joblib.load(scaler_path)

    input_dim = checkpoint["input_dim"]
    es_v2 = "hidden_dim" in checkpoint

    if es_v2:
        modelo = RedDerrocheV2(input_dim=input_dim, hidden_dim=checkpoint["hidden_dim"])
        umbral = checkpoint.get("best_threshold", 0.5)
    else:
        modelo = RedDerroche(input_dim=input_dim, hidden_dims=tuple(checkpoint["hidden_dims"]))
        umbral = 0.5

    modelo.load_state_dict(checkpoint["model_state"])
    modelo.eval()

    return Bundle(
        modelo=modelo,
        scaler=scaler,
        feature_cols=list(checkpoint["feature_cols"]),
        umbral=float(umbral),
        es_v2=es_v2,
    )


def predict(features_dict, model_path=None, scaler_path=None):
    """Predice si habrá derroche en la hora siguiente.

    Aplica primero una regla determinista: sin calefacción encendida no puede haber
    derroche tal y como se define el problema, así que no se invoca la red.

    Args:
        features_dict: lectura actual con las claves de `COLUMNAS_BASE`. Admite
            además `prev_1h`, `prev_2h` y `prev_3h` con las lecturas previas.
        model_path: checkpoint alternativo. Por defecto, el V2 de `models/`.
        scaler_path: escalador alternativo. Por defecto, el V2 de `models/`.

    Returns:
        `(prediccion, probabilidad)` — la predicción es 0 o 1 según el umbral que
        traiga el checkpoint.
    """
    if features_dict.get("calefaccion_encendida", 1.0) == 0.0:
        return 0, 0.0

    bundle = cargar_bundle(model_path, scaler_path)

    if bundle.es_v2:
        previas = {
            1: features_dict.get("prev_1h"),
            2: features_dict.get("prev_2h"),
            3: features_dict.get("prev_3h"),
        }
        x = build_vector(features_dict, previas)
    else:
        import numpy as np

        x = np.array(
            [[features_dict[col] for col in bundle.feature_cols]], dtype=np.float32
        )

    with torch.no_grad():
        logit = bundle.modelo(torch.tensor(bundle.scaler.transform(x), dtype=torch.float32))
        prob = torch.sigmoid(logit).item()

    return (1 if prob >= bundle.umbral else 0), prob
