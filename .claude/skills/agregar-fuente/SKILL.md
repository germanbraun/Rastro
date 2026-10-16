---
name: agregar-fuente
description: Sumar o cambiar un cargador de datos de Rastro (AACT, ChEMBL, openFDA, MeSH u otra fuente). Usalo cuando haya que descargar y cargar datos nuevos en Postgres o GraphDB.
---

# Agregar una fuente de datos

Un cargador baja datos, los guarda en `data/raw/` y los carga en Postgres (un esquema por fuente) o en GraphDB. Seguí el patrón de los que ya existen: `data/chembl/` y `data/openfda/` en Python, `data/aact/` en bash.

## Pasos

1. **Recorte primero.** Cargá solo lo que piden las preguntas de `ontology/competency-questions.md`, dentro del recorte de oncología. Si la fuente es grande, filtrá en origen.
2. **Registrá la fuente** en `infra/postgres/init/01-schemas.sql` (`rastro_meta.source`, con licencia) si es nueva.
3. **Escribí el cargador** en `data/<fuente>/`:
   - `schema.sql` con las tablas, con los nombres de la fuente original cuando existan.
   - `load.py` que descarga a `data/raw/<fuente>/` (con caché si la descarga es lenta) y carga con `COPY`.
   - Al final, una fila en `rastro_meta.load_run` por tabla, con la versión de la fuente.
4. **Sumá el servicio** `<fuente>-loader` en `infra/docker-compose.yml`, con `profiles: ["load"]` y la imagen `./loaders`.
5. **Credenciales** solo por variables de `.env`. Agregá la variable vacía a `.env.example`. Pasá contraseñas por parámetros de conexión, nunca dentro de una URL, porque los errores las imprimen.
6. **Corré la carga** y verificá con la skill `verificar`: conteos, un caso conocido (por ejemplo imatinib) y que nada quede fuera del recorte.
7. **Documentá:** una fila en la tabla "Cargar datos" del `README.md` y una entrada en `docs/decisions.md` (qué recorte, por qué, números de la carga).

## Cuidado con

- **Memoria:** importar RDF grande en GraphDB, por partes (ver `data/mesh/load.py`).
- **Respuestas comprimidas:** si el servidor manda `Content-Encoding`, `requests` descomprime solo.
- **Codificación de `+`:** en APIs que usan `+` como espacio, `requests` lo codifica como `%2B`. Usá espacios.
