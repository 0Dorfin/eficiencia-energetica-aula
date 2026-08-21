# Enunciado del proyecto

Transcripción del enunciado entregado por el centro. Se conserva como referencia de
los requisitos originales; las credenciales que aparecían en el original se han eliminado.

```
Proyecto de Eficiencia Energética del Aula
1. Contexto
El centro quiere reducir el consumo energético detectando situaciones de derroche: por
ejemplo, puertas/ventanas abiertas mientras está encendida la calefacción o el aire acondicionado.
Para ello, en el aula se ha desplegado una arquitectura IoT con sensores y un sistema
domótico que recoge y almacena datos históricos para analizarlos.
La duración del proyecto de 4 semanas hábiles de 13 horas cada semana. Desde el 1 de
marzo al 2 de Abril.
2. Infraestructura disponible
Home Assistant: servidor domótico que integra sensores y fuentes externas.
Mosquitto (MQTT): broker de mensajería.
Zigbee2MQTT + SLZB-06: pasarela Zigbee
MQTT.
TimescaleDB (PostgreSQL)
: base de datos de series temporales para almacenar medidas.
IP: [eliminada]
Puerto: 5432
usuario: postgres
contraseña: [eliminada]
Base de datos: postgres
Sensores:
Aqara MCCGQ11LM: puertas/ventanas (abierto/cerrado).
Aqara WSDCGQ11LM: temperatura, humedad, presión.
Shelly Pro EM-50: consumo eléctrico.
Integraciones Home Assistant:
Met.no: meteorología (temperatura exterior, nubosidad, etc.).
Sun: posición del sol.3. Objetivo del proyecto
Diseñar una solución basada en datos que:
1. Recopile y prepare los datos de los sensores por horas (agregación, limpieza, etc.).
2. Analice correlaciones para optimizar el número de sensores necesarios.
3. Detecte y/o prediga si la calefacción está encendida
4. Construya un modelo de ML
5. Construya un modelo de IA
6. Cree un cuadro de mando (dashboard) para visualizar el estado energético del aula en
tiempo real e histórico.
4. Entregables
Cada grupo creara un repositorio en GitHub con acceso de lectura para el profesor. Cutyo
contenido debe ser:
1. Documento técnico (PDF) con decisiones, justificación y resultados.
2. Scripts/Notebook (Python/SQL) de extracción, limpieza y agregación de datos.
3. Modelo de ML entrenado + evaluación y métricas.
4. Red neuronal entrenado + evaluación y métricas.
5. Dashboard funcional conectado a Home Assistant/TimescaleDB (o exportación) con
visualizaciones clave.
6. Presentación breve (5–8 diapositivas) con conclusiones y propuestas de mejora.
Ejemplo de como podría ser el Repositorio
energy-efficiency-medallion/
README.md
.gitignore
docs/
informe-tecnico.pdf
slides/
presentacion_final.pdfdashboard/
proyecto.pibx
screenshots/
01_overview.png
02_alertas.png
data/
bronze/ # datos crudos (raw) tal cual llegan (NO subir si son sensibles/grandes)
silver/ # datos limpios y normalizados (granularidad original)
gold/ # datos agregados y listos para analítica/IA (por hora)
README_data.md
sql/
01_bronze_extract.sql
02_silver_clean.sql
03_gold_features_hourly.sql
notebooks/
01_eda.ipynb
02_build_gold.ipynb
03_model_ml.ipynb
04_model_nn.ipynb
05_evaluation.ipynb
models/
model_ml.pkl
model_nn.keras
metrics.json
5. Origen de datos
La tabla de postgress con un volcado de datos de Home Assitant la podéis crear con estas
consultas SQL.
Creación de datos
Hitórico temparaturas calefacción Septiembre- Marzo.
Historico calefacción
Algoritmo de cuando se enciende la calefacción en función de la temperatura del aula.
Algoritmo calefacción
6. Fases y tareas
Fase A — Definición del problemaTarea 1: Target
Definir claramente:
¿Qué problema vais a resolver?
¿Qué queréis predecir o detectar?
¿Cuál será el target del modelo?
Target: Derroche (Cuando consideramos que es derroche 10%, 20 % , ..........)
Ventana inferior igual al doble de la superiro y la puerta como 2 ventanas inferiores
La idea es detectar situaciones de derroche energético, por ejemplo, cuando la calefacción
está encendida mientras las ventanas o puertas están abiertas. El target será una variable
binaria que indique "derroche" (1) o "no derroche" (0) en función de las condiciones
detectadas en los datos.
Pero esa condición se tiene que detectar con anterioridad. Es decir, que dado los datos de
los sensores a una hora, detectar si habrá derroche en la siguiente hora.
Fase B — Recopilación y preparación de datos
Tarea 1: Correlaciones entre sensores de temperatura
Calcular correlaciones entre sensores de temperatura.
Conclusión: ¿hay sensores redundantes? ¿cuáles podrías eliminar?
Tarea 2: Correlaciones entre sensores de humedad
Calcular correlaciones entre sensores de humedad.
Conclusión: ¿hay sensores redundantes? ¿cuáles podrías eliminar?
Tarea 3: Recopilar datos (agregación por horas) Los datos se trabajarán agrupados por horas.Generar un CSV con los siguientes datos por hora:
Hora del día
Día de la semana
Mes del año
Temperaturas, humedad, presión, etc de cada sensor del aula
Estado de puertas/ventanas (minutos abiertos en esa hora).
Sensores externos: temperatura exterior, nubosidad, posición del sol, etc.
Temperatura del sensor de calefacción (inferida).
Tarea 4: Cálculo de “calefacción encendida”
Construir un método para calcular la temperatura del sensor de calefacción en función
de la temperatura/humedad/sol,etc del aula.
Crear un modelo de Machine Lerning Lineal
Tarea 5: Nueva columna de temperatura de la calefación
Al CSV añadir la columna de la temperatura de la calefacción inferida con el modelo de ML
lineal.
Tarea 6: Nueva columna de calefación encendida
Al CSV añadir la columna de si la calefacción está encendida o no en función de la
temperatura inferida y del algoritmo de encendido de la calefacción.
Tarea 7: Derroche
Al CSV añadir las columnas:
Los minutos totales que la puerta o ventana estuvo abierta en esa hora.
Si hubo derroche o no (si la calefacción estaba encendida y las puertas o ventanas
estuvieron abiertas más de X minutos).
Tarea 8: Nueva columna de derroche en la hora siguiente
Al CSV añadir la columna de si hay derroche en la hora siguiente.Es el mismo dato que antes pero desplazado una hora hacia adelante.
Tarea 9: Dejar solo las columnas necesarias para el modelo de IA
Generar un CSV con los siguientes datos por hora:
Hora del día
Día de la semana
Mes del año
Temperaturas, humedad, presión, etc de cada sensor del aula
Sensores externos: temperatura exterior, nubosidad, posición del sol, etc.
Si está encendida la calefacción o no
Si hay derroche en la hora siguiente o no (target).
Este es el CSV ya definitivo que se usará para entrenar el modelo de IA. Debería tener solo
las columnas necesarias para predecir el target (derroche en la hora siguiente).
En este CSV se han quitado las columnas de estado de puertas/ventanas, minutos abiertos,
temperatura inferida de la calefacción, etc. porque se ha considerado que no aportan
información adicional a las otras columnas y podrían generar ruido o sobreajuste en el
modelo de IA.
Fase C — Modelo de IA
Tarea 10: Crear Red neuronal
Crear un modelo de clasificación binaria (derroche sí/no) con una red neuronal.
Evaluar su rendimiento con métricas y justificar su elección.
Tarea 11: App
Crear una app donde se pueda introducir los datos de los sensores y se muestre si hay
derroche o no en la siguiente hora.Fase D — Dashboard
Crear un cuadro de mando en tiempo real con Grafana para control y análisis con:
Mínimo 2 Visualizaciones:
Temperatura de los sensores en un rango de tiempo
GAugge con la temperatura media de uno o varios sensores
Y una variable para seleccionar el sensor de temperatura a mostrar.
7. Normas de trabajo
Trabajo en equipos de 2.
Todo resultado debe incluir:
decisión tomada
justificación
evidencia (gráficas/consultas/métricas).
```
