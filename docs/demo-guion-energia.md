# Guion de la demo de Rastro: petróleo y gas en Argentina (3 minutos)

> **Los datos cambian. Las preguntas, no.**

Para consultoras y equipos de datos del sector que saben SQL, sin conocimientos de tecnologías semánticas. Dos actos. **Rastro Layer, un número en el que se puede confiar:** responde con evidencia, se arregla en un lugar cuando una base cambia, y una corrección hecha una vez llega a todas las respuestas. **Rastro Lab, una predicción que se puede defender:** un modelo hereda todo lo anterior, y la misma corrección ya llegó a su entrada y a su explicación. El mazo de petróleo y gas (`docs/slides/energia.html`, diapositivas 1 a 9) y la app en la pestaña **Demo**, con «Ver detalles técnicos» apagado (así la app muestra solo petróleo y gas).

## Antes de empezar

1. Levantar todo, desde la carpeta del repo: `docker compose up -d` (lo hace alguien técnico, una vez).
2. Abrir http://localhost:8501/?inicio=demo&lang=es (sin `?inicio=demo` abre la portada: «Ver la demo» o «Armá tu capa semántica»), pestaña **Demo**. Recorrer los dos actos una vez: cada momento corre en vivo.
3. **Si la demo en vivo falla** (sin red, un servicio caído, otra computadora): el mazo es un archivo que abre sin servicios, y cada momento de la pestaña **Demo** está capturado en `docs/respaldo/es/` (`momento-1.png` a `momento-4.png`, y `momento-1-por-que.png` con YPF y Loma Campana abiertos). El video del recorrido queda en `data/raw/respaldo/demo-es.webm`, fuera del repo. Se capturan de nuevo con `python3 docs/respaldo/capturar.py` cada vez que cambia un número de la demo.

## 0:00 – 0:30 · Una pregunta, dos significados, y qué es una capa semántica (diapositivas 1 a 3)

> (Diapositiva 2) «¿Quién produjo más gas en Argentina en 2025? Los rankings publicados, un SQL sobre la declaración jurada y un asistente de IA con búsqueda dicen Total Austral, YPF y Tecpetrol: es lo que opera cada una, también el gas de sus socios. Si la pregunta es cuánto le corresponde a cada una, es YPF, Tecpetrol y Total Austral. Nadie dice qué midió. Rastro escribe la definición una vez, muestra las dos y por qué.»

> (Diapositiva 3, unos segundos) «Así se ve una capa semántica: a la izquierda las fuentes como vienen; en el medio, un diccionario de negocio (pozo, concesión, empresa, participación) con sus traducciones, sus uniones con evidencia y sus reglas; a la derecha, quien pregunta, y Rastro Lab, que devuelve sus predicciones con su evidencia. Los datos no se copian. Con datos públicos de la Secretaría de Energía, ENARGAS, el IGN y el registro global de empresas.»

## Rastro Layer: un número en el que se puede confiar

### 0:30 – 1:15 · 1 · Preguntar (app, momento 1; diapositiva 4)

> «¿Cuánto petróleo de 2025 le corresponde a cada empresa? Sumando por quien declara la producción, a YPF se le asignan 21,4 millones de m³: todo lo que opera, también lo de sus socios. Su parte es 12,6. Rastro separa los socios de cada concesión una vez, con su porcentaje, y vale para todas las preguntas.»

En **¿Por qué este número?**, con YPF y Loma Campana: el 50 % de la producción de la concesión, con el texto original del mapa y los nombres de YPF unidos entre fuentes por el mismo nombre. Si preguntan por Vista o Chevron: sus partes dependen de correcciones revisadas por un asistente de IA que esperan la confirmación de una persona, y la app lo dice. El recorrido completo con Chevron está en el anexo (diapositivas 15 a 17); guion breve: `docs/demo-layer.md`.

### 1:15 – 1:45 · 2 · La base cambia (app, momento 2; diapositiva 5)

> «La Secretaría publica una versión nueva y el petróleo pasa a estar en barriles. Sin Rastro, la consulta sigue funcionando: a YPF le corresponden ahora 79,1 millones de m³ en vez de 12,6, y nada avisa. Con Rastro, una regla escrita una vez avisa que el petróleo de 2025 suma mucho más que la producción nacional, se cambia una línea y vuelve a 12,6. Un número equivocado que nadie nota es peor que una consulta rota.»

Si preguntan por las consultas rotas: con una columna que cambia de nombre, sin Rastro se rompen 3 de 8 consultas y hay que buscarlas; con Rastro, todo falla junto y se arregla con una línea (Por qué confiar).

