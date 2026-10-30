"""A new domain's scaffold in one command (docs/method.md, «Before step 0»; skill start-domain).

    python layer/method.py new-domain <domain> --title "<título en español>"

Writes what every domain has before its first question, and nothing it does not have yet:
- ontology/<domain>/: the ontology with only its header, competency-questions.md, queries/
- mappings/<domain>.r2rml.ttl: the domain's sources (empty until the first source), so Ontop starts
- linking/<domain>/, layer/<domain>/: the assistant's notes and reader.sql (the read-only users, grants per source
  added by add-source)
- its registry entry in layer/dominios.yaml, with only the method keys whose piece exists
- its Ontop service in infra/docker-compose.yml, on the next free port, and its customer settings in
  infra/docker-compose.customer.yml

- app/dominios/<domain>.yaml and its line in app/dominios.yaml: the app hides the domain until it has a question
  (show-in-app fills the file)

It refuses to overwrite: an existing domain, file or service stops it before anything is written.
"""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r"^[a-z][a-z0-9_]*$")
PORT = re.compile(r"\$\{ONTOP_[A-Z_]*PORT:-(\d+)\}:8080")


def next_port(compose_text):
    """The next port after the highest Ontop default in the compose file."""
    return max(int(p) for p in PORT.findall(compose_text)) + 1


def files(domain, title):
    """Each new file and its content."""
    prefix = f"@prefix {domain}: <https://w3id.org/rastro/{domain}#> ."
    return {
        f"ontology/{domain}/{domain}.ttl": f"""# Business dictionary for {domain}: only what the approved questions need (skill map-source).
{prefix}
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix prov: <http://www.w3.org/ns/prov#> .

<https://w3id.org/rastro/{domain}> a owl:Ontology ;
    rdfs:label "Rastro · {title}"@es .

# Every domain names its sources, with their licence: the app shows them, and the mapping has a first valid map
{domain}:DataSource a owl:Class ;
    rdfs:label "Fuente de datos"@es .

{domain}:name a owl:DatatypeProperty ;
    rdfs:label "nombre"@es .

{domain}:license a owl:DatatypeProperty ;
    rdfs:domain {domain}:DataSource ;
    rdfs:label "licencia"@es ;
    rdfs:comment "La licencia con la que la fuente publica sus datos."@es .
""",
        f"ontology/{domain}/competency-questions.md": f"""# Competency questions: {domain}

The questions this domain has to answer, each approved by a person before it is implemented (skill add-question).
Each question's lifecycle state is in `layer/{domain}/lifecycle.json`.

| # | Question | Answer type | Role |
|---|---|---|---|
""",
        f"ontology/{domain}/queries/.gitkeep": "",
        f"mappings/{domain}.r2rml.ttl": f"""# R2RML mapping for {domain}, one section per source (skill map-source).
@prefix rr: <http://www.w3.org/ns/r2rml#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
{prefix}

# The domain's sources, from Rastro's load registry. Ontop needs at least one map to start; this one reads no source
# until add-source replaces «false» with «id IN ('<source>', ...)».
<#DataSource> a rr:TriplesMap ;
    rr:logicalTable [ rr:sqlQuery "SELECT id, name, license FROM rastro_meta.source WHERE false" ] ;
    rr:subjectMap [ rr:template "https://w3id.org/rastro/source/{{id}}" ; rr:class {domain}:DataSource ] ;
    rr:predicateObjectMap [ rr:predicate {domain}:name ; rr:objectMap [ rr:column "name" ] ] ;
    rr:predicateObjectMap [ rr:predicate {domain}:license ; rr:objectMap [ rr:column "license" ] ] .
""",
        f"linking/{domain}/.gitkeep": "",
        f"layer/{domain}/sparql-notes.md": f"# Notes for the assistant: {domain} (Rastro, SPARQL)\n\n"
                                          f"Prefix: `PREFIX {domain}: <https://w3id.org/rastro/{domain}#>`. "
                                          "Ontop does not support `*` or `+` paths.\n",
        f"layer/{domain}/sql-notes.md": f"# Notes for the assistant: {domain} (SQL over the sources as they come)\n",
        f"layer/{domain}/sql-enlaces-notes.md": f"# Notes for the assistant: {domain} (SQL with Rastro's links)\n",
        f"app/dominios/{domain}.yaml": f"""# What belongs to {domain} in the app (drawn by app/dominio/; skill
# show-in-app). The app hides the domain until «preguntas» has a question.
domain: {domain}
resumen: >-
  {title[:1].upper() + title[1:]}.
preguntas: []
""",
        f"layer/{domain}/reader.sql": f"""-- Read-only users for the evaluation of {domain}: «without Rastro» sees the source
-- tables as loaded, «SQL + links» also the tables Rastro builds. Each source's GRANTs are added with the source
-- (skill add-source).
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{domain}_reader') THEN
        CREATE ROLE {domain}_reader LOGIN PASSWORD '{domain}_reader';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{domain}_reader_links') THEN
        CREATE ROLE {domain}_reader_links LOGIN PASSWORD '{domain}_reader_links';
    END IF;
END $$;

ALTER ROLE {domain}_reader SET statement_timeout = '60s';
ALTER ROLE {domain}_reader_links SET statement_timeout = '60s';
""",
    }


