# Plan de desarrollo — Rastro

Dos MVP comerciales sobre tecnologías semánticas, en oncología y con datos públicos:

- **Rastro Layer:** preguntás en lenguaje natural y la respuesta junta datos de varias fuentes, diciendo de dónde viene cada dato.
- **Rastro Lab:** un modelo que predice si un ensayo clínico se va a detener, con explicaciones que cualquiera entiende.

El nombre resume lo que tienen en común: cada dato y cada predicción deja rastro de dónde viene.

## Principio: simple

Es un MVP comercial. Lo tiene que entender alguien de ventas, no solo un ingeniero.

- **Lo mínimo que funciona.** Si una pieza no hace falta para la demo o para un número de la demo, no se hace.
- **Palabras simples.** Nombres de clases, columnas y pantallas que se entiendan sin explicación: "Fármaco", "Ensayo", "detenido", no siglas internas.
- **Cada paso se puede mostrar.** Cada fase termina en algo que se ve funcionar.
- **Cada afirmación con un número propio.** Medido por nosotros, no prometido.
- **Todo levanta con un comando** (`docker compose up`).

Fuera de alcance: ontología completa del dominio, tiempo real, agentes, fine-tuning, usuarios y permisos.

## Qué hay en el repo

```
infra/       docker-compose: Postgres, Ontop, GraphDB
data/        scripts de descarga y carga (los datos no se versionan)
ontology/    preguntas, ontología y una query por pregunta
mappings/    cómo se leen las tablas como grafo: R2RML, que lee Ontop
linking/     enlace de fármacos entre fuentes
layer/       Rastro Layer: preguntas en lenguaje natural
lab/         Rastro Lab: features y modelo
app/         la interfaz de las dos demos
docs/        plan, decisiones, resultados y guion
```

## Fases

Cada fase cierra con un checkpoint que se puede mostrar. Las fases 0 a 4 construyen Rastro Layer, las 5 a 7 Rastro Lab y la 8 arma la demo.

### Fase 0 — Datos ✅

Postgres, Ontop y GraphDB levantan con un comando, con las cuatro fuentes cargadas: AACT (106 mil ensayos de oncología), ChEMBL (3.739 fármacos), openFDA (eventos adversos de 2.064 fármacos) y MeSH completo con búsqueda de texto.

**Checkpoint:** el conteo por fuente devuelve datos de las cuatro.

### Fase 1 — Preguntas y ontología ✅

Ocho preguntas de negocio y una ontología de siete clases (Ensayo, Fármaco, Target, Sponsor, dos de eventos adversos y Fuente) que alcanza para responderlas. Cada pregunta tiene su query SPARQL.

**Checkpoint:** la ontología carga y cada pregunta tiene su query.

### Fase 2 — Conectar las fuentes ✅

Mapeos R2RML para las cuatro fuentes, MeSH copiado en Postgres (sin federar) y enlaces en SQL legible: el 74 % de las intervenciones de tipo fármaco enlaza con ChEMBL, con 99 de 100 enlaces correctos en la revisión a mano, y el 99,8 % de los ensayos tiene su condición en MeSH. No hizo falta el LLM. Las ocho preguntas responden en un segundo.

**Checkpoint:** las ocho preguntas devuelven respuestas correctas, y sabemos qué porcentaje de enlaces está bien.

### Fase 3 — Preguntas en lenguaje natural ✅

El mismo LLM (Claude Opus 5.5) responde las mismas 20 preguntas de tres formas:

| | Cómo responde | Qué muestra |
|---|---|---|
| A. LLM solo | Con lo que sabe, sin datos | Inventa números y no cita fuentes |
| B. LLM + SQL crudo | SQL sobre las tablas de las fuentes tal como se cargaron | Tiene que adivinar cómo se cruzan las fuentes |
| C. LLM + Rastro | SPARQL sobre la ontología de Rastro | Los cruces ya están resueltos y cada dato tiene fuente |

- [x] 20 preguntas con su respuesta correcta (`layer/eval/questions.yaml`)
- [x] Las tres formas de responder (`layer/answer.py`), con los mismos reintentos para B y C
- [x] Un script que puntúa y guarda las respuestas en el repo (`layer/eval/`)
- [x] Correr la evaluación con Claude Opus 5.5 (subagentes de Claude Code, sin API key)
- [x] Adjudicar las diferencias entre B y C con ensayos reales (`layer/eval/adjudication.md`), y corregir los enlaces de Rastro que fallaban

