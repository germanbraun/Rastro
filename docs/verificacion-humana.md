# Verificación humana

Las 20 preguntas de evaluación, sus respuestas de referencia, la adjudicación (`layer/eval/adjudication.md`) y la revisión de enlaces (`linking/review-2026-10-16.md`) las hizo un asistente de IA (Claude Code). Los números salen de ejecutar queries sobre los datos y de un puntaje automático, pero **falta que una persona confirme que las referencias son correctas**. Esta lista lo hace en alrededor de una hora, sin conocimientos técnicos: solo abrir enlaces y mirar.

Anotá en la última columna **sí**, **no** o **dudoso**. Al terminar, completá el resultado al final y cambiá las notas de "pendiente de revisión humana" en los documentos.

## 1. El caso de la demo: 488 contra 438 (lo más importante, 20 minutos)

Pregunta q02: *¿Cuántos ensayos de fase 3 prueban fármacos que actúan sobre EGFR?* El SQL directo cuenta 488 y Rastro 438. Rastro dice que tiene razón. Todos los ensayos de Rastro también están en el SQL directo: la diferencia son **50 ensayos que cuenta solo el SQL directo**.

### 1a. Los 40 que salen de «humab»

El SQL directo encontró el fragmento «humab» dentro de nombres como «rhuMAb HER2» o «rhuMAb VEGF». Abrí estos cuatro y mirá en *Interventions* si el fármaco actúa sobre EGFR (por ejemplo cetuximab, panitumumab, erlotinib, gefitinib, osimertinib). Trastuzumab (HER2) y bevacizumab (VEGF) **no** cuentan.

