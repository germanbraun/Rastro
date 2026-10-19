# Guion de la demo de Rastro (5 minutos)

> **Los datos cambian. Tus preguntas, no.**

Para cualquier audiencia, sin conocimientos técnicos. Seis diapositivas (`docs/slides/`, abrir `index.html`) y la app en modo normal, con «Ver detalles técnicos» apagado. Para una audiencia técnica: [demo-guion-tecnico.md](demo-guion-tecnico.md).

## Antes de empezar

1. Levantar todo: `cd infra && docker compose up -d` (lo hace alguien técnico, una vez).
2. Abrir http://localhost:8501, pestaña **Preguntar**, y probar la primera pregunta.
3. Si no sos del dominio, mirá [fuentes.md](fuentes.md) (10 minutos). La app explica cada pregunta en palabras simples.

## 0:00 – 1:00 · El problema y qué es Rastro (diapositivas 1 a 3)

> «Las bases de datos no se hablan entre sí. El mismo fármaco aparece como "Pembrolizumab 200 mg" en un ensayo, como un código en otra base y como "KEYTRUDA" en la FDA. Cada consulta tiene que resolver eso, y cada una lo resuelve distinto.»
>
> «Rastro pone un diccionario de negocio entre tus bases y tus preguntas: ensayo, fármaco, sponsor, enfermedad. Traduce cada base a esas palabras una sola vez. Después preguntás con esas palabras.»

## 1:00 – 2:30 · Una pregunta en vivo (app, pestaña Preguntar; diapositiva 4)

1. Elegir la primera pregunta (*fármacos contra HER2 en cáncer de mama*). Mostrar el recuadro **En palabras simples**.
2. Apretar **Responder**.

> «Trastuzumab, pertuzumab, lapatinib… y las fuentes de donde sale.»

3. Abrir **¿Cómo lo supe?**

> «¿Y por qué dice eso? Acá está: lo que escribió quien registró cada ensayo, y qué fármaco es. "Adjuvant Systemic Therapy" es trastuzumab emtansina porque el sponsor lo declaró así. Cada ensayo se puede abrir y comprobar.»

## 2:30 – 4:00 · Por qué confiar (app, pestaña Por qué confiar; diapositiva 5)

> «Tres pruebas. Una: hicimos la misma pregunta de cuatro formas. Sin Rastro, la respuesta cambió: 488, 409… Con Rastro, siempre la misma.»

Elegir el escenario **Cambia cómo se escribe un valor**.

> «Dos: una base cambia algo menor. Sin Rastro, cinco respuestas pasan a cero y nadie se entera. Rastro avisa, y se arregla en una línea.»
>
> «Tres: cada respuesta se puede auditar, como vimos recién.»

## 4:00 – 5:00 · Cierre (diapositiva 6)

> «Lo que hay que saber: el valor está en integrar los datos una vez y mantenerlos en un lugar. Es una demo con datos públicos de octubre de 2026. El siguiente paso es un piloto con tus datos.»

## Opcional, 2 minutos · Un segundo dominio (diapositivas 7 a 9)

Para mostrar que Rastro no es solo para oncología. En la barra lateral de la app, cambiar **Dominio** a **Proveedores del Estado de EE. UU.**

> «El mismo Rastro, con otros datos: los contratos del gobierno de EE. UU. Los problemas son los mismos: la misma empresa escrita de varias formas, grupos con muchas empresas, y por qué Rastro dice lo que dice.»

1. Elegir la primera pregunta (*¿cuánto le contrata el gobierno al grupo Leidos?*) y apretar **Responder**.

> «Un solo grupo: 21 empresas, 54.700 millones de dólares. La base de contratos reparte a Leidos en seis "matrices" distintas; Rastro las une.»

2. Elegir *«Science Applications International Corporation», ¿es de Leidos o de SAIC?*, apretar **Responder** y abrir **¿Cómo lo supe?**

> «La trampa: en 2013 la vieja SAIC pasó a llamarse Leidos y una empresa nueva tomó el nombre SAIC. Sin Rastro, una de las consultas le sumó a Leidos 41.000 millones que son de SAIC. Rastro no, y acá dice por qué: el nombre legal de hoy le gana al nombre anterior, y muestra lo que descartó.»

3. Si hay tiempo, pestaña **Por qué confiar**:

> «Las mismas pruebas: con Rastro, 8 de 9 respuestas correctas; sin Rastro, 5 de 9. Y con honestidad: Rastro también se equivocó en una, y la revisión encontró empresas que todavía no une. Se ve en la evidencia y se corrige en un solo lugar.»

## Si preguntan

- **«¿Y esto no se puede hacer con SQL?»** Sí, en parte. Lo que da Rastro es hacerlo una vez, mantenerlo en un lugar y poder auditar cada respuesta. El detalle está en el anexo técnico y en la versión técnica del guion.
- **«¿Quién revisó las respuestas correctas?»** Las armó un asistente de IA; falta que una persona las confirme (`docs/verificacion-humana.md`).
- **«¿Necesito saber programar?»** No. Las preguntas de ejemplo funcionan solas; para preguntas propias se configura una vez un asistente de IA.

## Video de respaldo

Grabar la pantalla siguiendo este guion (Cmd+Shift+5 en la Mac, con micrófono) y guardarlo fuera del repo.