Las respuestas quedan guardadas: en otra máquina se ven y se puntúan sin API key.

**Resultado:** con Rastro, 20 de 20; con SQL directo, 18 de 20 (con queries 3 a 4 veces más largas); el LLM solo, 5 de 20. Detalle en `docs/results.md` y `layer/eval/adjudication.md`.

**Checkpoint:** un número para vender: "con Rastro acierta X de 20; con SQL directo, Y; solo, Z".

### Fase 4 — Interfaz de Rastro Layer

En Streamlit (`app/`), en http://localhost:8501 con `docker compose up`.

- [x] Una caja para preguntar: las 20 preguntas de ejemplo funcionan sin LLM (usan las queries guardadas, ejecutadas en vivo); las libres usan el LLM configurado
- [x] La respuesta en una tabla, con las fuentes que usó y la fuente de cada columna
- [x] Un botón "¿cómo lo supe?" con la query, las fuentes y sus licencias
- [x] Una pestaña "Con y sin Rastro": el puntaje y qué significa, las tres respuestas de cada pregunta lado a lado, por qué falló cada respuesta incorrecta, y el SQL que genera Ontop
- [x] Dónde vive cada fuente (🐘 Postgres, 🕸️ GraphDB) y una explicación de cómo funciona
- [x] El historial de intentos de cada query: qué falló y qué escribió el LLM después
- [x] Preguntas frecuentes en una pestaña (`app/faq.yaml`), en lugar de más texto en pantalla
- [x] Un diagrama de cómo responde cada forma, y la unificación de columnas de los mapeos visible
- [ ] Ensayar la demo de 3 minutos con alguien que no sea técnico

**Checkpoint:** demo de 3 minutos sin tocar la terminal.

### Fase 5 — Modelo base de Rastro Lab

- [ ] Qué se predice: si un ensayo cerrado terminó o se detuvo (terminado o retirado)
- [ ] Entrenar con ensayos que empezaron antes de un año de corte y evaluar con los posteriores
- [ ] Solo datos de AACT, un modelo estándar (LightGBM), y anotar el resultado en `docs/results.md`

**Checkpoint:** un comando entrena el modelo y muestra su precisión.

### Fase 6 — Features de la capa semántica

- [ ] Agregar lo que solo la capa sabe: eventos adversos previos de los fármacos, historial del sponsor, cantidad de targets y la condición agrupada por MeSH
- [ ] Siempre con datos anteriores al inicio de cada ensayo
- [ ] Reentrenar el mismo modelo y comparar

**Checkpoint:** una tabla "antes y después" con el mismo modelo y los mismos ensayos.

### Fase 7 — Interfaz de Rastro Lab

- [ ] Elegir un ensayo y ver la probabilidad de que se detenga
- [ ] Las tres razones principales, en palabras simples
- [ ] De qué fuente viene cada razón

**Checkpoint:** demo de 3 minutos sin tocar la terminal.

### Fase 8 — Demo comercial

- [ ] Guion de 5 minutos con los dos productos
- [ ] Video de respaldo
- [ ] Una página con los números de las fases 3 y 6

**Checkpoint:** alguien de ventas da la demo siguiendo solo el guion.

## Riesgos

| Riesgo | Qué hacemos |
|---|---|
| Los fármacos se llaman distinto en cada fuente | Resuelto con reglas simples: 81 % enlazado, 98-99 % correcto |
| El modelo usa datos del futuro sin querer | Solo datos anteriores al inicio de cada ensayo |
| Los eventos adversos de FAERS son ruidosos | Usarlos como conteos y decirlo en la interfaz |
| La mejora del modelo es chica | El argumento de Lab también es la explicación y la procedencia, no solo la precisión |
| Respuestas del LLM que cambian | Modelo fijo, temperatura 0 y respuestas guardadas |
| Licencias (ChEMBL es CC BY-SA) | Citar las fuentes en la interfaz |

## Decisiones

Tomadas (detalle en [decisions.md](decisions.md)):

- [x] Oncología como recorte
- [x] GraphDB Free como triplestore
- [x] Ontología mínima: siete clases, condiciones como descriptores de MeSH

- [x] MeSH copiado en Postgres: Ontop responde solo, sin federar con GraphDB
- [x] Claude Opus 5.5 para la evaluación; el modelo es configurable para la demo en vivo
- [x] Interfaz en Streamlit, lo más simple para un MVP

Abiertas:

- [ ] ¿El repo de GitHub queda privado?
