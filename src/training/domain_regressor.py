"""Regresor multi-dominio: un XGB por categoría geológica."""
from __future__ import annotations

import json
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from xgboost import XGBRegressor


@dataclass
class DomainRegressor:
    """Entrena un XGBRegressor independiente por cada dominio de `groups`.

    - `model_params`: dict global o dict-de-dicts `{domain: params}` para
      tuning independiente por dominio.
    - `features_per_domain`: si se pasa, cada dominio usa solo ese subset
      de columnas de X. Si es None, todos los dominios usan todas las columnas.

    El target debe venir ya transformado (ej: log1p) si corresponde.
    """
    domains: list[str]
    model_params: dict[str, Any] = field(default_factory=dict)
    features_per_domain: dict[str, list[str]] | None = None
    models_: dict[str, XGBRegressor] = field(default_factory=dict, init=False)
    feature_cols_: dict[str, list[str]] = field(default_factory=dict, init=False)

    def _params_for(self, domain: str) -> dict[str, Any]:
        # Soporta dos formas: params globales o {domain: params}
        if self.model_params and all(k in self.domains for k in self.model_params):
            return self.model_params.get(domain, {})
        return self.model_params

    def _features_for(self, domain: str, X: pd.DataFrame) -> list[str]:
        if self.features_per_domain is None:
            return list(X.columns)
        return self.features_per_domain[domain]

    def fit(self, X: pd.DataFrame, y: pd.Series, groups: pd.Series) -> "DomainRegressor":
        self.models_ = {}
        self.feature_cols_ = {}
        for domain in self.domains:
            mask = groups == domain
            if mask.sum() == 0:
                raise ValueError(f"Sin muestras para dominio {domain}")
            cols = self._features_for(domain, X)
            model = XGBRegressor(**self._params_for(domain))
            model.fit(X.loc[mask, cols], y.loc[mask])
            self.models_[domain] = model
            self.feature_cols_[domain] = cols
        return self

    def predict(self, X: pd.DataFrame, groups: pd.Series) -> np.ndarray:
        preds = np.full(len(X), np.nan)
        for domain, model in self.models_.items():
            mask = (groups == domain).values
            if mask.any():
                cols = self.feature_cols_[domain]
                preds[mask] = model.predict(X.loc[mask, cols])
        if np.isnan(preds).any():
            missing = groups[np.isnan(preds)].unique().tolist()
            raise ValueError(f"Grupos sin modelo entrenado: {missing}")
        return preds

    def save(self, directory: str | Path) -> None:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        for domain, model in self.models_.items():
            safe = domain.replace(" ", "_").replace("/", "_")
            with open(directory / f"{safe}.pkl", "wb") as f:
                pickle.dump(model, f)
        meta = {
            "domains": self.domains,
            "model_params": self.model_params,
            "features_per_domain": self.features_per_domain,
            "feature_cols": self.feature_cols_,
        }
        with open(directory / "meta.json", "w") as f:
            json.dump(meta, f, indent=2)

    @classmethod
    def load(cls, directory: str | Path) -> "DomainRegressor":
        directory = Path(directory)
        with open(directory / "meta.json") as f:
            meta = json.load(f)
        inst = cls(
            domains=meta["domains"],
            model_params=meta["model_params"],
            features_per_domain=meta.get("features_per_domain"),
        )
        inst.feature_cols_ = meta["feature_cols"]
        for domain in meta["domains"]:
            safe = domain.replace(" ", "_").replace("/", "_")
            with open(directory / f"{safe}.pkl", "rb") as f:
                inst.models_[domain] = pickle.load(f)
        return inst
