# Resultados: afiliaciones de investigación en Argentina, sin Rastro y con Rastro

Fecha: 2026-10-26. Respuestas escritas por subagentes de Claude Code (Claude Opus 5.5) que solo vieron el prompt. Referencias de una revisión a ciegas hecha por GPT (asistente de IA), sin ver Rastro; falta que una persona las confirme.

| | Sin Rastro (SQL) | SQL + enlaces de Rastro | Con Rastro |
|---|---|---|---|
| Correctas (de 5) | 3 | 5 | 5 |
| Misma respuesta en las 4 formas (de 2 preguntas) | 1 | 2 | 2 |
| Correctas en la prueba de consistencia (de 8) | 8 | 8 | 8 |

| # | Pregunta | Referencia | Sin Rastro (SQL) | SQL + enlaces de Rastro | Con Rastro |
|---|---|---|---|---|---|
| e1 | ¿En cuántas de las 100 publicaciones del conjunto alguna afiliación nombra al CONICET (organización ROR https://ror.org/03cqe8w59), contando cada publicación una vez y sin sumarle las de sus institutos? Una afiliación nombra a una organización cuando su texto contiene el nombre de la organización, un nombre o alias que registra ROR, o una sigla que en ROR usa solo esa organización argentina. Una organización madre no recibe las menciones de sus institutos. | 63 | ✅ 63 | ✅ 63 | ✅ 63 |
| e2 | ¿Qué organizaciones argentinas nombran las afiliaciones de la publicación con DOI 10.1001/jamaneurol.2025.0023? Respondé con el identificador ROR completo de cada una (https://ror.org/...). Una organización argentina es una organización con al menos una sede en Argentina en ROR (versión 2.15). Una afiliación nombra a una organización cuando su texto contiene el nombre de la organización, un nombre o alias que registra ROR, o una sigla que en ROR usa solo esa organización argentina. Una organización madre no recibe las menciones de sus institutos. | https://ror.org/0081fs513, https://ror.org/0145s0423, https://ror.org/03cqe8w59 y 1 más | ✅ https://ror.org/0081fs513, https://ror.org/03cqe8w59, https://ror.org/0469ejq24 | ✅ https://ror.org/0081fs513, https://ror.org/0145s0423, https://ror.org/03cqe8w59 y 1 más | ✅ https://ror.org/0081fs513, https://ror.org/0145s0423, https://ror.org/03cqe8w59 y 1 más |
| e3 | ¿Cuántas organizaciones argentinas distintas nombra al menos una afiliación de las 100 publicaciones del conjunto? Una organización argentina es una organización con al menos una sede en Argentina en ROR (versión 2.15). Una afiliación nombra a una organización cuando su texto contiene el nombre de la organización, un nombre o alias que registra ROR, o una sigla que en ROR usa solo esa organización argentina. Una organización madre no recibe las menciones de sus institutos. | 70 | ❌ 62 | ✅ 70 | ✅ 70 |
| e4 | ¿Qué publicaciones del conjunto nombran a la Universidad de Buenos Aires (organización ROR https://ror.org/0081fs513) en alguna afiliación? Respondé con el DOI de cada una, en minúsculas. Una afiliación nombra a una organización cuando su texto contiene el nombre de la organización, un nombre o alias que registra ROR, o una sigla que en ROR usa solo esa organización argentina. Una organización madre no recibe las menciones de sus institutos. | 10.1001/jamaneurol.2025.0023, 10.1002/14651858.cd016019, 10.1002/ange.202422693 y 19 más | ✅ 10.1001/jamaneurol.2025.0023, 10.1002/14651858.cd016019, 10.1002/ange.202422693 y 19 más | ✅ 10.1001/jamaneurol.2025.0023, 10.1002/14651858.cd016019, 10.1002/ange.202422693 y 19 más | ✅ 10.1001/jamaneurol.2025.0023, 10.1002/14651858.cd016019, 10.1002/ange.202422693 y 19 más |
| e5 | De las afiliaciones de las 100 publicaciones cuyo texto menciona Argentina (contiene «argentin», sin importar mayúsculas: Argentina, Argentine, argentino…), ¿cuántas no nombran ninguna organización argentina registrada en ROR? Cuente cada afiliación de cada autor por separado. Una organización argentina es una organización con al menos una sede en Argentina en ROR (versión 2.15). Una afiliación nombra a una organización cuando su texto contiene el nombre de la organización, un nombre o alias que registra ROR, o una sigla que en ROR usa solo esa organización argentina. | 38 | ❌ 49 | ✅ 37 | ✅ 37 |

## Consistencia

Respuestas por forma (la de la evaluación y sus 3 otras formas; en las listas, cantidad de nombres):

| # | Sin Rastro (SQL) | SQL + enlaces de Rastro | Con Rastro |
|---|---|---|---|
| e1 | ✅ 4/4 correctas · 63 / 63 / 63 / 63 | ✅ 4/4 correctas · 63 / 63 / 63 / 63 | ✅ 4/4 correctas · 63 / 63 / 63 / 63 |
| e4 | ❌ 4/4 correctas · 22 / 22 / 20 / 22 | ✅ 4/4 correctas · 22 / 22 / 22 / 22 | ✅ 4/4 correctas · 22 / 22 / 22 / 22 |
