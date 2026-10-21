# Guion de la demo de Rastro: ensayos clínicos de oncología (5 minutos)

> **Los datos cambian. Las preguntas, no.**

Para equipos de laboratorios, CROs y consultoras de salud, sin conocimientos técnicos. Tres momentos: **integración, consistencia y textos**, y un cierre con las pruebas. Se usa el mazo de oncología (`docs/slides/oncologia.html`) y la app en el caso **Oncología**: la app abre en petróleo y gas, así que hay que prender «Ver detalles técnicos» en la barra lateral y elegir **Oncología** en **Caso de uso**. Oncología no tiene pestaña **Demo**: en **Preguntar** se usa «Una pregunta de ejemplo» y «Una pregunta sobre textos».

## Antes de empezar

1. Levantar todo, desde la carpeta del repo: `docker compose up -d` (lo hace alguien técnico, una vez).
2. Abrir http://localhost:8501, prender «Ver detalles técnicos» y elegir **Oncología** en **Caso de uso**. Abrir una vez la pregunta de HER2 y la pregunta sobre textos: corren en vivo.

## 0:00 – 1:00 · Qué es Rastro y el problema (diapositivas 1 a 4)

> «Los datos de ensayos clínicos existen, pero no se hablan entre sí. El mismo fármaco aparece como "Pembrolizumab 200 mg" en el registro de ensayos, como CHEMBL3137343 en la base de fármacos y como "KEYTRUDA" en los reportes de efectos adversos. Sin unirlos, cada pregunta empieza de cero.»
>
> «Rastro incorpora un diccionario de negocio: ensayo, fármaco, enfermedad, target. Cada fuente se traduce a esos términos una sola vez. La demo usa cuatro fuentes públicas: ClinicalTrials.gov, ChEMBL, openFDA y MeSH.»

## 1:00 – 2:15 · 1 · Integración (app, «Una pregunta de ejemplo»; diapositiva 5)

Elegir la pregunta **¿Qué fármacos anti-HER2 se prueban en fase 3 de cáncer de mama?**

> «La respuesta cruza tres fuentes: el ensayo, el target del fármaco y la jerarquía de enfermedades, que incluye los subtipos de cáncer de mama. Rastro responde con 13 fármacos: trastuzumab, pertuzumab, lapatinib, neratinib, tucatinib y otros ocho.»

Abrir **¿De dónde sale la respuesta?**:

> «Y dice por qué: un ensayo escribió "Herceptin" y Rastro lo reconoció como trastuzumab, por su marca. Cada ensayo se puede abrir y comprobar.»

## 2:15 – 3:15 · 2 · Consistencia (diapositiva 6)

> «Hicimos cada pregunta de cuatro maneras distintas. Sin Rastro, el asistente de IA busca los fármacos en el texto de cada ensayo, y 9 de 10 preguntas cambiaron de respuesta: por ejemplo, 488, 488, 409 y 488 ensayos. Con Rastro, 10 de 10 dieron siempre lo mismo, porque cada fármaco se reconoció una sola vez, con su evidencia.»

## 3:15 – 4:15 · 3 · Textos (app, «Una pregunta sobre textos»; diapositiva 7)

> «¿Por qué se detuvieron los estudios grandes de cáncer de pulmón con inhibidores de quinasa? El grafo elige los 26 ensayos con una consulta exacta; la IA lee solo esos motivos y los resume, citando cada ensayo. Y cuando el motivo se puede clasificar, pasa a ser un dato: no consiguieron pacientes, 10; decisión de la empresa, 9.»

## 4:15 – 5:00 · Pruebas y cierre (diapositivas 8 y 9)

> «Tres pruebas medidas. Consistencia: 10 de 10. Cambios: si una fuente renombra una columna, se arregla una línea del mapeo en lugar de cinco consultas; si un valor cambia de formato, el SQL da cero sin avisar y Rastro avisa. Auditoría: cada enlace dice qué texto del ensayo se reconoció como cada fármaco.»
>
> «El valor está en integrar los datos una sola vez y mantenerlos en un único lugar. El siguiente paso es un piloto con datos propios, integrados con estas fuentes públicas.»

## Si preguntan

- **«¿Rastro acierta más?»** En la evaluación (pestaña **Por qué confiar**), Rastro acierta 20 de 20 y el SQL directo 18 de 20. Con las mismas tablas de enlaces de Rastro, un SQL bien hecho también acierta 20: la ventaja está en integrar una vez, no en la tecnología. Las referencias las armó un asistente de IA; falta que una persona las confirme (`docs/verificacion-humana.md`).
- **«¿Por qué 438 y no 488 ensayos de EGFR?»** El SQL directo encontró «humab» dentro de nombres como «rhuMAb HER2» y contó ensayos de trastuzumab o bevacizumab, que no actúan sobre EGFR. Está en la adjudicación (`layer/eval/adjudication.md`) y en la verificación humana, parte 1.
- **«¿Y si el negocio cambia una definición?»** Si la terapia hormonal pasa a contar como terapia dirigida, se cambia una línea del diccionario: 156 fármacos pasan a 188 en todas las preguntas (pestaña **Por qué confiar** → «3 · Cuando una base cambia»).
- **«¿Se puede sumar información de afuera?»** Una consulta une Rastro con Wikidata en vivo, sin cargar nada: afatinib y vandetanib están aprobados para otros cánceres y se prueban en mama (diapositiva «Datos de afuera», en el anexo). Necesita internet.
