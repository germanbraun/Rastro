# Resultados: proveedores del Estado, sin Rastro y con Rastro

Fecha: 2026-10-19. Respuestas escritas por subagentes de Claude Code (Claude Opus 5.5) que solo vieron el prompt. Las referencias las escribió un asistente de IA; falta que las confirme una persona.

| | Sin Rastro (SQL) | Con Rastro |
|---|---|---|
| Correctas (de 9) | 4 | 8 |
| Misma respuesta en las 4 formas (de 5 preguntas) | 3 | 4 |
| Correctas en la prueba de consistencia (de 20) | 12 | 16 |

| # | Pregunta | Referencia | Sin Rastro (SQL) | Con Rastro |
|---|---|---|---|---|
| p01 | ¿Cuánto suman, en dólares, los contratos del grupo empresario Leidos, es decir de Leidos Holdings y de todas sus empresas? | 63.362.671.931 | ❌ 56.388.914.832 | ✅ 64.085.535.830 |
| p02 | ¿Cuáles son los 5 grupos empresarios con más monto en contratos de servicios informáticos (sector NAICS 5415 y sus subsectores), sumando todas las empresas de cada grupo? | BOOZ ALLEN HAMILTON HOLDING CORPORATION, LEIDOS HOLDINGS, INC., GENERAL DYNAMICS CORP y 2 más | ✅ BOOZ ALLEN HAMILTON HOLDING CORPORATION, GENERAL DYNAMICS CORP, LEIDOS, INC. y 2 más | ✅ BOOZ ALLEN HAMILTON HOLDING CORPORATION, LEIDOS HOLDINGS, INC., GENERAL DYNAMICS CORP y 2 más |
| p03 | ¿Qué agencias tienen más de un tercio de su monto en contratos con un solo grupo empresario, sumando todas las empresas de ese grupo? | Agency for International Development, Commodity Futures Trading Commission, Court Services and Offender Supervision Agency y 14 más | ✅ Agency for International Development, Commodity Futures Trading Commission, Court Services and Offender Supervision Agency y 14 más | ✅ Agency for International Development, Commodity Futures Trading Commission, Court Services and Offender Supervision Agency y 14 más |
| p04 | ¿Cuántos proveedores (UEI distintos) tienen su matriz final, según GLEIF, fuera de EE. UU.? La matriz final es la de su grupo empresario o, si el grupo no tiene registro en GLEIF, la del propio proveedor. | 173 | ❌ 807 | ✅ 173 |
| p05 | ¿Cuántos proveedores (UEI distintos) tienen un nombre igual al nombre o a un alias de una empresa u organización de la Lista Consolidada de Control, sin contar mayúsculas, puntuación ni formas societarias como Inc., LLC o Corp.? | 8 | ❌ 7 | ❌ 4 |
| p06 | ¿Cuántos proveedores (UEI distintos) tiene el Departamento de Defensa en contratos de construcción (sector NAICS 23 y sus subsectores)? | 1.060 | ✅ 1.060 | ✅ 1.059 |
| p07 | ¿Qué grupos empresarios cotizan en bolsa, según Wikidata, y tienen contratos por más de US$1.000 millones en total, sumando todas sus empresas? | AECOM, Aerojet Rocketdyne Holdings, Inc., AEROVIRONMENT, INC. y 50 más | ❌ AEROJET ROCKETDYNE HOLDINGS, INC., AEROVIRONMENT, INC., BAE SYSTEMS PLC y 35 más | ✅ AECOM, Aerojet Rocketdyne Holdings, Inc., AEROVIRONMENT, INC. y 50 más |
| p08 | ¿A qué grupo empresario pertenece hoy el proveedor SCIENCE APPLICATIONS INTERNATIONAL CORPORATION con UEI MMLKPW9JLX64? Respondé con el nombre del grupo. | SCIENCE APPLICATIONS INTERNATIONAL CORPORATION | ✅ SCIENCE APPLICATIONS INTERNATIONAL CORPORATION | ✅ SCIENCE APPLICATIONS INTERNATIONAL CORPORATION |
| p09 | ¿Cuánto suman, en dólares, los contratos del Departamento de Defensa con proveedores para revisar? Un proveedor es para revisar si su matriz final según GLEIF está fuera de EE. UU. (la de su grupo o, si el grupo no tiene registro en GLEIF, la propia) o si su nombre, o el de su grupo, es igual al de una empresa u organización de la Lista Consolidada de Control, sin contar mayúsculas, puntuación ni formas societarias. | 116.901.124.122 | ❌ 390.761.358.534 | ✅ 115.955.142.324 |

## Consistencia

Respuestas por forma (la de la evaluación y sus 3 otras formas; en las listas, cantidad de nombres):

| # | Sin Rastro (SQL) | Con Rastro |
|---|---|---|
| p01 | ❌ 0/4 correctas · 56.388.914.832 / 97.788.197.519 / 56.388.914.832 / 56.388.914.832 | ❌ 4/4 correctas · 64.085.535.830 / 64.085.535.830 / 64.085.535.830 / 63.362.671.931 |
| p02 | ✅ 4/4 correctas · 5 / 5 / 5 / 5 | ✅ 4/4 correctas · 5 / 5 / 5 / 5 |
| p05 | ❌ 0/4 correctas · 7 / 11 / 6 / 7 | ✅ 0/4 correctas · 4 / 4 / 4 / 4 |
| p06 | ✅ 4/4 correctas · 1.060 / 1.060 / 1.060 / 1.060 | ✅ 4/4 correctas · 1.059 / 1.059 / 1.059 / 1.059 |
| p08 | ✅ 4/4 correctas · 1 / 1 / 1 / 1 | ✅ 4/4 correctas · 1 / 1 / 1 / 1 |
