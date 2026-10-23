# Guion de la demo de Rastro: petróleo y gas en Argentina (3 minutos)

> **Los datos cambian. Las preguntas, no.**

Para operadoras y consultoras del sector, sin conocimientos técnicos. Cuatro momentos, una frase cada uno: **Rastro responde con evidencia, se arregla en un lugar cuando una base cambia, explica las predicciones de un modelo con esa misma evidencia, y una corrección hecha una vez llega a todo.** El mazo de petróleo y gas (`docs/slides/energia.html`, diapositivas 1 a 8) y la app en la pestaña **Demo**, con «Ver detalles técnicos» apagado (así la app muestra solo petróleo y gas).

## Antes de empezar

1. Levantar todo, desde la carpeta del repo: `docker compose up -d` (lo hace alguien técnico, una vez).
2. Abrir http://localhost:8501, pestaña **Demo**. Recorrer los cuatro momentos una vez: cada uno corre en vivo.

## 0:00 – 0:30 · Una pregunta, dos significados, y qué es Rastro (diapositivas 1 a 3)

> (Diapositiva 1, unos segundos) «Cinco cifras, medidas con datos públicos reales: respuestas correctas, la misma respuesta aunque cambie la pregunta, una línea cuando una fuente cambia, un lugar para corregir un dato, y el origen de cada enlace. En los próximos tres minutos les muestro de dónde sale cada una.» No explicarlas ahora: salen en la demo y en el anexo.

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

- **«¿Y el modelo, qué más sabe?»** (Rastro Lab; diapositiva 17) Cada predicción queda en Rastro con los registros de origen que usó. Si la fuente corrige un registro, Rastro dice de antemano qué predicciones cambian, y lo comprobamos: corregida una fractura, cambió exactamente la predicción que dijo Rastro. El asistente de IA responde preguntas sobre las predicciones: 4 de 5 sin Rastro, 5 de 5 con SQL sobre los enlaces de Rastro y 5 de 5 con Rastro; sin Rastro falla la que necesita sus reglas (qué datos están corregidos).

- **«¿Quién opera cada pozo?»** (Preguntar; diapositiva 21, en el anexo) El padrón dice 12.006 pozos de YPF; las declaraciones juradas, 15.809. Rastro aplica una regla escrita, rige quien declara el último mes, y en cada pozo muestra lo que dice el padrón. Son pozos de todo tipo: 5.391 petrolíferos, 1.394 gasíferos y el resto de inyección o parados; 5.689 produjeron en 2025.
- **«¿Y los venteos de gas?»** (Preguntar; diapositiva 22) La capa satelital marca posibles venteos, pero solo dice la provincia. Rastro ubica cada punto en su concesión y llega a la operadora: La Calera, de Pluspetrol, tiene 482 y ningún punto de venteo declarado. Es un indicio para revisar, no una acusación.
- **«¿Funciona con otros datos?»** Sí: con «Ver detalles técnicos» se ven contratos del Estado de EE. UU. y oncología, con las mismas pruebas.
- **«¿El modelo predice bien?»** Explica el 45 % de la diferencia entre los pozos de 2025, que no vio al entrenar. Un trabajo publicado con las mismas fuentes llega más lejos con más variables y otra forma de separar la prueba; prediciendo pozos nuevos, ese trabajo y Rastro quedan parecidos (detalle en `docs/lab-gas-vaca-muerta.md`). Rastro no busca más precisión: busca que cada predicción se pueda defender.