### 1:45 – 2:10 · 3 · Una corrección (app, momento 3; diapositiva 6)

> «El mapa le da a Total el 27,27 % de Aguada Pichana Este; un documento, el Acuerdo Marco de Neuquén, dice 55 %. Se corrige una vez en Rastro, con el documento, y el gas de 2025 que le corresponde a Total ahí pasa de 1.118 a 2.256 millones de m³, en todas las respuestas a la vez. Sin Rastro, ese porcentaje vive en cinco lugares, y si se olvida uno los resultados no coinciden. Lo difícil se hace una vez, en un lugar.»

No decir todavía que la corrección llega al modelo: es la vuelta del acto siguiente.

## Rastro Lab: una predicción que se puede defender

### 2:10 – 2:50 · 4 · Predecir (app, momento 4; diapositiva 7)

> (El puente, una frase) «Todo lo que Rastro sabe (cada unión, cada regla, cada corrección) también lo hereda un modelo.»

> «Un modelo predice cuánto gas va a dar un pozo nuevo de Vaca Muerta. Es el mismo modelo con y sin Rastro, y predicen igual de bien. La diferencia: con Rastro, la predicción dice en qué se apoya (la concesión con su operadora, cómo se fracturó el pozo), de dónde sale cada dato y cuáles conviene revisar.»

Abrir **¿De dónde sale?** en la fractura: dice cuándo se cargó el dato. Después, la frase verde de abajo, la vuelta al momento 3:

> «¿Se acuerdan de la corrección de Aguada Pichana Este? Nadie tocó el modelo: ya entra con el 55 %, y su explicación dice que es un dato corregido con documento. El modelo sin Rastro sigue leyendo el 27,27 % del mapa.»

Si preguntan si cambió la predicción: casi nada (lo dice la prueba de la corrección); lo que cambia es que el dato es el correcto y lo dice.

## 2:50 – 3:00 · Cierre (diapositivas 8 y 9)

> (Diapositiva 8, unos segundos) «Eso es una capa semántica: el significado se define una vez, las fuentes se unen una vez con evidencia, las preguntas no dependen de cómo se guardan los datos, cada respuesta se audita, la IA pregunta por conceptos y todo está en estándares abiertos. Lo vieron con datos reales.»

> (Diapositiva 9) «Lo que todavía falta, dicho antes de que lo pregunten, y el siguiente paso: un piloto con datos propios.»

## Si preguntan

- **«¿Y el modelo, qué más sabe?»** (Rastro Lab; diapositiva 21) Cada predicción queda en Rastro con los registros de origen que usó. Si la fuente corrige un registro, Rastro dice de antemano qué predicciones cambian, y lo comprobamos: corregida una fractura, cambió exactamente la predicción que dijo Rastro. El asistente de IA responde preguntas sobre las predicciones: 4 de 5 sin Rastro, 5 de 5 con SQL sobre los enlaces de Rastro y 5 de 5 con Rastro; sin Rastro falla la que necesita sus reglas (qué datos están corregidos).

- **«¿Quién opera cada pozo?»** (Preguntar; diapositiva 27, en el anexo) El padrón dice 12.006 pozos de YPF; las declaraciones juradas, 15.809. Rastro aplica una regla escrita, rige quien declara el último mes, y en cada pozo muestra lo que dice el padrón. Son pozos de todo tipo: 5.391 petrolíferos, 1.394 gasíferos y el resto de inyección o parados; 5.689 produjeron en 2025.
- **«¿Y los venteos de gas?»** (Preguntar; diapositiva 28) La capa satelital marca posibles venteos, pero solo dice la provincia. Rastro ubica cada punto en su concesión y llega a la operadora: La Calera, de Pluspetrol, tiene 482 y ningún punto de venteo declarado. Es un indicio para revisar, no una acusación.
- **«¿Funciona con otros datos?»** Sí: con «Ver detalles técnicos» se ven contratos del Estado de EE. UU. y oncología, con las mismas pruebas.
- **«¿El modelo predice bien?»** Explica el 45 % de la diferencia entre los pozos de 2025, que no vio al entrenar. Un trabajo publicado con las mismas fuentes llega más lejos con más variables y otra forma de separar la prueba; prediciendo pozos nuevos, ese trabajo y Rastro quedan parecidos (detalle en `docs/lab-gas-vaca-muerta.md`). Rastro no busca más precisión: busca que cada predicción se pueda defender.

