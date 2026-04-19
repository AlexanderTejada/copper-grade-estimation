# Estimación de leyes de cobre con XGBoost y domaining geológico

Proyecto de machine learning aplicado a geología económica: predecir la **ley de cobre (%Cu)** de un depósito mineral a partir de sus características geoquímicas, litológicas y espaciales, usando un ensamble que especializa modelos por tipo geológico.

## Resultado

**HybridRegressor** entrenado sobre 989 depósitos mundiales del *Global Copper Deposit Dataset*:

| Modelo | RMSE (%Cu) | R² |
|---|---|---|
| Baseline global (un XGBoost único) | 1.129 | 0.371 |
| **HybridRegressor (este proyecto)** | **1.005** | **0.426** |

Mejora de **+11% en RMSE** y **+15% en R²** frente a un XGBoost único. El modelo rutea cada depósito al submodelo más adecuado según su tipo geológico.

## Idea central: *domaining*

Los depósitos de cobre no son todos iguales. Un *porphyry* tiene leyes típicas de 0.3-0.8% pero tonelajes de cientos de millones de toneladas; un *VMS* tiene leyes de 1-3% pero cuerpos chicos. Las relaciones entre features y ley de Cu **cambian de signo** entre tipos. Un solo modelo para todos diluye las señales finas.

La solución aplicada:
- **Porphyry (395 registros)** → modelo XGBoost dedicado con las 96 features
- **VMS (425)** → modelo dedicado con las top-25 features por importance + regularización fuerte
- **Sediment-Hosted / IOCG / Magmatic sulfide** → modelo global (muy poca data para un especialista confiable)

El `HybridRegressor` es un *router*: al predecir, mira el `Deposit_type` y envía la muestra al modelo correspondiente.

## Recorrido de los notebooks

| Notebook | Qué hace |
|---|---|
| `01_exploracion.ipynb` | EDA inicial sobre datasets USGS MRDS (primera iteración, descartado) |
| `02_datos_enriquecidos.ipynb` | Baseline global: 96 features + tuning, R² = 0.371 |
| `03_domaining.ipynb` | EDA por tipo geológico, Kruskal-Wallis valida diferencias entre tipos |
| `04_domain_models.ipynb` | Primera versión del domaining (3 modelos) — hallazgo contraintuitivo |
| `05_domain_models_tuned.ipynb` | Feature selection + tuning por dominio — VMS mejora, Porphyry no |
| `06_modelo_final.ipynb` | `HybridRegressor` consolidado + demo de inferencia |

La historia del proyecto (incluyendo el hallazgo negativo en `04`) está en [`reports/01_hallazgo_domaining.md`](reports/01_hallazgo_domaining.md).

## Feature engineering

De 20 columnas originales, se construyen **96 features**:
- **5 numéricas base**: Lat/Lon, Tonnage(Mt), Max_age(Ma), Min_age(Ma)
- **6 de edades isotópicas**: agregadas desde el dataset MED_ages (19k muestras)
- **5 one-hot de tipo geológico**
- **50 binarias de minerales** presentes (top-50 de `Mineral_assemblage`)
- **30 binarias de elementos químicos** (top-30 de `Chemical_Elements`)

El pipeline de features es reutilizable en `src/features/build_features.py`.

## Estructura del proyecto

```
.
├── data/external/         # Datasets crudos (GCDD, USGS MRDS)
├── notebooks/             # Exploración y modelado iterativo
├── src/
│   ├── features/          # build_features.py (pipeline reutilizable)
│   └── training/
│       ├── domain_regressor.py   # N modelos, uno por dominio
│       └── hybrid_regressor.py   # Router: global + especialistas
├── models/
│   ├── domain/            # v1: un XGB por tipo con todas las features
│   ├── domain_tuned/      # v2: features + hiperparámetros por dominio
│   └── final/             # HybridRegressor entregable
├── reports/               # Análisis de hallazgos
├── requirements.txt
└── README.md
```

## Stack técnico

- **Python 3.14** + `.venv`
- **pandas / numpy / scikit-learn / xgboost**: modelado
- **matplotlib / seaborn**: visualización
- **openpyxl**: lectura de datasets en Excel
- **jupyter**: notebooks iterativos

## Uso

Entrenar y evaluar el modelo final:

```bash
.venv/bin/jupyter nbconvert --to notebook --execute notebooks/06_modelo_final.ipynb
```

Inferencia en Python:

```python
from src.training.hybrid_regressor import HybridRegressor
import numpy as np

model = HybridRegressor.load("models/final")
# X: DataFrame con las 96 features; groups: Serie con Deposit_type
y_pred_log = model.predict(X_new, groups)
y_pred_cu_pct = np.expm1(y_pred_log)
```

## Limitaciones honestas

- El dataset son **989 depósitos globales** — suficiente para baseline pero justo para especializar por tipo.
- Los tipos con poca data (Sediment-Hosted, IOCG, Magmatic sulfide) **no son confiables** a nivel individual; el modelo los rutea al global.
- No se incluyeron **features estructurales** (distancia a márgenes convergentes, profundidad). Es el siguiente paso natural.
- La **incertidumbre del predictor** no está cuantificada todavía (regresión puntual, no bandas de predicción).

## Datos

- **Global Copper Deposit Dataset (GCDD)**: 1487 depósitos, 989 con ley de Cu reportada.
- **MED_ages (supplement)**: 19431 muestras de edades isotópicas, agregadas por depósito.

Los datos están en `data/external/Global-copper-deposit-dataset/` y no se versionan en git.
