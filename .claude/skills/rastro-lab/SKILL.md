---
name: rastro-lab
description: Entrenar, medir y explicar el modelo de gas de Rastro Lab (pozos nuevos de shale gas de Vaca Muerta) con variables de las tablas crudas y de Rastro, validarlo y armar la prueba a ciegas de las explicaciones. Usalo al tocar lab/, app/lab.py, energia:WellStart o energia:Fracturing, o al publicar un número de Lab.
---

# Rastro Lab

Rastro Lab muestra qué agrega la tecnología semántica al aprendizaje automático. **Lo que se mide es la explicación, no la precisión.** El estudio está en `docs/lab-gas-vaca-muerta.md`.

## Qué es

- **Lo que se predice:** el gas de los meses 2 a 7 de un pozo nuevo de shale gas de Vaca Muerta, en millones de m³ (`energia:gasMonths2to7`; el primer mes suele ser parcial).
- **El mismo modelo, dos veces** (`lab/gas/modelo.py`): una regresión lineal (ridge, en numpy). A toma las variables con SQL de las tablas crudas; B, de Rastro (SPARQL). Las mismas ideas de variables: operadora, concesión, participación y fractura (rama, etapas, arena, agua, presión).
- **Entrenar y probar por fecha:** entrena con los pozos que empezaron antes de 2025 y prueba con los de 2025.
- **La explicación** es exacta: la predicción es el pozo promedio más el aporte de cada variable. Con Rastro se agrupa en dos factores (la concesión con su operadora y socios, y cómo se fracturó), cada uno con por qué suma o resta y sus hechos con regla, evidencia y fuente.

## Reglas

1. **No usar el futuro.** La operadora y el tipo de pozo son los del primer mes (`energia:WellStart`), no los de hoy. La fractura es la informada hasta el mes en que arrancó. La fecha de carga de cada dato (`energia:loadedOn`) se guarda y se marca si llegó después.
2. **A tiene que ser lo que haría un analista razonable con SQL,** no algo mal armado a propósito. Si un dato se calcula por los dos caminos (el gas), tiene que coincidir: el script lo controla.
3. **La explicación no puede contradecir al modelo.** Si dos variables van juntas (la operadora y los socios son fijos dentro de una concesión; la rama y las etapas crecen juntas), se dice y se muestran juntas; nunca una regla general («más rama, más gas») que el modelo no cumple.
4. **La explicación no muestra lo que se predice** (el gas real del pozo no va en ninguna evidencia).
5. **Lo que se carga solo para Lab no cambia Layer** (`data/lab-gas/`, esquemas `capitulo4_anterior` y `fractura`). Después de cargar, la skill `evaluar` con `rerun` tiene que dar lo mismo.
6. **Números honestos:** la precisión depende del corte por fecha. Se informa el error y el R² hacia el futuro y se dice que es el mejor caso si lo es.

## Comandos (en la máquina, con `requirements-dev.txt` y Ontop de energía en :8082)

```bash
python3 lab/gas/modelo.py                 # error de A y B, datos dudosos, lo que aprendió, un pozo explicado
python3 lab/gas/modelo.py <idpozo>        # la explicación de otro pozo
python3 lab/gas/modelo.py --12-meses      # validación con el gas de 12 meses
python3 lab/gas/modelo.py --como-trabajo-publicado # validación con el diseño de un trabajo publicado con las mismas fuentes
python3 lab/gas/a_ciegas.py               # arma docs/lab-explicaciones-a-ciegas.md (clave en lab/gas/a-ciegas-clave.json)
python3 lab/gas/modelo.py --publicar      # guarda la corrida y sus predicciones en Rastro (esquema lab_gas, energia:Prediction)
```

La app lo muestra en la pestaña **Rastro Lab** (`app/lab.py`) y en el momento 3 de la demo. Después de cambiar `lab/gas/modelo.py` o `app/lab.py`, `docker compose restart app`.

## Las predicciones, en Rastro

Cada corrida publicada queda en Rastro: `energia:ModelRun` (versión = huella de `lab/gas/modelo.py`, fecha, corte, error, `energia:current`), `energia:Prediction` (valor, rango, `prov:wasGeneratedBy` la corrida, `prov:used` el inicio del pozo, su fractura y la participación de la operadora) y `energia:Contribution` (el aporte de cada factor). Las preguntas 11 y 12 de `ontology/energia/competency-questions.md` las consultan, y el asistente de IA las puede responder en «Mi propia pregunta». Las tablas (`lab_gas`) no se borran al rearmar los enlaces.

- **Publicá una corrida nueva** cada vez que cambie el modelo o sus datos, y revisá que la pregunta 11 cuente lo mismo que «datos dudosos» del modelo.
- **El rango** sale de los errores del año anterior a la prueba (sin mirar la prueba): se informa qué parte de los pozos de prueba cayó adentro (hoy 71 de 100), aunque no llegue a 80.

## Al cambiar algo

1. Corré `python3 lab/gas/modelo.py` y leé la explicación de dos o tres pozos: ¿dice algo falso? ¿muestra un dato que no debería?
2. Volvé a armar la prueba a ciegas si cambió la explicación.
3. Actualizá los números en `docs/lab-gas-vaca-muerta.md`, `docs/decisions.md`, el guion y la diapositiva «Predecir» (skill `mazos`).
