"""Detección y predicción de derroche energético en el aula.

Punto de entrada único para features, arquitecturas e inferencia, de modo que los
notebooks de entrenamiento y el código que sirve predicciones compartan una sola
definición y no puedan desincronizarse.
"""

from .features import (
    COLUMNA_TARGET,
    COLUMNAS_BASE,
    FEATURE_COLS,
    build_frame,
    build_vector,
)
from .inferencia import MODELO_V2, SCALER_V2, Bundle, cargar_bundle, predict
from .modelo import RedDerroche, RedDerrocheV2

__all__ = [
    "COLUMNAS_BASE",
    "COLUMNA_TARGET",
    "FEATURE_COLS",
    "build_frame",
    "build_vector",
    "RedDerroche",
    "RedDerrocheV2",
    "Bundle",
    "cargar_bundle",
    "predict",
    "MODELO_V2",
    "SCALER_V2",
]
