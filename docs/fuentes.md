# Las cuatro fuentes, para quien no es del dominio

> Esta guía describe las fuentes del caso de oncología. La demo actual es petróleo y gas: ver [demo-guion-energia.md](demo-guion-energia.md) y el [README](../README.md).

Una guía para presentar Rastro sin ser experto en oncología ni en desarrollo de fármacos. Para cada fuente: qué es, qué conceptos trae, un ejemplo real y con qué tener cuidado.

## El mapa en una frase

Un **fármaco** (ChEMBL) actúa sobre una **proteína del cuerpo**, su target (ChEMBL). Se prueba en **ensayos clínicos** (AACT) para tratar una **enfermedad** (MeSH). Cuando ya se usa en pacientes, se reportan sus **efectos adversos** (openFDA).

```
            actúa sobre                 se prueba en               para tratar
 Target  ◄─────────────  Fármaco  ─────────────────►  Ensayo  ─────────────────►  Enfermedad
 (ChEMBL)                (ChEMBL)                     (AACT)                      (MeSH)
                            │
                            │ tiene reportes de
                            ▼
                     Eventos adversos
                        (openFDA)
```

---

## 1. AACT: los ensayos clínicos

**Qué es.** Una copia en base de datos de **ClinicalTrials.gov**, el registro público de ensayos clínicos de Estados Unidos (y de buena parte del mundo). Por ley, muchos ensayos tienen que registrarse ahí antes de empezar. La mantiene CTTI, una alianza de la FDA y la Universidad de Duke. Dominio público.

**Qué es un ensayo clínico.** Un estudio en personas para saber si un tratamiento funciona y es seguro. Cada uno tiene un identificador, el **NCT** (por ejemplo NCT02252172).

**Conceptos que trae:**

| Concepto | Qué significa | Valores típicos |
|---|---|---|
| **Fase** | En qué etapa del desarrollo está el tratamiento | Fase 1: ¿es seguro?, pocas personas. Fase 2: ¿funciona?, decenas o cientos. Fase 3: ¿es mejor que lo que existe?, cientos o miles; es la que decide la aprobación. Fase 4: ya aprobado, seguimiento. «Fase 2/3» combina dos. |
| **Estado** | En qué punto está el ensayo | Reclutando, activo, completado, **terminado** (se cortó antes) o **retirado** (se canceló antes de empezar). Rastro llama **detenido** a terminado o retirado. |
| **Intervención** | Qué se prueba | Un fármaco, un biológico, una cirugía, radioterapia, un dispositivo. Es **texto libre**: «Pembrolizumab 200 mg», «MK-3475», «Keytruda». |
| **Condición** | La enfermedad que se estudia | Texto, más un término MeSH que asigna ClinicalTrials.gov |
| **Sponsor** | Quién organiza y paga el ensayo | **Principal** (uno) y **colaboradores**. Puede ser **industria** (una farmacéutica) o no (universidad, hospital, gobierno). |

**Ejemplo real.** NCT02252172 compara daratumumab, lenalidomida y dexametasona contra lenalidomida y dexametasona en mieloma múltiple. Fase 3, completado. El sponsor principal es una farmacéutica.

**Qué toma Rastro.** Los 106.483 ensayos de oncología: fase, estado, fechas, sponsor, intervenciones y condiciones.

**Cuidado con:**
- Las intervenciones son texto escrito por quien registra el ensayo. Por eso hace falta el entity linking para saber qué fármaco es.
- Un ensayo detenido no siempre fracasó: puede cortarse por falta de pacientes, por dinero o por una decisión del sponsor. El motivo está en `oncologia:whyStopped`, también como texto.

**Preguntas típicas:** ¿cuántos ensayos de fase 3 hay en cáncer de mama? ¿Qué sponsor tiene más ensayos detenidos?

---

## 2. ChEMBL: los fármacos y sus targets

**Qué es.** Una base de datos de moléculas con actividad biológica, de **EMBL-EBI**, el instituto europeo de bioinformática. Licencia CC BY-SA 3.0.

**Conceptos que trae:**

| Concepto | Qué significa |
|---|---|
| **Molécula** | Un fármaco o candidato. Identificador CHEMBL (por ejemplo CHEMBL941, imatinib). Tiene nombre preferido y **sinónimos**: códigos de laboratorio, nombres comerciales, nombres en otros idiomas. |
| **Molécula padre y sales** | El mismo fármaco puede venderse como sal (mesilato de imatinib). ChEMBL los registra por separado y los une con la molécula padre. Rastro los trata como un solo fármaco. |
| **Fase máxima** | Hasta dónde llegó el fármaco. 4 = **aprobado** en algún país. |
| **Target** | La proteína del cuerpo sobre la que actúa el fármaco. Casi siempre corresponde a un **gen**, que le da su nombre corto (EGFR, HER2/ERBB2, BRAF). |
| **Mecanismo de acción** | Qué le hace el fármaco al target: lo inhibe, lo bloquea, lo activa. |
| **Indicación** | Para qué enfermedades se usa o se estudia el fármaco. |

**Ejemplo real.** Imatinib (CHEMBL941) inhibe BCR-ABL, la proteína anómala de la leucemia mieloide crónica, y también KIT y PDGFRB. Por eso se usa en leucemia y en tumores del estroma gastrointestinal.

