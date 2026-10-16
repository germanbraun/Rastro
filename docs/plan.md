# Plan de desarrollo — MVPs de tecnologías semánticas

15 oct 2026 · German Braun

## Nombre comercial

Recomendación: **Rastro**, con dos productos: **Rastro Layer** (capa semántica, MVP 2) y **Rastro Lab** (pipeline de data science, MVP 1). El nombre resume el valor diferencial de ambos: cada dato y cada predicción deja rastro de dónde viene y por qué.

| Nombre | Idea que comunica | A favor | En contra |
|---|---|---|---|
| Rastro | Trazabilidad, linaje, explicabilidad | Corto, se pronuncia bien en inglés y español, conecta con el baqueano que sigue el rastro | Menos explícito sobre integración |
| Confluencia | Ríos que se unen: fuentes que convergen | Muy visual, raíz patagónica | Choca con Confluence (Atlassian) en software |
| Trama | Hilos distintos tejidos en una sola tela | Metáfora clara de integración | Palabra muy común, difícil de buscar |
| Sextante | Orientarse con referencias comunes | Suena a precisión | Más largo, menos cercano |

Antes de fijarlo: buscar el nombre en GitHub, en marcas registradas (INPI y EUIPO) y disponibilidad de dominio.

## Principios y alcance

Se construye primero Rastro Layer, porque Rastro Lab reutiliza su ontología, sus mapeos y la resolución de entidades. Cada fase termina con un checkpoint que se puede probar y mostrar antes de seguir.

- **Un área terapéutica, no todo el universo.** Recorte sugerido: oncología. Mantiene los volúmenes manejables en una laptop y los ejemplos son entendibles para un comercial.
- **Datos reales, sin copiarlos al repo.** El repo guarda scripts de descarga y carga, nunca los datos.
- **Preguntas de competencia antes que ontología.** Se escriben 10–15 preguntas de negocio y la ontología crece solo lo necesario para responderlas.
- **Cada afirmación comercial con un número propio.** Precisión de preguntas respondidas, métricas del modelo, tiempo de preparación de features.
- **Todo levanta con un comando** (`docker compose up`), para que la demo sea reproducible.

Fuera de alcance: ontología completa del dominio, tiempo real, agentes autónomos, fine-tuning de modelos, autenticación y multiusuario.

## Estructura del repositorio

Un monorepo con las piezas compartidas arriba y una carpeta por producto.

```
rastro/
├── infra/            docker-compose: Postgres, Ontop, triplestore
├── data/             scripts de descarga y carga (AACT, ChEMBL, openFDA, MeSH)
├── ontology/         ontología en Turtle + preguntas de competencia
├── mappings/         mapeos R2RML/OBDA por fuente
├── shapes/           shapes SHACL de validación
├── linking/          resolución de entidades de fármacos
├── layer/            Rastro Layer: NL→SPARQL, NL→SQL baseline, API
│   └── eval/         preguntas con respuestas de referencia
├── lab/              Rastro Lab: features, modelos, linaje
│   └── notebooks/
├── app/              frontend de ambas demos
└── docs/             guion de demo, decisiones, resultados
```

## Fases

Ocho fases: de la 0 a la 4 construyen Rastro Layer, de la 5 a la 7 Rastro Lab, y la 8 prepara la demo. Cada una cierra con un checkpoint verificable.

### Fase 0 — Infraestructura y datos

- [x] Crear el repo con la estructura y un README mínimo
- [x] docker-compose con Postgres, Ontop y GraphDB Free
- [x] Script de carga de AACT en Postgres
- [x] Script de carga de ChEMBL (subconjunto: compuestos con targets en oncología)
- [ ] Script de descarga de eventos adversos de openFDA para la lista de fármacos del recorte, guardados como JSON y cargados a una tabla
- [ ] Carga de MeSH (RDF) en el triplestore

**Checkpoint:** `docker compose up` y una consulta SQL de conteo por fuente devuelven datos.

### Fase 1 — Preguntas de competencia y ontología

- [ ] Escribir 10–15 preguntas de negocio en `ontology/competency-questions.md`
- [ ] Ontología de 10–15 clases: Fármaco, Target, Ensayo, Condición, Sponsor, Fase, EventoAdverso, Reporte
- [ ] Reutilizar MeSH para condiciones y alinear con estándares donde aporte (por ejemplo, Schema.org o vocabularios de ChEMBL)
- [ ] Escribir a mano la query SPARQL de cada pregunta de competencia

**Checkpoint:** la ontología carga sin errores y cada pregunta tiene su SPARQL escrito.

### Fase 2 — Mapeos virtuales y resolución de entidades

- [ ] Mapeos de AACT a la ontología (Ontop)
- [ ] Mapeos de ChEMBL a la ontología
- [ ] Mapeo de la tabla de eventos adversos de openFDA
- [ ] Resolución de fármacos entre las tres fuentes: por identificadores primero (ChEMBL ID, UNII, nombre normalizado), y LLM solo para los casos ambiguos
- [ ] Revisar a mano una muestra de 100 enlaces y medir precisión
- [ ] Shapes SHACL básicas sobre el grafo integrado