- **«¿Cómo saben que es correcto?»** Tres pruebas medidas (diapositiva 18 y pestaña **Por qué confiar**): Rastro acierta 10 de 10 y sin Rastro 8 de 10; la misma pregunta de cuatro formas da la misma respuesta en 5 de 5 (sin Rastro, 2 de 5); un cambio en una fuente se arregla en una línea. No salió perfecto de entrada: Rastro falló la participación de YPF porque el diccionario tenía dos palabras parecidas para «concesión» (se dejó una sola y se volvió a medir esa pregunta), y en los cambios de operadora dio 55 donde había 64, porque descartaba los meses sin producción (se corrigió la regla y se volvieron a ejecutar las mismas consultas). Las armó un asistente de IA; falta que una persona las confirme (`layer/energia/adjudicacion.md`).
- **«¿Por qué rige la declaración jurada?»** Es una decisión de negocio, escrita una vez y a la vista. Si se prefiere otra, se cambia en un solo lugar y vale para todas las preguntas.
- **«¿Los grupos salen de un registro?»** No: GLEIF no registra la matriz de estas empresas argentinas y Wikidata tampoco. Son correcciones revisadas, con su motivo.
- **«¿Y GraphRAG?»** En «Una pregunta sobre textos» (diapositiva 31): el grafo elige las cinco concesiones con más posibles venteos y los 72 estudios ambientales presentados en ellas desde 2022; la IA resume solo esos textos, citando cada estudio. Pluspetrol presenta las planillas de venteo cada semestre; en las de YPF, el listado solo muestra el informe anual (una pregunta para hacer, no una conclusión). Lo que lee es el listado de estudios ambientales, con el tipo de cada presentación y un texto corto, no los informes completos: no prometer que «lee los PDFs».
- **«¿Puedo conversar con los datos, como con un chat?»** (Preguntar → Conversar con los datos; diapositiva 32) Sí: la IA tiene como contexto el diccionario de negocio, no las tablas. Traduce cada pregunta, y la que sigue («¿y cuánto le corresponde por su participación?»), a una consulta; Rastro la ejecuta y la IA responde en palabras leyendo solo el resultado. Un código comprueba cada número de la respuesta contra los datos y marca el que no esté; debajo, los datos y de dónde salen. Es para números y listas; para lo que dicen los textos del listado de estudios está «Una pregunta sobre textos» (GraphRAG). Necesita la clave del modelo, y todavía no está medido: no dar porcentajes de acierto.
- **«¿Se puede ver en un mapa?»** En **Preguntar**, en la pregunta de los venteos y en «concesiones para revisar», la app dibuja los contornos de las concesiones, los posibles venteos y los gasoductos de ENARGAS. Las geometrías están en el grafo con el estándar GeoSPARQL, así que otras plataformas o herramientas de grafos de conocimiento las leen igual.
- **«¿Qué concesiones habría que mirar primero?»** (diapositiva 30) Rastro deduce una clase, «concesión para revisar», de dos reglas escritas una vez: posibles venteos con el gasoducto a 10 km o más (33) y 20 o más posibles venteos sin planillas de venteo presentadas desde 2022 (21). Son 45 concesiones, 9 con los dos motivos. Ninguna tabla dice «para revisar»: lo deduce Rastro, y cambiar una regla cambia la lista en todas las preguntas.
- **«¿Quién operaba antes?»** Con las declaraciones de 2023 a 2025, Rastro marca 64 cambios de operadora, con el mes y la producción antes y después. Se ven las áreas maduras que YPF cedió: por ejemplo Escalante - El Trébol pasó a Pecom en noviembre de 2024 y Barrancas a Petróleos Sudamericanos en abril de 2025.
- **«¿Se puede sumar información de afuera?»** (diapositiva 37) Sí: es **enriquecer** los datos. Con **Ver detalles técnicos**, en **Preguntar → Enriquecer con datos de afuera (Wikidata)**, «Consultar en vivo» une Rastro y Wikidata en una sola consulta, por el LEI, sin cargar nada (unos 15 segundos; necesita internet, y si Wikidata no responde se muestra el resultado guardado). Debajo, lo mismo **guardado en Rastro**, con el día de la consulta: no depende de internet y se puede repetir (hoy lo usa la pregunta 15, no el modelo). Aparece que YPF y Pampa Energía cotizan en la Bolsa de Nueva York, un dato que no está en ninguna de las seis fuentes. Solo 3 de las 12 empresas con LEI lo tienen cargado en Wikidata.
- **«¿Y el gas?»** Rastro tiene el petróleo y el gas de cada pozo, de las mismas declaraciones juradas. La pregunta de participación muestra las dos partes (YPF: 12,6 millones de m³ de petróleo y 12.300 millones de m³ de gas), y hay una pregunta de gas de shale: YPF, Tecpetrol (Fortín de Piedra), Pluspetrol, Total y Pampa. El tipo de cada pozo (petrolífero o gasífero) también está en el diccionario.
- **«¿Y cómo saben que los datos integrados están bien?»** (Por qué confiar → Reglas de calidad; diapositiva 19) Siete reglas escritas una vez con las palabras del diccionario, comprobadas sobre todos los datos de Rastro después de cada carga: cada enlace con su fuente y su evidencia (113.913), las participaciones entre 0 y 100 % y que no sumen más de 100 en una concesión, cada predicción con su inicio de pozo y dentro de su rango, una empresa con un solo LEI, y valores posibles de profundidad, rama, presión y agua. La primera vez encontraron 5 trayectorias sin evidencia y se arregló en un lugar. Las de valores posibles marcan 17 fracturas imposibles de la fuente, y Rastro sabe que 4 predicciones de la corrida vigente las usan. Con «Ver detalles técnicos», en «Bajo el capó», cada regla en SHACL.
- **«¿Y si la IA inventa?»** (Por qué confiar → Cuando no tiene el dato; diapositiva 20) Le hicimos preguntas que los datos no responden (precios, reservas, inversiones, 2026, empleo). Con la regla de decir qué falta, ningún camino inventó, tampoco la IA sola. La diferencia está en lo que sí está: el gas que declaró Tecpetrol en 2025 (6.910 millones de m³) lo responden los caminos con datos, con su fuente; la IA sola no puede.
- **«¿Y si leo una cifra en un informe?»** (con **Ver detalles técnicos**, Preguntar → Comprobar una afirmación; diapositiva 20) Rastro dice si se sostiene, si no (con el valor correcto) o si no tiene el dato. «Total Austral fue la mayor productora de gas de 2025» se sostiene para el gas que opera y no para el que le corresponde (es la tercera).



