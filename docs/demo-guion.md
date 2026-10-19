# Guion de la demo de Rastro (5 minutos + 1 de oncología)

> **Los datos cambian. Tus preguntas, no.**

Para cualquier audiencia, sin conocimientos técnicos. Nueve diapositivas (`docs/slides/`, abrir `index.html`) y la app en modo normal, con «Ver detalles técnicos» apagado. Primero proveedores del Estado de EE. UU., después el mismo Rastro en oncología. Para una audiencia técnica: [demo-guion-tecnico.md](demo-guion-tecnico.md).

## Antes de empezar

1. Levantar todo: `cd infra && docker compose up -d` (lo hace alguien técnico, una vez).
2. Abrir http://localhost:8501. En la barra lateral, **Dominio: Proveedores del Estado de EE. UU.** Probar la primera pregunta.

## 0:00 – 1:00 · Qué es Rastro y el problema (diapositivas 1 a 3)

> «Las bases de datos no se hablan entre sí. Rastro pone un diccionario de negocio entre tus bases y tus preguntas: contrato, empresa, grupo, agencia. Traduce cada base a esas palabras una sola vez, y después preguntás con esas palabras.»
>
> «La demo: ¿con quién hace negocios el gobierno de EE. UU.? Datos públicos de contratos federales. Tres problemas: la misma empresa escrita de varias formas, grupos con muchas empresas, y saber por qué la respuesta dice lo que dice.»

## 1:00 – 3:00 · El ejemplo: el grupo Leidos (app, pestaña Preguntar; diapositiva 4)

1. Elegir *¿cuánto le contrata el gobierno al grupo Leidos?* y apretar **Responder**.

> «Un solo grupo: 21 empresas, 54.700 millones de dólares. La base de contratos reparte a Leidos en seis "matrices" distintas; Rastro las une.»

2. Elegir *«Science Applications International Corporation», ¿es de Leidos o de SAIC?*, apretar **Responder** y abrir **¿Cómo lo supe?**

> «La trampa: en 2013 la vieja SAIC pasó a llamarse Leidos y una empresa nueva tomó el nombre SAIC. Sin Rastro, una de las consultas le sumó a Leidos 41.000 millones que son de SAIC. Rastro no, y acá dice por qué: el nombre legal de hoy le gana al nombre anterior, y muestra lo que descartó. Cada respuesta se puede auditar.»

## 3:00 – 4:00 · Por qué confiar (app, pestaña Por qué confiar; diapositiva 5)

> «Tres pruebas, medidas. Con Rastro, 8 de 9 respuestas correctas; sin Rastro, 5 de 9. La misma pregunta hecha de cuatro formas da la misma respuesta. Y si una base cambia, se arregla en una línea.»
>
> «Con honestidad: Rastro también se equivocó en una, y la revisión encontró empresas que todavía no une. Se ve en la evidencia y se corrige en un solo lugar.»

## 4:00 – 5:00 · El mismo Rastro, otro dominio (diapositivas 6 a 8)

En la barra lateral, cambiar **Dominio** a **Oncología**. Elegir *fármacos contra HER2 en cáncer de mama* y apretar **Responder**.

> «El mismo Rastro, con datos de otro mundo: ensayos clínicos de cáncer. El problema es el mismo: el mismo fármaco escrito como "Pembrolizumab 200 mg", como un código o como "KEYTRUDA". Rastro responde y muestra por qué. Con la misma pregunta hecha de cuatro formas, sin Rastro la respuesta cambió en 9 de 10 preguntas; con Rastro, en ninguna.»

## Cierre (diapositiva 9)

> «Lo que hay que saber: el valor está en integrar los datos una vez y mantenerlos en un lugar. Funciona en cualquier dominio: lo mostramos en dos. El siguiente paso es un piloto con tus datos.»

## Si preguntan

- **«¿Y esto no se puede hacer con SQL?»** Sí, en parte. Lo que da Rastro es hacerlo una vez, mantenerlo en un lugar y poder auditar cada respuesta. El detalle está en el anexo técnico y en la versión técnica del guion.
- **«¿Quién revisó las respuestas correctas?»** Las armó un asistente de IA; falta que una persona las confirme (`docs/verificacion-humana.md`).
- **«¿Necesito saber programar?»** No. Las preguntas de ejemplo funcionan solas; para preguntas propias se configura una vez un asistente de IA.
- **«No sé nada de oncología.»** No hace falta: la app explica cada pregunta en palabras simples, y [fuentes.md](fuentes.md) tiene un glosario.

## Video de respaldo

Grabar la pantalla siguiendo este guion (Cmd+Shift+5 en la Mac, con micrófono) y guardarlo fuera del repo.
