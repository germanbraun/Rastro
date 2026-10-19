# Preguntas de competencia: proveedores del Estado

Las preguntas que Rastro tiene que poder responder en el segundo dominio. El diccionario de negocio ([`proveedores.ttl`](proveedores.ttl)) tiene solo lo necesario para estas nueve, y cada una tiene su SPARQL en [`queries/`](queries/). Todas corren contra el segundo Ontop (http://localhost:8081/sparql).

Cada pregunta muestra al menos una ventaja de tener la capa, dicha sin jerga.

| # | Pregunta | Fuentes | Qué muestra |
|---|---|---|---|
| 1 | ¿Cuánto suman los contratos del grupo Leidos, contando todas sus empresas? | USAspending | El grupo suma solo todas sus filiales: nadie arma la lista de empresas en cada consulta. |
| 2 | ¿Cuáles son los 5 grupos con más contratos en servicios informáticos, incluidos sus subsectores? | USAspending, NAICS | «Servicios informáticos» incluye solo sus subsectores, y cada contrato se suma a su grupo. |
| 3 | ¿Qué agencias concentran más de un tercio de su gasto en un solo grupo? | USAspending | La concentración se mide por grupo, no por cada empresa suelta: si no, se esconde. |
| 4 | ¿Qué proveedores tienen su matriz final fuera de EE. UU.? | USAspending, GLEIF | «Matriz extranjera» está definida una vez y la usan varias preguntas; el LEI une USAspending con GLEIF. |
| 5 | ¿Algún proveedor, o su grupo, aparece en una lista de control del gobierno? | USAspending, Lista Consolidada | Cada coincidencia dice qué nombre coincidió y con qué regla, para que compliance la revise. |
| 6 | ¿Cuántos proveedores distintos tiene el Departamento de Defensa en construcción? | USAspending, NAICS | «Construcción» incluye solo todos sus subsectores (edificios, obras viales, instalaciones…). |
| 7 | ¿Qué grupos que cotizan en bolsa tienen contratos por más de US$1.000 millones, y dónde tienen su sede? | USAspending, GLEIF, Wikidata | Un identificador compartido (el LEI) trae datos de otra organización, Wikidata, sin integrarla a mano. |
| 8 | ¿A qué grupo pertenece «Science Applications International Corporation», y por qué? | USAspending | El nombre confuso (la vieja SAIC hoy es Leidos) se resuelve una vez, con la evidencia a la vista. |
| 9 | ¿Cuánto contrata cada agencia con proveedores para revisar? | USAspending, GLEIF, Lista Consolidada | «Proveedor para revisar» es una regla de negocio escrita una vez en el diccionario; Rastro la aplica sola. |

## Respuestas (19 oct 2026)

| # | Respuesta |
|---|---|
| 1 | El grupo Leidos: 30 empresas, 611 contratos, US$63.400 millones. Con las matrices de USAspending solas, Leidos queda partido en 13 grupos. |
| 2 | Booz Allen Hamilton, Leidos, General Dynamics, Accenture y SAIC. |
| 3 | 20 casos agencia–grupo; por ejemplo, la National Science Foundation concentra el 67 % en Leidos. |
| 4 | 173 proveedores, encabezados por empresas de BAE Systems (Reino Unido), Accenture (Irlanda), Austal (Australia) y Serco (Reino Unido). |
| 5 | 8 proveedores con un nombre igual a una entrada de una lista; en todos los que se pueden comparar, la entrada es de otro país: son homónimos. |
| 6 | 1.060 proveedores, 2.587 contratos. |
| 7 | 53 grupos que cotizan en bolsa con más de US$1.000 millones, encabezados por Boeing, Fluor, Honeywell, BAE Systems y Leidos, con su bolsa y su sede. |
| 8 | Las cinco «Science Applications International Corporation» son del grupo SAIC, no de Leidos, y la evidencia dice por qué. |
| 9 | Defensa contrata US$116.900 millones con 139 proveedores para revisar. |

## Notas

- **Monto:** es el monto total de cada contrato en toda su vida («Award Amount» de USAspending), no solo lo que se obligó en 2025. Los contratos son los que tuvieron actividad en el año fiscal 2025 y suman más de US$10 millones.
- **Grupo = matriz actual en USAspending, consolidada con GLEIF.** USAspending reparte un mismo grupo en varias matrices (Leidos figura en 13). Si la matriz tiene LEI, el grupo es su matriz final en GLEIF; si no, queda la matriz de USAspending. Las compras que ninguna fuente registra entran con una corrección revisada (`linking/proveedores/correcciones.csv`). USAspending también guarda las matrices que tuvo cada proveedor: Rastro no las usa para sumar (meterían a la SAIC de hoy en Leidos) y las muestra como evidencia (pregunta 8).
- **Los sectores son NAICS 2022**, más los códigos viejos que usan algunos contratos, colgados de su prefijo más largo. `:within` dice que un sector está dentro de sí mismo y de los más amplios; se precalcula en `proveedores.sector_ancestor` porque Ontop no recorre caminos de largo arbitrario.
- **Matriz final (GLEIF):** si GLEIF no registra una matriz, la entidad es su propia matriz final.
- **«Proveedor para revisar» no tiene mapeo.** El diccionario dice que lo son los proveedores con matriz extranjera y los que coinciden con una lista de control, y Ontop lo deduce (`rdfs:subClassOf`), como «terapia dirigida» en oncología.
- **Una coincidencia con una lista de control no es una confirmación.** Es un nombre igual después de normalizarlo; hay que revisarla.
- **Cada dato lleva su fuente** (`:fromSource`), y cada enlace entre fuentes, su evidencia con PROV-O (`:GroupLink`, `:LeiLink`, `:WatchlistLink`).