- **«¿Cómo saben que es correcto?»** Tres pruebas medidas (diapositiva 14 y pestaña **Por qué confiar**): Rastro acierta 10 de 10 y sin Rastro 7 de 10; la misma pregunta de cuatro formas da la misma respuesta en 5 de 5 (sin Rastro, 3 de 5); un cambio en una fuente se arregla en una línea. No salió perfecto de entrada: Rastro falló la participación de YPF porque el diccionario tenía dos palabras parecidas para «concesión» (se dejó una sola y se volvió a medir esa pregunta), y en los cambios de operadora dio 55 donde había 64, porque descartaba los meses sin producción (se corrigió la regla y se volvieron a ejecutar las mismas consultas). Las armó un asistente de IA; falta que una persona las confirme (`layer/energia/adjudicacion.md`).
- **«¿Por qué rige la declaración jurada?»** Es una decisión de negocio, escrita una vez y a la vista. Si se prefiere otra, se cambia en un solo lugar y vale para todas las preguntas.
- **«¿Los grupos salen de un registro?»** No: GLEIF no registra la matriz de estas empresas argentinas y Wikidata tampoco. Son correcciones revisadas, con su motivo.
- **«¿Y GraphRAG?»** En «Una pregunta sobre textos» (diapositiva 25): el grafo elige las cinco concesiones con más posibles venteos y los 72 estudios ambientales presentados en ellas desde 2022; la IA resume solo esos textos, citando cada estudio. Pluspetrol presenta las planillas de venteo cada semestre; en las de YPF, el listado solo muestra el informe anual (una pregunta para hacer, no una conclusión).
- **«¿Se puede ver en un mapa?»** En **Preguntar**, en la pregunta de los venteos y en «concesiones para revisar», la app dibuja los contornos de las concesiones, los posibles venteos y los gasoductos de ENARGAS. Las geometrías están en el grafo con el estándar GeoSPARQL, así que otras plataformas o herramientas de grafos de conocimiento las leen igual.
- **«¿Qué concesiones habría que mirar primero?»** (diapositiva 24) Rastro deduce una clase, «concesión para revisar», de dos reglas escritas una vez: posibles venteos con el gasoducto a 10 km o más (33) y 20 o más posibles venteos sin planillas de venteo presentadas desde 2022 (21). Son 45 concesiones, 9 con los dos motivos. Ninguna tabla dice «para revisar»: lo deduce Rastro, y cambiar una regla cambia la lista en todas las preguntas.
- **«¿Quién operaba antes?»** Con las declaraciones de 2023 a 2025, Rastro marca 64 cambios de operadora, con el mes y la producción antes y después. Se ven las áreas maduras que YPF cedió: por ejemplo Escalante - El Trébol pasó a Pecom en noviembre de 2024 y Barrancas a Petróleos Sudamericanos en abril de 2025.
- **«¿Se puede sumar información de afuera?»** (diapositiva 30) Sí: es **enriquecer** los datos. En **Preguntar → Enriquecer con datos de afuera (Wikidata)**, «Consultar en vivo» une Rastro y Wikidata en una sola consulta, por el LEI, sin cargar nada (unos 15 segundos; necesita internet, y si Wikidata no responde se muestra el resultado guardado). Debajo, lo mismo **guardado en Rastro**, con el día de la consulta: no depende de internet y se puede repetir (hoy lo usa la pregunta 15, no el modelo). Aparece que YPF y Pampa Energía cotizan en la Bolsa de Nueva York, un dato que no está en ninguna de las seis fuentes. Solo 3 de las 12 empresas con LEI lo tienen cargado en Wikidata.
- **«¿Y el gas?»** Rastro tiene el petróleo y el gas de cada pozo, de las mismas declaraciones juradas. La pregunta de participación muestra las dos partes (YPF: 12,6 millones de m³ de petróleo y 12.300 millones de m³ de gas), y hay una pregunta de gas de shale: YPF, Tecpetrol (Fortín de Piedra), Pluspetrol, Total y Pampa. El tipo de cada pozo (petrolífero o gasífero) también está en el diccionario.
- **«¿Y cómo saben que los datos integrados están bien?»** (Por qué confiar → Reglas de calidad; diapositiva 15) Siete reglas escritas una vez con las palabras del diccionario, comprobadas sobre todos los datos de Rastro después de cada carga: cada enlace con su fuente y su evidencia (113.913), las participaciones entre 0 y 100 % y que no sumen más de 100 en una concesión, cada predicción con su inicio de pozo y dentro de su rango, una empresa con un solo LEI, y valores posibles de profundidad, rama, presión y agua. La primera vez encontraron 5 trayectorias sin evidencia y se arregló en un lugar. Las de valores posibles marcan 17 fracturas imposibles de la fuente, y Rastro sabe que 4 predicciones de la corrida vigente las usan. Con «Ver detalles técnicos», en «Bajo el capó», cada regla en SHACL.
- **«¿Y si la IA inventa?»** (Por qué confiar → Cuando no tiene el dato; diapositiva 16) Le hicimos preguntas que los datos no responden (precios, reservas, inversiones, 2026, empleo). Con la regla de decir qué falta, ningún camino inventó, tampoco la IA sola. La diferencia está en lo que sí está: el gas que declaró Tecpetrol en 2025 (6.910 millones de m³) lo responden los caminos con datos, con su fuente; la IA sola no puede.
- **«¿Y si leo una cifra en un informe?»** (Preguntar → Comprobar una afirmación; diapositiva 16) Rastro dice si se sostiene, si no (con el valor correcto) o si no tiene el dato. «Total Austral fue la mayor productora de gas de 2025» se sostiene para el gas que opera y no para el que le corresponde (es la tercera).



