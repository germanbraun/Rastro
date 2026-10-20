# Rastro Lab, petróleo y gas: ¿qué gana un modelo de gas de Vaca Muerta con Rastro?

Estudio de factibilidad, sin modelo. 20 de octubre de 2026.

## En una línea

**Sí vale hacer el caso, si se mide bien qué se mide.** El objetivo de Rastro Lab no es el mejor pronóstico de gas, sino mostrar qué cambia en un modelo cuando sus variables salen de Rastro y no de las tablas tal como vienen. Con pozos de shale gas de Vaca Muerta eso se puede mostrar en tres frentes: **robustez** (la fuente cambia y las variables no se rompen ni mienten), **trazabilidad** (cada predicción dice de qué fuente y de qué regla sale cada variable) y **pozos en áreas nuevas** (donde una tabla sola no tiene historia). En precisión sobre las áreas conocidas, la ventaja va a ser chica, y hay que decirlo así.

## La pregunta del caso

Un pozo de shale gas nuevo en Vaca Muerta: ¿cuánto gas va a dar en sus primeros 6 meses, antes de que produzca?

Se entrena **el mismo modelo dos veces**:

- **A, tablas crudas:** variables sacadas con SQL de los archivos como vienen (Capítulo IV, padrón, mapa de concesiones, gasoductos), sin los enlaces de Rastro.
- **B, Rastro:** las mismas ideas de variables, pero leídas de Rastro: la empresa unida entre fuentes, los socios corregidos, la historia de la concesión, la distancia al gasoducto, cada una con su procedencia.

La diferencia entre A y B es el impacto de la tecnología semántica. Lo demás (algoritmo, objetivo, cortes por fecha) es igual.

## Cuántos pozos hay

Fuente: Capítulo IV de la Secretaría de Energía, producción por pozo y mes de enero de 2023 a diciembre de 2025 (ya cargada en Rastro: `capitulo4.produccion` y `capitulo4.produccion_historica`), y el padrón de pozos con coordenadas (`capitulo4.pozo`).

**Pozo nuevo:** formación vaca muerta, recurso shale, primer mes con producción después de enero de 2023. Se descartan 36 pozos que ya figuraban en enero de 2023 con producción cero: son pozos más viejos (identificador menor) que se reactivan o se conectan tarde. Los nuevos tienen identificador 164.000 o más; los gasíferos son todos horizontales («(h)» en la sigla).

| Año de inicio | Gasíferos nuevos | Con 6 meses de historia | Con 12 meses | Todos los pozos nuevos de Vaca Muerta (gas y petróleo) |
|---|---|---|---|---|
| 2023 (feb–dic) | 84 | 84 | 84 | 294 |
| 2024 | 85 | 85 | 85 | 403 |
| 2025 | 76 | 54 | 2 | 464 |
| **Total** | **245** | **223** | **171** | **1.161** |

**Cuánto producen los gasíferos** (gas acumulado en millones de m³; P10 = el 10 % más bajo, P90 = el 10 % más alto):

| Año | 6 meses: P10 / mediana / P90 | 12 meses: P10 / mediana / P90 |
|---|---|---|
| 2023 | 15,6 / 53,1 / 75,9 | 52,6 / 99,7 / 135,3 |
| 2024 | 15,9 / 49,3 / 74,9 | 34,9 / 89,5 / 134,7 |
| 2025 (1.er semestre) | 23,5 / 51,4 / 89,7 | — |

- Estable entre años (el año explica el 1 % de la variación): se puede separar entrenamiento y prueba por fecha.
- **Objetivo: 6 meses, no 12.** Van juntos (correlación 0,92) y con 6 meses hay 54 pozos de 2025 para probar; con 12, solo 2.
- El primer mes casi siempre es parcial. Mejor contar **los meses 2 a 7** (mediana 56,9) o cargar los días de producción, que el Capítulo IV publica y Rastro todavía no carga.
- 32 de 171 pozos tienen algún mes en cero en su primer año (paradas, conexión tardía): decidir si se excluyen.
- 171 pozos gasíferos dieron 16.200 millones de m³ en su primer año; los 669 petrolíferos nuevos del mismo período, 3.100.

**Por operadora y concesión.** 6 operadoras y 8 concesiones tienen el 92 % de los gasíferos nuevos, y cada concesión tiene una sola operadora.

