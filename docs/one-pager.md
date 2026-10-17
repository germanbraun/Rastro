# Rastro Layer · en una página

**Una capa semántica sobre cuatro fuentes públicas de oncología. Un LLM pregunta en conceptos de negocio, y cada respuesta dice de qué fuente sale.**

## El problema

Ensayos (AACT), fármacos (ChEMBL), eventos adversos (openFDA) y enfermedades (MeSH) no comparten claves. El mismo fármaco es «Pembrolizumab 200 mg», CHEMBL3137343 y «KEYTRUDA». Con SQL directo, cada consulta resuelve ese cruce a su manera.

## Qué es, en términos de SQL

| Pieza | Equivale a |
|---|---|
| Ontología | El esquema de negocio que te gustaría tener |
| Mapeos (R2RML) | Definiciones de vistas: esta columna es este concepto |
| Enlaces | Las claves de join que faltaban, calculadas una vez |
| SPARQL + Ontop | SQL sobre conceptos, compilado a SQL sobre las tablas reales |

## Los números (el mismo LLM, Claude Opus 5.5)

| | SQL directo | Rastro |
|---|---|---|
| Correctas, de 20 preguntas | 18 | **20** |
| La misma pregunta de 4 formas da lo mismo | 1 de 10 | **10 de 10** |
| Una columna cambia de nombre | 5 consultas rotas | **1 línea del mapeo** |
| Un valor cambia de formato | 5 respuestas en 0, sin aviso | **avisa; 1 línea** |
| Largo de la consulta del LLM (promedio) | 726 caracteres | **368** |
| Tiempo de las 20 consultas | 20 s | **2 s** |
| De dónde sale cada dato | No lo dice | **Fuente por columna** |

Solo, sin datos, el LLM acierta 5 de 20.

## Límites, dichos de entrada

- Con las mismas tablas de enlaces, el SQL directo acertaría casi igual. El valor está en la integración hecha una vez y expuesta como vocabulario estándar.
- Una foto de octubre de 2026: 106.483 ensayos, 3.739 fármacos, 81 % de las intervenciones enlazadas.
- Las preguntas y sus referencias las hizo un asistente de IA; falta la confirmación humana.

## Próximo paso

Un piloto con datos del cliente sumados a las fuentes públicas.

---

Cómo se midió cada número: [results.md](results.md).
