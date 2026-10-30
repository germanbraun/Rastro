# Rastro Layer · en una página (versión técnica)

> **Los datos cambian. Las preguntas, no.**

**Una capa semántica sobre fuentes públicas de petróleo y gas de Argentina. Los datos se integran una vez; un LLM
pregunta en conceptos de negocio, y cada respuesta dice de qué fuente sale.**

## Qué gana una empresa

- **Respuestas consistentes:** una sola definición de cada concepto (por ejemplo, «la parte de una empresa»).
- **Preguntas en lenguaje de negocio:** el LLM lee un vocabulario, no cientos de columnas.
- **Cada dato con su fuente:** respuestas auditables, y cada unión entre fuentes con su regla y su evidencia.
- **Menos mantenimiento:** si una fuente cambia, se arregla en un lugar.
- **Modelos explicados:** las variables de un modelo salen de la misma capa, con su evidencia.
- **Sin atarse a un proveedor:** estándares abiertos del W3C (OWL, R2RML, SHACL, PROV-O).

## Qué es, en términos de SQL

| Pieza | Equivale a |
|---|---|
| Ontología | El esquema de negocio que te gustaría tener |
| Mapeos (R2RML) | Definiciones de vistas: esta columna es este concepto |
| Enlaces | Las claves de join que faltaban, calculadas una vez y con su evidencia |
| Reglas de calidad (SHACL) | Los `CHECK` que las fuentes no tienen, sobre los datos ya integrados |
| SPARQL | SQL sobre conceptos, que Rastro traduce a SQL sobre las tablas reales |

## La evidencia (el mismo LLM, 10 preguntas, medido el 29 de octubre de 2026; referencias hechas por un asistente de IA, falta que una persona las confirme)

| | SQL directo | SQL + enlaces de Rastro | Rastro |
|---|---|---|---|
| Correctas, de 10 (tolerancia del 5 % en los números) | 8 | 10 | **10** |
| Misma respuesta, preguntando de 4 formas | 2 de 5 | 5 de 5 | **5 de 5** |
| Una columna de la fuente cambia de nombre | consultas rotas, a encontrar | igual | **1 línea del mapeo** |
| Un documento corrige una participación | 5 lugares | 5 lugares | **1 lugar**, con el documento |
| De dónde sale cada dato | no | no | **por columna** |

**Cómo leerla:** la precisión y la consistencia vienen de integrar una vez: con las tablas de enlaces, el SQL acierta
igual. La capa semántica agrega que esa integración se mantiene en un lugar, trae la fuente de cada dato y alimenta un
modelo que se explica con la misma evidencia.

**Rastro Lab** (el gas de los pozos nuevos de Vaca Muerta): el mismo modelo con variables de las tablas crudas y de
Rastro tiene el mismo error (16,7 en los dos); con Rastro, cada predicción dice qué datos conviene revisar (24 de 49).

**Otros dominios, mismo método:** contratos federales de EE. UU. y oncología, en la vista técnica de la app.

## Límites, dichos de entrada

- Con las tablas de enlaces de Rastro, el SQL acierta igual. Una capa de vistas SQL resolvería parte de lo demás.
- Una foto de los datos de 2025; las preguntas y sus referencias las hizo un asistente de IA y falta la confirmación
  humana (`layer/energia/adjudicacion.md`).

## Próximo paso

Un piloto de 6 semanas con datos del cliente sumados a las fuentes públicas: [piloto.md](piloto.md).

---

Versión para todos: [one-pager.md](one-pager.md). De dónde sale cada número: `layer/energia/resultados.json`,
`layer/energia/cambio/correccion.json` y `docs/slides/numeros/energia.json`. Los números de oncología siguen en
[results.md](results.md).
