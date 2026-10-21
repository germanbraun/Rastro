# Rastro

Dos MVP comerciales sobre tecnologías semánticas, con datos públicos:

- **Rastro Layer:** preguntas de negocio sobre fuentes integradas, con la procedencia de cada dato.
- **Rastro Lab:** un modelo de aprendizaje automático cuyas predicciones se explican con esa misma evidencia. Hoy, el gas de los pozos nuevos de shale de Vaca Muerta.

El caso de la demo es **petróleo y gas en Argentina** (`energia`). Proveedores del Estado de EE. UU. (`proveedores`) y oncología (`oncologia`) son prueba de que el mismo Rastro sirve para otros datos: la app los muestra solo con «Ver detalles técnicos». El plan está en `docs/plan.md`; las decisiones, en `docs/decisions.md`.

## Regla principal: simple

Es un MVP comercial: lo tiene que entender alguien de ventas, que tiene que poder contarlo en tres minutos.

- Hacé lo mínimo que funciona para la demo o para un número de la demo. Si una pieza no hace falta, no se hace.
- Nombres simples y en palabras de negocio: "Pozo", "Concesión", "operadora". Nada de siglas internas.
- Antes de agregar una clase, una tabla, un servicio o una dependencia, preguntate si se puede evitar.
- Cada paso termina en algo que se ve funcionar.

## Convenciones

- **Idioma:** código, comentarios, docs y commits en español. Los nombres de la ontología, en inglés (`energia:Well`).
- **Mapeos en R2RML**, un archivo por dominio (`mappings/rastro.r2rml.ttl` para oncología, `proveedores.r2rml.ttl`, `energia.r2rml.ttl`). Cada Ontop lee un solo archivo de mapeo.
- **Ontología mínima** (`ontology/<dominio>/`): solo lo que piden sus preguntas de competencia. Una sola propiedad por relación (por ejemplo, `energia:inConcession` es la única que une algo con su concesión). Una propiedad que usan dos clases va sin `rdfs:domain`.
- **Todo se consulta en Ontop**: oncología en :8080, proveedores en :8081, petróleo y gas en :8082. Cada dominio tiene su prefijo (`oncologia:`, `proveedores:`, `energia:`); nunca el prefijo vacío. Ontop no soporta caminos `*` ni `+`: lo que necesite clausura se precalcula en Postgres.
- **Enriquecer** es sumar lo que sabe una fuente de afuera (hoy, Wikidata) por una clave compartida (el LEI), sin perder de dónde vino. Se hace en vivo (una consulta federada, siempre al día) o guardado en Rastro (`energia:Enrichment`, con su fecha y la huella del archivo, para que se pueda consultar sin internet y repetir; hoy lo usa la pregunta 15, no el modelo). No es «aumentar datos» en el sentido de aprendizaje automático (ejemplos sintéticos).
- **Cada enlace es evidencia:** una `prov:Entity` con `prov:wasDerivedFrom` (la fuente) y su regla y evidencia en texto. Las correcciones van en un CSV revisado (`linking/<dominio>/`), con su motivo o su documento; las que revisó un asistente de IA dicen que falta que las confirme una persona.
- **Datos fuera del repo:** las descargas van a `data/raw/`, que no se versiona. El repo guarda scripts. Cada carga se registra en `rastro_meta.load_run`.
- **Secretos solo en `.env`**, nunca en `.env.example` ni en commits. Antes de commitear, revisá que `.env.example` no tenga claves.
- **Textos de la app** en YAML (`app/dominios/*.yaml`, `app/ayuda.yaml`, `app/faq*.yaml`), no en el código. Los números medidos se leen de sus JSON (`layer/<dominio>/resultados.json`, `layer/energia/cambio/*.json`), nunca escritos a mano.
- **Registro:** formal y sin jerga en la vista de negocio («diccionario de negocio», «evidencia»); lo técnico va detrás de «Ver detalles técnicos». En textos visibles, «Rastro deduce / traduce / genera», no el nombre de las herramientas; las herramientas se nombran solo donde se explican.
- **Sin nombres de productos ni empresas comerciales de grafos de conocimiento** en el repo (interfaz, docs, código, commits). Para hablar de interoperabilidad, decir "otras plataformas o herramientas de grafos de conocimiento".
- **Decisiones** en `docs/decisions.md`: una entrada corta por decisión, con el porqué y los números.

