# Guion de la demo de Rastro Layer (5 minutos + 3 de cambio)

Para consultores que saben SQL y no conocen tecnologías semánticas. La demo compara todo el tiempo con lo que ya conocen: SQL. Las diapositivas están en `docs/slides/` (abrir `index.html`).

## Antes de empezar

Si no sos del dominio, leé primero [fuentes.md](fuentes.md): qué tiene cada fuente, con ejemplos y un glosario (10 minutos). La app explica cada pregunta en palabras simples, así que no hace falta saber oncología.

1. Levantar todo: `cd infra && docker compose up -d` (lo hace alguien técnico, una vez).
2. Abrir http://localhost:8501 en el navegador y dejarlo en la pestaña **Preguntar**.
3. Probar una pregunta de ejemplo: si responde, está todo listo.
4. Para la parte de cambio, tener una terminal abierta en la carpeta del repo y correr una vez `layer/cambio/cambio.sh probar` (tarda medio minuto).
5. Si algo falla en vivo, las diapositivas tienen las mismas respuestas.

## 0:00 – 0:45 · El problema (diapositivas 1 y 2)

> «Cuatro fuentes públicas de oncología: ensayos clínicos, fármacos, eventos adversos y enfermedades. No comparten claves. El mismo fármaco es "Pembrolizumab 200 mg" en un ensayo, un código en otra base y "KEYTRUDA" en la FDA. Cualquier pregunta que cruce fuentes tiene que resolver eso primero, y en SQL lo resolvés en cada query.»

## 0:45 – 1:30 · Qué es una capa semántica, en SQL (diapositiva 3)

> «Rastro es una capa semántica: se pone entre las tablas y quien pregunta. Si sabés SQL, ya conocés cada pieza. La ontología es el esquema de negocio que te gustaría tener. Un mapeo es como la definición de una vista: "esta columna es este concepto". SPARQL es SQL sobre conceptos. Y Ontop es un compilador que traduce eso a SQL normal sobre las tablas reales. Los datos no se mueven.»

## 1:30 – 3:00 · Una pregunta en vivo (pestaña Preguntar)

1. Elegir **Una pregunta de ejemplo** y la primera: *fármacos con target HER2 en fase 3 de cáncer de mama*. Mostrar el recuadro **En palabras simples**.
2. Apretar **Responder**.

> «Trastuzumab, pertuzumab, lapatinib… con cuántos ensayos tiene cada uno. Cruza tres fuentes: el ensayo, el target del fármaco y la jerarquía de enfermedades. Cada columna dice de qué fuente sale.»

3. Abrir **¿Cómo lo supe?** Es el momento clave para esta audiencia.

> «El LLM no vio tablas: recibió la ontología como contexto y escribió esta consulta corta, en conceptos. Abajo está el SQL que generó Ontop: joins simples sobre enlaces ya revisados. La complejidad no desapareció: está en la capa, escrita una vez, y nadie tiene que escribir ni mantener este SQL.»

4. Pasar a la diapositiva 4: 1.543 caracteres de SQL escrito por el LLM, 435 de SPARQL, 742 de SQL generado por Ontop.

## 3:00 – 4:00 · Con y sin Rastro (pestaña Con y sin Rastro, diapositiva 5)

1. Mostrar el puntaje: el mismo LLM, 20 preguntas. Solo: 5. Con SQL directo: 18. Con Rastro: 20.

> «Con SQL directo acierta casi todo. La diferencia no está en cuántas acierta, sino en cuánto podés confiar.»

2. Elegir la pregunta de **EGFR**.

> «El SQL directo dice 488 y Rastro 438. Los dos parecen razonables. El SQL contó trastuzumab, que es anti-HER2, porque encontró "humab" dentro de otro nombre. Ese error no avisa. Y para llegar ahí, el LLM inventó cómo reconocer un fármaco en cada pregunta: de cuatro formas distintas en 20 preguntas.»

3. Mostrar la fila de consistencia de la diapositiva 5.

> «Hicimos la misma pregunta de cuatro formas. Con SQL directo, en 9 de 10 preguntas la respuesta cambia según cómo preguntes: 488, 409… Con Rastro, siempre la misma. Eso es lo que significa poder confiar.»

## 4:00 – 5:00 · Por qué no vistas, y cierre (diapositivas 8 y 9)

> «La pregunta obvia: ¿y si hago vistas SQL sobre las tablas de enlaces? Para un caso chico pueden alcanzar. La capa semántica agrega componer cualquier combinación de conceptos sin una vista por pregunta, jerarquías, la fuente de cada columna, un vocabulario que el LLM lee como contexto, y estándares abiertos.»
>
> «El siguiente paso: un piloto con datos propios del cliente sumados a las fuentes públicas.»

## Extra, 3 minutos · Cuando la fuente cambia (terminal, diapositiva 6)

Para consultores, esto es lo que más pesa: el costo de mantener. Detalle en [demo-cambio.md](demo-cambio.md).

1. `layer/cambio/cambio.sh valores`

> «AACT publica una versión nueva y los estados pasan de TERMINATED a Terminated. Algo menor.»

2. `layer/cambio/cambio.sh probar`

> «Ninguna query del SQL directo falla, pero cinco respuestas pasan a cero: "569 ensayos detenidos en páncreas" ahora es 0, y nadie se entera. Rastro también da cero, pero el control de vocabulario avisa: hay estados que la ontología no conoce.»

3. `layer/cambio/cambio.sh arreglar valores`, y otra vez `probar`.

> «Una línea en el mapeo. Rastro vuelve a 20 de 20. El SQL directo sigue mal hasta que alguien encuentre y arregle cada query.»

4. **Siempre al final:** `layer/cambio/cambio.sh deshacer`.

## Si preguntan

La pestaña **Preguntas frecuentes** de la app tiene las respuestas. Las más comunes para esta audiencia:

- **«¿Y si le doy al SQL las mismas tablas de enlaces?»** Probablemente acierte igual. El valor está en la integración revisada y en exponerla como un vocabulario estándar, con fuente.
- **«¿Ontop es lento?»** No en esta demo: las 20 consultas de Rastro tardan 2 segundos en total, contra 20 del SQL directo, porque Ontop genera joins simples sobre tablas indexadas.
- **«¿Quién revisó las respuestas correctas?»** Decirlo tal cual: las preguntas y la primera revisión las hizo un asistente de IA, y una persona las confirmó con ensayos reales (ver `docs/verificacion-humana.md`). Si esa revisión humana todavía no se hizo, decir que está pendiente.
- **«¿Funciona con otro LLM?»** Sí. Para la demo se usó Claude; también corre con un modelo local.
- **«¿Los datos están al día?»** Es una foto de octubre de 2026. Recargar es correr los cargadores de nuevo.

## Video de respaldo

Grabar la pantalla siguiendo este guion (por ejemplo con Cmd+Shift+5 en la Mac, con micrófono) y guardarlo fuera del repo. Conviene grabarlo después de la verificación humana. Pendiente: lo tiene que grabar una persona.