| Operadora | Pozos | Mediana 6 meses | Concesión principal |
|---|---|---|---|
| Pluspetrol | 65 | 39,2 | La Calera |
| Tecpetrol | 57 | 56,0 | Fortín de Piedra |
| Pampa Energía | 33 | 61,3 | Sierra Chata, El Mangrullo |
| Total Austral | 31 | 57,9 | Aguada Pichana Este |
| Pan American Energy | 30 | 71,5 | Aguada Pichana Oeste |
| YPF | 24 | 21,3 | Aguada de la Arena, Rincón del Mangrullo |
| Shell, Capex | 5 | — | Bajada de Añelo, Parva Negra Oeste |

La concesión explica el 63 % de la variación (en logaritmo) y la operadora el 47 %. Referencias sin modelo, entrenando con 2023–2024 (169 pozos) y probando con el primer semestre de 2025 (54): la mediana de la operadora tiene un error medio de 14,9 millones de m³ (R² 0,39), la de la concesión 16,4 (R² 0,29), la mediana general 19,0 (R² 0). Con otro corte (hasta junio de 2024 contra julio 2024–junio 2025, 74 pozos de prueba) el orden es el mismo. **Un modelo tiene que ganarle a «la mediana de la operadora».**

## Qué variables cambian entre A y B

Medido en los pozos nuevos de Vaca Muerta. Donde A y B dan lo mismo, se dice.

| Variable | A, tablas crudas | B, Rastro | ¿Cambia algo? (medido) |
|---|---|---|---|
| Operadora del pozo | El nombre que declara cada fila, o el del padrón | Una empresa, con la regla y la evidencia (`energia:OperatorLink`): rige la declaración jurada, con el padrón a la vista | El padrón dice otra empresa en 39 de 1.161 pozos nuevos (4 gasíferos). Pluspetrol declara con dos nombres: «Pluspetrol S.A.» (150 pozos de Vaca Muerta) y, desde 2025, «Pluspetrol Cuenca Neuquina» (51), la filial que compró las áreas de ExxonMobil. Para A, en 2025 aparece una operadora sin historia; para B, es Pluspetrol con sus 150 pozos anteriores. |
| Experiencia de la operadora | Pozos anteriores con ese mismo nombre | Pozos anteriores del grupo (correcciones revisadas: Pluspetrol, CGC, Chevron, Vista) | Cambia para los pozos de 2025 de Pluspetrol Cuenca Neuquina y de los socios de Chevron y Vista. |
| Socios y su participación | Texto libre del mapa de concesiones («YPF S.A.: 50 %»), con nombres distintos a los del Capítulo IV | Socios unidos a la misma empresa del Capítulo IV, con porcentaje y corrección documentada (`energia:Stake`) | En Aguada Pichana Este (31 pozos gasíferos), el mapa reparte en partes iguales (27,27 % Total); el Acuerdo Marco de Neuquén dice Total 55 %, Wintershall 22,5 %, YPF 16,9 %, Pan American 5,6 %. Hueco de Rastro: «Mobil Argentina» (socia de Sierra Chata en el mapa) y «ExxonMobil Exploration Argentina» (Capítulo IV) todavía no están unidas. |
| Historia de operadora de la concesión | Hay que armarla mes a mes desde la producción | Cambios con fecha y evidencia (`energia:OperatorChange`) | Ninguna de las 8 concesiones grandes de gas cambió de operadora en 2023–2025: en este grupo no aporta. Aporta en petrolíferos (las áreas de ExxonMobil que pasaron a Pluspetrol). |
| Distancia al gasoducto | Hay que cruzar contornos y trazas (geometría) | Kilómetros al gasoducto de transporte más cercano (`energia:PipelineLink`, ENARGAS) | Cubre 15 de 17 concesiones con gasíferos nuevos; de 0,3 km (La Calera) a 33,7 km (El Mangrullo). Es de la concesión: dentro de un área conocida no agrega nada a «en qué concesión está». |
| Pozos vecinos | Unir producción y padrón por idpozo y calcular | Igual, pero con la operadora y la concesión ya resueltas | Igual en A y B, salvo la operadora del vecino. |
| Clases deducidas | No existen | Shale o tight (`energia:ShaleProduction`), tipo de pozo, «concesión para revisar» | El tipo de pozo cambia en el tiempo en 20 pozos gasíferos; Rastro guarda el de la última declaración; el modelo necesita el del primer mes. |

**Lectura honesta:** en los 245 gasíferos, las diferencias entre A y B tocan pocos pozos (los socios de Aguada Pichana Este, Pluspetrol, 4 pozos con otra operadora en el padrón). En precisión sobre áreas conocidas, B le va a ganar a A por poco o nada: la concesión ya lo explica casi todo. El impacto se ve en otras métricas.

