# Resultados: petróleo y gas en Argentina, sin Rastro y con Rastro

Fecha: 2026-10-20. Respuestas escritas por subagentes de Claude Code (Claude Opus 5.5) que solo vieron el prompt. Las referencias las escribió un asistente de IA; falta que las confirme una persona.

| | Sin Rastro (SQL) | SQL + enlaces de Rastro | Con Rastro |
|---|---|---|---|
| Correctas (de 9) | 6 | 9 | 9 |
| Misma respuesta en las 4 formas (de 5 preguntas) | 3 | 5 | 5 |
| Correctas en la prueba de consistencia (de 20) | 11 | 20 | 20 |

| # | Pregunta | Referencia | Sin Rastro (SQL) | SQL + enlaces de Rastro | Con Rastro |
|---|---|---|---|---|---|
| e01 | ¿Cuántos metros cúbicos de petróleo producidos en 2025 le corresponden a YPF según su participación, es decir, sumando en cada concesión la producción de petróleo multiplicada por el porcentaje de YPF en esa concesión? | 12.570.093 | ✅ 12.581.213 | ✅ 12.570.093 | ✅ 12.570.093 |
| e02 | ¿Cuántos pozos con producción declarada en 2025 opera hoy YPF, si la operadora de un pozo es la empresa que declara su producción en el último mes en que el pozo aparece en 2025? | 15.809 | ✅ 15.809 | ✅ 15.809 | ✅ 15.809 |
| e03 | ¿Cuáles son las 5 concesiones con más posibles venteos detectados por satélite desde el 1 de enero de 2024, contando los puntos que caen dentro del contorno de cada concesión? | LOMA CAMPANA, LOMA LA LATA - SIERRA BARROSA, BAJO DEL CHOIQUE - LA INVERNADA y 2 más | ✅ LOMA CAMPANA, LOMA LA LATA - SIERRA BARROSA, BAJO DEL CHOIQUE - LA INVERNADA y 2 más | ✅ LOMA CAMPANA, LOMA LA LATA - SIERRA BARROSA, BAJO DEL CHOIQUE - LA INVERNADA y 2 más | ✅ LOMA CAMPANA, LOMA LA LATA - SIERRA BARROSA, BAJO DEL CHOIQUE - LA INVERNADA y 2 más |
| e04 | ¿Cuáles son las 5 empresas que declararon más petróleo no convencional (shale o tight) en 2025, contando como una sola empresa a Pluspetrol S.A. y Pluspetrol Cuenca Neuquina S.R.L.? | YPF S.A., VISTA ENERGY ARGENTINA SAU, PLUSPETROL y 2 más | ✅ YPF S.A., VISTA ENERGY ARGENTINA SAU, PLUSPETROL S.A. y 2 más | ✅ YPF S.A., VISTA ENERGY ARGENTINA SAU, PLUSPETROL y 2 más | ✅ YPF S.A., VISTA ENERGY ARGENTINA SAU, PLUSPETROL y 2 más |
| e05 | ¿Cuántas concesiones tienen al menos un posible venteo detectado por satélite desde el 1 de enero de 2024 dentro de su contorno y tienen el gasoducto de transporte de ENARGAS más cercano a 10 km o más de su contorno? | 33 | ❌ sin respuesta | ✅ 33 | ✅ 33 |
| e06 | ¿Cuántos posibles venteos detectados por satélite desde el 1 de enero de 2024, dentro del contorno de alguna concesión, caen dentro de un área protegida del Instituto Geográfico Nacional? | 60 | ❌ 43 | ✅ 60 | ✅ 60 |
| e07 | ¿Qué empresas que declaran producción en 2025 tienen un LEI activo en GLEIF cuyo nombre legal es el de la empresa? | CAPEX S.A., COMPAÑIA GENERAL DE COMBUSTIBLES, PAMPA ENERGIA S.A. y 9 más | ✅ CAPEX S.A., COMPAÑÍA GENERAL DE COMBUSTIBLES S.A., PAMPA ENERGIA S.A. y 6 más | ✅ CAPEX S.A., COMPAÑIA GENERAL DE COMBUSTIBLES, PAMPA ENERGIA S.A. y 9 más | ✅ CAPEX S.A., COMPAÑIA GENERAL DE COMBUSTIBLES, PAMPA ENERGIA S.A. y 9 más |
| e08 | ¿Cuántas concesiones hay que revisar por venteos, si se revisa una concesión que tiene posibles venteos detectados por satélite desde el 1 de enero de 2024 dentro de su contorno y además cumple al menos una de dos reglas, (a) el gasoducto de transporte de ENARGAS más cercano está a 10 km o más de su contorno, o (b) tiene al menos 20 de esos posibles venteos y no presentó ninguna planilla de venteo de gas (Res. 143/98) desde el 1 de enero de 2022 según el listado de estudios ambientales? | 45 | ❌ sin respuesta | ✅ 45 | ✅ 45 |
| e09 | ¿Cuántos cambios de operadora hubo en las concesiones entre 2023 y 2025, si cada mes la operadora de una concesión es la empresa que declara la mayor parte de su producción (petróleo en m³ más gas en miles de m³), solo cuentan las rachas de al menos 3 meses seguidos con la misma operadora, y hay un cambio cada vez que la racha siguiente es de otra empresa? Contar como una sola empresa a Pluspetrol S.A. y Pluspetrol Cuenca Neuquina S.R.L., a CGC Energía SAU y Compañía General de Combustibles S.A., y a GeoPark Argentina Ltd. (Sucursal Argentina) y GeoPark Argentina S.A. | 64 | ✅ 64 | ✅ 64 | ✅ 64 |

## Consistencia

Respuestas por forma (la de la evaluación y sus 3 otras formas; en las listas, cantidad de nombres):

| # | Sin Rastro (SQL) | SQL + enlaces de Rastro | Con Rastro |
|---|---|---|---|
| e01 | ✅ 4/4 correctas · 12.581.213 / 12.581.213 / 12.581.213 / 12.581.213 | ✅ 4/4 correctas · 12.570.093 / 12.570.093 / 12.570.093 / 12.570.093 | ✅ 4/4 correctas · 12.570.093 / 12.570.093 / 12.570.093 / 12.570.093 |
| e02 | ❌ 3/4 correctas · 15.809 / 15.809 / 6.263 / 15.809 | ✅ 4/4 correctas · 15.809 / 15.809 / 15.809 / 15.809 | ✅ 4/4 correctas · 15.809 / 15.809 / 15.809 / 15.809 |
| e03 | ✅ 4/4 correctas · 5 / 5 / 5 / 5 | ✅ 4/4 correctas · 5 / 5 / 5 / 5 | ✅ 4/4 correctas · 5 / 5 / 5 / 5 |
| e05 | ✅ 0/4 correctas · — / — / — / — | ✅ 4/4 correctas · 33 / 33 / 33 / 33 | ✅ 4/4 correctas · 33 / 33 / 33 / 33 |
| e06 | ❌ 0/4 correctas · 43 / 41 / 42 / — | ✅ 4/4 correctas · 60 / 60 / 60 / 60 | ✅ 4/4 correctas · 60 / 60 / 60 / 60 |
