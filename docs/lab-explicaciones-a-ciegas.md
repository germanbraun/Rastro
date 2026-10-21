# Prueba a ciegas: ¿se entienden estas explicaciones?

Un modelo predice cuánto gas va a dar un pozo nuevo de shale gas de Vaca Muerta en sus meses 2 a 7 (en millones de
m³). Abajo hay 20 explicaciones de predicciones, de 10 pozos de 2025. Para cada una, responda las tres preguntas
del 1 (nada) al 5 (totalmente). No hace falta saber cómo funciona el modelo.

1. **¿La entiende?** ¿Sabe por qué el modelo predice ese número?
2. **¿Puede comprobar los datos?** ¿Sabe de dónde sale cada dato y podría verificarlo?
3. **¿La defendería ante un cliente?**

Responda sin consultar a quien armó la prueba. Tiempo estimado: 30 minutos.

## Explicación 1

Se esperan 56,4 millones de m³: un pozo promedio da 51,6; estar en La Calera con Pluspetrol resta 4,2, y cómo se fracturó suma 8,9.

- **La Calera, con Pluspetrol: −4,2.** Los 73 pozos de La Calera que vio el modelo (todos de Pluspetrol) dieron una mediana de 45,5 millones de m³, menos que la de todos los pozos (52,2).
- **Cómo se fracturó: +8,9.** Pesan sobre todo: etapas de fractura 59 (típico: 39), +12,5; largo de la rama horizontal 3.589 m (típico: 2.278), −7,1. Un pozo con más rama tiene más etapas: el modelo reparte entre las dos un mismo efecto, y juntas suman +5,4.

Lo que respalda la predicción:

- **Operadora:** Pluspetrol (unión revisada por IA, a confirmar por una persona). Regla: rige quien declara el pozo en su primer mes. Evidencia: Primer mes con producción: 05/2025. Lo declara PLUSPETROL S.A como pozo gasífero, en LCA. Fuente: Capítulo IV de la Secretaría de Energía (declaraciones juradas).
- **Socios:** Pluspetrol 50 %, YPF S.A. 50 %. Regla: texto de socios del mapa. Evidencia: PLUSPETROL S.A.: 50 %. Fuente: Mapa de concesiones de la Secretaría de Energía (texto de socios).
- **Fractura:** 3.589 m de rama, 59 etapas (unión revisada por IA, a confirmar por una persona · cargada 1 mes después de que arrancó el pozo). Regla: las fracturas informadas hasta el mes en que arrancó el pozo, sumadas. Evidencia: Fractura informada por PLUSPETROL S.A desde 04/03/2025: rama horizontal de 3589 m, 59 etapas, 13749 t de arena, 127946 m³ de agua, presión máxima 11701 psi. Cargada en el portal el 24/06/2025. Fuente: Datos de fractura de pozos (Adjunto IV), Secretaría de Energía.

| ¿La entiende? | ¿Puede comprobar los datos? | ¿La defendería? |
|---|---|---|
|  |  |  |

## Explicación 2

Se esperan 37,0 millones de m³: un pozo promedio da 51,6; estar en Aguada Villanueva Norte con Pluspetrol resta 9,6, y cómo se fracturó resta 5,1.

- **Aguada Villanueva Norte, con Pluspetrol: −9,6.** El modelo no vio pozos de Aguada Villanueva Norte: usa lo que vio de Pluspetrol en otras concesiones.
- **Cómo se fracturó: −5,1.** Pesan sobre todo: etapas de fractura 25 (típico: 39), −8,5; largo de la rama horizontal 1.498 m (típico: 2.278), +4,2. Un pozo con más rama tiene más etapas: el modelo reparte entre las dos un mismo efecto, y juntas suman −4,3.

Lo que respalda la predicción:

