# Guion de la demo de Rastro: petróleo y gas en Argentina (3 minutos)

> **Los datos cambian. Las preguntas, no.**

Para operadoras y consultoras del sector, sin conocimientos técnicos. Cuatro momentos, una frase cada uno: **Rastro responde con evidencia, se arregla en un lugar cuando una base cambia, explica las predicciones de un modelo con esa misma evidencia, y una corrección hecha una vez llega a todo.** El mazo de petróleo y gas (`docs/slides/energia.html`, diapositivas 1 a 8) y la app en la pestaña **Demo**, con «Ver detalles técnicos» apagado (así la app muestra solo petróleo y gas).

## Antes de empezar

1. Levantar todo, desde la carpeta del repo: `docker compose up -d` (lo hace alguien técnico, una vez).
2. Abrir http://localhost:8501, pestaña **Demo**. Recorrer los cuatro momentos una vez: cada uno corre en vivo.

## 0:00 – 0:30 · Una pregunta, dos significados, y qué es Rastro (diapositivas 1 a 3)

> «¿Quién produjo más gas en Argentina en 2025? Los rankings publicados, un SQL sobre la declaración jurada y un asistente de IA con búsqueda dicen Total Austral, YPF y Tecpetrol: es lo que opera cada una, también el gas de sus socios. Si la pregunta es cuánto le corresponde a cada una, es YPF, Tecpetrol y Total Austral. Nadie dice qué midió. Rastro escribe la definición una vez, muestra las dos y por qué.»

> «Las bases de datos del sector no están conectadas entre sí. Rastro incorpora un diccionario de negocio: pozo, concesión, empresa, participación. Cada fuente se traduce a esos términos una sola vez, con datos públicos de la Secretaría de Energía, ENARGAS, el IGN y el registro global de empresas.»

## 0:30 – 1:15 · 1 · Preguntar (app, momento 1; diapositiva 4)

> «¿Cuánto petróleo de 2025 le corresponde a cada empresa? Sumando por quien declara, a YPF se le asignan 21,4 millones de metros cúbicos; repartiendo entre los socios, su parte es 12,6. Los socios estaban en un texto del mapa; Rastro los separa una vez.»

Debajo de la tabla, en **¿Por qué este número?**, elegir YPF: su parte concesión por concesión, con el porcentaje y el texto del mapa del que sale.

## 1:15 – 1:45 · 2 · La base cambia (app, momento 2; diapositiva 5)

> «La Secretaría publica una versión nueva y una columna cambia de nombre. Sin Rastro, 3 de 8 consultas se rompen y hay que encontrarlas una por una. Con Rastro, todo falla junto, en voz alta, y se arregla con una línea: las 10 preguntas vuelven a responder.»

## 1:45 – 2:30 · 3 · Predecir (app, momento 3; diapositiva 6)

> «Un modelo predice cuánto gas va a dar un pozo nuevo de Vaca Muerta. Es el mismo modelo con y sin Rastro, y predicen igual de bien. La diferencia: con Rastro, la predicción dice en qué se apoya (la concesión con su operadora, cómo se fracturó el pozo), de dónde sale cada dato y cuáles están corregidos o llegaron tarde.»

Abrir **¿De dónde sale?** en la fractura: dice cuándo se cargó el dato.

## 2:30 – 3:00 · 4 · Una corrección (app, momento 4; diapositivas 7 y 8)

> «Un documento dice que en Aguada Pichana Este Total tiene el 55 %, no el 27,27 % del mapa. Se corrige una vez en Rastro, con el documento, y cambian solos la respuesta, lo que entra al modelo y su explicación. Sin Rastro, ese dato vive en cinco lugares. Lo difícil se hace una vez, en un lugar. El siguiente paso es un piloto con datos propios.»

## Si preguntan

- **«¿Y el modelo, qué más sabe?»** (Rastro Lab; diapositiva 12) Cada predicción queda en Rastro con los registros de origen que usó. Si la fuente corrige un registro, Rastro dice de antemano qué predicciones cambian, y lo comprobamos: corregida una fractura, cambió exactamente la predicción que dijo Rastro. El asistente de IA responde preguntas sobre las predicciones: 4 de 5 sin Rastro, 5 de 5 con SQL sobre los enlaces de Rastro y 5 de 5 con Rastro; sin Rastro falla la que necesita sus reglas (qué datos están corregidos).

- **«¿Quién opera cada pozo?»** (Preguntar; diapositiva 13, en el anexo) El padrón dice 12.006 pozos de YPF; las declaraciones juradas, 15.809. Rastro aplica una regla escrita, rige quien declara el último mes, y en cada pozo muestra lo que dice el padrón. Son pozos de todo tipo: 5.391 petrolíferos, 1.394 gasíferos y el resto de inyección o parados; 5.689 produjeron en 2025.
- **«¿Y los venteos de gas?»** (Preguntar; diapositiva 14) La capa satelital marca posibles venteos, pero solo dice la provincia. Rastro ubica cada punto en su concesión y llega a la operadora: La Calera, de Pluspetrol, tiene 482 y ningún punto de venteo declarado. Es un indicio para revisar, no una acusación.
- **«¿Funciona con otros datos?»** Sí: con «Ver detalles técnicos» se ven contratos del Estado de EE. UU. y oncología, con las mismas pruebas.
- **«¿El modelo predice bien?»** Explica el 45 % de la diferencia entre los pozos de 2025, que no vio al entrenar. Un trabajo publicado con las mismas fuentes llega más lejos con más variables y otra forma de separar la prueba; prediciendo pozos nuevos, ese trabajo y Rastro quedan parecidos (detalle en `docs/lab-gas-vaca-muerta.md`). Rastro no busca más precisión: busca que cada predicción se pueda defender.

