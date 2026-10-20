Además, las tablas de Rastro (esquema `energia`), que ya resuelven los cruces entre fuentes. Son las mismas que lee el diccionario de negocio, con las mismas definiciones:

- `energia.empresa`: una empresa por `empresa_id`, con su nombre (`nombre`). Las sociedades de un mismo grupo, según correcciones revisadas, son una sola empresa (por ejemplo «CHEVRON», «PLUSPETROL»).
- `energia.empresa_nombre`: cada nombre de empresa en cada fuente (`fuente`, `nombre`) → `empresa_id`, con `regla` y `evidencia`.
- `energia.produccion_pozo`: la producción de 2025 por pozo y formación (`idpozo`, `id_concesion`, `empresa_id` de quien la declara, `formacion`, `tipo_recurso`, `sub_tipo_recurso`, `petroleo_m3`, `gas_mm3`).
- `energia.concesion`: las concesiones (`id_concesion`, `nombre`, `operadora_mapa` = `empresa_id` de la operadora según el mapa).
- `energia.participacion`: los socios de cada concesión, ya separados (`id_concesion`, `empresa_id`, `porcentaje` de 0 a 100, `texto`).
- `energia.operador_pozo`: quién opera hoy cada pozo (`idpozo` → `empresa_id`): la empresa que declara la producción de su último mes. `empresa_padron` dice lo que registra el padrón.
- `energia.venteo`: los venteos dentro de una concesión (`tipo` = 'detectado' desde 2024, o 'declarado'; `fecha`, `id_concesion`).
- `energia.concesion_gasoducto`: el gasoducto de transporte más cercano a cada concesión (`id_concesion`, `gasoducto`, `distancia_km`; 0 si lo cruza).
- `energia.venteo_entorno`: para cada posible venteo detectado (`id` = `venteo.id`), la localidad más cercana (`localidad`, `distancia_km`) y el área protegida que lo contiene (`area_protegida`, vacío si ninguna).
- `energia.empresa_lei`: el LEI de cada empresa en GLEIF (`empresa_id`, `lei`, `nombre_legal`), aceptado si coincide el nombre legal.
- `energia.estudio`: los estudios ambientales (`id_estudio`, `fecha_estudio`, `tipo_estudio`, `empresa_id`), con su concesión del mapa (`id_concesion`) cuando el nombre que da el estudio coincide con el del mapa; si no coincide, vacío.
- `energia.concesion_revisar`: las concesiones para revisar por venteos (`id_concesion`, `motivo`, `evidencia`), una fila por motivo: 'sin gasoducto cerca' (posibles venteos desde 2024 y el gasoducto de transporte más cercano a 10 km o más) o 'sin planillas de venteo' (al menos 20 posibles venteos desde 2024 y ninguna planilla de venteo de gas presentada desde 2022). Una concesión puede tener los dos motivos.
- `energia.operador_area_mes`: quién operó cada concesión cada mes de 2023 a 2025 (`id_concesion`, `mes`, `empresa_id`): la empresa que declara la mayor parte de su producción (petróleo en m³ más gas en miles de m³). Un mes sin producción cuenta si lo declara una sola empresa.
- `energia.cambio_operadora`: los cambios de operadora de 2023 a 2025 (`id_concesion`, `mes` desde el que opera la nueva, `anterior_id`, `nueva_id`, la producción por mes antes y después): otra empresa pasa a declarar la mayor parte de la producción al menos 3 meses seguidos.