def registry_entry(domain, title, port):
    return f"""
{domain}:
  base: >-
    Respondés preguntas de negocio sobre {title}. Seguí al pie de la letra las definiciones que trae la pregunta.
  ontop: http://ontop-{domain}:8080/sparql
  ontology: ontology/{domain}/{domain}.ttl
  sparql_notes: layer/{domain}/sparql-notes.md
  sql_notes: layer/{domain}/sql-notes.md
  links_notes: layer/{domain}/sql-enlaces-notes.md
  readers: {{B: {domain}_reader, D: {domain}_reader_links}}
  namespace: https://w3id.org/rastro/{domain}#
  # Written by `method.py new-domain`. Keys for pieces not built yet are left out (docs/method.md).
  method:
    questions: ontology/{domain}/competency-questions.md
    queries: ontology/{domain}/queries/
    mapping: mappings/{domain}.r2rml.ttl
    ontop: {{service: ontop-{domain}, port: {port}}}
    lifecycle: layer/{domain}/lifecycle.json
    app: app/dominios/{domain}.yaml
"""


def app_entry(domain, title):
    return f"""- id: {domain}
  name: {title[:1].upper() + title[1:]}
  config: /app/dominios/{domain}.yaml
"""


def ontop_service(domain, port):
    variable = f"ONTOP_{domain.upper()}_PORT"
    return f"""
  ontop-{domain}:
    build: ./ontop
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      ONTOP_ONTOLOGY_FILE: /opt/rastro/ontology/{domain}/{domain}.ttl
      ONTOP_MAPPING_FILE: /opt/rastro/mappings/{domain}.r2rml.ttl
      ONTOP_DB_URL: jdbc:postgresql://postgres:5432/${{PG_DB:-rastro}}
      ONTOP_DB_USER: ${{PG_USER:-rastro}}
      ONTOP_DB_PASSWORD: ${{PG_PASSWORD:-rastro}}
      ONTOP_DB_DRIVER: org.postgresql.Driver
      ONTOP_CORS_ALLOWED_ORIGINS: "*"
      ONTOP_DEV_MODE: "true"
    ports:
      - "${{{variable}:-{port}}}:8080"
    volumes:
      - ../ontology:/opt/rastro/ontology:ro
      - ../mappings:/opt/rastro/mappings:ro
"""


def customer_service(domain, port):
    return f"""
  ontop-{domain}:
    environment: *ontop-customer
    ports: !override
      - "127.0.0.1:${{ONTOP_{domain.upper()}_PORT:-{port}}}:8080"
"""


def before_volumes(text, addition):
    """addition placed at the end of the services, just before the top-level «volumes:»."""
    marker = "\nvolumes:\n"
    if text.count(marker) != 1:
        raise ValueError("Expected one top-level «volumes:» to place the service before")
    return text.replace(marker, addition + marker)


def scaffold(domain, title, root=ROOT):
    """Writes the domain's scaffold; returns the paths written. Checks everything before writing anything."""
    if not NAME.match(domain):
        raise ValueError(f"«{domain}»: a short name in lowercase, letters, digits and _ (it is also the prefix)")
    registry_path, compose_path = root / "layer/dominios.yaml", root / "infra/docker-compose.yml"
    app_list = root / "app/dominios.yaml"
    customer_path = root / "infra/docker-compose.customer.yml"
    registry_text, compose_text, customer_text = (p.read_text() for p in (registry_path, compose_path, customer_path))
    if domain in (yaml.safe_load(registry_text) or {}) or f"- id: {domain}\n" in (root / "app/dominios.yaml").read_text():
        raise ValueError(f"«{domain}» is already in layer/dominios.yaml")
    if f"\n  ontop-{domain}:\n" in compose_text + customer_text:
        raise ValueError(f"ontop-{domain} already exists in the compose files")
    new = files(domain, title)
    existing = [path for path in new if (root / path).exists()]
    if existing:
        raise ValueError("Would overwrite: " + ", ".join(existing))
    port = next_port(compose_text)
    compose_new = before_volumes(compose_text, ontop_service(domain, port))
    customer_new = before_volumes(customer_text, customer_service(domain, port))
    yaml.safe_load(compose_new)   # both still parse before anything is written
    for path, content in new.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(content)
    registry_path.write_text(registry_text.rstrip("\n") + "\n" + registry_entry(domain, title, port))
    app_list.write_text(app_list.read_text().rstrip("\n") + "\n" + app_entry(domain, title))
    compose_path.write_text(compose_new)
    customer_path.write_text(customer_new)
    return [*new, "layer/dominios.yaml", "app/dominios.yaml", "infra/docker-compose.yml",
            "infra/docker-compose.customer.yml"], port