- **«¿Cómo saben que es correcto?»** Tres pruebas medidas (diapositiva 10 y pestaña **Por qué confiar**): Rastro acierta 10 de 10 y sin Rastro 7 de 10; la misma pregunta de cuatro formas da la misma respuesta en 5 de 5 (sin Rastro, 3 de 5); un cambio en una fuente se arregla en una línea. No salió perfecto de entrada: Rastro falló la participación de YPF porque el diccionario tenía dos palabras parecidas para «concesión» (se dejó una sola y se volvió a medir esa pregunta), y en los cambios de operadora dio 55 donde había 64, porque descartaba los meses sin producción (se corrigió la regla y se volvieron a ejecutar las mismas consultas). Las armó un asistente de IA; falta que una persona las confirme (`layer/energia/adjudicacion.md`).
- **«¿Por qué rige la declaración jurada?»** Es una decisión de negocio, escrita una vez y a la vista. Si se prefiere otra, se cambia en un solo lugar y vale para todas las preguntas.
- **«¿Los grupos salen de un registro?»** No: GLEIF no registra la matriz de estas empresas argentinas y Wikidata tampoco. Son correcciones revisadas, con su motivo.
- **«¿Y GraphRAG?»** En «Una pregunta sobre textos» (diapositiva 17): el grafo elige las cinco concesiones con más posibles venteos y los 72 estudios ambientales presentados en ellas desde 2022; la IA resume solo esos textos, citando cada estudio. Pluspetrol presenta las planillas de venteo cada semestre; en las de YPF, el listado solo muestra el informe anual (una pregunta para hacer, no una conclusión).
- **«¿Se puede ver en un mapa?»** En **Preguntar**, en la pregunta de los venteos y en «concesiones para revisar», la app dibuja los contornos de las concesiones, los posibles venteos y los gasoductos de ENARGAS. Las geometrías están en el grafo con el estándar GeoSPARQL, así que otras plataformas o herramientas de grafos de conocimiento las leen igual.
- **«¿Qué concesiones habría que mirar primero?»** (diapositiva 16) Rastro deduce una clase, «concesión para revisar», de dos reglas escritas una vez: posibles venteos con el gasoducto a 10 km o más (33) y 20 o más posibles venteos sin planillas de venteo presentadas desde 2022 (21). Son 45 concesiones, 9 con los dos motivos. Ninguna tabla dice «para revisar»: lo deduce Rastro, y cambiar una regla cambia la lista en todas las preguntas.
- **«¿Quién operaba antes?»** Con las declaraciones de 2023 a 2025, Rastro marca 64 cambios de operadora, con el mes y la producción antes y después. Se ven las áreas maduras que YPF cedió: por ejemplo Escalante - El Trébol pasó a Pecom en noviembre de 2024 y Barrancas a Petróleos Sudamericanos en abril de 2025.
- **«¿Se puede sumar información de afuera?»** (diapositiva 22) Sí: es **enriquecer** los datos. En **Preguntar → Enriquecer con datos de afuera (Wikidata)**, «Consultar en vivo» une Rastro y Wikidata en una sola consulta, por el LEI, sin cargar nada (unos 15 segundos; necesita internet, y si Wikidata no responde se muestra el resultado guardado). Debajo, lo mismo **guardado en Rastro**, con el día de la consulta: no depende de internet y se puede repetir (hoy lo usa la pregunta 15, no el modelo). Aparece que YPF y Pampa Energía cotizan en la Bolsa de Nueva York, un dato que no está en ninguna de las seis fuentes. Solo 3 de las 12 empresas con LEI lo tienen cargado en Wikidata.
- **«¿Y el gas?»** Rastro tiene el petróleo y el gas de cada pozo, de las mismas declaraciones juradas. La pregunta de participación muestra las dos partes (YPF: 12,6 millones de m³ de petróleo y 12.300 millones de m³ de gas), y hay una pregunta de gas de shale: YPF, Tecpetrol (Fortín de Piedra), Pluspetrol, Total y Pampa. El tipo de cada pozo (petrolífero o gasífero) también está en el diccionario.
- **«¿Y cómo saben que los datos integrados están bien?»** (Por qué confiar → Reglas de calidad; diapositiva 11) Cinco reglas escritas una vez con las palabras del diccionario, comprobadas sobre todos los datos de Rastro después de cada carga: cada enlace con su fuente y su evidencia (113.913), las participaciones entre 0 y 100 % y que no sumen más de 100 en una concesión, cada predicción con su inicio de pozo y dentro de su rango, una empresa con un solo LEI. La primera vez encontraron 5 trayectorias sin evidencia y se arregló en un lugar. Con «Ver detalles técnicos», en «Bajo el capó», cada regla en SHACL.