- **Operadora:** Pluspetrol (unión revisada por IA, a confirmar por una persona). Regla: rige quien declara el pozo en su primer mes. Evidencia: Primer mes con producción: 04/2025. Lo declara PLUSPETROL S.A como pozo gasífero, en AVN. Fuente: Capítulo IV de la Secretaría de Energía (declaraciones juradas).
- **Socios:** YPF S.A. 100 % (Pluspetrol no figura entre los socios del mapa). Regla: texto de socios del mapa. Evidencia: Las declaraciones juradas dicen que opera Pluspetrol, pero el mapa no la lista entre los socios de Aguada Villanueva Norte. El modelo usa una participación típica. Fuente: Mapa de concesiones de la Secretaría de Energía (texto de socios).
- **Fractura:** 1.498 m de rama, 25 etapas (unión revisada por IA, a confirmar por una persona). Regla: las fracturas informadas hasta el mes en que arrancó el pozo, sumadas. Evidencia: Fractura informada por PLUSPETROL S.A desde 29/04/2024: rama horizontal de 1498 m, 25 etapas, 5942 t de arena, 49420 m³ de agua, presión máxima 11627 psi. Cargada en el portal el 25/07/2024. Fuente: Datos de fractura de pozos (Adjunto IV), Secretaría de Energía.

| ¿La entiende? | ¿Puede comprobar los datos? | ¿La defendería? |
|---|---|---|
|  |  |  |

## Explicación 3

Predicción: **52,6 millones de m³**. Un pozo promedio da 51,6; cada columna suma o resta (en millones de m³):

- `empresa = PLUSPETROL S.A.`: +1,4
- `area = LCA`: −7,7
- `porcentaje = 50`: +2,2
- `longitud_rama_horizontal_m = 3558`: −6,9
- `cantidad_fracturas = 54`: +9,4
- `arena_tn = 12325`: +0,2
- `agua_inyectada_m3 = 115065`: +2,5
- `presion_maxima_psi = 11867`: +0,0

| ¿La entiende? | ¿Puede comprobar los datos? | ¿La defendería? |
|---|---|---|
|  |  |  |

## Explicación 4

Se esperan 53,1 millones de m³: un pozo promedio da 51,6; estar en La Calera con Pluspetrol resta 4,2, y cómo se fracturó suma 5,7.

- **La Calera, con Pluspetrol: −4,2.** Los 73 pozos de La Calera que vio el modelo (todos de Pluspetrol) dieron una mediana de 45,5 millones de m³, menos que la de todos los pozos (52,2).
- **Cómo se fracturó: +5,7.** Pesan sobre todo: etapas de fractura 52 (típico: 39), +8,2; largo de la rama horizontal 3.142 m (típico: 2.278), −4,7. Un pozo con más rama tiene más etapas: el modelo reparte entre las dos un mismo efecto, y juntas suman +3,5.

Lo que respalda la predicción:

- **Operadora:** Pluspetrol (unión revisada por IA, a confirmar por una persona). Regla: rige quien declara el pozo en su primer mes. Evidencia: Primer mes con producción: 03/2025. Lo declara PLUSPETROL S.A como pozo gasífero, en LCA. Fuente: Capítulo IV de la Secretaría de Energía (declaraciones juradas).
- **Socios:** Pluspetrol 50 %, YPF S.A. 50 %. Regla: texto de socios del mapa. Evidencia: PLUSPETROL S.A.: 50 %. Fuente: Mapa de concesiones de la Secretaría de Energía (texto de socios).
- **Fractura:** 3.142 m de rama, 52 etapas (unión revisada por IA, a confirmar por una persona · cargada 1 mes después de que arrancó el pozo). Regla: las fracturas informadas hasta el mes en que arrancó el pozo, sumadas. Evidencia: Fractura informada por PLUSPETROL S.A desde 18/11/2024: rama horizontal de 3142 m, 52 etapas, 12082 t de arena, 103195 m³ de agua, presión máxima 11775 psi. Cargada en el portal el 24/04/2025. Fuente: Datos de fractura de pozos (Adjunto IV), Secretaría de Energía.

| ¿La entiende? | ¿Puede comprobar los datos? | ¿La defendería? |
|---|---|---|
|  |  |  |

## Explicación 5

Predicción: **37,2 millones de m³**. Un pozo promedio da 51,6; cada columna suma o resta (en millones de m³):

