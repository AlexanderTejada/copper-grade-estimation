"""Regresor híbrido: combina un modelo global con modelos especializados por dominio.

Motivación (ver reports/01_hallazgo_domaining.md):
- Porphyry se beneficia de un modelo dedicado con todas las features.
- VMS se beneficia de un modelo dedicado con feature selection + regularización.
- Sediment-Hosted tiene muy poca data y el domaining lo empeora; fallback al global.
- Cualquier tipo no previsto también usa el global (robustez ante OOD).
"""
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
class HybridRegressor:
    """Router: elige modelo global o especializado según `Deposit_type`.

    - `specialists`: dict `{domain: XGBRegressor}` ya ajustados (o se entrenan en fit).
    - `global_model`: modelo de fallback entrenado con todos los tipos.
    - `features_per_domain`: features que usa cada especialista.
      Los dominios no presentes en este dict van al global.
    """
    specialist_domains: list[str]
    global_params: dict[str, Any] = field(default_factory=dict)
    specialist_params: dict[str, dict[str, Any]] = field(default_factory=dict)
    features_per_domain: dict[str, list[str]] = field(default_factory=dict)
    global_model_: XGBRegressor | None = field(default=None, init=False)
    specialists_: dict[str, XGBRegressor] = field(default_factory=dict, init=False)
    global_features_: list[str] | None = field(default=None, init=False)

    def fit(self, X: pd.DataFrame, y: pd.Series, groups: pd.Series) -> "HybridRegressor":
        self.global_features_ = list(X.columns)
        self.global_model_ = XGBRegressor(**self.global_params)
        self.global_model_.fit(X, y)

        self.specialists_ = {}
        for domain in self.specialist_domains:
            mask = (groups == domain).values
            if mask.sum() == 0:
                raise ValueError(f"Sin muestras para dominio {domain}")
            cols = self.features_per_domain.get(domain, list(X.columns))
            params = self.specialist_params.get(domain, {})
            m = XGBRegressor(**params)
            m.fit(X.loc[mask, cols], y.loc[mask])
            self.specialists_[domain] = m
        return self

    def predict(self, X: pd.DataFrame, groups: pd.Series) -> np.ndarray:
        preds = np.full(len(X), np.nan)
        for domain in self.specialist_domains:
            mask = (groups == domain).values
            if not mask.any():
                continue
            cols = self.features_per_domain.get(domain, self.global_features_)
            preds[mask] = self.specialists_[domain].predict(X.loc[mask, cols])

        fallback_mask = np.isnan(preds)
        if fallback_mask.any():
            preds[fallback_mask] = self.global_model_.predict(
                X.loc[fallback_mask, self.global_features_]
            )
        return preds

    def route(self, groups: pd.Series) -> pd.Series:
        """Devuelve, para cada fila, qué modelo la va a atender. Útil para debugging."""
        return groups.where(groups.isin(self.specialist_domains), other="global")

    def save(self, directory: str | Path) -> None:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        with open(directory / "global.pkl", "wb") as f:
            pickle.dump(self.global_model_, f)
        for domain, model in self.specialists_.items():
            safe = domain.replace(" ", "_").replace("/", "_")
            with open(directory / f"specialist_{safe}.pkl", "wb") as f:
                pickle.dump(model, f)
        meta = {
            "specialist_domains": self.specialist_domains,
            "global_params": self.global_params,
            "specialist_params": self.specialist_params,
            "features_per_domain": self.features_per_domain,
            "global_features": self.global_features_,
        }
        with open(directory / "meta.json", "w") as f:
            json.dump(meta, f, indent=2)

    @classmethod
    def load(cls, directory: str | Path) -> "HybridRegressor":
        directory = Path(directory)
        with open(directory / "meta.json") as f:
            meta = json.load(f)
        inst = cls(
            specialist_domains=meta["specialist_domains"],
            global_params=meta["global_params"],
            specialist_params=meta["specialist_params"],
            features_per_domain=meta["features_per_domain"],
        )
        inst.global_features_ = meta["global_features"]
        with open(directory / "global.pkl", "rb") as f:
            inst.global_model_ = pickle.load(f)
        for domain in meta["specialist_domains"]:
            safe = domain.replace(" ", "_").replace("/", "_")
            with open(directory / f"specialist_{safe}.pkl", "rb") as f:
                inst.specialists_[domain] = pickle.load(f)
        return inst
