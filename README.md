# Rastro

Dos MVPs sobre tecnologías semánticas, en oncología, con datos públicos (AACT, ChEMBL, openFDA, MeSH):

- **Rastro Layer** — capa semántica virtual sobre fuentes heterogéneas y preguntas en lenguaje natural con trazabilidad de cada dato.
- **Rastro Lab** — pipeline de data science que reutiliza la capa para generar features semánticas, con linaje y explicabilidad.

El plan completo, por fases y con checkpoints, está en [docs/plan.md](docs/plan.md).

## Estructura

| Carpeta | Contenido |
|---|---|
| `infra/` | docker-compose: Postgres, Ontop, triplestore |
| `data/` | scripts de descarga y carga (los datos no se versionan) |
| `ontology/` | ontología en Turtle y preguntas de competencia |
| `mappings/` | mapeos R2RML/OBDA por fuente |
| `shapes/` | shapes SHACL de validación |
| `linking/` | resolución de entidades de fármacos |
| `layer/` | Rastro Layer: NL→SPARQL, baseline NL→SQL, API; `eval/` con el set de evaluación |
| `lab/` | Rastro Lab: features, modelos, linaje |
| `app/` | frontend de ambas demos |
| `docs/` | plan, decisiones, resultados y guion de demo |

## Levantar el entorno

```bash
docker compose up -d
```

| Servicio | URL local | Qué es |
|---|---|---|
| Postgres | `localhost:5434` (usuario y clave `rastro`) | Fuentes relacionales, un esquema por fuente, y `rastro_meta` con el registro de fuentes y cargas |
| Ontop | http://localhost:8080 | Endpoint SPARQL virtual sobre Postgres; recarga `ontology/` y `mappings/` al editarlos |
| GraphDB Free | http://localhost:7210 | Triplestore con el repositorio `rastro` (MeSH y grafos materializados) |

Los puertos se cambian copiando `.env.example` a `.env`. Por defecto evitan 5432 y 7200 para convivir con un Postgres y un GraphDB locales.

Conteo por fuente (checkpoint de la Fase 0):

```bash
docker compose exec postgres psql -U rastro -c "select * from rastro_meta.source_counts"
```

Cada script de `data/` registra sus cargas en `rastro_meta.load_run`, que alimenta esa vista.

## Cargar datos

Los cargadores corren a demanda y necesitan credenciales en `.env` (copiado de `.env.example`).

| Fuente | Comando | Requisito |
|---|---|---|
| AACT (oncología) | `docker compose run --rm aact-loader` | Cuenta gratuita de AACT (`AACT_USER`, `AACT_PASSWORD`) o un snapshot en `data/raw/` (`AACT_DUMP`) |
| ChEMBL (oncología) | `docker compose run --rm chembl-loader` | Ninguno: usa la API pública de ChEMBL, MeSH de NLM y UniChem |

Si una contraseña tiene `$`, va entre comillas simples en el `.env`: Docker Compose interpreta `$` en valores sin comillas.