- `empresa = PLUSPETROL S.A.`: +1,4
- `area = AVN`: −10,8
- `porcentaje = vacío (se usa 68.7244)`: −0,0
- `longitud_rama_horizontal_m = 1498`: +4,2
- `cantidad_fracturas = 25`: −8,5
- `arena_tn = 5942.01`: −0,2
- `agua_inyectada_m3 = 49419.6`: −0,7
- `presion_maxima_psi = 11627`: +0,1

| ¿La entiende? | ¿Puede comprobar los datos? | ¿La defendería? |
|---|---|---|
|  |  |  |

## Explicación 6

Se esperan 52,7 millones de m³: un pozo promedio da 51,6; estar en La Calera con Pluspetrol resta 4,2, y cómo se fracturó suma 5,3.

- **La Calera, con Pluspetrol: −4,2.** Los 73 pozos de La Calera que vio el modelo (todos de Pluspetrol) dieron una mediana de 45,5 millones de m³, menos que la de todos los pozos (52,2).
- **Cómo se fracturó: +5,3.** Pesan sobre todo: etapas de fractura 54 (típico: 39), +9,4; largo de la rama horizontal 3.558 m (típico: 2.278), −6,9. Un pozo con más rama tiene más etapas: el modelo reparte entre las dos un mismo efecto, y juntas suman +2,5.

Lo que respalda la predicción:

- **Operadora:** Pluspetrol (unión revisada por IA, a confirmar por una persona). Regla: rige quien declara el pozo en su primer mes. Evidencia: Primer mes con producción: 05/2025. Lo declara PLUSPETROL S.A como pozo gasífero, en LCA. Fuente: Capítulo IV de la Secretaría de Energía (declaraciones juradas).
- **Socios:** Pluspetrol 50 %, YPF S.A. 50 %. Regla: texto de socios del mapa. Evidencia: PLUSPETROL S.A.: 50 %. Fuente: Mapa de concesiones de la Secretaría de Energía (texto de socios).
- **Fractura:** 3.558 m de rama, 54 etapas (unión revisada por IA, a confirmar por una persona · cargada 1 mes después de que arrancó el pozo). Regla: las fracturas informadas hasta el mes en que arrancó el pozo, sumadas. Evidencia: Fractura informada por PLUSPETROL S.A desde 05/03/2025: rama horizontal de 3558 m, 54 etapas, 12325 t de arena, 115065 m³ de agua, presión máxima 11867 psi. Cargada en el portal el 24/06/2025. Fuente: Datos de fractura de pozos (Adjunto IV), Secretaría de Energía.

| ¿La entiende? | ¿Puede comprobar los datos? | ¿La defendería? |
|---|---|---|
|  |  |  |

## Explicación 7

Se esperan 72,5 millones de m³: un pozo promedio da 51,6; estar en Aguada Pichana Oeste con Pan American Energy SL suma 20,0, y cómo se fracturó suma 0,9.

- **Aguada Pichana Oeste, con Pan American Energy SL: +20,0.** Los 45 pozos de Aguada Pichana Oeste que vio el modelo (todos de Pan American Energy SL) dieron una mediana de 72,4 millones de m³, más que la de todos los pozos (52,2).
- **Cómo se fracturó: +0,9.** Pesan sobre todo: largo de la rama horizontal 2.831 m (típico: 2.278), −3,0; etapas de fractura 43 (típico: 39), +2,6. Un pozo con más rama tiene más etapas: el modelo reparte entre las dos un mismo efecto, y juntas suman −0,4.

Lo que respalda la predicción:

- **Operadora:** Pan American Energy SL. Regla: rige quien declara el pozo en su primer mes. Evidencia: Primer mes con producción: 04/2025. Lo declara PAN AMERICAN ENERGY SL como pozo gasífero, en APO. Fuente: Capítulo IV de la Secretaría de Energía (declaraciones juradas).
- **Socios:** Pan American Energy SL 60 %, YPF S.A. 40 %. Regla: texto de socios del mapa. Evidencia: PAN AMERICAN ENERGY SL: 60 %. Fuente: Mapa de concesiones de la Secretaría de Energía (texto de socios).
- **Fractura:** 2.831 m de rama, 43 etapas (cargada 3 meses después de que arrancó el pozo). Regla: las fracturas informadas hasta el mes en que arrancó el pozo, sumadas. Evidencia: Fractura informada por PAN AMERICAN ENERGY SL desde 12/02/2025: rama horizontal de 2831 m, 43 etapas, 10229 t de arena, 86619 m³ de agua, presión máxima 11900 psi. Cargada en el portal el 01/07/2025. Fuente: Datos de fractura de pozos (Adjunto IV), Secretaría de Energía.

