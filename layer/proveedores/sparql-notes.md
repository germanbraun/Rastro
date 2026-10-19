Endpoint SPARQL de Rastro (Ontop) sobre cinco fuentes públicas integradas: contratos federales de EE. UU. (USAspending), sectores (NAICS), el identificador global de empresas (GLEIF), la Lista Consolidada de Control y Wikidata.

- Prefijos: `PREFIX proveedores: <https://w3id.org/rastro/proveedores#>`, y `PREFIX prov: <http://www.w3.org/ns/prov#>` solo si la consulta usa `prov:` (la evidencia de los enlaces).
- Los contratos son los del año fiscal 2025 de más de US$10 millones. `proveedores:amount` es el monto total del contrato en dólares.
- `proveedores:group` es el grupo empresario de un proveedor, ya resuelto: incluye todas sus filiales.
- Los sectores son códigos NAICS (`proveedores:code`, por ejemplo "5415"); `?s proveedores:within ?x` incluye a `?x` y todos sus subsectores.
- Los nombres de agencias están en inglés, como en USAspending: "Department of Defense".
- Los nombres de empresas están como en cada fuente, casi siempre en mayúsculas.
- El endpoint no soporta caminos de largo arbitrario (`*`, `+`).
