# Resultados: ¿cuántas preguntas responde bien un LLM?

Modelo: `claude-opus-5-5 (subagentes de Claude Code)` · Fecha: —

LLM solo: **5 de 20** · LLM + SQL crudo: **18 de 20** · LLM + Rastro: **20 de 20**

- **LLM solo:** responde con lo que sabe, sin acceso a datos.
- **LLM + SQL crudo:** escribe SQL sobre las tablas de las fuentes tal como se cargaron.
- **LLM + Rastro:** escribe SPARQL sobre la ontología de Rastro.

Correcto: números a menos del 5% de la referencia; listas con al menos 80% de coincidencia (F1). Las queries generadas están en `results.json`.

| # | Pregunta | Referencia | LLM solo | LLM + SQL crudo | LLM + Rastro |
|---|---|---|---|---|---|
| q01 | ¿Qué fármacos con target HER2 (gen ERBB2) se prueban en ensayos de fase 3 (incluye fase 2/3) de cáncer de mama? | AFATINIB, DISITAMAB VEDOTIN, GANCOTAMAB, KN-026 y 9 más | ✅ Trastuzumab, Pertuzumab, Lapatinib, Neratinib y 9 más | ✅ AFATINIB, DISITAMAB VEDOTIN, GANCOTAMAB, KN-026 y 9 más | ✅ AFATINIB, DISITAMAB VEDOTIN, GANCOTAMAB, KN-026 y 9 más |
| q02 | ¿Cuántos ensayos de fase 3 (incluye fase 2/3) prueban fármacos que actúan sobre EGFR? | 438 | ❌ 650 | ❌ 488 | ✅ 438 |
| q03 | ¿Cuáles son los 3 sponsors de la industria con más ensayos detenidos (terminados o retirados) en cáncer de pulmón, contando como sponsor solo al principal? | Pfizer, Novartis Pharmaceuticals, AstraZeneca | ❌ AstraZeneca, Hoffmann-La Roche, Pfizer | ✅ Pfizer, Novartis Pharmaceuticals, AstraZeneca | ✅ Pfizer, Novartis Pharmaceuticals, AstraZeneca |
| q04 | ¿Cuál es la reacción adversa más reportada en FAERS (openFDA) para imatinib? | DEATH | ✅ DEATH | ✅ DEATH | ✅ DEATH |
| q05 | ¿Qué fármacos aprobados actúan sobre BRAF? | DABRAFENIB, ENCORAFENIB, REGORAFENIB, SORAFENIB y 2 más | ✅ vemurafenib, dabrafenib, encorafenib, tovorafenib y 2 más | ✅ DABRAFENIB, ENCORAFENIB, REGORAFENIB, SORAFENIB y 2 más | ✅ DABRAFENIB, ENCORAFENIB, REGORAFENIB, SORAFENIB y 2 más |
| q06 | ¿Cuántos ensayos de cáncer de mama hay en total? | 14,405 | ✅ 14,000 | ✅ 14,342 | ✅ 14,405 |
| q07 | ¿Cuántos reportes de eventos adversos en FAERS (openFDA) tenía lenalidomida recibidos antes de 2015? | 50,504 | ❌ 55,000 | ✅ 50,504 | ✅ 50,504 |
| q08 | ¿Qué porcentaje de los ensayos de fase 2 (incluye fase 1/2 y fase 2/3) cerrados (completados, terminados o retirados) de Pfizer como sponsor principal se detuvo antes de tiempo (terminados o retirados)? | 28 | ❌ 25 | ✅ 28 | ✅ 28 |
| q09 | ¿Cuántos ensayos activos (reclutando, activos sin reclutar, todavía sin reclutar o por invitación) prueban pembrolizumab? | 961 | ❌ 1,200 | ✅ 973 | ✅ 961 |
| q10 | ¿Cuántos ensayos de leucemia prueban fármacos que actúan sobre BTK? | 269 | ❌ 550 | ✅ 270 | ✅ 269 |
| q11 | ¿Qué sponsor de la industria tiene más ensayos de fase 3 (incluye fase 2/3) en cáncer colorrectal, contando como sponsor solo al principal? | Hoffmann-La Roche | ✅ Hoffmann-La Roche | ✅ Hoffmann-La Roche | ✅ Hoffmann-La Roche |
| q12 | ¿Cuántos ensayos de melanoma prueban nivolumab? | 293 | ❌ 450 | ✅ 301 | ✅ 293 |
| q13 | ¿Cuántos ensayos de cáncer de próstata prueban algún fármaco aprobado que actúa sobre el receptor de andrógenos (gen AR)? | 658 | ❌ 1,200 | ✅ 675 | ✅ 658 |
| q14 | ¿Cuántos ensayos detenidos (terminados o retirados) hay en cáncer de páncreas? | 569 | ❌ 850 | ✅ 569 | ✅ 569 |
| q15 | ¿Cuántos reportes serios de eventos adversos acumula osimertinib en FAERS (openFDA)? | 30,448 | ❌ 14,000 | ✅ 30,448 | ✅ 30,448 |
| q16 | ¿Cuántos fármacos distintos se prueban en ensayos de mieloma múltiple? | 604 | ❌ 150 | ❌ 545 | ✅ 604 |
| q17 | ¿Cuántos ensayos activos (reclutando, activos sin reclutar, todavía sin reclutar o por invitación) prueban fármacos dirigidos a TIGIT? | 34 | ❌ 60 | ✅ 34 | ✅ 34 |
| q18 | ¿Qué fármacos anti-PD-1 o anti-PD-L1 (genes PDCD1 o CD274) se prueban en ensayos de fase 3 (incluye fase 2/3) de cáncer de pulmón? | ADEBRELIMAB, ATEZOLIZUMAB, AVELUMAB, BINTRAFUSP ALFA y 18 más | ❌ Pembrolizumab, Nivolumab, Atezolizumab, Durvalumab y 18 más | ✅ ADEBRELIMAB, ATEZOLIZUMAB, AVELUMAB, BINTRAFUSP ALFA y 18 más | ✅ ADEBRELIMAB, ATEZOLIZUMAB, AVELUMAB, BINTRAFUSP ALFA y 18 más |
| q19 | ¿Cuántos ensayos de linfoma que empezaron en 2020 o después prueban rituximab? | 309 | ❌ 600 | ✅ 304 | ✅ 309 |
| q20 | ¿Qué fármacos comparten al menos un target con imatinib? | AMUVATINIB, ASCIMINIB, AT-9283, AVAPRITINIB y 44 más | ❌ Dasatinib, Nilotinib, Bosutinib, Ponatinib y 14 más | ✅ AMUVATINIB, ASCIMINIB, AT-9283, AVAPRITINIB y 52 más | ✅ AMUVATINIB, ASCIMINIB, AT-9283, AVAPRITINIB y 44 más |
