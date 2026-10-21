# Rastro

Dos MVPs sobre tecnologías semánticas, con datos públicos. El caso de la demo es **petróleo y gas en Argentina**. Los otros dos casos, proveedores del Estado de EE. UU. y ensayos clínicos de oncología (AACT, ChEMBL, openFDA, MeSH), muestran que lo mismo sirve para otros datos: en la app aparecen al prender «Ver detalles técnicos».

- **Rastro Layer** — capa semántica virtual sobre fuentes heterogéneas y preguntas en lenguaje natural con trazabilidad de cada dato.
- **Rastro Lab** — un modelo cuyas predicciones se explican con esa misma evidencia. Hoy: el gas de los pozos nuevos de shale gas de Vaca Muerta.

El plan completo, por fases y con checkpoints, está en [docs/plan.md](docs/plan.md). Cómo se integran las fuentes (heterogeneidad de esquema y de datos), en [docs/integracion.md](docs/integracion.md). Qué tiene cada fuente, para quien no es del dominio, en [docs/fuentes.md](docs/fuentes.md).

## Estructura

| Carpeta | Contenido |
|---|---|
| `infra/` | docker-compose: Postgres, Ontop, triplestore (`compose.yaml`, en la raíz, lo incluye) |
| `data/` | scripts de descarga y carga (los datos no se versionan) |
| `ontology/` | preguntas de competencia, ontología y una query por pregunta |
| `mappings/` | mapeos R2RML, uno por dominio (`rastro`, `proveedores`, `energia`), que lee el Ontop de cada dominio |
| `linking/` | enlaces entre fuentes de cada dominio (por ejemplo, ensayos con MeSH y ChEMBL), con su revisión |
| `layer/` | Rastro Layer: preguntas en lenguaje natural (`answer.py`) y su evaluación (`eval/`) |
| `lab/` | Rastro Lab: el modelo de gas de Vaca Muerta (`lab/gas/`) |
| `app/` | la demo (Streamlit) |
| `docs/` | plan, decisiones, resultados, mazos (`slides/`), guiones de demo y verificación humana |
| `tests/` | pruebas (pytest) |

Cada dominio usa su propio prefijo en SPARQL: `energia:`, `proveedores:` y `oncologia:` (por ejemplo, `energia:Well`).

## La demo

| Dominio | Guion | Mazo |
|---|---|---|
| Petróleo y gas en Argentina | [docs/demo-guion-energia.md](docs/demo-guion-energia.md) | `docs/slides/energia.html` |
| Proveedores del Estado de EE. UU. | [docs/demo-guion.md](docs/demo-guion.md) | `docs/slides/proveedores.html` |
| Oncología | [docs/demo-guion-oncologia.md](docs/demo-guion-oncologia.md) | `docs/slides/oncologia.html` |

Para una audiencia técnica: [docs/demo-guion-tecnico.md](docs/demo-guion-tecnico.md). Lo que falta que confirme una persona: [docs/verificacion-humana.md](docs/verificacion-humana.md). Una evaluación con preguntas que no armamos nosotros: [docs/preguntas-a-ciegas.md](docs/preguntas-a-ciegas.md).

## Levantar el entorno

Desde la carpeta del repo:

```bash
docker compose up -d
```

| Servicio | URL local | Qué es |
|---|---|---|
| **Demo de Rastro Layer** | **http://localhost:8501** | Abre en petróleo y gas; con «Ver detalles técnicos» aparece el selector **Caso de uso** con proveedores y oncología |
| Postgres | `localhost:5434` (usuario y clave `rastro`) | Fuentes relacionales, un esquema por fuente, y `rastro_meta` con el registro de fuentes y cargas |
| Ontop, uno por dominio | oncología http://localhost:8080, proveedores :8081, petróleo y gas :8082 (`/sparql`) | Endpoint SPARQL virtual sobre Postgres, con la ontología y los mapeos de su dominio; recarga al editarlos |
| GraphDB Free | http://localhost:7210 | Triplestore con el repositorio `rastro`: MeSH 2026 en el grafo `<http://id.nlm.nih.gov/mesh/2026>` y el conector Lucene `mesh` |

Los puertos se cambian copiando `.env.example` a `.env`. Por defecto evitan 5432 y 7200 para convivir con un Postgres y un GraphDB locales.