| ¿La entiende? | ¿Puede comprobar los datos? | ¿La defendería? |
|---|---|---|
|  |  |  |

## Explicación 8

Predicción: **56,3 millones de m³**. Un pozo promedio da 51,6; cada columna suma o resta (en millones de m³):

- `empresa = PLUSPETROL S.A.`: +1,4
- `area = LCA`: −7,7
- `porcentaje = 50`: +2,2
- `longitud_rama_horizontal_m = 3589`: −7,1
- `cantidad_fracturas = 59`: +12,5
- `arena_tn = 13749`: +0,3
- `agua_inyectada_m3 = 127946`: +3,1
- `presion_maxima_psi = 11701`: +0,0

| ¿La entiende? | ¿Puede comprobar los datos? | ¿La defendería? |
|---|---|---|
|  |  |  |

## Explicación 9

Se esperan 52,9 millones de m³: un pozo promedio da 51,6; estar en La Calera con Pluspetrol resta 4,2, y cómo se fracturó suma 5,5.

- **La Calera, con Pluspetrol: −4,2.** Los 73 pozos de La Calera que vio el modelo (todos de Pluspetrol) dieron una mediana de 45,5 millones de m³, menos que la de todos los pozos (52,2).
- **Cómo se fracturó: +5,5.** Pesan sobre todo: etapas de fractura 52 (típico: 39), +8,2; largo de la rama horizontal 3.187 m (típico: 2.278), −4,9. Un pozo con más rama tiene más etapas: el modelo reparte entre las dos un mismo efecto, y juntas suman +3,3.

Lo que respalda la predicción:

- **Operadora:** Pluspetrol (unión revisada por IA, a confirmar por una persona). Regla: rige quien declara el pozo en su primer mes. Evidencia: Primer mes con producción: 02/2025. Lo declara PLUSPETROL S.A como pozo gasífero, en LCA. Fuente: Capítulo IV de la Secretaría de Energía (declaraciones juradas).
- **Socios:** Pluspetrol 50 %, YPF S.A. 50 %. Regla: texto de socios del mapa. Evidencia: PLUSPETROL S.A.: 50 %. Fuente: Mapa de concesiones de la Secretaría de Energía (texto de socios).
- **Fractura:** 3.187 m de rama, 52 etapas (unión revisada por IA, a confirmar por una persona · cargada 2 meses después de que arrancó el pozo). Regla: las fracturas informadas hasta el mes en que arrancó el pozo, sumadas. Evidencia: Fractura informada por PLUSPETROL S.A desde 04/10/2024: rama horizontal de 3187 m, 52 etapas, 12306 t de arena, 104149 m³ de agua, presión máxima 11747 psi. Cargada en el portal el 24/04/2025. Fuente: Datos de fractura de pozos (Adjunto IV), Secretaría de Energía.

| ¿La entiende? | ¿Puede comprobar los datos? | ¿La defendería? |
|---|---|---|
|  |  |  |

## Explicación 10

Predicción: **53,0 millones de m³**. Un pozo promedio da 51,6; cada columna suma o resta (en millones de m³):

- `empresa = PLUSPETROL S.A.`: +1,4
- `area = LCA`: −7,7
- `porcentaje = 50`: +2,2
- `longitud_rama_horizontal_m = 3147`: −4,7
- `cantidad_fracturas = 52`: +8,2
- `arena_tn = 12261.5`: +0,2
- `agua_inyectada_m3 = 101993`: +1,9
- `presion_maxima_psi = 11661`: +0,0

| ¿La entiende? | ¿Puede comprobar los datos? | ¿La defendería? |
|---|---|---|
|  |  |  |

## Explicación 11

Predicción: **72,7 millones de m³**. Un pozo promedio da 51,6; cada columna suma o resta (en millones de m³):

