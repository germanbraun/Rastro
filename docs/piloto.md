# Rastro · Propuesta de piloto

> **Los datos cambian. Las preguntas, no.**

**Para:** [nombre de la empresa] · **Preparado por:** [nombre] · **Fecha:** [__]

Versión en inglés: [piloto-en.md](piloto-en.md). Las dos tienen que decir lo mismo.

## El problema que resuelve

Las preguntas de negocio cruzan bases que no se hablan: la misma empresa escrita de tres formas, los socios dentro
de un texto, una columna que cambia de nombre en la versión nueva de la fuente. Cada consulta, cada tablero y cada
modelo lo resuelve por su cuenta, y cada uno lo resuelve distinto. El resultado son números que no coinciden, que
nadie puede explicar y que se rompen cuando la fuente cambia.

## Qué hace Rastro

Pone un **diccionario de negocio** entre las bases y las preguntas, y resuelve **una vez** lo difícil: traduce cada
base a ese diccionario, une las mismas entidades entre fuentes (cada unión con su regla y su evidencia) y comprueba
los datos con reglas de calidad. Los datos no se copian: cada pregunta se traduce a las fuentes en el momento.
Todo queda en estándares abiertos del W3C, que pueden leer otras herramientas.

## Lo que ya muestra la demo, con datos públicos de petróleo y gas

Medido sobre la producción de 2025 de la Secretaría de Energía de Argentina (los números de la demo se leen de sus
archivos de resultados; ver `docs/demo-guion-energia.md`):

| | Sin Rastro | Con Rastro |
|---|---|---|
| **¿Cuánto petróleo le corresponde a YPF?** | sumando por quien declara, 21,4 millones de m³: le asigna también lo de sus socios | **12,6**, su parte en cada concesión, con la evidencia |
| **Lo asignado de más, sumando por quien declara** | 8,8 millones de m³: unos US$ 3.600 millones a US$ 65 el barril (un supuesto) | — |
| **La fuente cambia el nombre de una columna** | 3 consultas rotas, que hay que encontrar | **1 línea** |
| **Un documento corrige un porcentaje** | 5 lugares para corregir | **1 lugar**, y cambian solos la respuesta, el modelo y su explicación |
| **Un modelo de machine learning** | predice, pero no dice en qué se apoya | **predice igual de bien** y cada predicción dice de dónde sale cada dato y qué revisar |

## El piloto

**Duración:** 6 semanas. **Alcance:** hasta 3 fuentes de [empresa], sumadas a las fuentes públicas que
correspondan, y hasta 10 preguntas de negocio acordadas al comienzo.

| Semanas | Qué se hace | Qué ve [empresa] al terminar |
|---|---|---|
| 1 | Elegir las preguntas y las fuentes; inspeccionar las fuentes (solo lectura) | Las preguntas aprobadas por una persona de negocio, y qué fuente responde cada una |
| 2–3 | El diccionario de negocio, la traducción de cada fuente, las uniones entre fuentes con su evidencia | Cada pregunta respondida en la app de Rastro, con «¿Por qué este número?» |
| 4 | Reglas de calidad y las pruebas medidas: con y sin Rastro, la misma pregunta escrita de varias formas, una fuente que cambia | Los resultados de cada prueba, medidos sobre sus datos |
| 5–6 | Opcional: un modelo propio con sus variables tomadas de Rastro, y su explicación; presentación de resultados | Un informe con los números, los límites y una recomendación de próximo paso |

## Cómo se mide el éxito

Se acuerdan al comienzo y se miden sobre los datos de [empresa], con las mismas pruebas que la demo:

- Cada pregunta acordada se responde con su evidencia: de qué fuente sale cada número y con qué regla se unió.
- La misma pregunta, escrita de distintas formas, da la misma respuesta.
- Un cambio en una fuente (una columna renombrada) se arregla en un solo lugar.
- Cada unión entre fuentes tiene su evidencia, y las que revisó un asistente de IA las confirma una persona de
  [empresa].
- [Un criterio propio de [empresa], por ejemplo: un número que hoy se calcula a mano, igual y en minutos.]

## Qué necesitamos de [empresa]

- Acceso de **solo lectura** a las fuentes (o una copia), en su propia infraestructura si lo prefieren: Rastro no
  copia los datos fuera de donde están.
- Una persona de negocio, unas 2 horas por semana, para aprobar las preguntas y las definiciones y confirmar las
  uniones dudosas.
- Una persona técnica, para el acceso a las fuentes.

## Qué queda al terminar

El diccionario de negocio, las traducciones de cada fuente y las uniones con su evidencia, en estándares abiertos
(OWL, R2RML, SHACL, PROV-O): son de [empresa] y no dependen de Rastro para leerse. La app con sus preguntas, y el
informe de resultados.

## Lo que hay que saber

- El valor está en integrar los datos una vez y mantenerlos en un lugar, no en la tecnología por sí misma: con las
  mismas uniones, un SQL bien escrito también acierta, y la demo lo muestra.
- La demo usa datos públicos; las referencias de sus pruebas las armó un asistente de IA y falta que una persona
  las confirme. En el piloto, las confirma una persona de [empresa].

## Inversión

[US$ __] por el piloto de 6 semanas · [condiciones de pago] · [qué pasa si se continúa]

**Contacto:** [nombre · correo · teléfono]
