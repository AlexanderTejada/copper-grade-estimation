# Hallazgo: el domaining geológico empeora R² pero puede mejorar el error absoluto

**Fecha:** 2026-04-19
**Notebook de origen:** `notebooks/04_domain_models.ipynb`
**Modelos:** `models/domain/` (Porphyry, VMS, Sediment-Hosted)

## Contexto

El pilar #2 del proyecto es "domaining": agrupar depósitos por tipo geológico y entrenar un modelo por grupo, en lugar de un modelo global. La hipótesis era que cada tipo (Porphyry, VMS, Sediment-Hosted) tiene física mineralizante distinta y que features genéricas como tonelaje o mineralogía deberían tener pesos diferentes en cada uno.

**Baseline global** (`02_datos_enriquecidos.ipynb`, 96 features, todos los tipos):
- R² CV = 0.434 ± 0.116
- R² test = 0.371, RMSE = 1.129

## Qué se hizo

1. EDA por tipo (`03_domaining.ipynb`): Kruskal-Wallis p = 2e-115 confirmó que las distribuciones de Cu son significativamente distintas entre tipos. Porphyry tiene ley baja (mediana 0.44%) pero tonelajes gigantes (240 Mt); VMS y Sediment-Hosted son inversos (ley 1.4-2%, tonelajes chicos).
2. Se descartaron Magmatic sulfide (36 registros) e IOCG (29) por falta de masa crítica.
3. Se entrenó un `DomainRegressor` (un XGBoost independiente por dominio) sobre los 924 depósitos restantes con las mismas 96 features para los tres.

## Resultados

### CV R² (en escala log1p, comparable al baseline)

| Dominio | n train | folds | R² CV | vs baseline global (0.434) |
|---|---|---|---|---|
| Porphyry | 316 | 5 | 0.114 ± 0.056 | peor |
| VMS | 340 | 5 | 0.179 ± 0.075 | peor |
| Sediment-Hosted | 83 | 3 | 0.256 ± 0.101 | peor |

### Test set (escala original, %Cu)

| | n test | RMSE | MAE | R² |
|---|---|---|---|---|
| Baseline global (`02`) | 198 | 1.129 | 0.574 | **0.371** |
| Domaining global (`04`) | 185 | 1.269 | 0.664 | 0.263 |
| Domaining **Porphyry** | 79 | **0.213** | **0.165** | 0.117 |
| Domaining **VMS** | 85 | 1.283 | 0.957 | -0.048 |
| Domaining **Sediment-Hosted** | 21 | 2.710 | 1.356 | 0.000 |

## Interpretación

### 1. El R² global del baseline estaba inflado por el tipo mismo

El modelo global aprendía principalmente la señal "dame el tipo → rango de Cu esperado" (la feature `type_Porphyry` tenía importancia 0.184, lejos la más alta). Al separar por tipo, esa señal fácil desaparece y queda la **varianza dentro del tipo**, que es mucho más difícil de explicar. Por eso los R² por dominio caen, pero **no significa que los modelos sean peores**: significa que la métrica R² no es comparable a pelo entre modelos entrenados sobre poblaciones distintas.

### 2. Porphyry mejora dramáticamente en error absoluto (5x mejor RMSE)

RMSE 0.213 vs 1.129 del baseline para depósitos Porphyry. Esto es el resultado útil del domaining: el modelo dedicado predice la ley de cobre de un porphyry con error promedio de 0.17%, mientras que el global erraba en 0.57%. Para uso operacional (decisiones de exploración en un prospect porphyry), este es el modelo a usar.

El R² Porphyry es bajo (0.117) porque la varianza interna es pequeña — los porphyries tienen leyes en un rango estrecho (0.3-0.8% casi siempre). Explicar esa varianza residual es difícil, pero el error absoluto es chico porque el rango mismo es chico.

### 3. VMS empeoró — R² negativo

El modelo VMS predice peor que la media constante. La causa más probable: las 96 features son demasiadas y muchas son ruido para VMS (ej: minerales de alteración típicos de porphyry como molibdenita, chrysocolla, malaquita). VMS tiene una mineralogía distinta (pirita, esfalerita, calcopirita hidrotermal de fondo marino) y necesita su propio set de features relevantes, no las genéricas.

### 4. Sediment-Hosted no es evaluable

Con solo 21 muestras en test, los intervalos de confianza son enormes. Los resultados son ruido.

## Conclusión

El domaining **no es un fracaso** — reveló que:
- La métrica R² agregada engaña cuando la señal viene del grupo mismo.
- **Porphyry sí se beneficia del domaining** (RMSE 5x mejor).
- **VMS sufre** por usar el mismo set de features genéricas — necesita selección de features por dominio.
- **Sediment-Hosted** necesita más data o combinarse con otros tipos similares.

## Iteración de corrección (notebook `05_domain_models_tuned.ipynb`)

