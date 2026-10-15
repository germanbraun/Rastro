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

Pendiente (Fase 0): `docker compose up` desde `infra/`.
