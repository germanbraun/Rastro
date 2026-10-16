# Rastro

Dos MVP comerciales sobre tecnologías semánticas, en oncología: **Rastro Layer** (preguntas en lenguaje natural sobre fuentes integradas, con la procedencia de cada dato) y **Rastro Lab** (predicción de ensayos que se detienen, con explicaciones). El plan está en `docs/plan.md`.

## Regla principal: simple

Es un MVP comercial: lo tiene que entender alguien de ventas.

- Hacé lo mínimo que funciona para la demo o para un número de la demo. Si una pieza no hace falta, no se hace.
- Nombres simples y en palabras de negocio: "Fármaco", "Ensayo", "detenido". Nada de siglas internas.
- Antes de agregar una clase, una tabla, un servicio o una dependencia, preguntate si se puede evitar.
- Cada fase termina en algo que se ve funcionar.

## Convenciones

- **Idioma:** código, comentarios, docs y commits en español.
- **Mapeos en R2RML**, en un solo archivo, `mappings/rastro.r2rml.ttl`, con una sección por fuente. Ontop lee un solo archivo de mapeo.
- **Ontología mínima** (`ontology/rastro.ttl`): solo lo que piden las preguntas de `ontology/competency-questions.md`. Las condiciones son descriptores de MeSH.
- **Datos fuera del repo:** las descargas van a `data/raw/`, que no se versiona. El repo guarda scripts.
- **Secretos solo en `.env`**, nunca en `.env.example` ni en commits. Antes de commitear, revisá que `.env.example` tenga los valores vacíos.
- **Cada carga se registra** en `rastro_meta.load_run`, para que el conteo por fuente y la procedencia funcionen.
- **Decisiones** en `docs/decisions.md`: una entrada corta por decisión, con el porqué.

## Comandos

```bash
docker compose up -d                              # Postgres :5434, Ontop :8080, GraphDB :7210
docker compose run --rm <fuente>-loader           # aact, chembl, openfda, mesh
docker compose run --rm ontology-check            # ontología y queries
docker compose exec postgres psql -U rastro -c "select * from rastro_meta.source_counts"
```

## Skills del repo

- `agregar-fuente`: sumar o cambiar un cargador de datos
- `agregar-pregunta`: sumar una pregunta de competencia con su query
- `verificar`: comprobar que todo levanta y responde
- `cerrar-fase`: marcar el plan, documentar y commitear