**Por qué importan los targets en oncología.** Muchos tratamientos modernos son **terapias dirigidas**: atacan una proteína que el tumor necesita. Un tumor de mama «HER2 positivo» se trata con fármacos anti-HER2, como trastuzumab. Por eso «¿qué fármacos con target HER2 se prueban en cáncer de mama?» es una pregunta natural para alguien del área.

**Qué toma Rastro.** Las familias de fármacos con alguna indicación oncológica (3.739), sus targets y sus genes.

**Cuidado con:**
- Los sinónimos a veces tienen errores: ChEMBL lista «bicalutamide» como sinónimo de talazoparib. Rastro le da prioridad al nombre preferido.
- Una **prodroga** se convierte en el fármaco activo dentro del cuerpo (el acetato de abiraterona se convierte en abiraterona). Rastro le asigna los targets de la molécula activa.

**Preguntas típicas:** ¿qué fármacos aprobados actúan sobre BRAF? ¿Qué fármacos comparten target con imatinib?

---

## 3. openFDA: los eventos adversos

**Qué es.** La API pública de datos de la **FDA**, la agencia de medicamentos de Estados Unidos. Rastro usa **FAERS**, el sistema donde médicos, pacientes y farmacéuticas reportan problemas con medicamentos. Licencia CC0.

**Conceptos que trae:**

| Concepto | Qué significa |
|---|---|
| **Reporte** | Alguien avisó que una persona que tomaba el fármaco tuvo un problema. Es **espontáneo**: nadie lo pidió ni lo verificó. |
| **Reacción** | El problema reportado, con términos médicos estándar (náuseas, neutropenia, muerte). |
| **Serio** | El evento causó muerte, internación, discapacidad o riesgo de vida. |

**Ejemplo real.** La reacción más reportada para imatinib es «DEATH» (13.512 reportes), seguida de náuseas. **No significa que imatinib mate**: los pacientes tienen cáncer, y una muerte por la enfermedad también se reporta. Es el mejor ejemplo para explicar por qué estos datos se leen con cuidado.

**Qué toma Rastro.** Conteos de reportes por año, por reacción, serios y muertes, para los fármacos del recorte: 774 de los 778 fármacos aprobados tienen reportes.

**Cuidado con:**
- **No son frecuencias.** No se sabe cuántas personas tomaron el fármaco, así que no hay porcentaje de riesgo.
- Puede haber reportes duplicados, y el fármaco puede no ser el que causó el problema.
- Casi solo los fármacos aprobados tienen reportes: uno en desarrollo no se vende, así que no hay quién reporte.
- Sirven para **comparar y detectar señales**, no como verdad clínica.

**Preguntas típicas:** ¿cuál es la reacción más reportada para imatinib? ¿Cuántos reportes serios tiene osimertinib?

---

## 4. MeSH: las enfermedades y sus subtipos

**Qué es.** El vocabulario médico de la **Biblioteca Nacional de Medicina de Estados Unidos** (NLM), el que se usa para clasificar los artículos científicos de PubMed. Uso bajo los términos de NLM.

**Conceptos que trae:**

| Concepto | Qué significa |
|---|---|
| **Descriptor** | Un término médico con identificador, por ejemplo «Breast Neoplasms» (neoplasias de mama). |
| **Jerarquía** | Cada término tiene términos más generales y más específicos. «Carcinoma de pulmón de células no pequeñas» está dentro de «Neoplasias pulmonares». |

**Ejemplo.** Si alguien pregunta por «cáncer de pulmón», también quiere los ensayos que dicen «carcinoma de pulmón de células no pequeñas». MeSH sabe que uno está dentro del otro, y Rastro lo usa con `oncologia:within`.

**Qué toma Rastro.** MeSH 2026 completo en GraphDB, y su jerarquía copiada en Postgres para que Ontop la use.

**Cuidado con:**
- Los términos están en inglés. El LLM traduce «cáncer de mama» a «Breast Neoplasms».
- «Neoplasia» incluye tumores benignos. Por eso la web de ClinicalTrials.gov, que busca con sus propios sinónimos, da conteos distintos a los de Rastro (ver `docs/verificacion-humana.md`).

**Preguntas típicas:** cualquier pregunta que diga «ensayos de cáncer de X»: MeSH decide qué subtipos entran.

---

## Glosario rápido

| Término | En una línea |
|---|---|
| Oncología | La rama de la medicina que trata el cáncer |
| Neoplasia | Crecimiento anormal de tejido; puede ser benigno o maligno (cáncer) |
| Biológico | Fármaco hecho a partir de seres vivos, por ejemplo un anticuerpo |
| Anticuerpo monoclonal | Biológico que se une a una proteína específica. Sus nombres terminan en «-mab» (trastuzumab, pembrolizumab). |
| Inhibidor de quinasa | Molécula pequeña que bloquea una enzima del tumor. Sus nombres terminan en «-nib» (imatinib, osimertinib). |
| Inmunoterapia | Tratamiento que ayuda al sistema inmune a atacar el tumor; los anti-PD-1 (pembrolizumab, nivolumab) son los más conocidos |
| Terapia dirigida | Fármaco que ataca un target que el tumor necesita |
| HER2, EGFR, BRAF | Genes cuyas proteínas impulsan ciertos tumores; son targets frecuentes |
| Aprobado | Autorizado para venderse en algún país (fase máxima 4 en ChEMBL) |
| Sponsor | Quien organiza y paga un ensayo |
| Detenido | Ensayo terminado antes de tiempo o retirado antes de empezar |
