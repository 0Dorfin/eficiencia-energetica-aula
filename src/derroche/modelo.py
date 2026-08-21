"""Arquitecturas de las redes de clasificación de derroche.

Definición única: la importan tanto los notebooks que entrenan como la app y el
servicio en tiempo real que sirven. Si se cambia una capa aquí, los checkpoints
antiguos dejan de cargar de forma ruidosa (`load_state_dict` lanza) en vez de
producir predicciones de un modelo que ya no es el documentado.
"""

from __future__ import annotations

import torch.nn as nn


class RedDerroche(nn.Module):
    """V1: perceptrón multicapa sobre las 13 features del dataset.

    Se conserva para poder cargar checkpoints antiguos. El modelo en producción es
    `RedDerrocheV2`.
    """

    def __init__(self, input_dim, hidden_dims=(64, 32), dropout=0.3):
        super().__init__()
        capas = []
        previo = input_dim
        for unidades in hidden_dims:
            capas.extend([
                nn.Linear(previo, unidades),
                nn.ReLU(),
                nn.BatchNorm1d(unidades),
                nn.Dropout(dropout),
            ])
            previo = unidades
        self.encoder = nn.Sequential(*capas)
        self.classifier = nn.Linear(previo, 1)

    def forward(self, x):
        return self.classifier(self.encoder(x))


class RedDerrocheV2(nn.Module):
    """V2: red con conexión residual y activación GELU sobre las 31 features.

    Devuelve el logit sin activar; la sigmoide se aplica fuera, en `inferencia`.
    """

    def __init__(self, input_dim, hidden_dim=128, dropout=0.3):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.bn1 = nn.BatchNorm1d(hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.bn2 = nn.BatchNorm1d(hidden_dim)
        self.skip = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.bn3 = nn.BatchNorm1d(hidden_dim // 2)
        self.classifier = nn.Linear(hidden_dim // 2, 1)
        self.drop = nn.Dropout(dropout)
        self.act = nn.GELU()

    def forward(self, x):
        x = self.drop(self.act(self.bn1(self.fc1(x))))
        residual = x
        x = self.drop(self.act(self.bn2(self.fc2(x))))
        x = x + self.skip(residual)
        x = self.drop(self.act(self.bn3(self.fc3(x))))
        return self.classifier(x)
