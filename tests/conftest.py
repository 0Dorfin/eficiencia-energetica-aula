from pathlib import Path

import pandas as pd
import pytest
import torch

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def raiz():
    return RAIZ


@pytest.fixture(scope="session")
def checkpoint():
    ruta = RAIZ / "models" / "model_derroche_v2.pt"
    if not ruta.is_file():
        pytest.skip(f"falta {ruta.relative_to(RAIZ)}; ejecuta notebooks/05_red_neuronal_v2.ipynb")
    return torch.load(ruta, map_location="cpu", weights_only=False)


@pytest.fixture(scope="session")
def dataset():
    ruta = RAIZ / "data" / "gold" / "dataset_entrenamiento.csv"
    if not ruta.is_file():
        pytest.skip(f"falta {ruta.relative_to(RAIZ)}")
    return pd.read_csv(ruta, index_col=0, parse_dates=True).sort_index()
