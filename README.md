# Rastro

Dos MVPs sobre tecnologías semánticas, con datos públicos. Rastro Layer tiene tres dominios: petróleo y gas en Argentina, proveedores del Estado de EE. UU. y ensayos clínicos de oncología (AACT, ChEMBL, openFDA, MeSH).

- **Rastro Layer** — capa semántica virtual sobre fuentes heterogéneas y preguntas en lenguaje natural con trazabilidad de cada dato.
- **Rastro Lab** — pipeline de data science que reutiliza la capa para generar features semánticas, con linaje y explicabilidad.

El plan completo, por fases y con checkpoints, está en [docs/plan.md](docs/plan.md). Cómo se integran las fuentes (heterogeneidad de esquema y de datos), en [docs/integracion.md](docs/integracion.md). Qué tiene cada fuente, para quien no es del dominio, en [docs/fuentes.md](docs/fuentes.md).

## Estructura

| Carpeta | Contenido |
|---|---|
| `infra/` | docker-compose: Postgres, Ontop, triplestore |
| `data/` | scripts de descarga y carga (los datos no se versionan) |
| `ontology/` | preguntas de competencia, ontología y una query por pregunta |
| `mappings/` | mapeos R2RML, uno por dominio (`rastro`, `proveedores`, `energia`), que lee el Ontop de cada dominio |
| `linking/` | enlaces de ensayos con MeSH y ChEMBL, en SQL legible, y su revisión |
| `layer/` | Rastro Layer: preguntas en lenguaje natural (`answer.py`) y su evaluación (`eval/`) |
| `lab/` | Rastro Lab: features, modelos, linaje |
| `app/` | la demo (Streamlit) |
| `docs/` | plan, decisiones, resultados, mazos (`slides/`), guiones de demo y verificación humana |

Cada dominio usa su propio prefijo en SPARQL: `energia:`, `proveedores:` y `oncologia:` (por ejemplo, `energia:Well`).

## La demo

| Dominio | Guion | Mazo |
|---|---|---|
| Petróleo y gas en Argentina | [docs/demo-guion-energia.md](docs/demo-guion-energia.md) | `docs/slides/energia.html` |
| Proveedores del Estado de EE. UU. | [docs/demo-guion.md](docs/demo-guion.md) | `docs/slides/proveedores.html` |
| Oncología | [docs/demo-guion-oncologia.md](docs/demo-guion-oncologia.md) | `docs/slides/oncologia.html` |

Para una audiencia técnica: [docs/demo-guion-tecnico.md](docs/demo-guion-tecnico.md). Lo que falta que confirme una persona: [docs/verificacion-humana.md](docs/verificacion-humana.md). Una evaluación con preguntas que no armamos nosotros: [docs/preguntas-a-ciegas.md](docs/preguntas-a-ciegas.md).

## Levantar el entorno

```bash
docker compose up -d
```

| Servicio | URL local | Qué es |
|---|---|---|
| **Demo de Rastro Layer** | **http://localhost:8501** | Preguntar en lenguaje natural y comparar con y sin Rastro; un selector cambia de dominio (abre en petróleo y gas) |
| Postgres | `localhost:5434` (usuario y clave `rastro`) | Fuentes relacionales, un esquema por fuente, y `rastro_meta` con el registro de fuentes y cargas |
| Ontop | http://localhost:8080 | Endpoint SPARQL virtual sobre Postgres; recarga `ontology/` y `mappings/` al editarlos |
| Ontop de proveedores | http://localhost:8081 | Proveedores del Estado, con su ontología y sus mapeos |
| Ontop de petróleo y gas | http://localhost:8082 | Petróleo y gas en Argentina, con su ontología y sus mapeos |
| GraphDB Free | http://localhost:7210 | Triplestore con el repositorio `rastro`: MeSH 2026 en el grafo `<http://id.nlm.nih.gov/mesh/2026>` y el conector Lucene `mesh` |

Los puertos se cambian copiando `.env.example` a `.env`. Por defecto evitan 5432 y 7200 para convivir con un Postgres y un GraphDB locales.

Conteo por fuente (checkpoint de la Fase 0):

