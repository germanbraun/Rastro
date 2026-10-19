Base PostgreSQL con cinco fuentes públicas, cargadas tal como vienen:

- `usaspending.*`: USAspending, contratos federales de EE. UU. con actividad en el año fiscal 2025 y monto de más de US$10 millones.
  - `contract`: un contrato por fila. `amount` es el monto total del contrato en dólares. `awarding_agency` es la agencia (por ejemplo «Department of Defense»). `naics_code` es el sector (NAICS; algunos contratos usan códigos de versiones anteriores a 2022). `recipient_id` es el proveedor.
  - `recipient`: un proveedor por fila (`recipient_id`), con su UEI (`uei`), nombre, estado (`state_code`), país (`country_code`, de 3 letras) y su matriz actual según USAspending (`parent_uei`, `parent_name`).
  - `recipient_parent`: todas las matrices que USAspending registró para cada proveedor, actuales e históricas.
- `naics.sector`: sectores NAICS 2022, de 2 a 6 dígitos, con su sector padre directo (`parent_code`). Los sectores agrupados son rangos: 31-33, 44-45, 48-49.
- `gleif.*`: GLEIF, el identificador global de empresas (LEI). `name_query` y `candidate` son las búsquedas por nombre que se hicieron para los nombres de proveedores y matrices de USAspending (`candidate.name` es el nombre buscado, tal como está en USAspending; los candidatos están en el orden de relevancia de GLEIF y no están confirmados). `lei_record` tiene cada registro: nombre legal, nombres anteriores (`other_names`), país y región del domicilio legal y de la sede, estado y matriz final (`ultimate_parent_lei`, si GLEIF la tiene).
- `csl.entry`: la Lista Consolidada de Control del gobierno de EE. UU. (OFAC, Comercio, Estado): nombre, alias (`alt_names`), tipo (Entity, Individual, Vessel, Aircraft o vacío), lista (`source`) y países (códigos de 2 letras).
- `wikidata.company`: empresas de Wikidata que tienen uno de los LEI de `gleif.lei_record`, con las bolsas donde cotizan (`exchanges`, vacío si no cotiza) y su sede.
