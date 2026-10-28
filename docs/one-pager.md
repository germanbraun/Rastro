# Rastro · en una página

> **Los datos cambian. Las preguntas, no.**

**Rastro integra sus datos una vez. Se pregunta en palabras de negocio, y cada respuesta dice de dónde sale y se puede
auditar.**

## El problema

Las bases de datos no se hablan entre sí. En petróleo y gas, la producción la informa la operadora de cada pozo, pero
lo que le corresponde a cada empresa depende de su participación en la concesión, que está en otra base, a veces
dentro de un texto, y la misma empresa aparece escrita de varias formas. Cada consulta lo resuelve por su cuenta, y
cada una lo resuelve distinto.

## Qué hace Rastro

Pone un **diccionario de negocio** entre las bases y las preguntas: pozo, concesión, operadora, participación. Traduce
cada base a esas palabras una sola vez, une las mismas empresas entre fuentes (cada unión con su evidencia) y comprueba
los datos con reglas de calidad. Después, cualquiera pregunta con esas palabras, y Rastro busca en cada base.

## Cuatro pruebas, medidas sobre datos públicos de Argentina

| | Sin Rastro | Con Rastro |
|---|---|---|
| **¿Cuánto petróleo de 2025 le corresponde a YPF?** | 21,4 millones de m³: le suma lo de sus socios | **12,6**, su parte en cada concesión, con la evidencia |
| **La misma pregunta, hecha de 4 formas** | la misma respuesta en 3 de 5 preguntas | **en 5 de 5** |
| **La fuente cambia el nombre de una columna** | consultas rotas que hay que encontrar | **se arregla en 1 línea** |
| **Un documento corrige un porcentaje** | el dato vive en 5 lugares | **se corrige en 1**, y cambian solos la respuesta, el modelo y su explicación |

**Y un modelo de machine learning** (el gas de los pozos nuevos de Vaca Muerta): con las variables de Rastro predice
igual de bien, y cada predicción dice de dónde sale cada dato y cuáles conviene revisar.

## Lo que hay que saber

- El valor está en integrar los datos una vez y mantenerlos en un lugar: con las mismas uniones, un SQL bien escrito
  también acierta, y la demo lo muestra.
- La demo usa datos públicos de la Secretaría de Energía y de otras fuentes abiertas, de 2025.
- Las referencias de las pruebas las armó un asistente de IA; falta que una persona las confirme.

## Próximo paso

Un piloto de 6 semanas con sus datos y sus preguntas: [piloto.md](piloto.md).

---

Versión técnica: [one-pager-tecnico.md](one-pager-tecnico.md). De dónde sale cada número: `layer/energia/resultados.json`,
`layer/energia/cambio/*.json` y `docs/slides/numeros/energia.json`, que también llenan la demo y las diapositivas.
