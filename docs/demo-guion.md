# Guion de la demo de Rastro Layer (8 minutos)

> **Los datos cambian. Tus preguntas, no.**

Para consultores que saben SQL y no conocen tecnologías semánticas. Las diapositivas están en `docs/slides/` (abrir `index.html`).

## Antes de empezar

Si no sos del dominio, leé primero [fuentes.md](fuentes.md) (10 minutos). La app explica cada pregunta en palabras simples.

1. Levantar todo: `cd infra && docker compose up -d` (lo hace alguien técnico, una vez).
2. Abrir http://localhost:8501 en la pestaña **Preguntar** y probar una pregunta de ejemplo.
3. Si algo falla en vivo, las diapositivas tienen las mismas respuestas. No hace falta la terminal.

## 0:00 – 1:30 · Problema, capa y beneficios (diapositivas 1 a 4)

> «Cuatro fuentes públicas de oncología que no comparten claves: el mismo fármaco es "Pembrolizumab 200 mg" en un ensayo, un código en otra base y "KEYTRUDA" en la FDA. Con SQL, cada consulta resuelve ese cruce a su manera.»
>
> «Rastro es una capa semántica entre las tablas y quien pregunta. Si sabés SQL, ya conocés cada pieza: la ontología es el esquema de negocio que te gustaría tener, los mapeos son como definiciones de vistas, los enlaces son las claves de join que faltaban. Ontop traduce todo a SQL. Los datos no se mueven.»
>
> «Lo que gana una empresa: respuestas consistentes, preguntas en lenguaje de negocio, cada dato con su fuente, menos mantenimiento, datos de afuera sin cargarlos y estándares abiertos. Ahora, la evidencia.»

## 1:30 – 3:00 · Una pregunta en vivo (pestaña Preguntar, diapositiva 5)

1. Elegir la primera pregunta de ejemplo (*fármacos anti-HER2 en fase 3 de cáncer de mama*) y apretar **Responder**.

> «Trastuzumab, pertuzumab, lapatinib… Cruza tres fuentes, y cada columna dice de qué fuente sale.»

2. Abrir **¿Cómo lo supe?**

> «El LLM no vio tablas: recibió la ontología y escribió esta consulta corta, en conceptos. Abajo, el SQL que generó Ontop. Sin integración, el LLM escribió 1.543 caracteres de SQL adivinando nombres en el texto; con la integración hecha, 435.»

## 3:00 – 4:30 · La comparación honesta (diapositiva 6)

> «Le dimos los datos al mismo LLM de tres formas. SQL directo: acierta 18 de 20, y si hacés la misma pregunta de cuatro formas, la respuesta cambia en 9 de 10. SQL con nuestras tablas de enlaces: acierta todo y es consistente. O sea: la precisión viene de integrar una vez. Eso es lo primero que vendemos.»
>
> «La capa semántica agrega lo que las tablas solas no dan: cuando la fuente cambia se arregla en un lugar, cada dato trae su fuente, y se puede consultar junto con datos de afuera.»

## 4:30 – 6:30 · Cuando las fuentes cambian (pestaña Cuando las fuentes cambian, diapositivas 7 y 8)

1. Elegir **Cambia cómo se escribe un valor**.

> «AACT publica una versión nueva: los estados pasan de TERMINATED a Terminated. Con SQL, con o sin nuestros enlaces, nada falla, pero cinco respuestas pasan a cero: "569 ensayos detenidos" ahora es 0, y nadie se entera. Rastro también da cero, pero avisa: hay estados que la ontología no conoce. Se arregla con una línea del mapeo, y las 20 preguntas vuelven a funcionar. El SQL sigue mal hasta que alguien arregle cada consulta.»

2. Elegir **Cambia una definición de negocio**.

> «"Terapia dirigida" no está en ninguna tabla ni en ningún mapeo: está definida en la ontología, en dos líneas, y Ontop la deduce. Miren el SQL que generó: nadie lo escribió. Si el negocio decide que la terapia hormonal también cuenta, es una línea más, y todas las preguntas cambian a la vez: de 156 a 188 fármacos.»

3. Elegir **Se suma una fuente: Wikidata**.

> «Una consulta, tres grafos: Rastro, MeSH y Wikidata, unidos en vivo por el identificador del fármaco. Wikidata nos dice que afatinib está aprobado para pulmón y se prueba en mama. Eso no está en ninguna de nuestras fuentes, y no cargamos nada.»

## 6:30 – 8:00 · Cierre (diapositiva 10)

> «Los datos cambian; tus preguntas, no. Lo que vendemos es la integración hecha una vez, mantenida en un lugar, con fuente y conectada con datos de afuera. Con nuestros enlaces, el SQL acierta igual: lo decimos de entrada. El siguiente paso: un piloto con datos del cliente.»

## En vivo, para audiencias técnicas

El cambio se puede hacer de verdad sobre la base, desde una terminal. Detalle en [demo-cambio.md](demo-cambio.md): `cambio.sh valores`, `probar`, `arreglar valores`, `probar`, y **siempre** `deshacer` al final.

## Si preguntan

La pestaña **Preguntas frecuentes** tiene las respuestas. Las más comunes:

- **«¿Y por qué no vistas SQL?»** Para un caso chico pueden alcanzar. La capa semántica suma procedencia, datos de afuera, jerarquías y estándares abiertos.
- **«¿Ontop es lento?»** No en esta demo: las 20 consultas tardan 2,6 s en total. Una consulta muy pesada puede tardar más que el SQL equivalente.
- **«¿Quién revisó las respuestas correctas?»** Las preguntas y la primera revisión las hizo un asistente de IA; una persona las confirma con `docs/verificacion-humana.md`. Si todavía no se hizo, decir que está pendiente.
- **«¿Funciona con otro LLM?»** Sí: Claude o un modelo local.
- **«¿Los datos están al día?»** Es una foto de octubre de 2026. Recargar es correr los cargadores de nuevo.

## Video de respaldo

Grabar la pantalla siguiendo este guion (Cmd+Shift+5 en la Mac, con micrófono) y guardarlo fuera del repo, después de la verificación humana.