- `empresa = PAN AMERICAN ENERGY SL`: +10,2
- `area = APO`: +9,0
- `porcentaje = 60`: +1,0
- `longitud_rama_horizontal_m = 2831`: −3,0
- `cantidad_fracturas = 43`: +2,6
- `arena_tn = 10229`: +0,1
- `agua_inyectada_m3 = 86619`: +1,1
- `presion_maxima_psi = 11900`: +0,0

| ¿La entiende? | ¿Puede comprobar los datos? | ¿La defendería? |
|---|---|---|
|  |  |  |

## Explicación 12

Se esperan 48,6 millones de m³: un pozo promedio da 51,6; estar en La Calera con Pluspetrol resta 4,2, y cómo se fracturó suma 1,2.

- **La Calera, con Pluspetrol: −4,2.** Los 73 pozos de La Calera que vio el modelo (todos de Pluspetrol) dieron una mediana de 45,5 millones de m³, menos que la de todos los pozos (52,2).
- **Cómo se fracturó: +1,2.** Pesan sobre todo: etapas de fractura 44 (típico: 39), +3,2; largo de la rama horizontal 2.733 m (típico: 2.278), −2,5. Un pozo con más rama tiene más etapas: el modelo reparte entre las dos un mismo efecto, y juntas suman +0,8.

Lo que respalda la predicción:

- **Operadora:** Pluspetrol (unión revisada por IA, a confirmar por una persona). Regla: rige quien declara el pozo en su primer mes. Evidencia: Primer mes con producción: 06/2025. Lo declara PLUSPETROL S.A como pozo gasífero, en LCA. Fuente: Capítulo IV de la Secretaría de Energía (declaraciones juradas).
- **Socios:** Pluspetrol 50 %, YPF S.A. 50 %. Regla: texto de socios del mapa. Evidencia: PLUSPETROL S.A.: 50 %. Fuente: Mapa de concesiones de la Secretaría de Energía (texto de socios).
- **Fractura:** 2.733 m de rama, 44 etapas (unión revisada por IA, a confirmar por una persona). Regla: las fracturas informadas hasta el mes en que arrancó el pozo, sumadas. Evidencia: Fractura informada por PLUSPETROL S.A desde 26/04/2025: rama horizontal de 2733 m, 44 etapas, 10200 t de arena, 68120 m³ de agua, presión máxima 11176 psi. Cargada en el portal el 24/06/2025. Fuente: Datos de fractura de pozos (Adjunto IV), Secretaría de Energía.

| ¿La entiende? | ¿Puede comprobar los datos? | ¿La defendería? |
|---|---|---|
|  |  |  |

## Explicación 13

Predicción: **48,6 millones de m³**. Un pozo promedio da 51,6; cada columna suma o resta (en millones de m³):

- `empresa = PLUSPETROL S.A.`: +1,4
- `area = LCA`: −7,7
- `porcentaje = 50`: +2,2
- `longitud_rama_horizontal_m = 2733`: −2,5
- `cantidad_fracturas = 44`: +3,2
- `arena_tn = 10200`: +0,1
- `agua_inyectada_m3 = 68120`: +0,2
- `presion_maxima_psi = 11176`: +0,1

| ¿La entiende? | ¿Puede comprobar los datos? | ¿La defendería? |
|---|---|---|
|  |  |  |

## Explicación 14

Predicción: **53,1 millones de m³**. Un pozo promedio da 51,6; cada columna suma o resta (en millones de m³):

- `empresa = PLUSPETROL S.A.`: +1,4
- `area = LCA`: −7,7
- `porcentaje = 50`: +2,2
- `longitud_rama_horizontal_m = 3142`: −4,7
- `cantidad_fracturas = 52`: +8,2
- `arena_tn = 12081.8`: +0,2
- `agua_inyectada_m3 = 103195`: +1,9
- `presion_maxima_psi = 11775`: +0,0

| ¿La entiende? | ¿Puede comprobar los datos? | ¿La defendería? |
|---|---|---|
|  |  |  |

## Explicación 15