| # | Ensayo | Qué dice la intervención | ¿Prueba un fármaco anti-EGFR? |
|---|---|---|---|
| 1 | [NCT03199885](https://clinicaltrials.gov/study/NCT03199885) | rhuMAb 2C4, rhuMAb HER2 | |
| 2 | [NCT00109239](https://clinicaltrials.gov/study/NCT00109239) | rhuMAb VEGF (bevacizumab) | |
| 3 | [NCT00513292](https://clinicaltrials.gov/study/NCT00513292) | rhuMAb HER2 | |
| 4 | [NCT00569127](https://clinicaltrials.gov/study/NCT00569127) | anti-VEGF rhuMAb | |

Si los cuatro son **no**, el SQL directo se equivoca en esos 40 y el ejemplo de la demo se sostiene.

### 1b. Los otros 10

Acá Rastro podría estar perdiendo ensayos reales. La adjudicación estima que unos 10 son reales; en dos de ellos el texto parece otro fármaco.

| # | Ensayo | Qué dice la intervención | ¿Prueba un fármaco anti-EGFR? |
|---|---|---|---|
| 1 | [NCT00115700](https://clinicaltrials.gov/study/NCT00115700) | Erbitux, MabThera | |
| 2 | [NCT00716391](https://clinicaltrials.gov/study/NCT00716391) | TPF, radioterapia y cetuximab | |
| 3 | [NCT01211938](https://clinicaltrials.gov/study/NCT01211938) | Radioterapia con cetuximab | |
| 4 | [NCT01741038](https://clinicaltrials.gov/study/NCT01741038) | Monoterapia (por ejemplo, cetuximab) | |
| 5 | [NCT02714010](https://clinicaltrials.gov/study/NCT02714010) | Gefitinib, Tarceva, icotinib | |
| 6 | [NCT03833154](https://clinicaltrials.gov/study/NCT03833154) | Cohorte de osimertinib | |
| 7 | [NCT03357952](https://clinicaltrials.gov/study/NCT03357952) | JNJ-63723283 | |
| 8 | [NCT04658862](https://clinicaltrials.gov/study/NCT04658862) | JNJ-63723283 | |
| 9 | [NCT05714202](https://clinicaltrials.gov/study/NCT05714202) | JNJ-63723283 | |
| 10 | [NCT05804045](https://clinicaltrials.gov/study/NCT05804045) | Pimicotinib (ABSK021) | |

Contá los **sí**. La referencia es correcta (a menos del 5 % del valor real) si son 21 o menos.

## 2. Enlaces de fármacos (20 minutos)

Una muestra al azar de 20 enlaces, sin los casos triviales en que el texto es igual al nombre del fármaco. Para cada uno: ¿la intervención del ensayo es ese fármaco? Las sales y formulaciones cuentan como el mismo fármaco (por ejemplo, «imatinib mesylate» es imatinib). Si dudás, abrí el ensayo.

| # | Ensayo | Intervención en el ensayo | Fármaco en Rastro | ¿Bien? |
|---|---|---|---|---|
| 1 | [NCT07382687](https://clinicaltrials.gov/study/NCT07382687) | SHR-A1811 | TRASTUZUMAB REZETECAN | |
| 2 | [NCT00675597](https://clinicaltrials.gov/study/NCT00675597) | Bevacizumab (Avastin), Taxotere (Docetaxel), Vinorelbine Tartrate (Navelbine) | VINORELBINE | |
| 3 | [NCT06892431](https://clinicaltrials.gov/study/NCT06892431) | Mitoxantrone Hydrochloride Liposome | MITOXANTRONE | |
| 4 | [NCT01249690](https://clinicaltrials.gov/study/NCT01249690) | Bortezomib,Pirarubicin,Dexamethasone | BORTEZOMIB | |
| 5 | [NCT01494506](https://clinicaltrials.gov/study/NCT01494506) | 5 Fluorouracil | FLUOROURACIL | |
| 6 | [NCT01041781](https://clinicaltrials.gov/study/NCT01041781) | pemetrexed disodium | PEMETREXED | |
| 7 | [NCT01005914](https://clinicaltrials.gov/study/NCT01005914) | imatinib mesylate | IMATINIB | |
| 8 | [NCT05272696](https://clinicaltrials.gov/study/NCT05272696) | Nab-paclitaxel, cisplatin and Pembrolizumab combination | PEMBROLIZUMAB | |
| 9 | [NCT01271166](https://clinicaltrials.gov/study/NCT01271166) | Imatinib, Fluorouracil, Oxaliplatin, Leucovorin and Bevacizumab | BEVACIZUMAB | |
| 10 | [NCT05784987](https://clinicaltrials.gov/study/NCT05784987) | Mitoxantrone hydrochloride liposome | MITOXANTRONE | |
| 11 | [NCT00512798](https://clinicaltrials.gov/study/NCT00512798) | PS-341 (VELCADE) | BORTEZOMIB | |
| 12 | [NCT06559345](https://clinicaltrials.gov/study/NCT06559345) | Cyclophosphamide | CYCLOPHOSPHAMIDE ANHYDROUS | |
| 13 | [NCT07604766](https://clinicaltrials.gov/study/NCT07604766) | Rina-S | RINATABART SESUTECAN | |
| 14 | [NCT00093639](https://clinicaltrials.gov/study/NCT00093639) | imatinib mesylate | IMATINIB | |
| 15 | [NCT03221881](https://clinicaltrials.gov/study/NCT03221881) | Pegylated Liposomal Doxorubicin and docetaxel | DOXORUBICIN | |
| 16 | [NCT02201459](https://clinicaltrials.gov/study/NCT02201459) | Nilotinib (Tasigna ®) and Pegylated interferon alfa 2a (Pegasys®) | NILOTINIB | |
| 17 | [NCT00630760](https://clinicaltrials.gov/study/NCT00630760) | NRX 194204 | IRX-4204 | |
| 18 | [NCT01533090](https://clinicaltrials.gov/study/NCT01533090) | polyethylene glycol (PEG) | POLYETHYLENE GLYCOL | |
| 19 | [NCT06855810](https://clinicaltrials.gov/study/NCT06855810) | homoharringtonine | CYTARABINE | |
| 20 | [NCT04337632](https://clinicaltrials.gov/study/NCT04337632) | Doxorubicin Hydrochloride Liposome Injection+carboplatin | CARBOPLATIN | |

Precisión = sí / 20. La revisión con IA dice 98-99 % sobre todos los enlaces; esta muestra es más difícil a propósito, así que es esperable algo menos.

## 3. Conteos contra ClinicalTrials.gov (10 minutos)

La web de ClinicalTrials.gov **da más que Rastro**, y es esperable: busca con sus propios sinónimos y también encuentra tumores benignos, quistes y estudios que mencionan la enfermedad sin tratarla (se ven varios al mirar la lista). Rastro cuenta los ensayos cuya condición está codificada en MeSH como esa enfermedad o un subtipo. El 16 oct 2026 la web daba 16.913 y 717.

Este control es débil: sirve para detectar un error grueso, no para confirmar el número. Abrí 5 ensayos de la web y anotá cuántos son de verdad sobre esa enfermedad. Si la mayoría no lo son, la diferencia se explica. Si da menos que Rastro o más del doble, avisar.

| Pregunta | Rastro | Web (16 oct) | Buscar en | De 5 ensayos de la web, ¿cuántos son de esa enfermedad? |
|---|---|---|---|---|
| Ensayos de cáncer de mama | 14.405 | 16.913 | [cond=Breast Cancer](https://clinicaltrials.gov/search?cond=Breast%20Cancer) | |
| Ensayos de cáncer de páncreas terminados o retirados | 569 | 717 | [Pancreatic Cancer, terminados o retirados](https://clinicaltrials.gov/search?cond=Pancreatic%20Cancer&aggFilters=status:ter%20wit) | |

## 4. Una lista con criterio experto (5 minutos, si hay alguien del dominio)

Pregunta q01, fármacos anti-HER2 en fase 3 de cáncer de mama. Rastro responde: afatinib, disitamab vedotin, gancotamab, KN-026, lapatinib, neratinib, pertuzumab, pirotinib, trastuzumab, trastuzumab deruxtecán, trastuzumab duocarmazina, trastuzumab emtansina, tucatinib.

¿Falta alguno conocido o sobra alguno? Por ejemplo, margetuximab o zanidatamab: si tienen ensayos de fase 3 de mama, Rastro los está perdiendo.

## Resultado

| Parte | Resultado | Quién | Fecha |
|---|---|---|---|
| 1a. «humab» | __ de 4 son anti-EGFR | | |
| 1b. Los otros 10 | __ de 10 son anti-EGFR | | |
| 2. Enlaces | __ de 20 correctos | | |
| 3. Conteos | | | |
| 4. Lista HER2 | | | |

Con esto completo, los documentos pueden decir «revisado por una persona» con el número de acá.