## Reglas de medición

- **Las referencias salen de Rastro**, así que la ventaja de Rastro puede ser circular. Antes de publicar un número, adjudicar con los datos de cada fuente las preguntas donde los caminos difieren (`layer/<dominio>/adjudicacion.md`), y hacer las pruebas a ciegas (`docs/preguntas-a-ciegas.md`, `docs/lab-explicaciones-a-ciegas.md`).
- **Tres caminos, siempre:** sin Rastro (B, SQL sobre las fuentes tal como vienen), SQL con los enlaces de Rastro (D, la línea de base justa) y con Rastro (C).
- **Un arreglo después de medir** se vuelve a medir solo en lo afectado y se dice así. Cuando cambia una regla o un dato, se vuelven a ejecutar todas las consultas guardadas (`rerun`).
- **Rastro Lab compara el mismo modelo** con variables de las tablas crudas (A) y de Rastro (B). La precisión solo muestra que no se pierde nada; lo que se mide es la explicación.
- **Rastro Lab no usa el futuro:** la operadora y el tipo de pozo son los del mes en que arrancó; la fractura, la informada hasta ese mes. Lo que llegó después se marca.
- **Lo que carga solo Lab no cambia Layer:** va en su propio esquema, y se confirma volviendo a ejecutar la evaluación.

## Comandos

```bash
docker compose up -d                                   # app :8501, Postgres :5434, Ontop :8080/:8081/:8082, GraphDB :7210
docker compose run --rm energia-loader                 # cargadores: <fuente>-loader (ver README)
docker compose run --rm lab-gas-loader                 # Capítulo IV 2018–2022, fractura y trayectorias, solo para Lab
docker compose run --rm wikidata-energia-loader        # enriquecimiento con Wikidata, guardado (después del enlazador, y otra vez el enlazador)
docker compose run --rm energia-linker                 # enlaces de petróleo y gas (proveedores-linker, linker para oncología)
docker compose restart ontop-energia                   # después de cambiar mapeos, ontología o enlaces
docker compose run --rm ontology-check                 # ontologías y queries de competencia
docker compose run --rm calidad                        # reglas de calidad (SHACL) sobre los datos de petróleo y gas (~3 min)
docker compose run --rm -T layer-eval python /layer/fuera.py energia prompt|guardar|puntaje   # ¿dice cuándo no tiene el dato?
docker compose run --rm -T layer-eval python /layer/evaluar.py energia rerun|puntaje   # evaluación (energia_lab: las preguntas sobre las predicciones)
layer/energia/cambio/cambio.sh registrar               # prueba de cambio (siempre termina en «deshacer»)
layer/energia/cambio/correccion.sh registrar           # una corrección, todos los resultados (~15 min)
layer/energia/cambio/impacto.sh registrar              # qué predicciones cambian si la fuente corrige un registro (~15 min)
python3 lab/gas/modelo.py [<pozo>|--12-meses|--como-trabajo-publicado|--publicar|--comparar]   # Rastro Lab desde la consola
python3 docs/slides/build.py                           # arma los mazos HTML
```

Los scripts de `lab/` y `layer/energia/cambio/correccion.py` corren en la máquina, no en Docker: necesitan Python con `requirements-dev.txt` y Ontop de energía en localhost:8082.

## Skills del repo

- `verificar`: comprobar que todo levanta y responde, en los tres dominios
- `agregar-fuente`: sumar o cambiar un cargador de datos
- `agregar-pregunta`: sumar una pregunta de competencia con su query
- `evaluar`: medir las preguntas con los tres caminos, puntuar y adjudicar
- `rastro-lab`: entrenar, medir y explicar el modelo de gas con y sin Rastro
- `pruebas-de-cambio`: la prueba de cambio y la de la corrección, y dónde se ven
- `mazos`: armar y publicar los mazos y mantener el guion de la demo
- `cerrar-fase`: marcar el plan, documentar y commitear