## Recorrido opcional: cómo Rastro une los datos (fuera de los 3 minutos)

**Para qué:** mostrar, con un pozo y una empresa reales, lo que en SQL habría que resolver a mano en cada consulta.
Pestaña **Paso a paso** de la app, o las diapositivas 10 a 13, al comienzo del anexo: los tres pasos y por qué
importa para un asistente de IA (diapositiva 13). Los datos son reales y la app los
consulta en vivo: el pozo 164166 de la Compañía General de Combustibles (CGC), en Cañadón Seco, Santa Cruz.

1. **Un pozo, dos tablas** (parte de Rastro: *diccionario y mapeos*). El padrón y las declaraciones juradas describen
   el mismo pozo con columnas distintas. Rastro los une por el identificador oficial del pozo, no por el nombre.
2. **Una empresa, dos nombres** (parte de Rastro: *enlaces con evidencia*). «CGC ENERGIA SAU» y «COMPAÑÍA GENERAL DE
   COMBUSTIBLES S.A.» son la misma empresa según una corrección revisada, con su motivo. Decir que la revisó un
   asistente de IA y que espera la confirmación de una persona.
3. **La respuesta y su origen** (parte de Rastro: *la respuesta y su trazabilidad*). ¿Cuánto gas declaró la empresa
   en 2025? En SQL, cada nombre encuentra una parte; con Rastro, es una sola empresa, y el porqué es el enlace del
   paso 2.

## Recorrido opcional de Rastro Lab: del dato a la explicación

**Para qué:** responder la duda más común. El modelo no lee la ontología: recibe una tabla armada con los conceptos
de Rastro, y cada número de la explicación vuelve a sus registros. Pestaña **Rastro Lab → Paso a paso · Del dato a la
explicación**, o las diapositivas 18 a 20, después de la de Rastro Lab. Es el mismo pozo real que abre la pestaña (165404).

1. **Dar significado a las fuentes** (parte de Rastro: *diccionario, mapeos y enlaces*). Las variables salen de Inicio
   del pozo, Fractura, Trayectoria y Participación, con la concesión y la empresa ya unidas.
2. **Preparar y entrenar** (parte de Rastro: *Rastro Lab*). El objetivo es el gas de los meses 2 a 7. Se entrena con
   pozos anteriores a 2025 y se prueba con los de 2025, sin usar datos que llegaron después.
3. **Explicar el número** (parte de Rastro: *la explicación*). De dónde sale la fórmula: una regresión lineal, cuyos
   coeficientes se aprenden con los pozos anteriores a 2025. La app muestra en vivo la cuenta de ese pozo, variable por
   variable (valor, promedio, coeficiente, aporte), y agrupada por concepto. Usar el coeficiente negativo de la rama
   para explicar por qué se agrupa la fractura. La calcula el código; no prueba causas.
4. **Abrir la evidencia** (parte de Rastro: *trazabilidad*). La predicción publicada de ese pozo, consultada en vivo:
   su número, sus factores guardados y los cuatro registros que usó (inicio, fractura, trayectoria y participación),
   cada uno con su regla, su evidencia y su fuente. Señalar la fractura: informada antes del arranque, cargada después.
