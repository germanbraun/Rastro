# Guion de la demo de Rastro Layer (5 minutos)

Para quien da la demo, sin conocimientos técnicos. Las diapositivas acompañan los minutos 0-1 y 4-5. El resto se hace en la app.

## Antes de empezar

Si no sos del dominio, leé primero [fuentes.md](fuentes.md): qué tiene cada fuente, con ejemplos y un glosario (10 minutos).

1. Levantar todo: `cd infra && docker compose up -d` (lo hace alguien técnico, una vez).
2. Abrir http://localhost:8501 en el navegador y dejarlo en la pestaña **Preguntar**.
3. Probar una pregunta de ejemplo: si responde, está todo listo.
4. Si algo falla en vivo, usar las diapositivas 4 a 6, que tienen las mismas respuestas.

## 0:00 – 1:00 · El problema (diapositivas 1 y 2)

> «En oncología hay cuatro fuentes públicas muy buenas: ensayos clínicos, fármacos, eventos adversos y enfermedades. El problema es que no se hablan. El mismo fármaco aparece como "Pembrolizumab 200 mg" en un ensayo, como un código en ChEMBL y como "KEYTRUDA" en la FDA. Cualquier pregunta que cruce fuentes tiene que resolver eso primero. Rastro es una capa semántica que lo resuelve una vez: entre las fuentes y quien pregunta, habla en conceptos de negocio.»

## 1:00 – 2:30 · Una pregunta en vivo (pestaña Preguntar)

1. Elegir **Una pregunta de ejemplo** y la primera: *¿Qué fármacos con target HER2 se prueban en ensayos de fase 3 de cáncer de mama?*
2. Apretar **Responder**.

> «Trastuzumab, pertuzumab, lapatinib… con cuántos ensayos tiene cada uno. Esta pregunta cruza tres fuentes: el ensayo, el target del fármaco y la jerarquía de enfermedades, que incluye los subtipos de cáncer de mama.»

3. Señalar la fila de fuentes bajo la tabla.

> «Cada columna dice de qué fuente sale. El ícono dice dónde vive: 🐘 base relacional, 🕸️ grafo.»

4. Abrir **¿Cómo lo supe?**

> «Esto es lo que escribió el LLM. No adivinó cómo se cruzan las tablas: recibió la ontología de Rastro, con cada concepto definido, y escribió una consulta corta en esos conceptos, "fármaco", "target", "ensayo". Debajo, el SQL que Rastro generó solo. Y las fuentes con su licencia. Nada es una caja negra.»

## 2:30 – 4:00 · Con y sin Rastro (pestaña Con y sin Rastro)

1. Mostrar el puntaje arriba.

> «Le hicimos 20 preguntas de negocio al mismo LLM de tres formas. Solo, sin datos: 5 de 20, inventa todos los números. Con acceso directo a las tablas: 18. Con Rastro: 20.»

2. Elegir la pregunta *¿Cuántos ensayos de fase 3 prueban fármacos que actúan sobre EGFR?*

> «Acá está lo importante. El SQL directo dice 488. Rastro dice 438. Los dos parecen razonables. Revisamos ensayo por ensayo: el SQL directo contó trastuzumab, que es anti-HER2, porque encontró "humab" dentro de otro nombre. Ese error no avisa.»

3. Abrir **Ver los intentos** en la respuesta del SQL directo, si los tiene.

> «Y para llegar ahí, el LLM tuvo que inventar cómo reconocer un fármaco en el texto, en cada pregunta. Lo hizo de cuatro formas distintas en 20 preguntas. Rastro usa siempre una, la misma, revisada.»

## 4:00 – 5:00 · Cierre (diapositivas 7 a 9)

> «La ventaja no es que acierte más: es que podés confiar en cada respuesta. Una sola definición, revisada, más rápida, y con la fuente de cada dato. El trabajo difícil, unir las fuentes, se hace una vez.»
>
> «El siguiente paso: un piloto con sus datos sumados a las fuentes públicas. ¿Qué pregunta le harían a sus datos?»

## Si preguntan

La pestaña **Preguntas frecuentes** de la app tiene las respuestas. Las más comunes:

- **«¿Y si le doy al SQL las mismas tablas de enlaces?»** Probablemente acierte igual. El valor está en la integración revisada y en exponerla como un vocabulario estándar, con fuente.
- **«¿Quién revisó las respuestas correctas?»** Decirlo tal cual: las preguntas y la primera revisión las hizo un asistente de IA, y una persona las confirmó con ensayos reales (ver `docs/verificacion-humana.md`). Si esa revisión humana todavía no se hizo, decir que está pendiente.
- **«¿Funciona con otro LLM?»** Sí. Para la demo se usó Claude; también corre con un modelo local.
- **«¿Los datos están al día?»** Es una foto de octubre de 2026. Recargar es correr los cargadores de nuevo.

## Video de respaldo

Grabar la pantalla siguiendo este guion (por ejemplo con la grabación de pantalla del sistema operativo) y guardarlo fuera del repo. Pendiente: lo tiene que grabar una persona.
