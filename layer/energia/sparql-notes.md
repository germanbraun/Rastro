Endpoint SPARQL de Rastro (Ontop) sobre dos fuentes públicas de la Secretaría de Energía de Argentina: la producción declarada pozo por pozo (Capítulo IV) y los mapas de concesiones y venteos (WFS).

- Prefijos: `PREFIX : <https://w3id.org/rastro/energia#>`, y `PREFIX prov: <http://www.w3.org/ns/prov#>` solo si la consulta usa `prov:` (la evidencia de los enlaces).
- La producción es la de 2025. `:oil` es petróleo en m³ y `:gas` es gas en miles de m³, por pozo y formación (`:WellProduction`).
- `:declaredBy` es la empresa que declara la producción; `:Stake` es la participación de una empresa en una concesión (`:percent`, de 0 a 100). Para «lo que le corresponde» a una empresa, multiplicar la producción de la concesión por su porcentaje.
- `:operator` de un `:Well` es quién lo opera hoy (la empresa que declara su último mes).
- `:formation` está en minúsculas: "vaca muerta". `:UnconventionalProduction` incluye shale y tight.
- `:DetectedVenting` son posibles venteos vistos por satélite desde 2024 (un indicio, no una confirmación); `:DeclaredVenting`, los puntos de quema declarados. Los dos tienen `:inConcession`.
- Las empresas tienen un solo nombre por grupo cuando una corrección revisada lo dice: "CHEVRON", "PLUSPETROL", "COMPAÑIA GENERAL DE COMBUSTIBLES".
- El endpoint no soporta caminos de largo arbitrario (`*`, `+`).
