# Verificación humana

Las 20 preguntas de evaluación, sus respuestas de referencia, la adjudicación (`layer/eval/adjudication.md`) y la revisión de enlaces (`linking/review-2026-10-16.md`) las hizo un asistente de IA (Claude Code). Los números salen de ejecutar queries sobre los datos y de un puntaje automático, pero **falta que una persona confirme que las referencias son correctas**. Esta lista lo hace en alrededor de una hora, sin conocimientos técnicos: solo abrir enlaces y mirar.

Las partes 1 a 4 son de oncología. Proveedores (parte 5) y petróleo y gas (parte 6) tienen la misma idea, más corta: unos 20 minutos cada uno.

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


## 5. Proveedores del Estado de EE. UU. (20 minutos)

Revisión con IA en `layer/proveedores/adjudicacion.md` y correcciones en `linking/proveedores/correcciones.csv`.

### 5a. Las empresas que Rastro suma al grupo Leidos

El ejemplo de la demo (US$63.400 millones contra 56.400) depende de que estas empresas sean hoy de Leidos. Buscá cada una en la web de Leidos o en una noticia de la compra.

| # | Empresa | Lo que dice Rastro | ¿Es de Leidos? |
|---|---|---|---|
| 1 | Dynetics | Leidos la compró en enero de 2020 | |
| 2 | QTC Management | Pasó a Leidos en 2016, con el negocio de tecnología de Lockheed Martin | |
| 3 | Gibbs & Cox | Leidos la compró en 2021 | |
| 4 | 1901 Group | Leidos la compró en 2021 | |
| 5 | Leidos Security Detection & Automation | Leidos compró a L3Harris su negocio de detección de seguridad en 2020 | |

### 5b. La corrección de Austal USA

USAspending registra como matriz de Austal USA a Computershare Limited, un registro de acciones. Rastro la corrige a Austal Limited. ¿La matriz de Austal USA es Austal Limited (Australia)? ____

### 5c. El resumen de textos (GraphRAG)

En la app, **Proveedores → Una pregunta sobre textos**, abrí 3 temas y, en cada uno, 2 contratos citados. ¿La descripción del contrato dice lo que resume el tema?

| Tema | Contratos mirados | ¿Coincide? |
|---|---|---|
| | | |
| | | |
| | | |

## 6. Petróleo y gas en Argentina (20 minutos)

Revisión con IA en `layer/energia/adjudicacion.md` y correcciones en `linking/energia/correcciones.csv`.

### 6a. Los socios de cuatro concesiones

La pregunta de la participación (YPF: 12,6 millones de m³) depende de los socios que Rastro lee del mapa de concesiones. Comparalos con lo que publica cada operadora o la prensa del sector.

| Concesión | Socios según Rastro | ¿Coincide? |
|---|---|---|
| Loma Campana | YPF 50 %, Chevron 50 % (como Compañía de Hidrocarburo No Convencional) | si |
| La Amarga Chica | YPF 50 %, Petronas 50 % | Vista Energy compro el 50% a Petronas en 2025 |
| Bandurria Sur | YPF 44,9 %, Shell 30 %, Vista 25,1 % | si |
| Aguada Pichana Este | Total, Wintershall Dea e YPF 27,27 % cada una; Pan American 18,18 % | https://www.legislaturaneuquen.gob.ar/SVRFILES/Neuleg/ArchivoInicial/30836V_42218.pdf aparece Total 55%, Wintershall 22,65%, YPF 16,69%, Pan American 5,6 % |

**Qué se hizo con 6a:** La Amarga Chica: Vista compró en abril de 2025 el 100 % de Petronas E&P Argentina, que sigue siendo la titular del 50 %; se agregó como corrección de grupo (Petronas E&P Argentina → Vista) en `linking/energia/correcciones.csv`. Aguada Pichana Este: el Acuerdo Marco de la Legislatura de Neuquén (Anexo IV, páginas 28 y 29) dice Total 55 %, Wintershall 22,5 %, YPF 16,9 % y Pan American 5,6 % (no 22,65 % ni 16,69 %); se agregó en `linking/energia/participaciones-revisadas.csv`, con el documento. La parte de YPF pasa de 12.581.213 a 12.570.093 m³ (Aguada Pichana Este es de gas y produce poco petróleo); Vista sube a 7,0 millones con la mitad de La Amarga Chica.

### 6b. Las empresas que Rastro trata como una sola

| Nombre en la fuente | Grupo en Rastro | ¿Es la misma empresa o grupo? |
|---|---|---|
| CGC Energía SAU | Compañía General de Combustibles | si |
| Compañía de Hidrocarburo No Convencional S.R.L. | Chevron | es una sociedad comercial argentina creada en el marco del acuerdo de YPF y Chevron |
| Chevron Argentina S.R.L. | Chevron | si |
| Pluspetrol Cuenca Neuquina S.R.L. | Pluspetrol | si |

### 6c. Posibles venteos en áreas protegidas

Rastro cuenta 60 posibles venteos dentro de un área protegida del IGN. Abrí un punto de ejemplo de cada área en el mapa. ¿Cae dentro del área (o en su borde)?