## Recorrido opcional: cómo Rastro une los datos (fuera de los 3 minutos)

**Para qué:** mostrar, con un pozo y una empresa reales, lo que en SQL habría que resolver a mano en cada consulta.
En la app, **Por qué confiar → Paso a paso** (o su pestaña, con «Ver detalles técnicos»), o las diapositivas 11 a 14, al comienzo del anexo: los tres pasos y por qué
importa para un asistente de IA (diapositiva 14). Los datos son reales y la app los
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

**Para qué:** seguir un mismo pozo desde el registro de origen hasta el modelo y la evidencia. En la pestaña
**Rastro Lab**, elegir el pozo arriba: esa selección gobierna el recorrido y la comparación de predicciones.
Las diapositivas 22 a 26 muestran la instantánea del pozo 165404 verificada el 24/10/2026; los valores actuales se ven en la app.

1. **Fuente → significado → entrada.** Abrir «Paso a paso». La primera tabla une campo de origen, valor calculado
   sobre las fuentes, propiedad de Rastro, columna del modelo y valor efectivo. Para etapas: parte 4799,
   `cantidad_fracturas` → `energia:fracStages` → `etapas = 53`. No se etiqueta a mano cada fila.
2. **Preparar y entrenar.** El objetivo es el gas de los meses 2 a 7. El corte es cronológico; los faltantes usan
   el promedio del entrenamiento y se conservan como «No informado» en la columna original. Mostrar los estados:
   observado, imputado, llegó tarde y pendiente de confirmación humana. La fractura de 165404 llegó en abril de
   2025, después del inicio de febrero: es un recorrido retrospectivo, no una garantía de disponibilidad histórica.
3. **Predicción → aporte → variable.** Mostrar la fórmula general y la misma cuenta partiendo del promedio.
   Cada aporte es un coeficiente aprendido por la diferencia respecto del promedio; «Fractura» reúne cinco. Abrir «Fractura», seleccionar «Etapas» y ver su valor, coeficiente y aporte.
   Debajo están los registros originales y las URI de la evidencia. Cambiar de pozo actualiza todas estas vistas.
   Los valores se calculan sin redondear; el texto explica la cuenta, no causas físicas.
4. **Corrida → evidencia.** Leer identificador, fecha y versión de la corrida publicada. El estado compara la
   versión, toda su tabla de entradas, y la predicción, los aportes y los identificadores de origen del pozo elegido.
   Si algo difiere, la app lo indica sin sobrescribir la corrida. La evidencia consultada es actual, no una copia
   histórica inmutable de sus textos. Una predicción aislada no alcanza para reconstruir todo.

Los modelos de árbol son un experimento de la vista técnica, no parte de la demo: si preguntan, Rastro mantiene la
regresión, porque la diferencia con ella es pequeña y no se midió su incertidumbre.