Conteo por fuente (checkpoint de la Fase 0):

```bash
docker compose exec postgres psql -U rastro -c "select * from rastro_meta.source_counts"
```

Cada script de `data/` registra sus cargas en `rastro_meta.load_run`, que alimenta esa vista.

## Evaluar Rastro Layer

Petróleo y gas y proveedores comparan tres formas de responder: **B**, sin Rastro (SQL sobre las tablas crudas); **D**, SQL con las tablas de enlaces de Rastro; y **C**, con Rastro (SPARQL). En petróleo y gas: B 7 de 10, D 10 de 10 y C 10 de 10.

```bash
docker compose run --rm -T layer-eval python /layer/evaluar.py energia puntaje   # o proveedores; también prompt, try y rerun
```

Los resultados quedan en `layer/<dominio>/resultados.md`; el detalle de cada comando, en el docstring de `layer/evaluar.py`.

Oncología compara cuántas de 20 preguntas responde bien un LLM solo, con SQL directo y con Rastro:

```bash
docker compose run --rm layer-eval
```

Los resultados están en `layer/eval/results.md`. Las respuestas ya generadas se guardan en `layer/eval/results.json`, así que esto funciona sin API key. Para generar respuestas nuevas hace falta `ANTHROPIC_API_KEY` en `.env` (Claude API, de pago por uso: una corrida completa con Claude Opus 5.5 cuesta unos pocos dólares). `RASTRO_MODEL` elige otro modelo, por ejemplo uno más barato para una demo en vivo.

Para revisar la ontología y las queries:

```bash
docker compose run --rm ontology-check
```

## Rastro Lab

Un modelo lineal (regresión ridge) predice el gas de los meses 2 a 7 de un pozo nuevo de shale gas de Vaca Muerta, con las tablas crudas y con Rastro, y explica cada predicción con el aporte exacto de cada variable. Los dos predicen igual de bien; con Rastro, cada variable dice de dónde sale y cuáles están corregidas o llegaron tarde. En la app, pestaña **Rastro Lab**. Detalle en [docs/lab-gas-vaca-muerta.md](docs/lab-gas-vaca-muerta.md).

Corre en la máquina, no en Docker: necesita `python3 -m pip install -r requirements-dev.txt`, el Ontop de petróleo y gas en `localhost:8082` y los datos de `lab-gas-loader` (abajo).

```bash
python3 lab/gas/modelo.py              # o un pozo, --12-meses, --como-trabajo-publicado
python3 lab/gas/modelo.py --publicar   # guarda la corrida, su entrada y sus predicciones en Rastro, para consultarlas
python3 lab/gas/modelo.py --comparar   # qué cambió entre las dos últimas corridas, pozo por pozo
layer/energia/cambio/impacto.sh registrar   # Rastro dice qué predicciones cambian si la fuente corrige un registro, y se comprueba
python3 lab/gas/a_ciegas.py            # arma la prueba a ciegas: docs/lab-explicaciones-a-ciegas.md
```

## Calidad

```bash
python3 -m ruff check .
python3 -m pytest -q
```

También corren en GitHub con cada cambio (`.github/workflows/calidad.yml`).

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
| Rastro Lab, gas de Vaca Muerta | `docker compose run --rm lab-gas-loader` y después `docker compose run --rm energia-linker` | Ninguno: Capítulo IV de 2018 a 2022, datos de fractura de pozos (Adjunto IV) y trayectorias de pozo de Vaca Muerta, de datos.energia.gob.ar; unos 1,5 GB. No cambia lo que usa Rastro Layer |
| Enlaces de oncología | `docker compose run --rm linker` | Las fuentes de arriba ya cargadas. Enlaza ensayos con MeSH y con ChEMBL en unos segundos |
| Tablas y enlaces de proveedores | `docker compose run --rm proveedores-linker` | USAspending y NAICS cargados (y GLEIF, la Lista Consolidada y Wikidata para los enlaces). Arma proveedores, grupos y sectores, y los enlaces con su evidencia |

Las descargas quedan en `data/raw/`, que no se versiona: openFDA guarda ahí un JSON por fármaco y no lo vuelve a pedir.

Si una contraseña tiene `$`, va entre comillas simples en el `.env`: Docker Compose interpreta `$` en valores sin comillas.
