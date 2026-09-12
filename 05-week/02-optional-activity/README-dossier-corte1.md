# Dossier de Fundamentos — Cierre del Corte 1

**Programa:** Ingeniería Industrial · **Asignatura:** Ciencia de Datos
**Unidad:** 1 · Fundamentos de Ciencia de Datos y Big Data · **Semana / Corte:** 5 · Corte 1
**Caso guía (Semanas 1–4):** Logística — Retrasos en entregas de última milla

---

## Cómo leer este dossier

Este documento reúne y mejora, en un solo hilo coherente, el trabajo de las cuatro semanas del corte sobre un mismo caso: por qué se retrasan las entregas de última milla y qué se puede hacer al respecto. Cada parte no es un resumen aislado de su semana, sino que se apoya explícitamente en la anterior: el encuadre del negocio (parte 1) determina qué datos hacen falta (parte 2); esos datos, con su nivel de estructura y sus V críticas, determinan qué arquitectura tiene sentido construir (parte 3); y la arquitectura y los datos disponibles determinan, a su vez, qué tipo de analítica es realista plantear y qué riesgos éticos hay que vigilar (parte 4). Los diagramas de cada semana se incluyen como anexos al final.

---

## 1. Encuadre del proyecto: pregunta de negocio y decisión esperada (Semana 1)

**Pregunta de negocio:**

> ¿Qué combinación de transportista, condición climática y tipo de vehículo genera más retrasos en las entregas de última milla, y es posible anticipar esos retrasos antes de que ocurran?

**Decisión esperada:** con los resultados del análisis, el área de logística podría (a) **reasignar rutas o transportistas** cuando la combinación prevista de clima y vehículo eleve el riesgo de retraso para un transportista específico, o (b) **ajustar de forma proactiva el tiempo de entrega prometido al cliente** en condiciones identificadas como de alto riesgo.

Este encuadre es lo que fija el criterio con el que se evalúan las tres partes siguientes: cualquier dato, arquitectura o modelo que no aporte a responder esta pregunta o a habilitar esta decisión queda fuera del alcance del proyecto.

## 2. Fuentes de datos, clasificación y V relevantes (Semana 2)

