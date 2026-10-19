# Rastro · en una página

> **Los datos cambian. Tus preguntas, no.**

**Rastro integra tus datos una vez. Preguntás en lenguaje de negocio, y cada respuesta dice de dónde sale y se puede auditar.**

## El problema

Las bases de datos no se hablan entre sí. En oncología, el mismo fármaco aparece como «Pembrolizumab 200 mg» en un ensayo clínico, como un código en una base de fármacos y como «KEYTRUDA» en los reportes de la FDA. Cada consulta tiene que resolver eso por su cuenta, y cada una lo resuelve distinto.

## Qué hace Rastro

Pone un **diccionario de negocio** entre tus bases y tus preguntas: ensayo, fármaco, sponsor, enfermedad. Traduce cada base a esas palabras una sola vez. Después, cualquiera pregunta con esas palabras, y Rastro busca en cada base.

## Tres pruebas, medidas sobre datos reales

| | Sin Rastro | Con Rastro |
|---|---|---|
| **La misma pregunta, hecha de 4 formas** | la respuesta cambió en 9 de 10 preguntas | **la misma, en 10 de 10** |
| **Si una base cambia** | hay que reescribir cada consulta; algunas dan cero sin avisar | **se arregla en una línea** |
| **¿Por qué dice eso?** | no se sabe | **muestra la evidencia de cada fármaco, con el enlace al ensayo** |

Sin datos integrados, un asistente de IA solo acierta 5 de 20 preguntas: responde de memoria.

**Funciona en otro dominio.** Con contratos del gobierno de EE. UU., sus empresas y sus grupos, el mismo asistente acierta 8 de 9 preguntas con Rastro y 5 de 9 sin Rastro, y Rastro no cae en la trampa de dos empresas con el mismo nombre (SAIC y Leidos).

## Lo que hay que saber

- El valor está en integrar los datos una vez y mantenerlos en un lugar.
- La demo usa cuatro bases públicas de oncología, con datos de octubre de 2026.
- Las pruebas las armó un asistente de IA; falta que una persona las confirme.

## Próximo paso

Un piloto con tus datos sumados a las fuentes públicas.

---

Versión técnica, con la comparación completa: [one-pager-tecnico.md](one-pager-tecnico.md). Cómo se midió cada número: [results.md](results.md).
