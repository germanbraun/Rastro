# Guion de la demo de Rastro: petróleo y gas en Argentina (5 minutos)

> **Los datos cambian. Las preguntas, no.**

Para operadoras y consultoras del sector, sin conocimientos técnicos. Tres momentos: **integración, trazabilidad y cruce con mapas**, y un cierre con las fuentes que se suman. Cada momento termina en un número: sin Rastro y con Rastro. El mazo de petróleo y gas (`docs/slides/energia.html`) y la app en el dominio **Petróleo y gas en Argentina**, modo **Demo en 3 pasos**, con «Ver detalles técnicos» apagado.

## Antes de empezar

1. Levantar todo: `cd infra && docker compose up -d` (lo hace alguien técnico, una vez).
2. Abrir http://localhost:8501. Dominio: **Petróleo y gas en Argentina**; la pestaña **Demo en 3 pasos**. Recorrer los tres pasos una vez: cada uno corre en vivo. Arriba de los pasos, «¿Por qué estos 3 pasos?» resume para qué sirve cada uno.

## 0:00 – 1:00 · Qué es Rastro y el problema (diapositivas 1 a 4)

> «Las bases de datos del sector no están conectadas entre sí. Rastro incorpora un diccionario de negocio: pozo, concesión, empresa, participación. Cada fuente se traduce a esos términos una sola vez.»
>
> «La demo usa seis fuentes públicas de cuatro organismos: la producción declarada pozo por pozo, los mapas y los estudios ambientales de la Secretaría de Energía, los gasoductos de ENARGAS, el Instituto Geográfico Nacional y el registro global de empresas.»

## 1:00 – 2:00 · 1 · Integración (app, paso 1; diapositiva 5)

> «¿Cuánto petróleo de 2025 le corresponde a cada empresa? Sumando por quien declara la producción, a YPF se le asignan 21,4 millones de metros cúbicos. Pero el petróleo se reparte entre los socios: su parte es 12,6. Petronas, que no opera ningún pozo, tiene 2,1. Los socios estaban en un texto del mapa; Rastro los separa una vez. Dicho en plata: son unos 3.600 millones de dólares de producción de los socios, con un precio supuesto de 65 dólares por barril.»

Debajo de la tabla, en **¿Por qué este número?**, elegir YPF: aparece su parte concesión por concesión, con el porcentaje y el texto del mapa del que sale cada uno.

## 2:00 – 3:00 · 2 · Trazabilidad (app, paso 2; diapositiva 6)

> «¿Cuántos pozos opera YPF? El padrón dice 12.006; las declaraciones juradas, 15.809. Rastro aplica una regla escrita, rige quien declara el último mes, y en cada pozo muestra lo que dice el padrón.»

Abrir **¿De dónde sale la respuesta?** para mostrar un pozo en desacuerdo.

## 3:00 – 4:00 · 3 · Cruce con mapas (app, paso 3; diapositiva 7)

> «La capa satelital marca posibles venteos de gas, pero solo dice la provincia. Rastro ubica cada punto en su concesión y llega a la operadora: La Calera, de Pluspetrol, tiene 482 y ningún punto de venteo declarado. Es un indicio para revisar, no una acusación.»

## 4:00 – 5:00 · Más fuentes y cierre (diapositivas 8 y 9)

> «Sumar fuentes no rehace nada: con ENARGAS, 33 concesiones con posibles venteos tienen el gasoducto de transporte más cercano a 10 km o más; con el IGN, 60 caen en áreas protegidas; con GLEIF, 12 empresas tienen identificador global.»
>
> «En síntesis: el valor está en integrar los datos una sola vez y mantenerlos en un único lugar. El siguiente paso es un piloto con datos propios.»

## Si preguntan

- **«¿Cómo saben que es correcto?»** Tres pruebas medidas (diapositiva 10 y pestaña **Por qué confiar**): Rastro acierta 9 de 9 y sin Rastro 6 de 9; la misma pregunta de cuatro formas da la misma respuesta en 5 de 5 (sin Rastro, 3 de 5); un cambio en una fuente se arregla en una línea. No salió perfecto de entrada: Rastro falló la participación de YPF porque el diccionario tenía dos palabras parecidas para «concesión» (se dejó una sola y se volvió a medir esa pregunta), y en los cambios de operadora dio 55 donde había 64, porque descartaba los meses sin producción (se corrigió la regla y se volvieron a ejecutar las mismas consultas). Las armó un asistente de IA; falta que una persona las confirme (`layer/energia/adjudicacion.md`).
- **«¿Por qué rige la declaración jurada?»** Es una decisión de negocio, escrita una vez y a la vista. Si se prefiere otra, se cambia en un solo lugar y vale para todas las preguntas.
- **«¿Los grupos salen de un registro?»** No: GLEIF no registra la matriz de estas empresas argentinas y Wikidata tampoco. Son correcciones revisadas, con su motivo.
- **«¿Y GraphRAG?»** En «Una pregunta sobre textos» (diapositiva 9): el grafo elige las cinco concesiones con más posibles venteos y los 72 estudios ambientales presentados en ellas desde 2022; la IA resume solo esos textos, citando cada estudio. Pluspetrol presenta las planillas de venteo cada semestre; en las de YPF, el listado solo muestra el informe anual (una pregunta para hacer, no una conclusión).
- **«¿Se puede ver en un mapa?»** En el paso 3 y en la pregunta «concesiones para revisar» la app dibuja los contornos de las concesiones, los posibles venteos y los gasoductos de ENARGAS. Las geometrías están en el grafo con el estándar GeoSPARQL, así que otras plataformas o herramientas de grafos de conocimiento las leen igual.
- **«¿Qué concesiones habría que mirar primero?»** Rastro deduce una clase, «concesión para revisar», de dos reglas escritas una vez: posibles venteos con el gasoducto a 10 km o más (33) y 20 o más posibles venteos sin planillas de venteo presentadas desde 2022 (21). Son 45 concesiones, 9 con los dos motivos. Ninguna tabla dice «para revisar»: lo deduce Rastro, y cambiar una regla cambia la lista en todas las preguntas.
- **«¿Quién operaba antes?»** Con las declaraciones de 2023 a 2025, Rastro marca 64 cambios de operadora, con el mes y la producción antes y después. Se ven las áreas maduras que YPF cedió: por ejemplo Escalante - El Trébol pasó a Pecom en noviembre de 2024 y Barrancas a Petróleos Sudamericanos en abril de 2025.
- **«¿Se puede sumar información de afuera?»** En **Preguntar → Datos de afuera (Wikidata)**, «Consultar en vivo» une Rastro y Wikidata en una sola consulta, por el LEI, sin cargar nada (unos 15 segundos; necesita internet, y si Wikidata no responde se muestra el resultado guardado). Aparece que YPF y Pampa Energía cotizan en la Bolsa de Nueva York, un dato que no está en ninguna de las seis fuentes. Solo 3 de las 12 empresas con LEI lo tienen cargado en Wikidata.
