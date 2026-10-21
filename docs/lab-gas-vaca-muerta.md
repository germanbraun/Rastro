# Rastro Lab, petróleo y gas: explicar el gas de un pozo nuevo de Vaca Muerta

Estudio de factibilidad, sin modelo. 20 de octubre de 2026.

## En una línea

**Vale hacer el caso.** Un modelo predice cuánto gas va a dar un pozo nuevo de Vaca Muerta en sus primeros meses. Rastro no lo hace más preciso: hace que **cada predicción se explique en conceptos de negocio, cada uno con su fuente, y que se pueda comprobar**. Eso es lo que se muestra. Lo segundo es que esas explicaciones no se rompan cuando la fuente cambia. La precisión solo muestra que no se pierde nada.

## Qué aporta Rastro a la explicación, y qué no

El peso de cada variable en una predicción lo calcula una técnica estándar (por ejemplo, SHAP), igual con o sin Rastro. Rastro no vuelve transparente al modelo por dentro.

Lo que Rastro sí aporta:

- **Conceptos, no columnas.** Cada variable es un término del diccionario de negocio («operadora», «socio», «distancia al gasoducto»), no `idempresa` ni `APE`.
- **Fuente, regla y evidencia.** Cada valor dice de dónde sale y cómo se calculó, y lleva a la fila original.
- **Un experto puede juzgarla.** Si la explicación dice «opera Total, que tiene el 55 %», un consultor sabe si eso tiene sentido.
- **Agrupar por concepto.** Los pesos se suman por operadora, ubicación o (después) fractura: «la mitad de la predicción es la ubicación».
- **«¿Qué pasaría si…?» en términos de negocio.** «Si lo operara Tecpetrol…», «si estuviera a 30 km del gasoducto…», con valores reales de Rastro.
- **Marca los datos dudosos.** Si una variable sale de una corrección hecha a mano o de un enlace sin confirmar, la explicación lo dice.

## Un ejemplo real: el mismo pozo, dos explicaciones

Pozo TAU.Nq.AP-1094(h), Aguada Pichana Este. Empezó a producir en marzo de 2025 y dio 47,0 millones de m³ de gas en 6 meses.

| Sin Rastro | Con Rastro | ¿Por qué? (lo que se abre al hacer clic) |
|---|---|---|
| `empresa` = TOTAL AUSTRAL S.A. | **Operadora:** Total Austral, con 22 pozos de gas nuevos en Vaca Muerta antes de este | Capítulo IV, declaración jurada del mes de inicio; regla «rige la declaración jurada» |
| `porcentaje` = 27,27 (del mapa) | **Participación de la operadora:** 55 % (socios: Wintershall 22,5 %, YPF 16,9 %, Pan American 5,6 %) | Corrección con documento: Acuerdo Marco de Neuquén, Anexo IV. El mapa de la Secretaría reparte en partes iguales. **Dato corregido a mano**: Rastro lo marca |
| `idareapermisoconcesion` = APE | **Concesión:** Aguada Pichana Este | Capítulo IV y mapa de concesiones, unidos por código |
| (no está en ninguna tabla) | **Gasoducto más cercano:** Gas Pacífico, a 12 km | Traza de ENARGAS y contorno de la concesión; regla de distancia en `linking/energia/link.py` |
| `vecinos_g6` = 52,8 | **Pozos vecinos:** los 5 más cercanos que ya producían dieron una mediana de 52,8 millones de m³ | Padrón de pozos (coordenadas) y producción del Capítulo IV |

Otros dos ejemplos del mismo tipo:

- **La Calera** (Pluspetrol, socia YPF 50 %): el gasoducto Gas Pacífico pasa a 0,3 km del contorno.
- **Pluspetrol** declara con dos nombres: «Pluspetrol S.A.» y, desde 2025, «Pluspetrol Cuenca Neuquina», la filial que compró las áreas de ExxonMobil. Sin Rastro, en 2025 aparece una operadora sin historia; con Rastro es Pluspetrol, con 37 pozos nuevos en Vaca Muerta antes de febrero de 2025 (150 pozos de Vaca Muerta en total, de 2023 a 2025). La unión es una corrección revisada por IA, a confirmar por una persona, y la explicación lo dice.

## Los datos alcanzan

Capítulo IV de la Secretaría de Energía (producción por pozo y mes, 2023–2025, ya en Rastro) y el padrón de pozos. Consulta: `lab/gas/pozos-nuevos.sql`.

| Año de inicio | Pozos de gas nuevos | Con 6 meses de historia | Todos los pozos nuevos de Vaca Muerta |
|---|---|---|---|
| 2023 | 84 | 84 | 294 |
| 2024 | 85 | 85 | 403 |
| 2025 | 76 | 54 | 464 |
| **Total** | **245** | **223** | **1.161** |