## Cómo medir el impacto

El mismo modelo (por ejemplo, un modelo de árboles chico o una regresión sobre el logaritmo del gas), entrenado con 2023–2024 y probado con 2025, con las variables de A y con las de B.

1. **Error en pozos de áreas conocidas.** Error medio en millones de m³ y R², contra la referencia «mediana de la operadora». Esperable: empate o mejora chica.
2. **Error en pozos de áreas nuevas.** Dejar afuera una concesión entera por vez y predecir sus pozos (como si fuera un área nueva). Ahí A solo tiene «una concesión que no conozco»; B tiene la operadora con su grupo y su experiencia en otras áreas, los socios, la distancia al gasoducto y los vecinos. En 2025 hay 11 gasíferos en 5 concesiones sin pozos nuevos anteriores (Bajada de Añelo de Shell, Meseta Buena Esperanza I, Aguada Villanueva Norte, Las Tacanas II, Parva Negra Este). Es donde más se espera ver la diferencia.
3. **Estabilidad ante cambios de la fuente.** Repetir con el modelo los escenarios de la prueba de cambio que ya existe (`layer/energia/cambio/`): una columna renombrada, el gas en otra unidad, una empresa que cambia de nombre (como Pluspetrol en 2025). Métrica: cuántas variables se rompen o cambian sin aviso en A y en B, y cuánto se mueven las predicciones. En la prueba de la capa, el petróleo en barriles daba 79 millones de m³ en vez de 12,6 en las dos formas, pero solo Rastro avisaba.
4. **Trazabilidad.** Para cada predicción, qué parte de sus variables se puede rastrear hasta una fuente, una regla y una evidencia. En B, todas (cada enlace guarda su fuente y su regla); en A, ninguna fuera del código SQL. La explicación de cada pozo se escribe con eso: «Se esperan 55 millones de m³ porque opera Total (55 %, Acuerdo Marco de Neuquén), en Aguada Pichana Este, a 12 km del Gas Pacífico (ENARGAS), y sus 5 vecinos dieron…».
5. **Costo de mantener.** Líneas que hay que cambiar en A y en B cuando cambia una fuente (en la capa: una línea de mapeo contra reescribir cada consulta).

Para la venta, 3, 4 y 5 son el argumento fuerte (los datos de fractura, que se revisan todos los días, son el caso real para la 3); 1 y 2 muestran que no se pierde precisión y que en áreas nuevas se gana.

## Datos de terminación del pozo (contexto)

**Existen, son públicos y se unen por idpozo.** Es lo que más explica la productividad de un pozo según los estudios, y en este caso sirve para dos cosas: que el modelo no sea de juguete y que haya una fuente más que cambia y que hay que unir.

| Conjunto (datos.energia.gob.ar) | Qué trae | Cobertura | ¿Se une por idpozo? |
|---|---|---|---|
| Datos de fractura de pozos (Adjunto IV) | Largo de la rama horizontal, cantidad de fracturas (etapas), arena nacional e importada (t), agua (m³), presión máxima, potencia, fechas de inicio y fin de fractura, empresa que informa | 4.999 filas, 4.755 pozos, 2006–2026; 3.096 pozos de Vaca Muerta. Se actualiza todos los días y el portal lo marca «preliminar, sujeto a revisión» | Sí |
| Capítulo IV – Pozos | Profundidad, tipo de pozo, fechas de perforación y terminación, coordenadas | 85.611 pozos | Sí |
| Trayectorias de pozo Vaca Muerta | Profundidad, largo de rama, traza | 1.903 pozos | Sí (columna `idpo`) |

**Medido en los pozos de este estudio:** 237 de los 245 gasíferos nuevos tienen fractura (83, 84 y 70 por año), todas con fecha anterior o igual al mes de inicio, así que no hay fuga por fecha. Mediana: rama de 2.800 m y 47 etapas. Solos, la rama y las etapas se correlacionan poco con el gas de 6 meses (0,19 y 0,20): ayudan combinadas con el área, no reemplazan a la ubicación. De todos los pozos nuevos de Vaca Muerta, 1.098 de 1.161 tienen fractura.