**Checkpoint:** las preguntas de competencia de la Fase 1 devuelven resultados correctos sobre las tres fuentes, sin copiar datos.

### Fase 3 — Preguntas en lenguaje natural

- [ ] Conjunto de evaluación: 20–30 preguntas con su respuesta de referencia, en `layer/eval/`
- [ ] Baseline: LLM que genera SQL directo sobre los esquemas crudos
- [ ] Rastro Layer: LLM que genera SPARQL con la ontología como contexto
- [ ] Script que corre ambos y produce una tabla de precisión por pregunta
- [ ] Registrar qué fuente aportó cada dato de la respuesta

**Checkpoint:** tabla comparativa de precisión, SQL directo contra capa semántica, con el mismo modelo.

### Fase 4 — Interfaz de Rastro Layer

- [ ] Vista de esquemas fuente, ontología y mapeos
- [ ] Caja de pregunta con respuesta en tabla y una marca de fuente por celda
- [ ] Panel «¿cómo lo supe?»: query generada y camino en el grafo
- [ ] Modo comparación lado a lado contra el baseline SQL

**Checkpoint:** demo de 3 minutos de Rastro Layer sin tocar la terminal.

### Fase 5 — Modelo baseline de Rastro Lab

- [ ] Definir la variable objetivo: ensayo terminado o retirado contra completado, sobre ensayos cerrados
- [ ] Split temporal: entrenar con ensayos iniciados hasta un año de corte y evaluar con los posteriores
- [ ] Features planas solo desde AACT
- [ ] Entrenar LightGBM y registrar métricas (AUC, F1) en `docs/results.md`

**Checkpoint:** baseline reproducible con un solo comando.

### Fase 6 — Features semánticas

- [ ] Normalizar condiciones de texto libre a MeSH con el LLM y medir precisión sobre una muestra
- [ ] Generalizar condiciones por la jerarquía de MeSH
- [ ] Agregar features de la capa integrada: eventos adversos del fármaco, cantidad de targets, historial del sponsor, siempre con datos anteriores a la fecha de inicio del ensayo
- [ ] Validación SHACL previa al entrenamiento, con conteo de registros rechazados
- [ ] Reentrenar el mismo modelo y comparar

**Checkpoint:** tabla A/B baseline contra semántico en el mismo split.

### Fase 7 — Linaje, explicabilidad e interfaz de Rastro Lab

- [ ] Linaje con PROV-O: cada feature enlazada a su fuente y concepto
- [ ] Catálogo de features navegable
- [ ] Explicación de una predicción individual: valores SHAP traducidos a conceptos y caminos en el grafo
- [ ] Vista del pipeline y de métricas comparadas

**Checkpoint:** demo de 3 minutos de Rastro Lab sin tocar la terminal.

### Fase 8 — Demo para comerciales

- [ ] Guion de 5 minutos que une ambos productos
- [ ] Video grabado como respaldo
- [ ] One-pager con los números obtenidos en las fases 3 y 6

**Checkpoint:** alguien de ventas da la demo siguiendo solo el guion.

## Riesgos y decisiones abiertas

El riesgo técnico principal es la resolución de fármacos entre fuentes. El riesgo comercial principal es que la mejora del modelo sea chica: por eso el argumento de Rastro Lab se apoya también en reutilización, linaje y explicabilidad.

| Riesgo | Mitigación |
|---|---|
| Nombres de fármacos inconsistentes entre AACT, ChEMBL y FAERS | Identificadores primero, LLM solo para ambiguos, precisión medida a mano |
| Fuga de información en el modelo (usar datos posteriores al inicio del ensayo) | Split temporal y features calculadas con fecha de corte por ensayo |
| FAERS es ruidoso y con duplicados | Usarlo agregado (conteos por fármaco), nunca como verdad clínica; aclararlo en la demo |
| Costo y variabilidad del LLM en la evaluación | Fijar modelo y temperatura 0, cachear respuestas, versionar los resultados |
| Licencias (ChEMBL es CC BY-SA) | Revisar condiciones antes de mostrar a clientes y citar las fuentes en la interfaz |
| Rendimiento de la virtualización con Ontop | Materializar solo lo que sea lento, documentando por qué |

### Decisiones abiertas

- [x] ¿Oncología u otra área terapéutica? → Oncología (ver [decisions.md](decisions.md))
- [x] ¿Qué triplestore? ¿Se construye sobre otra plataforma o de forma independiente? → GraphDB Free, independiente (ver [decisions.md](decisions.md))
- [ ] ¿Qué LLM para la evaluación, y se prueba también con un modelo abierto?
- [ ] ¿Frontend propio (React) o una herramienta rápida (Streamlit) para la primera versión?
- [ ] ¿Repo público o privado?