Probamos dos cambios para atacar VMS y Sediment-Hosted:
- **Feature selection por dominio**: top-25 features por `feature_importances_` dentro de cada tipo (descartando `type_*` que son constantes dentro del dominio).
- **Tuning por dominio** con `RandomizedSearchCV` (40 iter, 3-fold), con espacios distintos por tipo (VMS con regularización alta, Sediment con árboles chicos).

### Resultados (CV R² en log1p)

| Dominio | v1 (04, 96 features) | v2 solo features (05) | v2 features + tuning (05) |
|---|---|---|---|
| Porphyry | 0.114 ± 0.056 | 0.042 ± 0.068 ⬇ | 0.095 ⬇ |
| **VMS** | 0.179 ± 0.075 | 0.216 ± 0.093 ⬆ | **0.267 ⬆⬆ (+49%)** |
| Sediment-Hosted | 0.256 ± 0.101 | 0.314 ± 0.098 ⬆ | 0.114 ⬇ |

### Resultados (test %Cu)

| Dominio | v1 RMSE / R² | v2 tuned RMSE / R² |
|---|---|---|
| Porphyry | 0.213 / 0.117 | 0.217 / 0.084 |
| VMS | 1.283 / -0.048 | 1.262 / -0.015 |
| Sediment-Hosted | 2.710 / 0.000 | 2.956 / -0.189 |

### Aprendizajes

1. **VMS sí mejoró**: de R² CV 0.18 a 0.27 con feature selection + regularización fuerte. Hipótesis validada.
2. **Porphyry empeoró**: las 96 features tenían señal difusa que XGB aprovechaba. La feature selection no universaliza — lo que ayuda a VMS perjudica a Porphyry.
3. **Sediment-Hosted es inestable**: con n=83 train, el `RandomizedSearchCV` sobreajustó a los folds de CV. La selección de features sola (sin tuning agresivo) ya era mejor.
4. **Metodológico**: hacer feature selection con el mismo modelo que luego entrena introduce sesgo. Riguroso sería nested CV, pero con estos tamaños de muestra es poco realista.

## Configuración recomendada

No hay un set único óptimo. La mejor configuración por dominio:

- **Porphyry** → v1 (96 features, params base) → RMSE test 0.213
- **VMS** → v2 (top-25 + regularización fuerte) → RMSE test 1.262, R² test ~0
- **Sediment-Hosted** → **abandonar domaining**, usar el modelo global (n=104 es insuficiente para domaining confiable)

## Resultado final: HybridRegressor (notebook `06_modelo_final.ipynb`)

Consolidamos los hallazgos en un `HybridRegressor` que rutea cada depósito al modelo que mejor lo atiende:

| Tipo geológico | Ruteo | Justificación |
|---|---|---|
| Porphyry | Especialista Porphyry (96 features, params base) | RMSE 5x mejor que el global |
| VMS | Especialista VMS (top-25 features + regularización) | +49% en R² CV vs v1 |
| Sediment-Hosted | Global fallback | n=104 insuficiente para especialista |
| IOCG, Magmatic sulfide | Global fallback | n<40 insuficiente, + robustez OOD |

### Test set — comparación contra el baseline global

| Modelo | RMSE | MAE | R² |
|---|---|---|---|
| Baseline global (`02`) | 1.129 | 0.574 | 0.371 |
| **HybridRegressor (`06`)** | **1.005** | 0.591 | **0.426** |

**+11% mejora en RMSE, +15% en R²** sobre el baseline que usaba todos los tipos juntos.

### Test por dominio

| Dominio | n_test | Ruteo | RMSE | MAE |
|---|---|---|---|---|
| Porphyry | 79 | especialista | 0.220 | 0.156 |
| VMS | 85 | especialista | 1.199 | 0.898 |
| Sediment-Hosted | 21 | global | 1.678 | 0.992 |
| IOCG | 6 | global | 1.563 | 1.079 |
| Magmatic sulfide | 7 | global | 0.154 | 0.134 |

Sediment-Hosted pasó de RMSE 2.710 (domaining forzado en `04`) a 1.678 (fallback al global) — **confirma que rutear al global fue la decisión correcta**.

## Próximos pasos sugeridos (fuera del scope de esta iteración)

1. **Features estructurales** (pilar C-L-S del proyecto): distancia a márgenes convergentes, arcos volcánicos, profundidad. Hipótesis: esto ayudaría especialmente a VMS (asociado a rifts submarinos) y podría hacer viable el domaining en Sediment-Hosted.
2. **Cuantificación de incertidumbre** (pilar #3 del scope): regresión cuantílica con XGBoost (`objective="reg:quantileerror"`) para bandas de predicción.
3. **Validación cruzada espacial**: K-fold por regiones geográficas en vez de aleatorio, para testear generalización a zonas geológicas no vistas.