Se esperan 52,9 millones de m³: un pozo promedio da 51,6; estar en La Calera con Pluspetrol resta 4,2, y cómo se fracturó suma 5,4.

- **La Calera, con Pluspetrol: −4,2.** Los 73 pozos de La Calera que vio el modelo (todos de Pluspetrol) dieron una mediana de 45,5 millones de m³, menos que la de todos los pozos (52,2).
- **Cómo se fracturó: +5,4.** Pesan sobre todo: etapas de fractura 51 (típico: 39), +7,6; largo de la rama horizontal 3.056 m (típico: 2.278), −4,2. Un pozo con más rama tiene más etapas: el modelo reparte entre las dos un mismo efecto, y juntas suman +3,4.

Lo que respalda la predicción:

- **Operadora:** Pluspetrol (unión revisada por IA, a confirmar por una persona). Regla: rige quien declara el pozo en su primer mes. Evidencia: Primer mes con producción: 04/2025. Lo declara PLUSPETROL S.A como pozo gasífero, en LCA. Fuente: Capítulo IV de la Secretaría de Energía (declaraciones juradas).
- **Socios:** Pluspetrol 50 %, YPF S.A. 50 %. Regla: texto de socios del mapa. Evidencia: PLUSPETROL S.A.: 50 %. Fuente: Mapa de concesiones de la Secretaría de Energía (texto de socios).
- **Fractura:** 3.056 m de rama, 51 etapas (unión revisada por IA, a confirmar por una persona · cargada 2 meses después de que arrancó el pozo). Regla: las fracturas informadas hasta el mes en que arrancó el pozo, sumadas. Evidencia: Fractura informada por PLUSPETROL S.A desde 14/12/2024: rama horizontal de 3056 m, 51 etapas, 12087 t de arena, 100341 m³ de agua, presión máxima 11576 psi. Cargada en el portal el 24/06/2025. Fuente: Datos de fractura de pozos (Adjunto IV), Secretaría de Energía.

| ¿La entiende? | ¿Puede comprobar los datos? | ¿La defendería? |
|---|---|---|
|  |  |  |

## Explicación 16

Predicción: **52,8 millones de m³**. Un pozo promedio da 51,6; cada columna suma o resta (en millones de m³):

- `empresa = PLUSPETROL S.A.`: +1,4
- `area = LCA`: −7,7
- `porcentaje = 50`: +2,2
- `longitud_rama_horizontal_m = 3056`: −4,2
- `cantidad_fracturas = 51`: +7,6
- `arena_tn = 12086.6`: +0,2
- `agua_inyectada_m3 = 100341`: +1,8
- `presion_maxima_psi = 11576`: +0,1

| ¿La entiende? | ¿Puede comprobar los datos? | ¿La defendería? |
|---|---|---|
|  |  |  |

## Explicación 17

Predicción: **76,3 millones de m³**. Un pozo promedio da 51,6; cada columna suma o resta (en millones de m³):

- `empresa = PAMPA ENERGIA S.A.`: +19,1
- `area = SICH`: +7,0
- `porcentaje = 45.55`: +2,7
- `longitud_rama_horizontal_m = 2511`: −1,3
- `cantidad_fracturas = 36`: −1,7
- `arena_tn = 7660`: −0,1
- `agua_inyectada_m3 = 45737.3`: −0,9
- `presion_maxima_psi = 12711`: −0,1

| ¿La entiende? | ¿Puede comprobar los datos? | ¿La defendería? |
|---|---|---|
|  |  |  |

## Explicación 18

Se esperan 76,2 millones de m³: un pozo promedio da 51,6; estar en Sierra Chata con Pampa Energia S.A. suma 28,7, y cómo se fracturó resta 4,1.

- **Sierra Chata, con Pampa Energia S.A.: +28,7.** Los 18 pozos de Sierra Chata que vio el modelo (todos de Pampa Energia S.A.) dieron una mediana de 81,3 millones de m³, más que la de todos los pozos (52,2).
- **Cómo se fracturó: −4,1.** Pesan sobre todo: etapas de fractura 36 (típico: 39), −1,7; largo de la rama horizontal 2.511 m (típico: 2.278), −1,3.

Lo que respalda la predicción:

