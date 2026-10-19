# Rastro Layer · en una página (versión técnica)

> **Los datos cambian. Tus preguntas, no.**

**Una capa semántica sobre cuatro fuentes públicas de oncología. Los datos se integran una vez; un LLM pregunta en conceptos de negocio, y cada respuesta dice de qué fuente sale.**

## Qué gana una empresa

- **Respuestas consistentes:** una sola definición de cada concepto.
- **Preguntas en lenguaje de negocio:** el LLM lee un vocabulario, no cientos de columnas.
- **Cada dato con su fuente:** respuestas auditables.
- **Menos mantenimiento:** si una fuente cambia, se arregla en un lugar.
- **Datos de afuera sin cargarlos:** se une con Wikidata por identificadores compartidos.
- **Sin atarse a un proveedor:** estándares abiertos del W3C.

## Qué es, en términos de SQL

| Pieza | Equivale a |
|---|---|
| Ontología | El esquema de negocio que te gustaría tener |
| Mapeos (R2RML) | Definiciones de vistas: esta columna es este concepto |
| Enlaces | Las claves de join que faltaban, calculadas una vez |
| SPARQL + Ontop | SQL sobre conceptos, compilado a SQL sobre las tablas reales |

## La evidencia (el mismo LLM, Claude Opus 5.5)

| | SQL directo | SQL + enlaces de Rastro | Rastro |
|---|---|---|---|
| Correctas, de 20 | 18 | 20 | **20** |
| Misma respuesta, preguntando de 4 formas | 1 de 10 | 10 de 10 | **10 de 10** |
| Una columna de la fuente cambia de nombre | 5 consultas rotas | 5 consultas rotas | **1 línea del mapeo** |
| Un valor cambia de formato | 5 respuestas en 0, sin aviso | igual | **avisa; 1 línea** |
| El negocio cambia una definición | cada consulta | cada consulta | **1 línea de la ontología** |
| De dónde sale cada dato | no | no | **por columna** |
| Une datos de Wikidata en la misma consulta | no | no | **sí** |

**Cómo leerla:** la precisión y la consistencia vienen de integrar una vez. La capa semántica agrega que esa integración se mantiene en un lugar, trae la fuente de cada dato y se conecta con datos de afuera. Solo, sin datos, el LLM acierta 5 de 20.

**Segundo dominio** (contratos federales de EE. UU., sus empresas, grupos y listas de control; otro Ontop, mismo método): SQL directo 5 de 9, Rastro 8 de 9; misma respuesta en las 4 formas, 3 de 5 contra 4 de 5. El SQL falla al unir USAspending con GLEIF, porque toma el primer candidato sin verificarlo. La referencia, que sale de Rastro, se queda corta en 2 preguntas (`layer/proveedores/adjudicacion.md`).

## Límites, dichos de entrada

- Con las tablas de enlaces de Rastro, el SQL acierta igual, incluso en preguntas de 3 o 4 cruces. Una capa de vistas SQL resolvería parte de lo demás.
- Una foto de octubre de 2026: 106.483 ensayos, 3.739 fármacos, 81 % de las intervenciones enlazadas.
- Las preguntas y sus referencias las hizo un asistente de IA; falta la confirmación humana.

## Próximo paso

Un piloto con datos del cliente sumados a las fuentes públicas.

---

Versión para todos: [one-pager.md](one-pager.md). Cómo se midió cada número: [results.md](results.md).
