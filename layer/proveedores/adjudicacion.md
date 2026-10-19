# Adjudicación: dónde difieren sin Rastro y con Rastro

Las referencias salen de Rastro, así que la ventaja de Rastro puede ser circular. Acá se revisan con los datos las preguntas donde las dos formas de responder difieren o donde alguna falla. La revisión la hizo un asistente de IA (Claude Code), mirando los datos de cada fuente; falta que la confirme una persona.

## p01 · Monto del grupo Leidos (las dos «correctas»)

- **Referencia (Rastro):** US$54.700 millones, el grupo consolidado LEIDOS HOLDINGS.
- **Con Rastro:** US$55.600 millones en 3 de 4 formas. El LLM filtró los grupos cuyo nombre contiene «LEIDOS» y sumó también NORTH WIND-LEIDOS (un *joint venture*) y LEIDOS MANAGEMENT SYSTEMS DESIGNERS.
- **Sin Rastro:** US$56.400 millones en 3 de 4 formas (proveedores o matrices con «leidos» en el nombre). En una forma sumó US$97.800 millones: siguió las matrices históricas de USAspending y metió a la SAIC de hoy, la trampa del ejemplo estrella.
- **Con los datos:** las dos quedan cerca de la referencia, pero la referencia también se queda corta. Dynetics, QTC Management, Gibbs & Cox y 1901 Group son hoy de Leidos y USAspending las registra como su propia matriz (Leidos solo aparece en su historia), y GLEIF tiene a Leidos Security Detection & Automation bajo L3Harris, su dueña anterior. Con ellas, el grupo pasaría los US$62.000 millones. Ninguna forma lo resuelve: hace falta una corrección revisada por una persona, que en Rastro se hace en un lugar.

## p04 · Proveedores con matriz final fuera de EE. UU. (sin Rastro falla)

- **Referencia y con Rastro:** 147. **Sin Rastro:** 587.
- El SQL toma, para cada nombre, el primer candidato que devolvió la búsqueda en GLEIF, sin comprobar que sea la misma empresa. En una muestra al azar de 12 de los 440 que agrega, 9 son enlaces falsos (AMERICAN BUREAU OF SHIPPING → un fondo de pensiones británico; ERNST & YOUNG LLP → una empresa de biocombustibles; SRI INTERNATIONAL → una fundación india).
- Pero 3 de los 12 sí tienen matriz extranjera (LEONARDO S.P.A., BOMBARDIER INC, DELOITTE CONSULTING LIMITED): Rastro no las enlazó. La referencia se queda corta; el número real está entre los dos, más cerca de Rastro. Se anota para mejorar el enlace con GLEIF (formas como «S.P.A.» y proveedores sin búsqueda en GLEIF).

## p05 · Proveedores con nombre igual a una entrada de la Lista Consolidada (fallan las dos)

- **Referencia:** 8. **Con Rastro:** 4, igual en las 4 formas. **Sin Rastro:** 7, 11, 6 y 7: cada consulta normaliza los nombres a su manera.
- **Con Rastro** filtró las entradas de tipo «Entity» y dejó afuera las que no traen tipo, como las de la Entity List de Comercio, que también son empresas u organizaciones. El diccionario de negocio no lo decía: el comentario de `:entryType` listaba los cuatro tipos sin aclarar que algunas listas lo dejan vacío. Se corrigió el comentario, sin volver a correr la prueba.
- **Con los datos:** las 8 de la referencia cumplen la definición de la pregunta (nombre o alias igual, sin mayúsculas, puntuación ni formas societarias). En todas, la entrada es de otro país: son homónimos.

## p06 · Proveedores de Defensa en construcción (las dos correctas)

- 1.060 sin Rastro y en la referencia; 1.059 con Rastro. La diferencia es un proveedor sin perfil en USAspending (la API devolvió error para tres perfiles), que la consulta de Rastro deja afuera al pedir su UEI.

## p07 · Grupos que cotizan en bolsa con más de US$1.000 millones (sin Rastro falla)

- **Referencia y con Rastro:** 41 grupos. **Sin Rastro:** 36.
- El SQL deja afuera a THE BOEING COMPANY, NORTHROP GRUMMAN, HONEYWELL, IBM y FLUOR, que cotizan en Nueva York, y nombra filiales en lugar de grupos (GENERAL DYNAMICS LAND SYSTEMS, NORTHROP GRUMMAN SYSTEMS, MODERNATX, CSL BEHRING) y a ROCKWELL COLLINS, que hoy es parte de otro grupo. La referencia aguanta.

## p09 · Monto de Defensa con proveedores para revisar (sin Rastro falla)

- **Referencia:** US$106.500 millones; **con Rastro:** US$105.500 millones (correcta); **sin Rastro:** US$280.000 millones, inflado por los mismos enlaces falsos con GLEIF de p04.

## Conclusión

Sin Rastro, las preguntas que necesitan unir USAspending con GLEIF (p04, p07, p09) fallan porque cada consulta inventa el enlace, sin verificarlo. Con Rastro, el enlace está hecho una vez y con reglas; su error es otro: se queda corto donde el enlace no encontró a la empresa. Los dos errores se ven en la evidencia, y el de Rastro se corrige en un lugar.
