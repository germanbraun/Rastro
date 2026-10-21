---
name: evaluar
description: Medir las preguntas de evaluación de un dominio (petróleo y gas o proveedores) con los tres caminos (sin Rastro, SQL con enlaces, con Rastro), puntuar, adjudicar y publicar el número. Usalo al sumar o cambiar una pregunta de evaluación, después de cambiar datos o reglas, o antes de mostrar un número.
---

# Evaluar un dominio

La evaluación compara tres caminos sobre las mismas preguntas, con el mismo asistente de IA:

- **B, sin Rastro:** SQL sobre las fuentes tal como se cargaron.
- **D, SQL con los enlaces de Rastro:** la línea de base justa. Se informa siempre.
- **C, con Rastro:** SPARQL sobre el Ontop del dominio.

Los archivos están en `layer/<dominio>/`: preguntas en `eval/questions.yaml`, respuestas guardadas en `respuestas/<q>-<n>-<B|D|C>.json`, resultado en `resultados.json` (lo lee la app) y `resultados.md`. El script es `layer/evaluar.py` (su docstring tiene el detalle).

## Medir una pregunta nueva o cambiada

1. **La pregunta,** en `eval/questions.yaml`, en palabras de negocio, con las definiciones que usa y su referencia (SPARQL sobre Rastro). Si tiene paráfrasis, en `consistencia/parafrasis.yaml`.
2. **Un subagente por camino, que solo ve el prompt:** generá el prompt con
   `docker compose run --rm -T layer-eval python /layer/evaluar.py energia prompt <q> 0 <B|D|C>`,
   pasáselo a un subagente nuevo sin más contexto, y probá lo que devuelve con
   `... evaluar.py energia try <q> 0 <B|D|C> < query.sql`. Hasta 3 intentos, devolviéndole el mensaje de error. Nunca le muestres la referencia ni otras respuestas.
3. **Puntuá:** `... evaluar.py energia puntaje`. Tolerancia: 5 % para números; para listas, F1 de 80 % o más.
4. **Adjudicá** cada pregunta donde los caminos difieren, con los datos de cada fuente, en `layer/<dominio>/adjudicacion.md`: quién tenía razón y por qué. La referencia sale de Rastro, así que la ventaja de Rastro puede ser circular hasta adjudicar.

## Después de cambiar datos, mapeos o reglas

```bash
docker compose run --rm -T layer-eval python /layer/evaluar.py energia rerun     # las mismas consultas guardadas, sin pedir nada nuevo
docker compose run --rm -T layer-eval python /layer/evaluar.py energia puntaje
git diff layer/energia/resultados.md
```

Si solo cambió la fecha, descartá el cambio (`git checkout layer/energia/resultados.*`). Si cambió un puntaje, explicá por qué en `docs/decisions.md`.

## Otros conjuntos de preguntas

`energia_lab` (`layer/energia_lab/`) mide las preguntas sobre las predicciones de Rastro Lab, aparte de la evaluación de Layer, con sus propios usuarios de solo lectura y notas de SQL (`layer/dominios.yaml`). Un conjunto nuevo es una entrada en `layer/dominios.yaml` (puede heredar de otra con `<<: *ancla`) y su carpeta con `eval/questions.yaml`, `consistencia/parafrasis.yaml` y `reader.sql`.

## Cuando no tiene el dato

`layer/fuera.py` mide si el asistente dice qué falta en lugar de inventar: preguntas que los datos no responden y una de control que sí (`layer/<dominio>/fuera/preguntas.yaml`). Un subagente por camino (A, B, D y C) con todas las preguntas juntas: `prompt <camino>`, después `guardar <camino>` con su JSON por stdin y, al final, `puntaje`. Todos los caminos tienen la misma regla: si los datos no alcanzan, «SIN DATOS:» y qué falta (`NO_DATA_RULE` en `layer/answer.py`).

## Reglas

- Un arreglo después de medir (al diccionario, a una regla) se vuelve a medir solo en lo afectado, con subagentes nuevos, y se dice así en `docs/decisions.md`.
- Lo reproducible son las respuestas guardadas, no la temperatura del modelo.
- Si Rastro falla por algo del diccionario, se anota; no se arregla en silencio antes de publicar.
- La prueba con preguntas que no armamos nosotros está en `docs/preguntas-a-ciegas.md`.