- **Pozo nuevo:** formación Vaca Muerta, shale, primer mes con producción después de enero de 2023. Se descartan 36 pozos viejos que se reactivan.
- **Qué se predice:** el gas de los meses 2 a 7 (el primer mes suele ser parcial). Mediana: unos 51 millones de m³ en 6 meses, estable entre años. Con 12 meses quedarían solo 2 pozos de 2025 para probar.
- **Entrenar con 2023–2024 y probar con 2025** (169 y 54 pozos). Sin modelo, «la mediana de la operadora» ya explica el 39 % de la variación (error medio de 14,9 millones de m³). La concesión sola explica el 63 % de la variación total: la ubicación manda.

## Paso 1: lo que salió (20 de octubre de 2026)

**Rastro ya da cómo arrancó cada pozo** (`energia:WellStart`): el primer mes con producción, quién lo declaró ese mes, con qué nombre y qué tipo de pozo. Son 2.263 pozos nuevos de 2023 a 2025, 244 de shale gas de Vaca Muerta. La operadora de hoy sigue en `energia:operator`.

**El mismo modelo, dos veces** (`lab/gas/modelo.py`): una regresión lineal; la predicción es el gas de un pozo promedio más el aporte de cada variable, en millones de m³. 216 pozos con sus meses 2 a 7: 167 de 2023 y 2024 para entrenar, 49 de 2025 para probar.

| | Error medio (millones de m³) | R² |
|---|---|---|
| La mediana de todos los pozos | 22,1 | — |
| La mediana de la operadora | 17,7 | — |
| A, tablas crudas: empresa como se declara, código de concesión, porcentaje del mapa | 16,7 | 0,44 |
| B, Rastro: operadora (grupo), concesión, participación corregida | 16,7 | 0,44 |

**La precisión es la misma, como se esperaba.** La diferencia está en lo que dice cada explicación. Pozo 166271 de Aguada Pichana Este (empezó en marzo de 2025, dio 58,4; los dos predicen 61,4):

| Sin Rastro (A) | Con Rastro (B) |
|---|---|
| `empresa` = TOTAL AUSTRAL S.A.: +4,4 | **Operadora: Total Austral: +5,7.** ¿Por qué? La declara en el primer mes (marzo de 2025) como pozo gasífero; regla: rige la declaración jurada del primer mes; Capítulo IV |
| `area` = APE: −1,8 | **Concesión: Aguada Pichana Este: −0,5.** El mismo código en la declaración jurada y en el mapa |
| `porcentaje` = 27,27: +3,6 | **Participación: 55 %: +1,0 · dato corregido con documento.** ¿Por qué? El mapa reparte en partes iguales; el Acuerdo Marco de Neuquén (Anexo IV, pp. 28–29) dice 55 % |
| — | **Por concepto:** la empresa +6,7; la ubicación −0,5 |

Sin Rastro, la explicación usa el 27,27 % del mapa y nadie lo nota. Con Rastro, cada variable dice de dónde sale y la corregida está marcada.

**Datos dudosos, medido:** 24 de las 49 predicciones de prueba se apoyan en un dato que no sale tal cual de la fuente: 18 de Pluspetrol (unión de nombres revisada por IA, a confirmar por una persona) y 6 de Aguada Pichana Este (participación corregida con documento). Sin Rastro no se puede saber cuáles son.

**Lo que se dejó afuera:** la distancia al gasoducto. Es una sola por concesión y, con la concesión en el modelo, solo la repite: salía al revés (estar a 0,3 km restaba 9 millones de m³). Es justo el tipo de explicación sin sentido que un experto detecta cuando la variable tiene nombre y fuente; vuelve en la prueba de áreas nuevas, donde sí agrega.

**Qué aprendió el modelo, y por qué la explicación es un solo factor.** En las 11 concesiones de entrenamiento, la operadora y los socios no cambian dentro de una concesión: el modelo aprende un efecto por concesión, y repartirlo entre «operadora», «concesión» y «participación» es arbitrario (sin Rastro salen tres números que se reparten un mismo efecto; en una primera versión, la concesión «restaba» aunque sus pozos daban más que el promedio). Por eso la explicación con Rastro dice un solo factor, «estar en esta concesión con esta operadora», con lo que aprendió el modelo (sus pozos de 2023 y 2024 y su mediana) y los hechos de Rastro que lo respaldan, cada uno con regla y evidencia: la operadora, los socios (con las correcciones marcadas) y que la concesión no cambió de operadora. El gas que se predice también sale de Rastro (`energia:gasMonths2to7`) y coincide con el que calcula el SQL en todos los pozos.

**Validación, y por qué 0,44 es el mejor caso.** El resultado depende del corte por fecha: con los meses 2 a 7, el R² va de 0,06 (entrenando solo con 2023) a 0,44 (entrenando con 2023 y 2024); mejora cuanto más pozos ve. Con el gas de los primeros 12 meses, el objetivo de otros trabajos, no valida (R² entre −0,20 y 0,23 según el corte, con 15 a 87 pozos de prueba): hay pocos pozos con 12 meses y la ventana empieza en 2023. Otros trabajos con las mismas fuentes usan pozos desde 2012 y datos de fractura. Para el paso 2: cargar más años del Capítulo IV (está publicado desde 2006) y la fractura. Se corre con `python3 lab/gas/modelo.py --12-meses`.

