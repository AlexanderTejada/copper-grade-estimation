# Estado del proyecto

**Última actualización:** 2026-04-19

## Lo que está hecho

### Modelo operativo
- `HybridRegressor` entrenado y persistido en `models/final/` (3.4 MB).
- Performance en test: **RMSE 1.005 %Cu, R² 0.426** (+15% R² vs baseline global).
- Ruteo automático por `Deposit_type`: Porphyry y VMS → especialistas; resto → global fallback.

### Código
- `src/features/build_features.py` — pipeline de 96 features reutilizable.
- `src/training/domain_regressor.py` — N modelos independientes por dominio.
- `src/training/hybrid_regressor.py` — router final (clase entregable).

### Notebooks (historia iterativa)
| # | Contenido |
|---|---|
| 02 | Baseline global con todos los tipos — R² 0.371 |
| 03 | EDA por `Deposit_type` + Kruskal-Wallis |
| 04 | Domaining v1 — hallazgo contraintuitivo (R² cae) |
| 05 | Feature selection + tuning por dominio — VMS mejora +49% CV |
| 06 | `HybridRegressor` consolidado + demo de inferencia |

### Documentación
- `README.md` — presentación del proyecto.
- `reports/01_hallazgo_domaining.md` — análisis técnico honesto con iteraciones.

## Lo que quedó pendiente (próxima sesión)

### Gap más grande: visualización geoespacial
Tenemos Lat/Lon pero solo como features numéricas. **No hay mapa.** Para un proyecto minero es crítico.

### Plan sugerido (en orden)

1. **`notebooks/07_mapa.ipynb`** (~30 min)
   - Folium con 989 depósitos
   - Color = `Deposit_type`, tamaño = `Tonnage(Mt)`, popup = nombre + ley real
   - Exportar HTML interactivo en `reports/mapa_depositos.html`

2. **`app.py` con Streamlit** (~2-3 h)
   - Sidebar: form para ingresar features de un prospecto nuevo (tipo, coords, edad, minerales observados)
   - Centro: mapa con todos los depósitos + marker del prospecto ingresado
   - Footer: predicción del modelo (`%Cu` estimado) con explicación del ruteo (qué modelo atendió la query)
   - Deploy gratuito a Hugging Face Spaces → **URL pública para el CV**

3. **Mejoras opcionales (no bloqueantes)**
   - Bandas de incertidumbre con XGBoost cuantílico (`objective="reg:quantileerror"`)
   - Features estructurales (distancia a arcos volcánicos, márgenes convergentes) — requiere dataset geológico adicional
   - Validación cruzada espacial (K-fold por región geográfica)

## Cómo retomar

```bash
cd /home/alexander/machine-learning/copper-grade-estimation
source .venv/bin/activate.fish

# Probar que el modelo sigue funcionando
python -c "
import sys; sys.path.insert(0, '.')
from src.training.hybrid_regressor import HybridRegressor
m = HybridRegressor.load('models/final')
print('Modelo cargado OK, dominios:', m.specialist_domains)
"

# Instalar folium para empezar con el mapa (pedírselo al usuario)
# pip install folium

# Crear notebook 07_mapa.ipynb
```

## Archivos clave para orientarse

```
├── README.md                       # Overview del proyecto
├── reports/
│   ├── 00_estado.md                # ← este archivo
│   └── 01_hallazgo_domaining.md    # Análisis técnico
├── src/
│   ├── features/build_features.py  # 96 features
│   └── training/hybrid_regressor.py # Modelo final
├── models/final/                   # Pesos entrenados (cargables)
└── notebooks/06_modelo_final.ipynb # Pipeline completo + demo
```