- **Operadora:** Pampa Energia S.A.. Regla: rige quien declara el pozo en su primer mes. Evidencia: Primer mes con producción: 06/2025. Lo declara PAMPA ENERGIA S.A como pozo gasífero, en SICH. Fuente: Capítulo IV de la Secretaría de Energía (declaraciones juradas).
- **Socios:** Mobil Argentina S.A. 54,5 %, Pampa Energia S.A. 45,5 %. Regla: texto de socios del mapa. Evidencia: PAMPA ENERGIA S.A.: 45.55 %. Fuente: Mapa de concesiones de la Secretaría de Energía (texto de socios).
- **Fractura:** 2.511 m de rama, 36 etapas (cargada 6 meses después de que arrancó el pozo). Regla: las fracturas informadas hasta el mes en que arrancó el pozo, sumadas. Evidencia: Fractura informada por PAMPA ENERGIA S.A desde 11/05/2025: rama horizontal de 2511 m, 36 etapas, 7660 t de arena, 45737 m³ de agua, presión máxima 12711 psi. Cargada en el portal el 02/12/2025. Fuente: Datos de fractura de pozos (Adjunto IV), Secretaría de Energía.

| ¿La entiende? | ¿Puede comprobar los datos? | ¿La defendería? |
|---|---|---|
|  |  |  |

## Explicación 19

Se esperan 53,1 millones de m³: un pozo promedio da 51,6; estar en La Calera con Pluspetrol resta 4,2, y cómo se fracturó suma 5,6.

- **La Calera, con Pluspetrol: −4,2.** Los 73 pozos de La Calera que vio el modelo (todos de Pluspetrol) dieron una mediana de 45,5 millones de m³, menos que la de todos los pozos (52,2).
- **Cómo se fracturó: +5,6.** Pesan sobre todo: etapas de fractura 52 (típico: 39), +8,2; largo de la rama horizontal 3.147 m (típico: 2.278), −4,7. Un pozo con más rama tiene más etapas: el modelo reparte entre las dos un mismo efecto, y juntas suman +3,5.

Lo que respalda la predicción:

- **Operadora:** Pluspetrol (unión revisada por IA, a confirmar por una persona). Regla: rige quien declara el pozo en su primer mes. Evidencia: Primer mes con producción: 03/2025. Lo declara PLUSPETROL S.A como pozo gasífero, en LCA. Fuente: Capítulo IV de la Secretaría de Energía (declaraciones juradas).
- **Socios:** Pluspetrol 50 %, YPF S.A. 50 %. Regla: texto de socios del mapa. Evidencia: PLUSPETROL S.A.: 50 %. Fuente: Mapa de concesiones de la Secretaría de Energía (texto de socios).
- **Fractura:** 3.147 m de rama, 52 etapas (unión revisada por IA, a confirmar por una persona · cargada 1 mes después de que arrancó el pozo). Regla: las fracturas informadas hasta el mes en que arrancó el pozo, sumadas. Evidencia: Fractura informada por PLUSPETROL S.A desde 18/11/2024: rama horizontal de 3147 m, 52 etapas, 12261 t de arena, 101993 m³ de agua, presión máxima 11661 psi. Cargada en el portal el 24/04/2025. Fuente: Datos de fractura de pozos (Adjunto IV), Secretaría de Energía.

| ¿La entiende? | ¿Puede comprobar los datos? | ¿La defendería? |
|---|---|---|
|  |  |  |

## Explicación 20

Predicción: **52,9 millones de m³**. Un pozo promedio da 51,6; cada columna suma o resta (en millones de m³):

- `empresa = PLUSPETROL S.A.`: +1,4
- `area = LCA`: −7,7
- `porcentaje = 50`: +2,2
- `longitud_rama_horizontal_m = 3187`: −4,9
- `cantidad_fracturas = 52`: +8,2
- `arena_tn = 12306.1`: +0,2
- `agua_inyectada_m3 = 104149`: +2,0
- `presion_maxima_psi = 11747`: +0,0

| ¿La entiende? | ¿Puede comprobar los datos? | ¿La defendería? |
|---|---|---|
|  |  |  |