```bash
docker compose exec postgres psql -U rastro -c "select * from rastro_meta.source_counts"
```

Cada script de `data/` registra sus cargas en `rastro_meta.load_run`, que alimenta esa vista.

## Evaluar Rastro Layer

Compara cuántas de 20 preguntas responde bien un LLM solo, con SQL directo y con Rastro:

```bash
docker compose run --rm layer-eval
```

Los resultados están en `layer/eval/results.md`. Las respuestas ya generadas se guardan en `layer/eval/results.json`, así que esto funciona sin API key. Para generar respuestas nuevas hace falta `ANTHROPIC_API_KEY` en `.env` (Claude API, de pago por uso: una corrida completa con Claude Opus 5.5 cuesta unos pocos dólares). `RASTRO_MODEL` elige otro modelo, por ejemplo uno más barato para una demo en vivo.

Para revisar la ontología y las queries:

```bash
docker compose run --rm ontology-check
```

## Cargar datos

Los cargadores corren a demanda y necesitan credenciales en `.env` (copiado de `.env.example`).

| Fuente | Comando | Requisito |
|---|---|---|
| AACT (oncología) | `docker compose run --rm aact-loader` | Cuenta gratuita de AACT (`AACT_USER`, `AACT_PASSWORD`) o un snapshot en `data/raw/` (`AACT_DUMP`) |
| ChEMBL (oncología) | `docker compose run --rm chembl-loader` | Ninguno: usa la API pública de ChEMBL, MeSH de NLM y UniChem |
| openFDA (eventos adversos) | `docker compose run --rm openfda-loader` | ChEMBL cargado antes. API key gratuita recomendada (`OPENFDA_API_KEY`): sin ella, 1000 requests por día y la descarga sigue en la próxima corrida |
| MeSH 2026 (GraphDB) | `docker compose run --rm mesh-loader` | Unos 3 GB de memoria libres en Docker durante la importación. Crea también el conector Lucene `mesh` y copia descriptores y jerarquía a Postgres |
| USAspending (proveedores) | `docker compose run --rm usaspending-loader` | Ninguno: API pública. Contratos del año fiscal 2025 de más de US$10 millones y el perfil de cada proveedor con sus matrices; la primera vez tarda alrededor de una hora y es reanudable |
| NAICS 2022 (proveedores) | `docker compose run --rm naics-loader` | Ninguno: planilla pública del Census. Sectores de 2 a 6 dígitos con sus ancestros |
| Lista Consolidada de Control (proveedores) | `docker compose run --rm csl-loader` | Ninguno: CSV público de trade.gov |
| GLEIF (proveedores) | `docker compose run --rm gleif-loader` | USAspending cargado antes. Candidatos a LEI de matrices y de los 1000 proveedores que más facturan; 60 consultas por minuto, reanudable |
| Wikidata (proveedores) | `docker compose run --rm wikidata-loader` | GLEIF cargado antes. Empresas con esos LEI en Wikidata, su sede y si cotizan en bolsa |
| Petróleo y gas (Secretaría de Energía) | `docker compose run --rm energia-loader` y después `docker compose run --rm energia-linker` | Ninguno: producción 2025 por pozo y padrón de pozos (datos.energia.gob.ar), concesiones, venteos y gasoductos de ENARGAS del WFS, localidades y áreas protegidas del IGN y el LEI de las empresas en GLEIF; unos 350 MB, reanudable |
| Enlaces | `docker compose run --rm linker` | Las fuentes de arriba ya cargadas. Enlaza ensayos con MeSH y con ChEMBL en unos segundos |
| Tablas y enlaces de proveedores | `docker compose run --rm proveedores-linker` | USAspending y NAICS cargados (y GLEIF, la Lista Consolidada y Wikidata para los enlaces). Arma proveedores, grupos y sectores, y los enlaces con su evidencia |

Las descargas quedan en `data/raw/`, que no se versiona: openFDA guarda ahí un JSON por fármaco y no lo vuelve a pedir.

Si una contraseña tiene `$`, va entre comillas simples en el `.env`: Docker Compose interpreta `$` en valores sin comillas.
