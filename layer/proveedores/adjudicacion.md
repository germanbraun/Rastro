# Adjudicación: dónde difieren sin Rastro y con Rastro

Las referencias salen de Rastro, así que la ventaja de Rastro puede ser circular. Acá se revisan con los datos las preguntas donde las dos formas de responder difieren o donde alguna falla. La revisión la hizo un asistente de IA (Claude Code), mirando los datos de cada fuente; falta que la confirme una persona.

## p01 · Monto del grupo Leidos (sin Rastro falla)

- **Referencia (Rastro):** US$63.400 millones, el grupo consolidado LEIDOS HOLDINGS: 30 empresas de 13 matrices de USAspending.
- **Con Rastro:** US$64.100 millones en 3 de 4 formas. El LLM filtró los grupos cuyo nombre contiene «LEIDOS» y sumó también NORTH WIND-LEIDOS, un *joint venture*. Queda a menos del 5 %.
- **Sin Rastro:** US$56.400 millones en 3 de 4 formas (proveedores o matrices con «leidos» en el nombre): un 11 % menos, porque no sabe que Dynetics, QTC o Gibbs & Cox son de Leidos. En una forma sumó US$97.800 millones: siguió las matrices históricas de USAspending y metió a la SAIC de hoy, la trampa del ejemplo estrella.
- **Con los datos:** en la primera versión de esta revisión, la referencia se quedaba corta (US$54.700 millones): Dynetics, QTC Management, Gibbs & Cox, 1901 Group y Leidos Security Detection & Automation son hoy de Leidos, pero USAspending las registra como su propia matriz (Leidos solo aparece en su historia) y GLEIF no les registra matriz o las tiene bajo su dueña anterior. Ahora entran con una corrección revisada, con su motivo (`linking/proveedores/correcciones.csv`). Kudu Dynamics y Aranea Solutions tienen a Leidos solo en su historia: quedan pendientes.

## p04 · Proveedores con matriz final fuera de EE. UU. (sin Rastro falla)

- **Referencia y con Rastro:** 173. **Sin Rastro:** 807.
- El SQL toma, para cada nombre, el primer candidato que devolvió la búsqueda en GLEIF, sin comprobar que sea la misma empresa. En una muestra al azar de 12 de los que agregaba, 9 eran enlaces falsos (AMERICAN BUREAU OF SHIPPING → un fondo de pensiones británico; ERNST & YOUNG LLP → una empresa de biocombustibles; SRI INTERNATIONAL → una fundación india).
- Los 3 que sí tenían matriz extranjera y Rastro no enlazaba se resolvieron: LEONARDO S.P.A. y BOMBARDIER INC con un LEI revisado (GLEIF los llama «LEONARDO - SOCIETA' PER AZIONI» y «BOMBARDIER INC.», y las búsquedas no los encontraban), y en general con dos búsquedas más en GLEIF (por nombre normalizado y, para los grupos grandes, por nombre legal), que sumaron 90 matrices y 150 proveedores con LEI. DELOITTE CONSULTING LIMITED es una empresa de Tanzania que no está en GLEIF: el SQL la contaba por un enlace falso con DELOITTE MCS LIMITED, de Reino Unido.
- De paso apareció un error de la fuente: USAspending registra como matriz de AUSTAL USA a COMPUTERSHARE LIMITED, un registro de acciones; su historia y GLEIF dicen AUSTAL LIMITED. Se corrigió con una corrección revisada.

## p05 · Proveedores con nombre igual a una entrada de la Lista Consolidada (fallan las dos)

- **Referencia:** 8. **Con Rastro:** 4, igual en las 4 formas. **Sin Rastro:** 7, 11, 6 y 7: cada consulta normaliza los nombres a su manera.
- **Con Rastro** filtró las entradas de tipo «Entity» y dejó afuera las que no traen tipo, como las de la Entity List de Comercio, que también son empresas u organizaciones. El diccionario de negocio no lo decía: el comentario de `proveedores:entryType` listaba los cuatro tipos sin aclarar que algunas listas lo dejan vacío. Se corrigió el comentario, sin volver a correr la prueba.
- **Con los datos:** las 8 de la referencia cumplen la definición de la pregunta (nombre o alias igual, sin mayúsculas, puntuación ni formas societarias). En todas, la entrada es de otro país: son homónimos.

## p06 · Proveedores de Defensa en construcción (las dos correctas)

- 1.060 sin Rastro y en la referencia; 1.059 con Rastro. La diferencia es un proveedor sin perfil en USAspending (la API devolvió error para tres perfiles), que la consulta de Rastro deja afuera al pedir su UEI.

## p07 · Grupos que cotizan en bolsa con más de US$1.000 millones (sin Rastro falla)

- **Referencia y con Rastro:** 53 grupos. **Sin Rastro:** 38.
- El SQL deja afuera a THE BOEING COMPANY, NORTHROP GRUMMAN, HONEYWELL, IBM y FLUOR, que cotizan en Nueva York, y nombra filiales en lugar de grupos (GENERAL DYNAMICS LAND SYSTEMS, NORTHROP GRUMMAN SYSTEMS, MODERNATX, CSL BEHRING) y a ROCKWELL COLLINS, que hoy es parte de otro grupo. La referencia aguanta.

## p09 · Monto de Defensa con proveedores para revisar (sin Rastro falla)

- **Referencia:** US$116.900 millones; **con Rastro:** US$116.000 millones (correcta); **sin Rastro:** US$390.800 millones, inflado por los mismos enlaces falsos con GLEIF de p04.

## Conclusión

Sin Rastro, las preguntas que necesitan unir USAspending con GLEIF (p04, p07, p09) fallan porque cada consulta inventa el enlace, sin verificarlo. Con Rastro, el enlace está hecho una vez y con reglas; su error es otro: se queda corto donde el enlace no encuentra a la empresa. Los dos errores se ven en la evidencia, y el de Rastro se corrige en un lugar: eso fue lo que se hizo con las filiales de Leidos y con Leonardo y Bombardier.