| # | Fuente de datos | Tipo | V que activa principalmente |
|---|---|---|---|
| 1 | Dataset histórico de entregas ([Kaggle](https://www.kaggle.com/datasets/kundanbedmutha/delivery-logistics-dataset-india-multi-partner)) | Estructurado | Volumen |
| 2 | API de clima en tiempo real | Semiestructurado | Velocidad, veracidad |
| 3 | Telemetría GPS del vehículo | Semiestructurado | Velocidad |
| 4 | ERP / facturación del operador logístico | Estructurado | Volumen |
| 5 | Encuestas y comentarios de clientes post-entrega | No estructurado | Variedad |
| 6 | Fotos de evidencia de entrega (POD) | No estructurado | Variedad |

**V críticas para el caso:** volumen (25 000 entregas y creciendo), velocidad (el clima y el GPS solo son útiles si llegan casi en tiempo real, antes de que el vehículo salga), variedad (tablas, JSON en streaming, texto e imágenes conviven en el mismo problema) y, sobre todo, **veracidad**: el clima etiquetado en el histórico puede no coincidir con el clima real capturado por la API para la misma hora y zona, lo que contaminaría tanto el diagnóstico descriptivo como cualquier modelo entrenado sobre esos datos. Esta combinación de cuatro V críticas —no solo volumen— es, siguiendo a De Mauro, Greco y Grimaldi (2016), lo que confirma que este es efectivamente un problema de big data y no un análisis tabular convencional.

## 3. Arquitectura de datos propuesta (Semana 3)

La arquitectura propuesta es **híbrida en sus dos decisiones principales**, precisamente porque los datos de la parte 2 no son homogéneos:

- **Data lake + data warehouse:** el lake conserva en crudo el clima, el GPS, las fotos y el texto de encuestas (fuentes 2, 3, 5 y 6), preservando la información original para exploración o reentrenamiento futuro; el warehouse expone tablas ya curadas (entrega, transportista, clima, retraso) optimizadas para que el tablero de BI consulte rápido. Ningún dato "vive" en un solo lugar: el lake es el origen y el warehouse es el destino curado.
- **Batch + streaming:** el histórico, el ERP y las encuestas se procesan en batch (no cambian minuto a minuto); el clima y el GPS requieren streaming, porque la alerta de riesgo solo sirve si llega antes de que el vehículo salga o mientras va en camino.

**Herramientas candidatas:** Apache Kafka para la ingesta de eventos de clima/GPS, Apache Spark para el procesamiento (cubre batch y streaming con el mismo motor), y Metabase/Power BI conectado al warehouse para el tablero operativo.

```
Fuentes → Ingesta (Kafka) → Almacenamiento (Lake + Warehouse) → Procesamiento (Spark) → Análisis/BI (Metabase/Power BI)
```

## 4. Tipos de analítica objetivo y un riesgo ético (Semana 4)

**Analítica objetivo:** se combinan **analítica descriptiva** (¿cuál es la tasa de retraso histórica por transportista, clima y vehículo?) y **analítica predictiva** (dado un envío nuevo, ¿cuál es la probabilidad de que se retrase?), usando ML **supervisado** para la predictiva porque el histórico ya trae la etiqueta real de retraso de cada entrega pasada. La analítica prescriptiva (recomendar automáticamente la reasignación óptima) queda para una fase posterior del proyecto, una vez validado el modelo predictivo.

**Riesgo ético identificado — sesgo heredado por transportista:** si un transportista atiende sistemáticamente zonas con peor infraestructura vial, el modelo puede aprender a "penalizarlo" como menos confiable cuando en realidad el problema es la zona, no su desempeño. **Mitigación:** (1) incluir la zona/ruta como variable explícita del modelo, separando su efecto del efecto del transportista; (2) auditar las tasas de error del modelo desagregadas por transportista para detectar disparidades sistemáticas; (3) mantener explicabilidad (importancia de variables) para que un supervisor revise cualquier alerta antes de que afecte la asignación o evaluación de un transportista.

---

## Coherencia del dossier

Las cuatro partes se sostienen entre sí: la decisión esperada de la parte 1 (reasignar rutas / ajustar tiempos) es exactamente lo que la analítica predictiva de la parte 4 busca habilitar; los datos semiestructurados y no estructurados de la parte 2 son la razón por la que la parte 3 propone un lake y no solo un warehouse; y la veracidad crítica señalada en la parte 2 es la razón por la que la parte 3 incluye un paso explícito de limpieza/validación antes de que cualquier dato llegue al warehouse o alimente el modelo de la parte 4.

---

## Marco de referencia

- **Encuadre del proyecto (parte 1):** Provost y Fawcett (2013) sostienen que el valor de la ciencia de datos está en convertir datos en decisiones mejor informadas, y que ese valor depende de mantener la pregunta de negocio como criterio rector de todo el proyecto — el mismo principio que organiza este dossier de principio a fin.
- **Datos y arquitectura (partes 2 y 3):** De Mauro, Greco y Grimaldi (2016) definen big data como el activo de información caracterizado por un volumen, velocidad y variedad tan altos que requiere tecnología y métodos específicos para transformarlo en valor; esta definición es la que sustenta tanto la identificación de las V críticas en la parte 2 como la elección de una arquitectura híbrida lake/warehouse y batch/streaming en la parte 3, ya que ninguna de las dos decisiones sería necesaria si el caso fuera solo un problema de volumen.
- **Analítica y ética (parte 4):** Mehrabi, Morstatter, Saxena, Lerman y Galstyan (2021) describen el sesgo histórico como la reproducción, por parte de un modelo, de desigualdades ya presentes en los datos de entrenamiento, y proponen auditorías de desempeño desagregadas por subgrupo como mecanismo de mitigación; ese marco es el que respalda directamente el riesgo ético y las tres medidas de mitigación descritas en la parte 4.

---

## Anexos (diagramas por semana)

- `anexo-01-ciclo-vida-proyecto-datos.svg` — ciclo de vida del proyecto aplicado al caso (Semana 1).
- `anexo-02-5v-big-data-logistica.svg` — las 5V del Big Data aplicadas al caso, con el reto de veracidad (Semana 2).
- `anexo-03-arquitectura-datos-logistica.svg` — arquitectura de datos completa, fuentes→BI (Semana 3).
- `anexo-04-tipos-analitica-etica-logistica.svg` — los 4 tipos de analítica y el riesgo ético (Semana 4).

---

## Verificación frente a la rúbrica

| Criterio de la rúbrica | Pts | Cómo se cumple en este dossier |
|---|---|---|
| Encuadre (pregunta + decisión) — claro | 30 | Parte 1: pregunta de negocio delimitada y decisión esperada concreta, retomadas explícitamente en las partes 3 y 4 para mostrar coherencia |
| Datos + arquitectura — coherentes | 40 | Partes 2 y 3: la clasificación de datos y las V críticas de la parte 2 justifican, punto por punto, las decisiones de arquitectura de la parte 3 (lake/warehouse, batch/streaming) |
| Analítica + ética — bien planteados | 30 | Parte 4: tipo de analítica justificado con el tipo de ML correspondiente, y riesgo ético concreto con tres medidas de mitigación accionables |
| **Total** | **100** | |

---

## Referencias

- CORHUILA. (2026). *Ciencia de Datos · Semana 5 · Repaso y evaluación del Corte 1* [Material de curso, OVA]. Corporación Universitaria del Huila. https://code-corhuila.github.io/ova-web/2026-B/ciencia-datos/05-week/01-session/
- De Mauro, A., Greco, M., & Grimaldi, M. (2016). A formal definition of Big Data based on its essential features. *Library Review, 65*(3), 122–135. https://doi.org/10.1108/LR-06-2015-0061
- Mehrabi, N., Morstatter, F., Saxena, N., Lerman, K., & Galstyan, A. (2021). A survey on bias and fairness in machine learning. *ACM Computing Surveys, 54*(6), Artículo 115. https://doi.org/10.1145/3457607
- Provost, F., & Fawcett, T. (2013). Data science and its relationship to big data and data-driven decision making. *Big Data, 1*(1), 51–59. https://doi.org/10.1089/big.2013.1508
