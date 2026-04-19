"""Feature engineering reutilizable para los notebooks de modelado."""
from collections import Counter

import numpy as np
import pandas as pd


NUMERIC_BASE = ["Latitude", "Longitude", "Tonnage(Mt)", "Max_age(Ma)", "Min_age(Ma)"]
MED_AGE_COLS = ["n_age_samples", "age_mean", "age_std", "age_min", "age_max", "n_dating_methods"]


def load_base_with_cu(xlsx_path: str) -> pd.DataFrame:
    df = pd.read_excel(xlsx_path)
    df = df.dropna(subset=["Copper_grade(Cu; %)"]).copy()
    df["Mindat_id"] = pd.to_numeric(df["Mindat_id"], errors="coerce").astype("Int64")
    return df


def aggregate_med_ages(ages_xlsx_path: str) -> pd.DataFrame:
    df_ages = pd.read_excel(ages_xlsx_path)
    df_ages["mindat_id"] = pd.to_numeric(df_ages["mindat_id"], errors="coerce").astype("Int64")
    df_ages = df_ages.dropna(subset=["mindat_id"])
    agg = df_ages.groupby("mindat_id").agg(
        n_age_samples=("modeled_age_ma", "size"),
        age_mean=("modeled_age_ma", "mean"),
        age_std=("modeled_age_ma", "std"),
        age_min=("modeled_age_ma", "min"),
        age_max=("modeled_age_ma", "max"),
        n_dating_methods=("dating_method", "nunique"),
    ).reset_index()
    return agg.rename(columns={"mindat_id": "Mindat_id"})


def add_mineral_features(df: pd.DataFrame, top_n: int = 50) -> tuple[pd.DataFrame, list[str]]:
    all_minerals = []
    for s in df["Mineral_assemblage"].dropna():
        all_minerals.extend([m.strip() for m in s.split(",")])
    top = [m for m, _ in Counter(all_minerals).most_common(top_n)]

    minerals_set = df["Mineral_assemblage"].apply(
        lambda s: {m.strip() for m in s.split(",")} if pd.notna(s) else set()
    )
    cols = []
    for mineral in top:
        col = f"has_min_{mineral.lower().replace(' ', '_').replace('-', '_')}"
        df[col] = minerals_set.apply(lambda s, m=mineral: int(m in s))
        cols.append(col)
    return df, cols


def add_element_features(df: pd.DataFrame, top_n: int = 30) -> tuple[pd.DataFrame, list[str]]:
    def parse(s):
        if pd.isna(s):
            return set()
        return {e.strip() for e in s.split("-") if e.strip()}

    elements_set = df["Chemical_Elements"].apply(parse)
    all_elements = [e for es in elements_set for e in es]
    top = [e for e, _ in Counter(all_elements).most_common(top_n)]

    cols = []
    for elem in top:
        col = f"elem_{elem}"
        df[col] = elements_set.apply(lambda s, e=elem: int(e in s))
        cols.append(col)
    return df, cols


def build_feature_matrix(
    main_xlsx: str,
    ages_xlsx: str,
    top_minerals: int = 50,
    top_elements: int = 30,
) -> tuple[pd.DataFrame, pd.Series, pd.Series, list[str]]:
    """Devuelve (X, y_log, deposit_type, feature_cols). Filtra tipos afuera."""
    df = load_base_with_cu(main_xlsx)
    ages = aggregate_med_ages(ages_xlsx)
    df = df.merge(ages, on="Mindat_id", how="left")
    for c in MED_AGE_COLS:
        df[c] = df[c].fillna(0)

    df = pd.get_dummies(df, columns=["Deposit_type"], prefix="type", dummy_na=False)
    type_cols = [c for c in df.columns if c.startswith("type_")]
    df, mineral_cols = add_mineral_features(df, top_minerals)
    df, element_cols = add_element_features(df, top_elements)

    deposit_type = pd.Series(
        np.select(
            [df[c] == 1 for c in type_cols],
            [c.replace("type_", "") for c in type_cols],
            default="Unknown",
        ),
        index=df.index,
        name="Deposit_type",
    )

    feature_cols = NUMERIC_BASE + MED_AGE_COLS + type_cols + mineral_cols + element_cols
    X = df[feature_cols].copy()
    y_log = np.log1p(df["Copper_grade(Cu; %)"])
    return X, y_log, deposit_type, feature_cols
