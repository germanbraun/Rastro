Endpoint SPARQL de Rastro (Ontop) sobre cinco fuentes públicas: la producción declarada pozo por pozo (Capítulo IV) y los mapas de concesiones y venteos (WFS) de la Secretaría de Energía de Argentina, los gasoductos de transporte de ENARGAS, las localidades y áreas protegidas del IGN, y GLEIF.

- Prefijos: `PREFIX energia: <https://w3id.org/rastro/energia#>`, y `PREFIX prov: <http://www.w3.org/ns/prov#>` solo si la consulta usa `prov:` (la evidencia de los enlaces).
- La producción es la de 2025. `energia:oil` es petróleo en m³ y `energia:gas` es gas en miles de m³, por pozo y formación (`energia:WellProduction`).
- `energia:declaredBy` es la empresa que declara la producción; `energia:Stake` es la participación de una empresa en una concesión (`energia:percent`, de 0 a 100). Para «lo que le corresponde» a una empresa, multiplicar la producción de la concesión por su porcentaje.
- `energia:operator` de un `energia:Well` es quién lo opera hoy (la empresa que declara su último mes).
- `energia:formation` está en minúsculas: "vaca muerta". `energia:UnconventionalProduction` incluye shale y tight.
- `energia:DetectedVenting` son posibles venteos vistos por satélite desde 2024 (un indicio, no una confirmación); `energia:DeclaredVenting`, los puntos de quema declarados. Los dos tienen `energia:inConcession`.
- `energia:inConcession` es la única propiedad que une algo con su concesión: la producción (`energia:WellProduction`), la participación (`energia:Stake`), los venteos, los enlaces y los estudios ambientales.
- Las empresas tienen un solo nombre por grupo cuando una corrección revisada lo dice: "CHEVRON", "PLUSPETROL", "COMPAÑIA GENERAL DE COMBUSTIBLES".
- `energia:PipelineLink` (`energia:aboutConcession`, `energia:pipeline`, `energia:distanceKm`): el gasoducto de transporte de ENARGAS más cercano a cada concesión; 0 km si la cruza.
- `energia:SurroundingsLink` (`energia:aboutVenting`, `energia:nearestTown`, `energia:distanceKm`, `energia:protectedArea`): la localidad más cercana a cada posible venteo y su área protegida, según el IGN.
- `energia:lei` de una `energia:Company` es su identificador global en GLEIF (solo las que lo tienen).
- Los nombres de empresas están como en cada fuente, casi siempre en mayúsculas y con su forma societaria («S.A.», «SAU», «S.R.L.»).
- `energia:ConcessionToReview` (concesión para revisar) se deduce de `energia:VentingFarFromPipeline` y `energia:VentingWithoutReports`; `energia:reviewReason` dice el motivo.
- Las concesiones, los venteos y los gasoductos (`energia:Pipeline`) tienen su geometría en `geo:asWKT` (GeoSPARQL; prefijo `PREFIX geo: <http://www.opengis.net/ont/geosparql#>`).
- El endpoint no soporta caminos de largo arbitrario (`*`, `+`).
