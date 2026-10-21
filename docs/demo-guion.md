# Guion de la demo de Rastro: proveedores del Estado de EE. UU. (5 minutos)

> **Los datos cambian. Las preguntas, no.**

Para cualquier audiencia, sin conocimientos técnicos. Tres momentos, todos con el mismo ejemplo, el grupo Leidos: **integración, trazabilidad y análisis de textos**. Cada momento termina en un número: sin Rastro y con Rastro. El mazo de proveedores (`docs/slides/proveedores.html`, nueve diapositivas y un anexo) y la app en la pestaña **Demo**. La app abre en petróleo y gas: para ver proveedores, prender «Ver detalles técnicos» en la barra lateral y elegirlo en **Caso de uso**. Los otros casos de uso tienen su propio mazo y su guion: [petróleo y gas](demo-guion-energia.md) y [oncología](demo-guion-oncologia.md). Para una audiencia técnica: [demo-guion-tecnico.md](demo-guion-tecnico.md).

## Antes de empezar

1. Levantar todo, desde la carpeta del repo: `docker compose up -d` (lo hace alguien técnico, una vez).
2. Abrir http://localhost:8501, prender «Ver detalles técnicos» y elegir en **Caso de uso** **Proveedores del Estado de EE. UU.**; la pestaña **Demo**. Recorrer los tres pasos una vez: cada uno corre en vivo. Arriba de los pasos, «¿Por qué estos 3 momentos?» resume para qué sirve cada uno.

## 0:00 – 1:00 · Qué es Rastro (diapositivas 1 a 4)

> «Las bases de datos de una organización no están conectadas entre sí. Rastro incorpora un diccionario de negocio entre las bases y las preguntas: contrato, empresa, grupo, agencia. Cada base se traduce a esos términos una sola vez, y las preguntas se formulan con ellos.»
>
> «La demo responde una pregunta concreta: ¿con quién contrata el gobierno de EE. UU.? Con datos públicos de contratos federales y un solo ejemplo, el grupo Leidos, en tres momentos.»

## 1:00 – 2:00 · 1 · Integración (app, paso 1; diapositiva 5)

> «¿Cuánto contrata el gobierno con el grupo Leidos? Una consulta SQL que busca el nombre "Leidos" obtiene 56.400 millones: omite las empresas del grupo con otra razón social, como QTC o Dynetics. Rastro define el grupo una sola vez: 30 empresas y 63.400 millones, con la justificación de cada vínculo.»

Debajo de la tabla, en **¿Por qué este número?**, se ven las 30 empresas del grupo, cada una con su regla y su evidencia.

## 2:00 – 3:00 · 2 · Trazabilidad (app, paso 2; diapositiva 6)

> «Un caso que suele inducir a error: en 2013, la antigua SAIC adoptó el nombre Leidos y una nueva empresa tomó el nombre SAIC. Con otra formulación de la pregunta, la consulta SQL atribuyó a Leidos 41.400 millones que corresponden a SAIC. Rastro asigna cada empresa correctamente y muestra el motivo: la razón social vigente prevalece sobre la denominación anterior.»

Abrir **¿De dónde sale la respuesta?** para mostrar la evidencia.

## 3:00 – 4:00 · 3 · Análisis de textos (app, paso 3; diapositiva 7)

> «Por último, el análisis de textos: ¿en qué trabaja Leidos para el gobierno? Una búsqueda de la palabra "Leidos" en los contratos, como la de un buscador, encuentra 33 de los 40 más grandes: omite 5.600 millones y dos temas completos. Rastro selecciona los 40 con una consulta exacta, y la IA analiza solo esos textos, con la cita de cada contrato. Un RAG convencional decide qué leer según la similitud de los textos; Rastro, según el significado de los datos.»

## 4:00 – 5:00 · Por qué confiar y cierre (diapositivas 8 y 9)

> «Tres pruebas medidas: con Rastro, 8 de 9 respuestas correctas; sin Rastro, 4 de 9. La misma pregunta hecha de cuatro formas da la misma respuesta, y un cambio en una base se arregla en una línea.»
>
> «En síntesis: el valor está en integrar los datos una sola vez y mantenerlos en un único lugar. El siguiente paso es un piloto con datos propios.»

## Si preguntan

- **«¿Cómo saben que es correcto?»** Tres pruebas medidas, en la app (pestaña **Por qué confiar**) y en la diapositiva 8: 8 de 9 correctas con Rastro y 4 de 9 sin Rastro; la misma pregunta de cuatro formas; un cambio en una base se arregla en una línea. Las armó un asistente de IA; falta que una persona las confirme (`docs/verificacion-humana.md`).
- **«¿Y esto no se puede hacer con SQL?»** Sí, en parte: con las mismas tablas de enlaces que arma Rastro, un SQL bien hecho acierta igual. Lo que da Rastro es hacerlo una vez, mantenerlo en un lugar y poder auditar cada respuesta. El detalle está en el anexo técnico.
- **«¿Esto es GraphRAG?»** En parte, del lado que permite confiar: el grafo elige con una consulta exacta qué registros leer, y la IA resume solo esos textos, citando cada uno (paso 3). En oncología, además, el motivo escrito de cada ensayo detenido se vuelve un dato que se cuenta exacto (mazo de oncología; en la app, Oncología → «Una pregunta sobre textos»).
- **«¿Se puede ver en otro dominio?»** Sí: el mismo Rastro está armado para petróleo y gas en Argentina y para oncología, cada uno con su mazo. En la app, con «Ver detalles técnicos» prendido, cambiar **Caso de uso**.
- **«¿Necesito saber programar?»** No. Las preguntas de ejemplo funcionan solas; para preguntas propias se configura una vez un asistente de IA.

## Video de respaldo

Grabar la pantalla siguiendo este guion (Cmd+Shift+5 en la Mac, con micrófono), con la app en la pestaña **Demo**, y guardarlo fuera del repo.
