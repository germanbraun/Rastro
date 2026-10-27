# Resultados: las predicciones de Rastro Lab, sin Rastro y con Rastro

Fecha: 2026-10-27. Respuestas escritas por subagentes de Claude Code (Claude Opus 5.5) que solo vieron el prompt. Las referencias las escribió un asistente de IA; falta que las confirme una persona.

| | Sin Rastro (SQL) | SQL + enlaces de Rastro | Con Rastro |
|---|---|---|---|
| Correctas (de 5) | 4 | 5 | 5 |
| Misma respuesta en las 4 formas (de 0 preguntas) | 0 | 0 | 0 |
| Correctas en la prueba de consistencia (de 0) | 0 | 0 | 0 |

| # | Pregunta | Referencia | Sin Rastro (SQL) | SQL + enlaces de Rastro | Con Rastro |
|---|---|---|---|---|---|
| l01 | En la corrida vigente del modelo de gas, ¿cuántas predicciones de pozos de prueba (los que empezaron a producir en 2025) se apoyan en un dato corregido a mano, es decir, una participación de la operadora corregida con un documento o una operadora cuyo nombre se unió a su grupo por una corrección revisada? | 24 | ❌ 0 | ✅ 24 | ✅ 24 |
| l02 | En la corrida vigente del modelo de gas, ¿cuáles son los 3 pozos de prueba (los que empezaron a producir en 2025) con más gas esperado? Devolvé sus identificadores de pozo. | 166586, 166587, 166588 | ✅ 166586, 166587, 166588 | ✅ 166586, 166587, 166588 | ✅ 166586, 166587, 166588 |
| l03 | En la corrida vigente del modelo de gas, ¿cuántas predicciones de pozos de prueba (los que empezaron a producir en 2025) usaron una fractura que se cargó en el portal en un mes posterior al primer mes con producción del pozo? La fractura de un pozo son las fracturas informadas hasta el mes en que arrancó; se cuenta la fecha de carga más reciente de esas fracturas. | 36 | ✅ 36 | ✅ 36 | ✅ 36 |
| l04 | Si la fuente corrige la fractura informada número 4799 (su identificador en los datos de fractura, Adjunto IV), ¿qué pozos tienen una predicción en la corrida vigente que hay que rehacer porque usó esa fractura? Devolvé sus identificadores de pozo. | 165404 | ✅ 165404 | ✅ 165404 | ✅ 165404 |
| l05 | En la corrida vigente del modelo de gas, ¿qué porcentaje de participación de su operadora en la concesión usó la predicción del pozo 166271? | 55 | ✅ 55 | ✅ 55 | ✅ 55 |

## Consistencia

Respuestas por forma (la de la evaluación y sus 3 otras formas; en las listas, cantidad de nombres):

| # | Sin Rastro (SQL) | SQL + enlaces de Rastro | Con Rastro |
|---|---|---|---|
