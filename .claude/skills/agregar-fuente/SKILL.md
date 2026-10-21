---
name: agregar-fuente
description: Sumar o cambiar un cargador de datos de Rastro en cualquier dominio (Capítulo IV, mapas de la Secretaría de Energía, fractura, USAspending, AACT u otra fuente). Usalo cuando haya que descargar y cargar datos nuevos en Postgres o GraphDB.
---

# Agregar una fuente de datos

Un cargador baja datos, los guarda en `data/raw/` y los carga en Postgres (un esquema por fuente) o en GraphDB. Seguí el patrón de los que ya existen: `data/energia/` (varias fuentes de un dominio) y `data/lab-gas/` (una fuente que usa solo Rastro Lab), en Python.

## Pasos

1. **Recorte primero.** Cargá solo lo que piden las preguntas de competencia del dominio. Si la fuente es grande, filtrá en origen.
2. **No cambies lo que ya mide la demo.** Si la fuente es solo para Rastro Lab, va en su propio esquema y su propio cargador (como `capitulo4_anterior` y `fractura` en `data/lab-gas/`). Después de cargar, volvé a ejecutar la evaluación del dominio (skill `evaluar`, `rerun`) y confirmá que da lo mismo.
3. **Escribí el cargador** en `data/<fuente>/`:
   - `schema.sql` con las tablas, con los nombres de la fuente original. Si el enlazador lo necesita aunque la fuente no esté cargada, que no borre nada (`CREATE ... IF NOT EXISTS`) y que el cargador vacíe las tablas antes de cargar.
   - `load.py` que registra la fuente en `rastro_meta.source` (con licencia), descarga a `data/raw/<fuente>/` con caché y reintentos, y carga con `COPY`.
   - Una fila en `rastro_meta.load_run` por tabla, con la versión de la fuente: usá `copiar()` de `data/comun.py` y pasale el archivo descargado (`archivo=`), así queda su huella SHA-256 y el día en que se bajó.
4. **Sumá el servicio** `<fuente>-loader` en `infra/docker-compose.yml`, con `profiles: ["load"]` y la imagen `./loaders`.
5. **Credenciales** solo por variables de `.env`. Agregá la variable vacía a `.env.example`. Pasá contraseñas por parámetros de conexión, nunca dentro de una URL, porque los errores las imprimen.
6. **Enlaces:** si la fuente nombra empresas, pozos o concesiones, sumala al enlazador del dominio (`linking/<dominio>/links.sql`): sus nombres a `empresa_nombre` con su `fuente`, y una tabla de enlace con regla y evidencia. Mapeala con `prov:wasDerivedFrom` a la fuente y sumá sus términos a `layer/dominios.yaml`.
7. **Corré la carga y el enlazador**, reiniciá el Ontop del dominio y verificá con la skill `verificar`: conteos, un caso conocido y que nada quede fuera del recorte.
8. **Documentá:** una fila en la tabla «Cargar datos» del `README.md` y una entrada en `docs/decisions.md` (qué recorte, por qué, números de la carga).

## Cuidado con

- **Archivos grandes** (el Capítulo IV son unos 300 MB por año): corré el cargador en segundo plano y filtrá las consultas por los pozos que hacen falta antes de unir años.
- **Memoria:** importar RDF grande en GraphDB, por partes (ver `data/mesh/load.py`).
- **Fuentes que se actualizan todos los días** (fractura): guardá la fecha de carga de cada dato si la tiene (`fecha_data` → `energia:loadedOn`).
- **Codificación de `+`:** en APIs que usan `+` como espacio, `requests` lo codifica como `%2B`. Usá espacios.
