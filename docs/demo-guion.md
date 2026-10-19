# Guion de la demo de Rastro (5 minutos)

> **Los datos cambian. Tus preguntas, no.**

Para cualquier audiencia, sin conocimientos técnicos. Tres momentos, todos con el mismo ejemplo, el grupo Leidos: **une, explica, lee**. Cada momento termina en un número: sin Rastro, con Rastro. Ocho diapositivas (`docs/slides/`, abrir `index.html`) y la app en **Demo en 3 pasos**, con «Ver detalles técnicos» apagado. Lo demás (pruebas, oncología en vivo, anexo) queda para las preguntas. Para una audiencia técnica: [demo-guion-tecnico.md](demo-guion-tecnico.md).

## Antes de empezar

1. Levantar todo: `cd infra && docker compose up -d` (lo hace alguien técnico, una vez).
2. Abrir http://localhost:8501. Dominio: **Proveedores del Estado de EE. UU.**; arriba, **Demo en 3 pasos**. Recorrer los tres pasos una vez: cada uno corre en vivo.

## 0:00 – 1:00 · Qué es Rastro (diapositivas 1 a 3)

> «Las bases de datos no se hablan entre sí. Rastro pone un diccionario de negocio entre tus bases y tus preguntas: contrato, empresa, grupo, agencia. Traduce cada base a esas palabras una sola vez, y después preguntás con esas palabras.»
>
> «La demo: ¿con quién hace negocios el gobierno de EE. UU.? Datos públicos de contratos federales, y un solo ejemplo: el grupo Leidos. Tres momentos.»

## 1:00 – 2:00 · 1 · Une (app, paso 1; diapositiva 4)

> «¿Cuánto le contrata el gobierno a Leidos? Buscando la palabra "Leidos", un SQL da 56.400 millones: le faltan las empresas del grupo que se llaman de otra forma, como QTC o Dynetics. Rastro arma el grupo una vez: 30 empresas, 63.400 millones, y dice por qué cada una es parte.»

## 2:00 – 3:00 · 2 · Explica (app, paso 2; diapositiva 5)

> «La trampa: en 2013 la vieja SAIC pasó a llamarse Leidos y una empresa nueva tomó el nombre SAIC. Preguntando de otra forma, el SQL le sumó a Leidos 41.400 millones que son de SAIC. Rastro no, y muestra por qué: el nombre legal de hoy le gana al nombre anterior.»

Abrir **¿Cómo lo supe?** para mostrar la evidencia.

## 3:00 – 4:00 · 3 · Lee (app, paso 3; diapositiva 6)

> «Ahora sobre textos: ¿en qué trabaja Leidos? Si buscamos la palabra "Leidos" en los contratos, como haría un buscador, encontramos 33 de los 40 más grandes: se pierden 5.600 millones y dos temas enteros. Rastro elige los 40 con una consulta exacta, y la IA lee solo esos textos, citando cada contrato. Un RAG común decide qué leer por cómo se ven los textos; Rastro, por lo que significan los datos.»

## 4:00 – 5:00 · Otro dominio y cierre (diapositivas 7 y 8)

> «El mismo Rastro funciona con ensayos clínicos de cáncer: haciendo cada pregunta de cuatro formas, sin Rastro la respuesta cambió en 9 de 10; con Rastro, en ninguna.»
>
> «Lo que hay que saber: el valor está en integrar los datos una vez y mantenerlos en un lugar. El siguiente paso es un piloto con tus datos.»

## Si preguntan

- **«¿Cómo saben que es correcto?»** Tres pruebas medidas, en la app (pestaña **Por qué confiar**) y en la diapositiva 9: 8 de 9 correctas con Rastro y 4 de 9 sin Rastro; la misma pregunta de cuatro formas; un cambio en una base se arregla en una línea. Las armó un asistente de IA; falta que una persona las confirme (`docs/verificacion-humana.md`).
- **«¿Y esto no se puede hacer con SQL?»** Sí, en parte: con las mismas tablas de enlaces que arma Rastro, un SQL bien hecho acierta igual. Lo que da Rastro es hacerlo una vez, mantenerlo en un lugar y poder auditar cada respuesta. El detalle está en el anexo técnico.
- **«¿Esto es GraphRAG?»** En parte, del lado que permite confiar: el grafo elige con una consulta exacta qué registros leer, y la IA resume solo esos textos, citando cada uno (paso 3). En oncología, además, el motivo escrito de cada ensayo detenido se vuelve un dato que se cuenta exacto (diapositiva 13; en la app, Oncología → «Una pregunta sobre textos»).
- **«¿Se puede ver en otro dominio?»** Cambiar **Dominio** a **Oncología** y elegir *fármacos contra HER2 en cáncer de mama* (diapositivas 10 a 12).
- **«¿Necesito saber programar?»** No. Las preguntas de ejemplo funcionan solas; para preguntas propias se configura una vez un asistente de IA.
- **«No sé nada de oncología.»** No hace falta: la app explica cada pregunta en palabras simples, y [fuentes.md](fuentes.md) tiene un glosario.

## Video de respaldo

Grabar la pantalla siguiendo este guion (Cmd+Shift+5 en la Mac, con micrófono), con la app en **Demo en 3 pasos**, y guardarlo fuera del repo.