**En la app:** la pestaña «Rastro Lab» de petróleo y gas muestra el error de los dos modelos, cuántas predicciones se apoyan en un dato corregido y, para cada pozo de 2025, las dos explicaciones lado a lado, con «¿Por qué?» (regla, evidencia y fuentes) en cada variable de Rastro.

**Lo que falta del paso 1:** la prueba a ciegas con un consultor.

## Datos de fractura (paso 2)

Existen, son públicos y se unen por pozo: «Datos de fractura de pozos (Adjunto IV)» en datos.energia.gob.ar. Traen el largo de la rama horizontal, la cantidad de etapas, la arena y el agua. Se actualizan todos los días y el portal los marca «preliminar, sujeto a revisión».

- 237 de los 245 pozos de gas nuevos los tienen, siempre con fecha anterior al inicio. Mediana: rama de 2.800 m y 47 etapas.
- La fractura nombra la empresa con su propio texto (por ejemplo, «Phoenix Global Resources» donde la producción dice «Petrolera El Trébol») y el área por nombre. Es otro cruce que Rastro hace con regla y evidencia.

Descargados en `data/raw/fractura/` (no se versiona), el 20 de octubre de 2026.

## Plan en tres pasos

**1. Explicaciones sin fractura**, con lo que Rastro ya tiene: operadora con su grupo, socios, concesión, gasoducto y vecinos.
- Único cambio previo a la capa: **la operadora y el tipo de pozo del mes de inicio de cada pozo.** Hoy Rastro da los de diciembre de 2025, y para un modelo eso es usar el futuro. La regla ya existe por concesión y mes (`energia.operador_area_mes`).
- Lo que se ve: un pozo de 2025, el mismo modelo, dos explicaciones lado a lado, «Sin Rastro» y «Con Rastro», con «¿Por qué?» en cada variable que lleva a la fuente.

**2. Sumar la fractura como fuente nueva.**
- Le da credibilidad al modelo: son las variables que usa cualquier ingeniero.
- Es el caso real de robustez: como la fuente se revisa todos los días, se guardan dos versiones y se mide qué predicciones y qué explicaciones cambian, y si Rastro avisa.

**3. Precisión, en una línea:** «el mismo error que sin Rastro, y mejor en áreas nuevas». En 2025 hay 11 pozos de gas en 5 concesiones sin pozos anteriores (por ejemplo, Bajada de Añelo, de Shell). Ahí una tabla sola no tiene historia, y Rastro tiene la operadora con su grupo, los socios y el gasoducto.

**Paso siguiente, fuera por ahora:** guardar las explicaciones en el grafo para poder consultarlas («¿qué pozos se predijeron altos por su ubicación?»).

## Cómo se mide la explicabilidad

Con números, no con opiniones.

- **Prueba a ciegas con personas.** 10 explicaciones «Sin Rastro» y 10 «Con Rastro», mezcladas, para un consultor que no armó Rastro. Por cada una: ¿la entendés?, ¿podés comprobar el dato?, ¿la defenderías ante un cliente? Es la misma idea que `docs/preguntas-a-ciegas.md` y protege contra la circularidad: la explicación sin Rastro tiene que ser la que armaría un analista razonable con SQL (`layer/energia/sin-rastro.sql`), no una hecha mal a propósito.
- **Trazabilidad.** Qué parte de las variables de cada explicación llega a una fuente y a una regla. Con Rastro deberían ser todas; sin Rastro, solo lo que diga el código.
- **Datos dudosos.** Cuántas predicciones se apoyan en un dato corregido a mano o en un enlace sin confirmar. Medido hoy en los pozos de gas nuevos: 96 de 245. Son los 65 de Pluspetrol (unión de nombres revisada por IA) y los 31 de Aguada Pichana Este (socios corregidos con documento). En todos los pozos nuevos de Vaca Muerta se suman los 28 de Chevron.

## Riesgos

- **Pocos pozos.** Unos 85 pozos de gas nuevos por año en 8 concesiones. Mostrar rangos, no un número.
- **Fugas de futuro.** La operadora y el tipo de pozo de hoy (ver paso 1), y los socios y correcciones actuales: el Acuerdo Marco es de septiembre de 2026. Fecharlos o declararlos.
- **Un hueco de Rastro:** «Mobil Argentina» (socia de Sierra Chata en el mapa) y «ExxonMobil Exploration Argentina» (Capítulo IV) todavía no están unidas.
- **El gas no depende solo del pozo:** la demanda de invierno y la capacidad de transporte también pesan.
