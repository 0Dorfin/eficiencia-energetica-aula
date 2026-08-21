# Capturas

Imágenes referenciadas desde la documentación.

| Fichero | Contenido | Origen |
|---|---|---|
| `03_heatmap_temperatura.png` | Correlaciones entre los 4 sensores de temperatura | `notebooks/01_eda.ipynb` |
| `04_heatmap_humedad.png` | Correlaciones entre los 4 sensores de humedad | `notebooks/01_eda.ipynb` |
| `05_heatmap_ventanas.png` | Correlaciones entre puerta y las 12 ventanas | `notebooks/01_eda.ipynb` |
| `06_serie_temporal_calefaccion.png` | Temperatura de calefacción real vs. predicha | `notebooks/02_build_gold.ipynb` |
| `07_scatter_real_vs_predicho.png` | Dispersión real vs. predicho del modelo lineal | `notebooks/03_model_ml.ipynb` |
| `serie_temporal_derroche.png` | Horas de derroche por semana | `notebooks/02_build_gold.ipynb` |
| `08_distribucion_target.png` | Distribución del target (73 % / 27 %) | `notebooks/02_build_gold.ipynb` |
| `09_curvas_entrenamiento.png` | Train Loss y Val F1 por época (67 épocas) | `notebooks/04b_model_nn_improved.ipynb` |
| `10_matriz_confusion.png` | Matriz de confusión en test | `notebooks/05_evaluation.ipynb` |
| `11_curva_roc.png` | Curva ROC, AUC = 0.9660 | `notebooks/04b_model_nn_improved.ipynb` |
| `12_curva_precision_recall.png` | Curva Precision-Recall, AP = 0.9005 (línea base 0.268) | `notebooks/05_evaluation.ipynb` |
| `13_app_formulario.png` | Formulario de la app Streamlit | App |
| `14_app_resultado_alerta.png` | Resultado con alerta de derroche (69,2 %) | App |
| `14_grafana_tiempo_real.png` | Estado actual del aula (gauges, alerta) | Grafana :3001 |
| `20_grafana_live_ambiente.png` | Temperatura interior/exterior y ambiente | Grafana :3001 |
| `21_grafana_live_aperturas.png` | Puertas/ventanas y condiciones por hora | Grafana :3001 |
| `17_grafana_hist_distribucion.png` | Distribución del sensor y temperatura histórica | Grafana :3000 |
| `18_grafana_hist_comparativa.png` | Comparativa de los 4 sensores frente al exterior | Grafana :3000 |
| `19_grafana_hist_meteorologia.png` | Meteorología histórica | Grafana :3000 |
| `15_grafana_heatmap_derroche.png` | Análisis de derroche histórico (heatmap, mensual, aperturas) | Grafana :3000 |

Las figuras de notebook se regeneran reejecutando el notebook correspondiente. Las de Grafana
proceden de los dashboards en `infra/grafana*/dashboards/`.
