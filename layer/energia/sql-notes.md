Base PostgreSQL con seis fuentes públicas, cargadas tal como vienen:

- `capitulo4.*`: Capítulo IV de la Secretaría de Energía de Argentina.
  - `produccion`: las declaraciones juradas mensuales de 2025, una fila por pozo, mes y formación. `prod_pet` es petróleo en m³ y `prod_gas` gas en miles de m³. `empresa` es la empresa que declara (la operadora ese mes). `idareapermisoconcesion` es el código de la concesión. `formacion` está en minúsculas («vaca muerta»). `tipo_de_recurso` es CONVENCIONAL o NO CONVENCIONAL y `sub_tipo_recurso` SHALE o TIGHT.
  - `produccion_historica`: las mismas declaraciones de 2023 y 2024, con las mismas columnas (más `areapermisoconcesion`, el nombre de la concesión).
  - `pozo`: el padrón de pozos, con la empresa que tiene registrada cada pozo y su ubicación (`lon`, `lat`).
- `sig_energia.*`: el servicio de mapas (WFS) de la Secretaría de Energía.
  - `concesion`: las concesiones de explotación (`id_concesion`, el mismo código que `produccion.idareapermisoconcesion`), su operadora (`empresa_operadora`), la empresa que informó el contorno (`empresa_informante`), los socios en un texto (`participacion`, con el formato «<br> EMPRESA: 50 %<br> OTRA: 50 %») y el contorno (`anillo`, JSON con una lista de [lon, lat]).
  - `venteo_declarado`: puntos de venteo y quema declarados, con `lon` y `lat`.
  - `venteo_detectado`: posibles venteos detectados por satélite (anomalías térmicas): `fecha`, `provincia`, `satelite`, `lon`, `lat`.
- `ambiental.estudio`: el listado de estudios e informes ambientales de la Secretaría de Energía (`id_estudio`, `fecha_estudio`, `tipo_estudio`, `empresa`). `concesion` nombra la concesión como texto, escrito como lo escribió quien lo presentó (no tiene el código). Las planillas de venteo de gas son el `tipo_estudio` «Inf. de presentación de planillas Aventamiento de Gas(Res143/98)».
- `enargas.gasoducto`: los gasoductos de transporte de ENARGAS (`nombregaso`, `licenciata`), con sus tramos en `lineas` (JSON con listas de [lon, lat]).
- `ign.*`: el Instituto Geográfico Nacional. `localidad` (BAHRA: `fna` es el nombre, `lon`, `lat`) y `area_protegida` (`fna`, contornos en `anillos`, JSON con listas de [lon, lat]).
- `gleif_energia.candidato`: lo que devolvió GLEIF al buscar por nombre las empresas que más producen (`nombre_buscado`, `lei`, `nombre_legal`, `estado`). Los candidatos no están confirmados.

Los nombres de empresa pueden variar entre fuentes (con o sin «S.A.», acentos, mayúsculas). La base no tiene PostGIS.