| Área protegida | Puntos | Ejemplo | ¿Cae dentro? |
|---|---|---|---|
| Reserva Provincial de Uso Múltiple Auca Mahuida | 35 | [-37,73132, -68,90842](https://www.google.com/maps?q=-37.73132,-68.90842) | si |
| Reserva Hidrogeológica Meseta Espinosa y El Cordón | 23 | [-46,79979, -67,91453](https://www.google.com/maps?q=-46.79979,-67.91453) | si |
| Reserva Provincial Cabo Vírgenes | 2 | [-52,38787, -68,41644](https://www.google.com/maps?q=-52.38787,-68.41644) | si |

### 6d. El identificador global (LEI) de tres empresas

| Empresa | LEI según Rastro | ¿Es esa empresa en GLEIF? |
|---|---|---|
| YPF S.A. | [5493003N7447U18U5U53](https://search.gleif.org/#/record/5493003N7447U18U5U53) | si |
| Pampa Energía S.A. | [254900QNIK0CVURGML24](https://search.gleif.org/#/record/254900QNIK0CVURGML24) | si |
| Pecom Servicios Energía SAU | [549300BFZLJSODUHB179](https://search.gleif.org/#/record/549300BFZLJSODUHB179) | si |

### 6e. Cambios de operadora

Rastro marca 64 cambios de operadora entre 2023 y 2025 (9 de ellos en áreas sin producción, donde cambió la empresa que presenta las declaraciones). ¿Coinciden estos con las cesiones conocidas (por ejemplo, las áreas maduras que YPF cedió)?

| Concesión | Desde | Antes | Después | ¿Coincide? |
|---|---|---|---|---|
| Escalante - El Trébol | 11/2024 | YPF | Pecom | https://www.pecomenergia.com.ar/index.php/es/medios/104-pecom-asumi%C3%B3-la-titularidad-como-operador-de-la-concesi%C3%B3n-el-tr%C3%A9bol-escalante-en-chubut 10/2024|
| Barrancas | 04/2025 | YPF | Petróleos Sudamericanos | si https://vacamuertaonline.com.ar/articulo/cambio-de-manos-en-rio-negro-petroleos-sudamericanos-toma-el-control-del-yacimiento-mas-productivo-de-la-provincia.php|
| Bajo del Choique - La Invernada | 02/2025 | ExxonMobil | Pluspetrol | esto es https://www.pluspetrol.net/es/articulo/pluspetrol-adquiere-exxon-mobil-exploration-argentina-emea-1 de 12/2024 pero puede ser 2/2025|

**Sobre 6e:** los tres cambios coinciden. El desfase de 1 a 2 meses (Escalante - El Trébol: traspaso el 28/10/2024, Rastro dice 11/2024; Bajo del Choique - La Invernada: compra cerrada el 16/12/2024, Rastro dice 02/2025) es esperable: Rastro marca el cambio en el primer mes en que la otra empresa declara la mayor parte de la producción, 3 meses seguidos, y las declaraciones juradas siguieron saliendo un tiempo con el nombre anterior. El enlace de Barrancas anotado es de un área de Río Negro; la Barrancas de Rastro es la de Mendoza, cedida por YPF a Petróleos Sudamericanos con efecto el 1 de abril de 2025, según el formulario 6-K de YPF ante la SEC (https://www.sec.gov/Archives/edgar/data/904851/000119312525180832/d10518d6k.htm).

### 6f. El resumen de los estudios ambientales (GraphRAG)

En la app, **Petróleo y gas → Preguntar → Una pregunta sobre textos → Responder**. En el paso 4 («El resumen, con citas»), el primer tema es «Planillas de venteo de gas (Res. 143/98)», con los números de los estudios que cita. Buscá 3 de esos números en el paso 3 («Los 72 textos que leyó»): al elegir una fila se ve el texto completo. Ojo: son registros del listado de presentaciones ambientales de la Secretaría de Energía (conjunto «Actividad ambiental de petróleo y gas» de datos.energia.gob.ar), no las planillas: el listado dice qué se presentó, cuándo, de qué concesión y empresa, pero no trae el documento. Para ver una planilla hay que pedirla a la Secretaría o a la provincia, con su número de estudio. ¿Son registros de planillas de venteo de esas concesiones? ¿Es cierto que en las concesiones de YPF el listado no muestra ninguna desde 2022? ____

## Resultado

| Parte | Resultado | Quién | Fecha |
|---|---|---|---|
| 1a. «humab» | __ de 4 son anti-EGFR | | |
| 1b. Los otros 10 | __ de 10 son anti-EGFR | | |
| 2. Enlaces | __ de 20 correctos | | |
| 3. Conteos | | | |
| 4. Lista HER2 | | | |
| 5a. Empresas de Leidos | __ de 5 | | |
| 5b. Austal | | | |
| 5c. Textos de Leidos | __ de 3 temas | | |
| 6a. Socios | 2 de 4 (las otras 2, corregidas con su documento) | persona | 2026-10-20 |
| 6b. Grupos | 4 de 4 | persona | 2026-10-20 |
| 6c. Áreas protegidas | 3 de 3 | persona | 2026-10-20 |
| 6d. LEI | 3 de 3 | persona | 2026-10-20 |
| 6e. Cambios de operadora | 3 de 3 (dos con 1 a 2 meses de desfase, esperable) | persona | 2026-10-20 |
| 6f. Textos de venteos | pendiente: el listado no trae las planillas; se deja para más adelante | | |

Con esto completo, los documentos pueden decir «revisado por una persona» con el número de acá.