**Antecedente:** una tesis de la Universidad Torcuato Di Tella (Fernández Gazzaniga, 2025, [repositorio UTDT](https://repositorio.utdt.edu/handle/20.500.13098/14415)) une estas cuatro fuentes (producción, padrón, fractura y trayectorias) para 642 pozos de gas de Vaca Muerta de 2012 a 2025 y predice el gas de 12 meses. La mediana por área da R² 0,47; su mejor modelo, R² 0,75 sobre los 128 pozos más recientes. Las variables más importantes: área, longitud geográfica, presión máxima, largo de rama y etapas. Muestra que la precisión se puede lograr con datos públicos; Rastro Lab no compite ahí, muestra qué agrega la capa semántica a ese mismo trabajo.

**Por qué importa para el impacto:** la fractura nombra la empresa que informa con su propio texto (por ejemplo, «Phoenix Global Resources» donde la producción declara «Petrolera El Trébol», o los dos nombres de Pluspetrol) y el área por nombre, no por código. Es otro cruce de nombres que una tabla sola hace a mano y que Rastro haría con regla y evidencia. Y como se revisa todos los días, es el caso natural para medir la estabilidad: guardar dos versiones y ver qué variables cambian.

Descargados en `data/raw/fractura/` (no se versiona): `fractura.csv`, `capitulo-iv-pozos.csv`, `trayectorias-vm.csv`, el 20 de octubre de 2026.

## Riesgos

- **Pocos pozos.** Unos 85 gasíferos nuevos por año, 6 operadoras, 8 concesiones. Una diferencia chica entre A y B no se distingue del azar con 54 pozos de prueba: mostrar rangos y repetir con varios cortes. Sumar los petrolíferos (1.161 pozos, 14 operadoras) da más pozos y más casos donde Rastro cambia algo.
- **Ventana corta.** Tres años. Cargar el Capítulo IV desde 2018 (publicado) duplica o triplica los pozos de entrenamiento y suma cambios de nombres y de operadora.
- **Fugas de futuro.** Toda variable se calcula con lo que se sabía antes del inicio del pozo: experiencia, vecinos e historia, solo con pozos anteriores. Las participaciones del mapa y las correcciones son las de hoy (el Acuerdo Marco es de septiembre de 2026): en el modelo tienen que estar fechadas, o declararse como fuga conocida.
- **Rastro hoy responde «quién opera hoy».** La operadora de cada pozo es la que declara en diciembre de 2025 (`energia.operador_pozo`), y las participaciones son las del mapa actual. Para el modelo eso es usar el futuro: Rastro Lab necesita la operadora del mes de inicio (la regla ya existe por concesión y mes, `energia.operador_area_mes`) y fechas en los socios. Es el primer cambio a la capa que pide el caso.
- **El gas no depende solo del pozo.** Demanda de invierno, capacidad de transporte y pozos que se ahogan a propósito explican parte de la variación.
- **Circularidad**, como en oncología: si A queda mal armado a propósito, la ventaja de B es aparente. A tiene que ser el SQL que escribiría un analista razonable (`layer/energia/sin-rastro.sql` es el punto de partida), y las diferencias se adjudican pozo por pozo.

## Recomendación

**Hacer el caso, con este objetivo:** predecir el gas de los meses 2 a 7 de un pozo nuevo de Vaca Muerta, y comparar el mismo modelo con variables de las tablas crudas (A) y de Rastro (B), en cinco métricas: error en áreas conocidas, error en áreas nuevas, estabilidad ante cambios de la fuente, trazabilidad de cada variable y costo de mantener.

- **Población:** los 245 gasíferos como titular («el gas de Vaca Muerta»), y los 1.161 pozos nuevos (gas y petróleo, con el tipo de pozo como variable) para medir A contra B: más pozos, 14 operadoras y más casos donde Rastro cambia algo (Pluspetrol, Phoenix, Chevron, Vista).
- **Prometer lo que se puede mostrar:** en áreas conocidas, «la misma precisión, con cada número explicado y con su fuente»; en áreas nuevas y ante cambios de la fuente, «mejor». No prometer «Rastro predice mejor el gas» en general.
- **Antes del modelo, tres cambios chicos:** cargar los datos de fractura como fuente de Rastro (con su enlace de empresa y de área), sumar la operadora y el tipo de pozo **del mes de inicio** (hoy Rastro da los de diciembre de 2025) y unir «Mobil Argentina» con ExxonMobil. Opcional: cargar el Capítulo IV desde 2018 para tener más pozos y más cambios de nombre y de operadora.
- **Objetivo más alcanzable, si hace falta recortar:** sin modelo de aprendizaje, la referencia «mediana de pozos parecidos» calculada con A y con B, más la prueba de estabilidad y la explicación por pozo. Ya muestra lo esencial (variables que no se rompen y que dicen de dónde salen) con la mitad del trabajo.
