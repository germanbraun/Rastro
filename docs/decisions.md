# Decisiones

## 2026-10-15 — Área terapéutica: oncología

Mantiene los volúmenes manejables en una laptop, hay abundantes ensayos en AACT y targets en ChEMBL, y los ejemplos son fáciles de contar en una demo comercial.

## 2026-10-15 — Triplestore: GraphDB Free

Rastro se construye de forma independiente, sobre GraphDB Free. Por usar estándares (RDF, R2RML, SPARQL), se puede conectar después a otras plataformas de grafos de conocimiento sin rehacer ontología, mapeos ni datos.

## 2026-10-15 — Registro de fuentes en Postgres y puertos locales

`rastro_meta.source` y `rastro_meta.load_run` registran cada fuente (licencia incluida) y cada carga. Ontop ya expone las fuentes como `:DataSource`: es la base de la marca de procedencia por celda de la Fase 4 y del linaje PROV-O de la Fase 7.

Puertos por defecto 5434 (Postgres) y 7210 (GraphDB) para no chocar con un Postgres local ni con otra GraphDB local. GraphDB va sin inferencia (ruleset `empty`): la jerarquía de MeSH se recorre con property paths.

## 2026-10-16 — Recorte de AACT a oncología

Se cargan los estudios con algún término de condición bajo *Neoplasms* (MeSH C04) en `browse_conditions`, que ya incluye los ancestros de cada término. El criterio sale de la jerarquía y no de buscar texto, así que es reproducible y explicable.

Se extrae de la base de AACT en la nube (cuenta gratuita) y no del snapshot completo de varios GB. El snapshot sigue como alternativa (`AACT_DUMP`).

Carga del 2026-10-16: 106.483 estudios (83.680 intervencionales), 13 tablas, 4,0 M filas, 1,2 GB. Sin `facilities` ni `outcomes` por volumen; se suman si una pregunta de competencia las necesita.

Para Rastro Lab hay 23.898 ensayos intervencionales con fármaco completados, contra 7.019 terminados y 2.201 retirados: alcanza para la variable objetivo de la Fase 5.

## 2026-10-16 — Subconjunto de ChEMBL desde la API, por familia de moléculas

Se cargan las familias de moléculas (padre y sales) con alguna indicación bajo *Neoplasms* (MeSH C04, 703 descriptores consultados al SPARQL de NLM), con todas sus indicaciones, mecanismos, targets y componentes. Es el mismo criterio que el recorte de AACT.

- **API y no dump:** el dump de ChEMBL 37 pesa 2 GB comprimido y mucho más restaurado, para quedarnos con 270 mil filas. La API da la versión exacta (`ChEMBL_37`), que queda en `rastro_meta.load_run`.
- **Por familia:** ChEMBL registra indicaciones y mecanismos tanto sobre la molécula padre como sobre sus sales (el mecanismo de imatinib está en el mesilato). La resolución de entidades de la Fase 2 trabaja a nivel padre (`parent_chembl_id`).
- **Tablas con nombres de ChEMBL:** se respetan nombres de tablas y columnas del esquema original, pero las claves son los ChEMBL ID porque la API no expone `molregno`.
- **Llaves de enlace ya disponibles:** UNII por UniChem (2.063 familias, para openFDA) y los NCT de las referencias de indicaciones (3.000 familias enlazadas con 32.039 estudios de AACT), además de sinónimos e InChIKey.

Carga del 2026-10-16: 3.739 familias, 4.455 moléculas, 833 targets, 9 tablas.

## 2026-10-16 — openFDA agregado por fármaco, desde la API

Por cada familia de ChEMBL con UNII (2.064) se consulta `drug/event` por sus UNII y se guardan: reportes por año de recepción (totales, serios y con muerte) y las 100 reacciones más reportadas. Nada de reportes individuales: FAERS se usa solo agregado, como dice el plan.

- **Por año:** permite las features de Rastro Lab con datos estrictamente anteriores al inicio de cada ensayo.
- **Cualquier rol:** openFDA no permite exigir que el UNII y el rol de sospechoso estén en el mismo fármaco del reporte, así que se cuentan también los concomitantes. Se aclara en la interfaz.
- **Caché reanudable:** un JSON por fármaco en `data/raw/openfda/`. Sin API key (1000 requests por día) la descarga se completa en varias corridas.
- **Detalle de la API:** en `search`, los espacios hacen de OR/AND. `requests` codifica `+` como `%2B`, que openFDA toma literal y devuelve cero resultados.

Carga del 2026-10-16: 2.064 fármacos consultados, 673 con reportes (625 de los 778 aprobados), 13.558 filas año-fármaco y 65.268 reacciones. Los fármacos en ensayo casi nunca tienen reportes, como es de esperar en FAERS.

## 2026-10-16 — MeSH 2026 en GraphDB, importado por trozos, con conector Lucene

MeSH 2026 completo (15,4 M triples) en el grafo `<http://id.nlm.nih.gov/mesh/2026>` del repositorio `rastro`.

- **Por trozos de 500 mil triples:** importarlo en una sola transacción hacía que el OOM killer de la VM de Docker matara a GraphDB cuando otras pilas (otros triplestores y plataformas) compartían la memoria. Si GraphDB igual se cae, se reinicia solo (`restart: unless-stopped`) y el cargador reintenta el trozo.
- **Carpeta de importación explícita:** GraphDB busca por defecto en `${user.home}/graphdb-import`; se fija `/import`, montada sobre `data/raw/mesh/`.
- **Descarga sin descomprimir:** NLM responde con `Content-Encoding: x-gzip` y `requests` lo descomprime solo; se guardan los bytes crudos.
- **Conector Lucene `mesh`:** indexa descriptores y SCR de enfermedades por etiqueta, sinónimos (concepto → término) y número de árbol (sin analizar, para filtrar por rama, por ejemplo `C04*`). Sirve para normalizar condiciones de texto libre (Fase 6) y resolver nombres en NL→SPARQL (Fase 3).

## 2026-10-16 — Todo simple: es un MVP comercial

Lo tiene que entender alguien de ventas. Se aplica a todas las fases: lo mínimo que funciona para la demo, nombres en palabras de negocio y cada fase cerrando en algo que se ve. Está en `CLAUDE.md` para que guíe todo el trabajo, y el plan se reescribió con esa regla (sin SHACL ni PROV-O por ahora: la procedencia se resuelve con `:fromSource`).

## 2026-10-16 — Ontología mínima (v0.2)

Un primer borrador tenía 13 preguntas y 17 clases. Se recortó a **8 preguntas y 7 clases**: Ensayo, Fármaco, Target, Sponsor, Reportes por año, Reacción reportada y Fuente.

- **Las condiciones son descriptores de MeSH**, sin clase propia. "Cáncer de pulmón y sus subtipos" se resuelve con `meshv:broaderDescriptor*`.
- **Fase y estado como texto**, con los valores de ClinicalTrials.gov (`PHASE3`, `TERMINATED`). Es menos elegante que modelarlos como clases, pero cualquiera lo lee.
- **Fármaco → target directo**, sin reificar el mecanismo.
- **Eventos adversos como conteos**, nunca como reportes individuales.

## 2026-10-16 — Mapeos en R2RML

Los mapeos se escriben en R2RML (estándar W3C, en Turtle) y no en el formato propio de Ontop. Es portable (lo leen Ontop y otras herramientas) y no ata Rastro a un motor. Ontop lee un solo archivo de mapeo, así que va todo en `mappings/rastro.r2rml.ttl`, con una sección por fuente.

## 2026-10-16 — MeSH en Postgres, sin federar

Para que una sola query cruce ensayos (Ontop) y la jerarquía de MeSH (GraphDB) había dos caminos: federar con `SERVICE` o copiar. Se copió a Postgres lo único que hace falta: descriptores (30.512) y su jerarquía (41.809 relaciones). Es chico, y así Ontop responde todo solo. GraphDB queda para MeSH completo y la búsqueda Lucene.

Ontop no soporta caminos de largo arbitrario (`meshv:broaderDescriptor*`), así que se precalculó cada descriptor con todos sus ancestros (`mesh.ancestor`, 245.641 filas) y se expone como `:within`. "Cáncer de pulmón y sus subtipos" queda en una sola línea: `?c :within ?pulmon`. La tabla no se llama `within` porque es palabra reservada de SQL y Ontop no la acepta.

## 2026-10-16 — Enlaces con reglas simples, sin LLM

Los enlaces están en SQL legible en `linking/`:

- **Condiciones:** el término MeSH que trae AACT igual a la etiqueta del descriptor. 99,8 % de los ensayos.
- **Fármacos:** nombre normalizado (minúsculas, sin marca entre corchetes o paréntesis, sin puntuación, sin vía ni forma al final) contra nombres y sinónimos de ChEMBL sin ambigüedad. En orden: nombre, alias, partes de una combinación ("A + B") y un diccionario de 10 regímenes (FOLFOX, R-CHOP…).

Resultado: 74,4 % de las intervenciones enlazadas y 99 de 100 correctas en la revisión de una muestra (hecha con IA, pendiente de revisión humana). El plan preveía un LLM para los casos ambiguos, pero con este nivel no hace falta para el MVP. Lo que no enlaza es sobre todo lo que no es un fármaco ("placebo", "chemotherapy").

## 2026-10-16 — Tipos explícitos en mapeos con GROUP BY o DISTINCT

Ontop no infiere el tipo de una columna calculada con `GROUP BY` o `DISTINCT`. En esos mapeos se declara con `rr:datatype`. Es el error más probable al agregar mapeos nuevos.

## 2026-10-16 — openFDA: buscar también por nombre del principio activo

openFDA deja vacío el bloque `openfda` (donde está el UNII) en muchos reportes. Buscar solo por UNII perdía fármacos enteros: osimertinib (Tagrisso) daba 0 reportes y tiene 32.521. Ahora cada fármaco se busca por sus UNII **o** por el nombre de su principio activo (los nombres de ChEMBL de la molécula y sus sales), en una sola búsqueda con OR, así que ningún reporte se cuenta dos veces. Imatinib pasó de 41.417 a 61.334 reportes.

## 2026-10-16 — Fase 3: tres formas de responder, comparación justa

El mismo modelo responde las mismas 20 preguntas de tres formas: solo, con SQL sobre las tablas crudas y con SPARQL sobre Rastro.

- **Lo que recibe cada una:** B recibe el esquema de las tablas de AACT, ChEMBL, openFDA y MeSH, más una página de notas (qué es cada fuente y cómo se escriben sus valores); no ve los enlaces de `linking/`. C recibe la ontología y una página de notas equivalente. Es lo que tendría un equipo de datos con y sin Rastro.
- **Seguridad:** B corre con un usuario de Postgres de solo lectura (`rastro_reader`) y un límite de 60 segundos por query.
- **Mismas reglas:** mismo modelo y esfuerzo, salida en JSON con esquema, y hasta tres intentos si la query falla (el modelo ve el error).
- **Referencias:** las respuestas correctas salen de queries SPARQL escritas a mano sobre Rastro. Las definiciones (qué es "detenido", "fase 3", "activo") van dentro de cada pregunta para que cualquier enfoque pueda responderla. Para "ensayos de X", AACT ya trae los ancestros MeSH de cada ensayo, así que B también llega a los subtipos (difiere de Rastro en un 0,4 %).
- **Puntaje:** un número es correcto a menos del 5 % de la referencia; una lista, con al menos 80 % de coincidencia (F1), comparando fármacos por sinónimos de ChEMBL.
- **Respuestas guardadas en el repo** (`layer/eval/results.json`): se paga una sola vez. Otra persona puede ver y puntuar los resultados sin API key.
- **Claude Opus 5.5** no acepta `temperature`. La reproducibilidad viene de guardar las respuestas, no de fijar la temperatura.

## 2026-10-16 — Respuestas generadas con subagentes de Claude Code

No había API key de Claude. Las 60 respuestas (20 preguntas × 3 enfoques) se generaron con subagentes de Claude Code (el mismo modelo, Claude Opus 5.5), cada uno con contexto limpio: leía solo su prompt, el mismo texto que enviaría `answer.py` a la API, y respondía el JSON pedido. Sus queries se ejecutaron con `manual.py` y, si fallaban, el subagente recibía el error con el mismo mensaje que usa la versión con API. B necesitó un reintento en 3 preguntas (las tres por tiempo límite); C respondió todo al primer intento.

El LLM es intercambiable (`RASTRO_PROVIDER`): Claude API, Ollama en la Mac, o a mano con `manual.py`.

## 2026-10-16 — La evaluación mejoró Rastro: adjudicar antes de publicar

Como las referencias salen de Rastro, la ventaja de C podía ser en parte circular. Se revisaron con ensayos reales las preguntas donde B y C diferían (`layer/eval/adjudication.md`). B tenía razón en varios casos, y eso llevó a corregir Rastro:

- **Regla "nombre como palabra entera"** para dosis, separadores y texto libre ("Pembrolizumab 200 mg", "Nivolumab or Pembrolizumab"): 94 % de precisión en una muestra revisada con IA, cobertura de 74 % a 81 % de las intervenciones.
- **El nombre preferido de ChEMBL gana sobre los sinónimos de otros fármacos.** ChEMBL lista "bicalutamide" como sinónimo de talazoparib, y eso dejaba sin enlazar todos los ensayos con bicalutamida.
- **Prodrogas:** ChEMBL trata a la abiraterona y su acetato como familias distintas. Ahora una prodroga actúa sobre los targets de su molécula activa (`active_chembl_id` de ChEMBL).
- **Una pregunta ambigua** (q08, ¿"fase 2" incluye 1/2 y 2/3?) se reescribió y se volvió a responder. Con la definición clara, SQL directo y Rastro coinciden.

Resultado final: LLM solo 5/20, SQL directo 18/20, Rastro 20/20.

Regla para el futuro: ningún número de la evaluación se publica sin adjudicar las diferencias.

## 2026-10-16 — Demo en Streamlit, que funciona sin LLM

La interfaz es Streamlit (`app/`), lo más simple para un MVP: un solo archivo de Python, sin frontend aparte. Se levanta con `docker compose up` en el puerto 8501.

- **Funciona sin LLM:** las preguntas de ejemplo usan las queries que el LLM escribió en la evaluación, ejecutadas en vivo sobre los datos. Las preguntas libres usan el LLM configurado (Claude API u Ollama).
- **Fuente por columna:** se deduce de la query. Una columna que sale de `:reports` viene de openFDA, y una que sale de `:name` sobre un fármaco, de ChEMBL. No hace falta anotar los datos.
- **"Con y sin Rastro"** muestra el puntaje y las tres respuestas de cada pregunta, con el largo de cada query: el argumento visual de la demo.

## 2026-10-16 — Cómo leer 18 contra 20

El SQL directo con un LLM fuerte acierta casi tanto como Rastro. El argumento de venta no es la precisión, sino la confianza: definiciones consistentes entre preguntas (el SQL directo reconoce los fármacos de 4 formas distintas), errores que no avisan, el costo de integrar pagado en cada pregunta (20 s contra 2 s, 3 reintentos contra 0) y procedencia por dato. La demo lo dice así, con números, y explica por qué falla cada respuesta incorrecta.

## 2026-10-16 — Mostrar el SQL que genera Ontop

"¿De dónde sale la respuesta?" muestra la consulta del LLM, el SQL que Ontop genera y ejecuta (`/ontop/reformulate`, disponible en modo desarrollo) y las fuentes. Hace visible que Rastro no copia datos: traduce la pregunta a SQL sobre las tablas originales y los enlaces, con uniones simples. En la comparación, ese SQL queda al lado del que el LLM escribió a mano.

Cada fuente lleva un ícono según dónde vive: 🐘 Postgres (AACT, ChEMBL, openFDA, enlaces de Rastro) y 🕸️ GraphDB (MeSH completo, con su jerarquía copiada en Postgres).


## 2026-10-16 — Posicionamiento: el valor es la integración revisada

Rastro acierta porque la parte difícil (qué ensayo prueba qué fármaco) se resolvió una vez, con reglas explícitas, y se revisó sobre muestras. Si al SQL directo le diéramos las mismas tablas de enlaces, probablemente acertaría casi todas. El mensaje honesto es: **el valor de Rastro es la integración revisada, expuesta como un vocabulario de negocio**. La capa semántica la hace estable ante cambios de tablas, autodocumentada, estándar y con procedencia por dato. La demo lo explica así en "Por qué Rastro acierta".

Pendiente, si se quiere medir: un cuarto enfoque, "LLM + SQL sobre las tablas de Rastro", para separar cuánto aporta la integración y cuánto la capa semántica.

## 2026-10-16 — Las explicaciones van en Preguntas frecuentes

La demo se mantiene corta: cada pestaña muestra lo esencial y una línea que manda a "Preguntas frecuentes". Las explicaciones viven en `app/faq.yaml`, una pregunta y una respuesta corta por entrada, editable sin tocar código. Los números de las respuestas (reintentos, tiempos, formas de reconocer un fármaco) los completa la app desde la evaluación guardada, así que no quedan desactualizados.

## 2026-10-16 — Hacer visible la unificación de columnas de los mapeos

Una parte central de la capa semántica es que columnas distintas que significan lo mismo terminan en el mismo concepto: openFDA identifica un fármaco con `query_id`, ChEMBL con `chembl_id` y los enlaces con `parent_chembl_id`, y los mapeos los unen en un solo `:Drug`. Rastro ya lo hacía, pero no se veía. Ahora:

- una pregunta frecuente lo explica con una tabla **generada desde `mappings/rastro.r2rml.ttl`**, que no se desactualiza cuando cambian los mapeos;
- el diagrama "Cómo responde cada forma" (`app/como-funciona.svg`, en la pestaña de comparación) lo menciona en la capa de Ontop.

Las condiciones usan los identificadores de MeSH, así que un descriptor en Postgres y el mismo en GraphDB son la misma entidad.

## 2026-10-16 — Rastro es un Virtual Knowledge Graph (VKG)

Se adopta la terminología del tutorial *Designing Virtual Knowledge Graphs with Ontop and Ontopic Studio* (Calvanese, Cogrel y Lanti, Ontobras 2022, https://www.inf.ufrgs.br/ontobras/wp-content/uploads/2022/11/ontobras-2022-tutorial-vkgs.pdf):

- **Rastro es un VKG** (también llamado OBDA): una ontología con el vocabulario del dominio, mapeos declarativos a las fuentes y un grafo virtual, con los estándares del W3C (RDF, OWL, R2RML, SPARQL).
- **Cuatro tipos de heterogeneidad**: de modelo de datos y de sistema (los resuelven los cargadores), de esquema (ontología y mapeos) y de datos (entity linking). La demo lo explica así en "Preguntas frecuentes".
- **Es un VKG pragmático:** las fuentes se cargan en Postgres (ETL) y los enlaces y la jerarquía de MeSH están precalculados. Sobre eso, el grafo es virtual.

## 2026-10-16 — Las referencias de la evaluación las hizo una IA

Las 20 preguntas, sus respuestas de referencia, la adjudicación y la revisión de enlaces las hizo Claude Code, no una persona. Los números salen de ejecutar queries y de un puntaje automático, pero si la referencia está mal, el puntaje también. Por eso los documentos dejan de decir "revisado a mano" y dicen que falta la revisión humana, hasta completar `docs/verificacion-humana.md` (una hora, sin conocimientos técnicos). Al revisar el control contra la web de ClinicalTrials.gov apareció que la web da 15-30 % más que Rastro en conteos por enfermedad, porque busca con sinónimos propios: conviene tenerlo listo si un cliente compara.

## 2026-10-17 — La demo es para consultores que saben SQL

La audiencia son consultores que saben SQL y no conocen tecnologías semánticas. Su primera pregunta va a ser «¿por qué no vistas SQL?». Por eso la demo compara todo con SQL y suma dos evidencias que el puntaje de 18 contra 20 no mostraba:

- **Consistencia:** la misma pregunta escrita de 4 formas. Con SQL directo la respuesta cambia en 9 de 10 preguntas; con Rastro, en ninguna (`layer/consistencia/`).
- **Cambio:** una versión nueva de AACT simulada. Un cambio de nombre rompe 5 consultas del SQL directo y en Rastro se arregla con una línea; un cambio de formato deja 5 respuestas en 0 sin aviso, y el control de vocabulario de Rastro lo detecta (`layer/cambio/`).

También se simplificó todo: 9 diapositivas en lugar de 13, 14 preguntas frecuentes en lugar de 22, y un guion con la comparación con SQL en el centro.

## 2026-10-17 — La línea de base justa cambia el mensaje

Siguiendo una revisión externa, se agregó un enfoque más: SQL sobre las fuentes más las tablas de enlaces de Rastro, documentadas. Acertó 20 de 20, fue tan consistente como Rastro (10 de 10) y resolvió las 5 preguntas de 3 o 4 cruces. Su consulta es tan corta y tan rápida como la de Rastro.

Conclusión: **la precisión viene de integrar una vez, no de SPARQL.** El mensaje comercial pasa a ser «integramos una vez y lo mantenemos como una capa estándar», con tres ventajas medidas de la capa semántica sobre las tablas solas: el cambio de una fuente se arregla en un lugar (también con SQL + enlaces se rompen 5 consultas), cada dato trae su fuente, y una consulta une Rastro con Wikidata en vivo (`layer/externo/`). Se dice de entrada que una capa de vistas SQL resolvería parte de esto.

Para que Wikidata acepte las consultas federadas, GraphDB se identifica con `-Dhttp.agent`.

## 2026-10-17 — Clases de fármaco y razonamiento en Ontop

Para mostrar que el conocimiento vive en el modelo, se sumaron clases de fármaco según ATC (`linking.drug_class`, con un mapeo por clase) y la clase «terapia dirigida» sin mapeo: Ontop aplica las reglas de la ontología (OWL 2 QL, `rdfs:subClassOf`) y genera el SQL con las dos clases. Cambiar la definición es una línea de la ontología. La prueba con 3 preguntas no mostró diferencia de precisión con el SQL con enlaces, que tenía la misma definición documentada.

## 2026-10-18 — Evidencia de cada enlace, con PROV-O

La procedencia por columna se puede imitar en SQL con el nombre del esquema. Lo que convence es la evidencia por registro: por qué Rastro dice que un ensayo prueba un fármaco. `linking.trial_drug` guarda ahora también el texto de la intervención, y un mapeo nuevo expone cada enlace como `:DrugLink` (subclase de `prov:Entity`) con el texto, lo que coincidió, la regla, `prov:wasDerivedFrom` AACT y ChEMBL, y `prov:wasGeneratedBy` el entity linking. La app lo muestra en «¿Por qué?».

## 2026-10-18 — Dos niveles: negocio por defecto, técnico si se pide

Todo era demasiado complejo para quien no conoce estas tecnologías. Regla nueva: un mensaje («integrás una vez, preguntás en lenguaje de negocio, cada respuesta se puede auditar») y tres pruebas (misma respuesta, cambios en un lugar, evidencia). Sin jerga en la capa principal: «diccionario de negocio» en lugar de ontología, «traducciones» en lugar de mapeos, «evidencia» en lugar de procedencia o PROV-O. La app arranca en modo negocio y tiene «Ver detalles técnicos»; el mazo tiene 6 diapositivas y un anexo; el guion, el one-pager y las preguntas frecuentes tienen versión para todos y versión técnica. Nada técnico se borró.

## 2026-10-18 — Segundo dominio: proveedores del Estado de EE. UU.

Para mostrar que Rastro sirve para cualquier dominio, con un caso de negocio que entiende cualquiera (compras, riesgo, compliance), se suma un segundo dominio en la misma app: contratos federales de EE. UU. de más de US$10 millones del año fiscal 2025 (36.147), sus proveedores y grupos, y las listas de control del gobierno. Se eligió EE. UU. porque sus datos son los más abiertos (todas las fuentes, sin clave). Tiene los mismos ingredientes que oncología: nombres de empresas escritos de varias formas (entity linking), jerarquías (grupo → filiales, sector → subsectores) y evidencia. Cada dominio tiene su propio Ontop, con su ontología y su archivo de mapeos.


## 2026-10-19 — Proveedores, P0: datos cargados

Cuatro cargadores nuevos, un esquema por fuente en el mismo Postgres (`data/<fuente>/`, servicios `<fuente>-loader`):

| Fuente | Tablas | Filas |
|---|---|---|
| USAspending | `contract`, `recipient`, `recipient_parent` | 36.145 contratos, 8.380 proveedores, 14.071 matrices (actuales e históricas) |
| NAICS 2022 | `sector`, `ancestor` | 2.125 sectores, 8.952 filas de ancestros |
| Lista Consolidada | `entry` | 26.154 entradas de 12 listas |
| GLEIF | `name_query`, `candidate`, `lei_record` | 3.626 nombres buscados, 8.743 candidatos, 2.610 registros LEI |

- **Recorte:** contratos (tipos A, B, C y D) con actividad en el año fiscal 2025 y monto total de más de US$10 millones: 36.147 según la API, que suman US$4,6 billones. «Monto» es el total del contrato en toda su vida, no lo obligado en 2025: la búsqueda por contrato de USAspending no da lo del año. Llegaron 36.145: la paginación ordena por monto y dos contratos se pierden en empates entre páginas.
- **Proveedores:** un perfil por proveedor distinto (8.383) con la matriz actual y la lista de matrices que tuvo. Tres perfiles devuelven siempre error 502 y quedan afuera. La API corta conexiones si se le pide rápido: el cargador usa 2 hilos, guarda cada respuesta en `data/raw/usaspending/` y se puede volver a correr. La primera carga tardó unas tres horas.
- **Caso conocido verificado:** el proveedor SCIENCE APPLICATIONS INTERNATIONAL CORPORATION (UEI MMLKPW9JLX64) tiene como matriz actual a SAIC (RE7WMNV9L719) y, en su historia, a LEIDOS HOLDINGS (ZL41ERXMPAR3).
- **NAICS:** el Census publica la jerarquía solo en Excel; se lee con la biblioteca estándar para no sumar dependencias. Los sectores agrupados (31-33, 44-45, 48-49) son el padre de sus códigos de 3 dígitos. 2.218 contratos usan códigos de versiones anteriores a 2022 (por ejemplo 541712); se resuelve en P1.
- **Lista Consolidada:** el `_id` se repite entre listas (la misma entidad en SDN y SSI), así que la clave es `(id, source)`.
- **GLEIF, limitado:** se buscan las matrices con contratos por US$50 millones o más (3.260, el 98 % del monto) y los 1.000 proveedores que más facturan; buscar las 7.355 matrices llevaría horas con el límite de 60 consultas por minuto. Se usa `filter[fulltext]`, que también mira nombres anteriores, y se guardan los 5 primeros candidatos con su matriz final, sin decidir el enlace (es P2). 1.533 nombres no tienen ningún resultado. El caso SAIC muestra la trampa: para «SCIENCE APPLICATIONS INTERNATIONAL CORPORATION», GLEIF pone primero a LEIDOS, INC. (ese era su nombre anterior) y segunda a la SAIC de hoy.

## 2026-10-19 — Proveedores, P1: diccionario, mapeos y segundo Ontop

- **Un Ontop por dominio:** `ontop-proveedores` (puerto 8081) lee `ontology/proveedores/proveedores.ttl` y `mappings/proveedores.r2rml.ttl`. El Ontop de oncología no cambia. El diccionario usa su propio espacio de nombres (`https://w3id.org/rastro/proveedores#`).
- **Nueve preguntas**, cada una con la ventaja que muestra en palabras simples (`ontology/proveedores/competency-questions.md`). Se sumó la 9, «proveedor para revisar», para tener una regla de negocio deducida por Ontop como «terapia dirigida» en oncología. Las 1, 2, 3, 6 y 8 responden ya, en menos de un segundo; las 4, 5, 7 y 9 necesitan los enlaces de P2.
- **Tablas precalculadas** en el esquema `proveedores` (`linking/proveedores/entities.sql`, servicio `proveedores-linker`): proveedor, grupo, agencia, proveedor → grupo con su evidencia, y sectores con sus ancestros. Los mapeos no usan GROUP BY ni DISTINCT.
- **Códigos NAICS viejos:** los 2.218 contratos con códigos anteriores a 2022 (58 códigos) suman US$452.000 millones. Cada código viejo cuelga de su prefijo más largo que existe en 2022 (541712 queda dentro de 54171 y de 54), así «dentro de un sector» no los pierde.
- **Hallazgo: USAspending fragmenta los grupos.** Su «matriz actual» reparte a Leidos en seis matrices distintas (LEIDOS HOLDINGS, LEIDOS, INC., LEIDOS INC…), así que la pregunta 1 da seis grupos. Se resuelve en P2 con la matriz final de GLEIF; es la heterogeneidad que la capa tiene que resolver y un buen ejemplo para la demo.
- `ontology/check.py` acepta la carpeta de un dominio: `docker compose run --rm ontology-check python /ontology/check.py /ontology/proveedores`.

## 2026-10-19 — Proveedores, P2: enlaces con su evidencia

Todo en SQL legible (`linking/proveedores/links.sql`), cada enlace con el texto de cada fuente, lo que coincidió y la regla, expuesto con PROV-O (`:GroupLink`, `:LeiLink`, `:WatchlistLink`). Las nueve preguntas responden contra el segundo Ontop, en menos de medio segundo.

- **Nombre normalizado:** mayúsculas, sin puntuación y sin formas societarias (Inc., LLC, Corp., Ltd., PLC…).
- **Proveedor o matriz → LEI:** solo entre los candidatos que devolvió GLEIF para ese nombre. Reglas, de más fuerte a más débil: nombre legal y estado; nombre legal y país; nombre anterior y estado; nombre legal sin ubicación en USAspending (solo entidades activas). Gana la más fuerte; si empatan dos LEI distintos, no se enlaza. Resultado: 563 proveedores y 535 matrices con LEI. Así se resuelve SAIC: el nombre legal de la SAIC de hoy le gana a LEIDOS, INC., que solo coincide por su nombre anterior, y la evidencia dice qué se descartó.
- **Grupo consolidado:** USAspending fragmenta los grupos (Leidos en seis matrices). Si la matriz tiene LEI, el grupo pasa a ser su matriz final en GLEIF: 7.302 grupos, 482 con LEI. Leidos queda con 21 empresas y US$54.700 millones.
- **No se usa la historia de matrices para sumar.** Sin fechas, no se distingue una compra de una escisión, y metería a la SAIC de hoy en Leidos (332 contratos, US$34.300 millones). Límite conocido: 1.341 proveedores figuran como su propia matriz y tienen otra en su historia (Dynetics, QTC y Gibbs & Cox, hoy de Leidos, entre ellos); se ve en la evidencia y queda para una revisión manual.
- **Lista de control:** nombre o alias igual, normalizado, contra entradas que son empresas (sin personas, barcos ni aviones). 8 proveedores coinciden; en todos los que se pueden comparar, la entrada es de otro país, y la regla lo dice. Son homónimos: un «ninguno confirmado» bien respaldado.
- **Wikidata por LEI:** cargador nuevo (`data/wikidata/`): de 2.610 LEI, 353 están en Wikidata y 236 cotizan en bolsa. 201 grupos tienen Wikidata y 137 cotizan.
- **«Proveedor para revisar»** se deduce en Ontop de dos clases mapeadas: matriz final fuera de EE. UU. (147 proveedores) y coincidencia con una lista (8).
- **Precisión de proveedor → LEI:** muestra al azar de 50, revisada por un asistente de IA (`linking/proveedores/review-2026-10-19.md`): 46 seguros, 3 probables (la misma empresa con otra forma societaria) y 1 dudoso (nombre genérico, otro estado). Entre 92 % y 98 %. Falta que la confirme una persona.
- **Detalle de Ontop:** `matched` es palabra reservada para su lector de SQL y rompe los mapeos con consulta; en las tablas de enlaces la columna se llama `matched_text`.

## 2026-10-19 — Proveedores, P3: con y sin Rastro, con números

El mismo método que oncología, en `layer/proveedores/`: las 9 preguntas respondidas por subagentes de Claude Code (Claude Opus 5.5) que solo ven el prompt, sin Rastro (SQL sobre las fuentes tal como se cargaron) y con Rastro (SPARQL sobre el segundo Ontop).

- **Correctas:** sin Rastro 5 de 9, con Rastro 8 de 9. Sin Rastro fallan las que unen USAspending con GLEIF (p04, p07, p09): cada consulta toma el primer candidato de GLEIF sin verificarlo. Con Rastro falló p05: el diccionario no decía que algunas listas dejan vacío el tipo de entrada (se corrigió el comentario, sin volver a correr la prueba).
- **Consistencia** (5 preguntas × 4 formas): misma respuesta en 3 de 5 sin Rastro y 4 de 5 con Rastro. En una forma, el SQL siguió las matrices históricas y le sumó a Leidos US$41.000 millones de SAIC.
- **Cambio:** si USAspending renombra la columna de la agencia, sin Rastro se rompen 3 consultas y con Rastro falla todo junto, en voz alta, y se arregla con una línea del mapeo. Si los montos pasan a miles de dólares, las dos dan 3 respuestas distintas sin error; Rastro avisa con un control del recorte (todos los contratos superan US$10 millones) y se arregla con una línea. Resultado en `layer/proveedores/cambio/resultado.json` (el de oncología sigue en `layer/cambio/`).
- **Adjudicación** (`layer/proveedores/adjudicacion.md`): la referencia sale de Rastro y se queda corta en p01 (Dynetics, QTC y Gibbs & Cox son de Leidos y no están en el grupo) y en p04 (Leonardo, Bombardier y Deloitte Consulting Limited tienen matriz extranjera y Rastro no las enlazó). El número publicable es la diferencia de método, no un «Rastro siempre acierta».
- **`answer.py` por dominio:** lo propio de cada dominio (endpoint, diccionario, notas, usuario de solo lectura, fuente de cada término) pasó a `layer/dominios.yaml`. Cada función recibe el dominio y, si no se dice, usa oncología: los prompts de oncología quedaron idénticos (comprobado).
- Al correr 8 subagentes a la vez, dar permisos en cada llamada chocaba («tuple concurrently updated») antes de ejecutar la consulta; no se perdió ningún intento y ahora se ignora ese choque.

## 2026-10-19 — Proveedores, P4: un selector de dominio en la app

- **Selector de dominio** en la barra lateral (Oncología / Proveedores del Estado de EE. UU.), definido en `app/dominios.yaml`. Oncología sigue con su pantalla de siempre, sin cambios. Proveedores se dibuja con `app/dominio.py`, una pantalla genérica con las mismas tres pestañas y los mismos dos modos (negocio por defecto, técnico con el interruptor).
- **Lo propio del dominio va en configuración** (`app/dominios/proveedores.yaml`): las preguntas en palabras simples y su versión técnica, qué ventaja muestra cada una, el glosario, los nombres de negocio de las columnas, la evidencia de «¿De dónde sale la respuesta?» (una consulta y un formato por pregunta), las tres tarjetas de «Por qué confiar» con sus números tomados de la evaluación y de la prueba de cambio, los escenarios de cambio y las preguntas frecuentes. Sumar un dominio es escribir un YAML así, sin tocar código.
- **Oncología no se migró** a la pantalla genérica: funciona y tiene detalles propios (evidencia por fármaco, escenarios de Wikidata y de definición de negocio). Queda para cuando haga falta.
- **Arreglos que aparecieron al probar:** la barra lateral de oncología listaba también las fuentes de proveedores (su mapeo lee todo `rastro_meta.source`; se filtra en la app, sin tocar el mapeo); las fuentes de una respuesta no contaban los términos dentro de caminos como `:supplier/:group` (se corrigió en `answer.py`, también mejora oncología); dos «US$» en un mismo texto Streamlit los toma como fórmula (se escapa `$`).
- Probado en el navegador: los dos dominios, los dos modos, «¿De dónde sale la respuesta?», «Por qué confiar» y las preguntas frecuentes.

## 2026-10-19 — Proveedores, P5: el segundo dominio en la demo

- **Tres diapositivas** después de las 6 de oncología y antes del anexo (`docs/slides/slides/dominio2.html`, `leidos.html`, `pruebas2.html`; sección nueva en `deck.json`): la misma idea con otros datos, el ejemplo de Leidos (grupo de 21 empresas y US$54.700 millones; sin Rastro, una consulta sumó US$41.000 millones de SAIC; la evidencia de por qué) y las tres pruebas con los números de P3, con lo que encontró la adjudicación. Mismo estilo; ninguna se sale de 1920×1080. Las de oncología no cambiaron.
- **Guiones:** una parte opcional de 2 minutos en `docs/demo-guion.md` (cambiar el dominio, la pregunta de Leidos y «¿De dónde sale la respuesta?» de SAIC) y su versión técnica en `docs/demo-guion-tecnico.md`.
- **One-pager:** una línea con el resultado en el segundo dominio (8 de 9 contra 5 de 9), y una fila en la versión técnica.
- Se eligieron 3 diapositivas y no 4: con el ejemplo y las pruebas alcanza para mostrar que Rastro sirve en otro dominio; el detalle queda en la app y en el anexo.

## 2026-10-19 — Preguntas sobre textos: GraphRAG anclado en la capa semántica

La pregunta «¿esto es GraphRAG?» va a aparecer. La respuesta: Rastro es la parte estructurada y auditable; para texto, el grafo elige con una consulta exacta qué registros importan y un LLM resume solo esos textos, con cita de cada registro. No se arma un grafo desde texto con un LLM: iría contra el argumento principal (exacto, revisado, auditable). Primer ejemplo: los 26 ensayos de fase 3 de cáncer de pulmón con inhibidores de quinasa que se detuvieron y tienen motivo escrito, agrupados en 7 motivos (`layer/textos/detenidos-pulmon.json`). El resumen lo hizo un asistente de IA leyendo los 26 textos y está guardado; los textos se leen en vivo del grafo (`:whyStopped`).


## 2026-10-19 — Proveedores: las filiales y las matrices que faltaban

La adjudicación de P3 encontró que Rastro se quedaba corto en el grupo Leidos y en algunas matrices extranjeras. Se arregló con reglas simples, a la vista:

- **Dos búsquedas más en GLEIF** (`data/gleif/load.py`): si ningún candidato coincide con el nombre, se busca otra vez con el nombre normalizado (la forma societaria tapaba a la empresa: «LEONARDO S.P.A.» traía otras S.P.A.) y, para los grupos de US$250 millones o más, por nombre legal. Suman 90 matrices y 150 proveedores con LEI (ahora 625 y 713). La normalización también saca S.P.A., S.R.L., S.A.S., PTY y SE.
- **LEI revisados** (`data/gleif/lei-revisados.csv`): LEONARDO S.P.A. y BOMBARDIER INC, que ninguna búsqueda encuentra (en GLEIF son «LEONARDO - SOCIETA' PER AZIONI» y «BOMBARDIER INC.»). Su LEI se pide directo y le gana a cualquier regla.
- **Correcciones revisadas de grupo** (`linking/proveedores/correcciones.csv`, 9 filas): empresas que hoy son de un grupo y que ni USAspending ni GLEIF ponen ahí. Criterio: USAspending tiene a la matriz en la historia del proveedor y lo confirma su nombre o una compra pública (Dynetics, QTC, Gibbs & Cox, 1901 Group, Leidos Security Detection & Automation, Leidos Management Systems Designers, dos «LEIDOS, INC.» que USAspending pone bajo la SAIC nueva) o GLEIF (Austal USA, que USAspending pone bajo COMPUTERSHARE LIMITED, un registro de acciones). El motivo queda en la evidencia del enlace. Kudu Dynamics y Aranea Solutions tienen a Leidos solo en su historia: quedan pendientes de revisión.
- **El ejemplo de Leidos cambia:** 30 empresas de 13 matrices de USAspending, 611 contratos, US$63.400 millones (antes 21 empresas y US$54.700 millones). Proveedores con matriz extranjera: 173 (antes 147). DELOITTE CONSULTING LIMITED (Tanzania) no está en GLEIF y no se cuenta.
- **P3 con los datos nuevos:** las consultas guardadas se volvieron a ejecutar, sin pedirle nada nuevo al LLM. Con Rastro sigue 8 de 9; sin Rastro baja a 4 de 9, porque su total de Leidos queda un 11 % por debajo del grupo real. La consistencia no cambia (3 de 5 y 4 de 5). La consulta 4 repetía contratos cuando el grupo y el proveedor llevaban a la misma matriz final; se corrigió.
- Se actualizaron los números en las diapositivas, los guiones, los one-pagers, la app y las preguntas de competencia.

## 2026-10-19 — Proveedores: la línea de base justa da lo mismo que en oncología

Como en oncología, el mismo LLM respondió las 9 preguntas con SQL sobre las fuentes más las tablas de enlaces de Rastro (esquema `proveedores`), documentadas con lo mismo que dice el diccionario (`layer/proveedores/sql-enlaces-notes.md`, usuario `proveedores_reader_links`). Subagentes que solo ven el prompt, los mismos 3 intentos, sobre los datos ya corregidos.

| | Sin Rastro (SQL) | SQL + enlaces de Rastro | Con Rastro |
|---|---|---|---|
| Correctas (de 9) | 4 | **8** | **8** |
| Misma respuesta en las 4 formas (de 5) | 3 | 3 | 4 |

- **El mismo mensaje que en oncología:** con las tablas de enlaces, el SQL acierta lo mismo que Rastro. La precisión viene de integrar una vez. Falla en la misma pregunta (p05) y por la misma razón: filtra las entradas de tipo «Entity» y deja afuera las que no traen tipo.
- **Consistencia:** las diferencias son chicas. En p01, una forma filtró los grupos por nombre («leidos») y sumó un *joint venture*, como hizo Rastro en tres formas; en p05, una forma unió mal dos columnas y dio 0.
- **Lo que suma la capa semántica**, como en oncología: la integración se mantiene en un lugar (la prueba de cambio no se repitió con esta línea de base: en oncología, las consultas con tablas de enlaces se rompían igual que las de SQL directo), la evidencia de cada enlace y los datos de afuera.
- Se muestra en la app (modo técnico, «Por qué confiar»), en `layer/proveedores/README.md`, en el plan, en la diapositiva de las pruebas del dominio, en el one-pager técnico y en el guion técnico.

## 2026-10-19 — El motivo de detención, de texto a dato del grafo

El resumen de la IA sirve para leer; para contar hace falta un dato. El motivo que escribió el sponsor (12.611 ensayos detenidos) se clasifica con reglas legibles en SQL (`linking/stop_reasons.sql`, 12 motivos más «otro»), como el entity linking: explicable, repetible y sin costo por consulta. Un ensayo puede tener varios motivos. Antes de buscar se sacan las negaciones («no safety concerns» no es un problema de seguridad), con una regla más estrecha para eficacia, para no borrar «did not meet efficacy goals».

Queda en el grafo como `:stopReason` del ensayo, y su evidencia como `:StopReasonLink` (subclase de `prov:Entity`): el texto que coincidió, la regla, `prov:wasDerivedFrom` AACT y `prov:wasGeneratedBy` la clasificación. Se usaron propiedades propias (`:aboutTrial`, `:evidenceText`) porque `:linkTrial` y `:matchedText` tienen dominio `:DrugLink` y Ontop habría deducido que cada motivo es un enlace de fármaco.

Medición (`linking/review-stop-reasons-2026-10-19.md`, revisada por un asistente de IA): en una muestra independiente de 50, 45 de 49 motivos asignados correctos (92 %) y 42 de 50 ensayos con al menos un motivo correcto (84 %). Alrededor del 19 % queda como «otro», con su texto a la vista. Con los 26 ensayos del resumen de la IA, las reglas coinciden en los 26 (después de ajustarlas con ellos: es optimista).


## 2026-10-19 — Proveedores: una pregunta sobre textos (Leidos)

El mismo GraphRAG anclado que en oncología, en el dominio de proveedores: «¿En qué trabaja el grupo Leidos para el gobierno?». El grafo elige con una consulta exacta los 40 contratos más grandes del grupo (`layer/proveedores/textos/leidos.rq`), con todas sus empresas; un asistente de IA agrupó sus descripciones en 12 temas citando cada contrato (`leidos.json`). Los contratos y montos se leen en vivo; el resumen está guardado.

Por qué con el grafo y no buscando en los textos: de esos 40 contratos, solo 1 nombra a Leidos en su descripción, y 7 son de empresas del grupo con otro nombre (QTC, Dynetics, Mission Support Alliance). Una búsqueda por texto no los encuentra, no puede elegir «los más grandes» y podría traer contratos de la SAIC de hoy. No se convirtió en dato del grafo (temas clasificados): por ahora alcanza con el resumen citado.

Para que se vea, la app compara en vivo con una búsqueda por texto (`leidos-texto.rq`: «Leidos» en la descripción o en el nombre de la empresa, como haría alguien con SQL o un buscador). Encuentra 33 de los 40 contratos del grupo: pierde 7 (5.607 millones de dólares, de QTC, Dynetics y Mission Support Alliance) y dos temas enteros. Se eligió una búsqueda por palabra y no un RAG con vectores: muestra lo mismo sin otra dependencia, y cualquiera puede leer la consulta.

## 2026-10-19 — La demo en tres momentos: integración, trazabilidad y análisis de textos

La demo tenía demasiadas piezas para recordar. Ahora son tres momentos, todos con el grupo Leidos, y cada uno termina en la misma tarjeta: sin Rastro a la izquierda, con Rastro a la derecha.

- **Integración:** US$56.400 M buscando «Leidos» en los nombres (faltan QTC, Dynetics, Gibbs & Cox y 1901 Group, US$7.700 M, y entra un consorcio que no es del grupo) contra US$63.400 M con el grupo de Rastro.
- **Trazabilidad:** US$97.800 M cuando el SQL siguió las matrices viejas y sumó US$41.400 M de la SAIC de hoy, contra US$63.400 M con Rastro y la evidencia de por qué.
- **Análisis de textos:** 33 de 40 contratos buscando en los textos, contra 40 de 40.

Los números «sin Rastro» de los dos primeros salen de la evaluación (`layer/proveedores/resultados.json`, SQL sin enlaces) y están guardados en `app/dominios/proveedores.yaml`; los del tercero se calculan en vivo. La app tiene un modo **Demo en 3 pasos** con «Siguiente», para no elegir preguntas en vivo. El mazo principal quedó en ocho diapositivas, con oncología en una; las pruebas y oncología completa pasaron a «Si preguntan».


## 2026-10-19 — Un registro más formal

El texto visible (app, diapositivas principales y guion) pasó a un registro formal e impersonal: «Los datos cambian. Las preguntas, no.», «¿De dónde sale la respuesta?» en lugar de «¿Cómo lo supe?», imperativos con usted y sin expresiones coloquiales («pedazos», «trampa», «no alcanza»). Las notas del orador (`<aside>`), que no se ven en pantalla, conservan un tono más conversacional.

## 2026-10-19 — Tercer dominio: petróleo y gas en Argentina

Para operadoras y consultoras del sector. Dos fuentes públicas de la Secretaría de Energía: la producción declarada de 2025 pozo por pozo y el padrón de pozos (Capítulo IV, CC-BY 4.0), y el servicio de mapas (WFS) con las concesiones, sus socios y los venteos de gas. Un tercer Ontop (puerto 8082), su ontología (`ontology/energia/`) y sus mapeos (`mappings/energia.r2rml.ttl`).

- **2025 y no 2026:** el archivo de 2026 trae solo 21 operadoras (falta, por ejemplo, Pan American Energy). El de 2025 tiene 69 operadoras, 83.172 pozos y unos 803.000 barriles por día, lo que coincide con la producción nacional.
- **El WFS:** la dirección pública devuelve siempre el documento de capacidades; los datos salen de la dirección que ese documento anuncia (`/mapserv?map=...`). El certificado viene sin la cadena completa, así que se descarga sin verificarlo: son datos públicos de solo lectura.
- **Tres momentos, como en proveedores:** producción por participación (YPF opera 21,4 M m³ y le corresponden 12,6), quién opera cada pozo (padrón 12.006, declaraciones 15.809; rige la declaración del último mes, con el padrón a la vista en 7.453 pozos en desacuerdo) y posibles venteos por satélite ubicados en su concesión (6.636 de 6.887 desde 2024).
- **Nombres de empresas:** se unen por nombre normalizado (sin acentos, puntuación ni forma societaria) y, donde eso no alcanza, con correcciones revisadas (`linking/energia/correcciones.csv`): CGC, Chevron y Pluspetrol. Las revisó un asistente de IA; falta que una persona las confirme.
- **Punto dentro de polígono en Python** (`linking/energia/link.py`): Postgres no tiene PostGIS acá y son 300 contornos. Se guarda la concesión de cada punto, con su evidencia.
- **Sin evaluación medida todavía:** los números «sin Rastro» salen de SQL directo y legible (`layer/energia/sin-rastro.sql`), no de un LLM. La pestaña «Por qué confiar» no se muestra en este dominio hasta que haya una evaluación.
- **Referencia:** una tesis de la UTDT usa los mismos datos abiertos para predecir la productividad de pozos de shale gas en Vaca Muerta; es un antecedente para un paso de predicción (Rastro Lab), no para esta demo.

## 2026-10-19 — PROV-O visible en la evidencia

Ocho tipos de enlace son entidades PROV-O (`prov:Entity`, con `prov:wasDerivedFrom` y `prov:wasGeneratedBy`): `:DrugLink` y `:StopReasonLink` en oncología; `:GroupLink`, `:LeiLink` y `:WatchlistLink` en proveedores; `:Stake`, `:OperatorLink` y `:CompanyName` en petróleo y gas. Se suma `:LocationLink` (en qué concesión cae cada venteo), que antes era solo un texto del venteo. Las consultas de evidencia ahora piden la fuente con `prov:wasDerivedFrom`, y la app dice «entidad PROV-O» solo cuando la consulta la usa.

## 2026-10-19 — Petróleo y gas: tres fuentes más (ENARGAS, IGN, GLEIF)

Para que el dominio no dependa de un solo organismo:

- **ENARGAS:** los 303 tramos de gasoductos de transporte, servidos por el mismo WFS. Para cada concesión, la distancia de su contorno al gasoducto más cercano (`:PipelineLink`). 29 concesiones con posibles venteos tienen el más cercano a 10 km o más (un primer conteo dio 38 porque siete concesiones tienen dos polígonos en el mapa y se contaban dos veces; ahora hay una fila por concesión). No incluye los ductos internos de cada yacimiento: es una pista, no una conclusión.
- **IGN (listado en IDERA):** 3.528 localidades (BAHRA) y 506 áreas protegidas. Para cada posible venteo, la localidad más cercana y si cae en un área protegida (`:SurroundingsLink`): 60 caen en áreas protegidas y 61 a menos de 3 km de una localidad.
- **GLEIF:** el LEI de las 40 empresas que más producen, buscado por nombre en Argentina y aceptado solo si coincide el nombre legal normalizado (`:LeiLink`, guarda lo descartado): 12 empresas. En su propio esquema (`gleif_energia`), porque el cargador de proveedores borra el esquema `gleif`.
- **Los grupos no salen de un registro:** GLEIF no registra la matriz de ninguna de estas empresas argentinas, las sociedades de Chevron no tienen LEI y Wikidata no tiene esas relaciones. Chevron, Pluspetrol y CGC siguen siendo correcciones revisadas.
- Distancias con una aproximación plana en km, en Python (`linking/energia/link.py`), sin PostGIS.

## 2026-10-19 — Un mazo por caso de uso

Un solo mazo mezclaba tres dominios. Ahora hay tres (`docs/slides/mazos/`), con la misma estructura: qué es Rastro, el dominio, las preguntas, la demo en tres momentos, por qué confiar, consideraciones y un anexo con arquitectura, diccionario y por qué funciona. Comparten las diapositivas genéricas; las que nombraban datos de un dominio tienen una versión por mazo. El de petróleo y gas no tiene diapositiva de GraphRAG ni de pruebas medidas: todavía no hay una fuente de textos ni una evaluación. Publicados: proveedores en el enlace de siempre y dos mazos nuevos para petróleo y gas y para oncología.

## 2026-10-19 — Petróleo y gas: evaluación medida, GraphRAG, «Explicame la consulta», logo y favicons

- **Evaluación medida** (`layer/energia/resultados.md`), con el mismo protocolo que proveedores: 66 respuestas de subagentes que solo vieron el prompt. Correctas: Rastro 6 de 7, sin Rastro 5 de 7, SQL + enlaces 7 de 7. Misma respuesta en 4 formas: 5 de 5, 3 de 5 y 5 de 5. Sin Rastro no pudo medir distancias a gasoductos (se le acabó el tiempo) y contó mal los venteos en áreas protegidas (las partes de un área con varios polígonos). Rastro falló la participación de YPF en las 4 formas: el diccionario tiene `:concession` e `:inConcession` y el LLM eligió mal; queda como debilidad a corregir. La adjudicación (`layer/energia/adjudicacion.md`) encontró además un error de Rastro: las concesiones sin gasoducto a menos de ~100 km no tenían distancia; se corrigió y se volvieron a ejecutar las consultas. `layer/evaluar.py` ahora sirve para cualquier dominio, y la consistencia compara números salvo redondeo (no cambió proveedores).
- **Prueba de cambio** (`layer/energia/cambio/`): con una columna renombrada, sin Rastro se rompen 2 consultas; con el petróleo en barriles, una da 79 millones de m³ en lugar de 12,6 sin avisar, y Rastro avisa con un control de unidades. En este dominio el arreglo es una línea de `linking/energia/links.sql` (los mapeos leen las tablas de enlaces).
- **GraphRAG anclado**: una fuente nueva, los estudios ambientales de la Secretaría de Energía (12.957, unidos por nombre de concesión con evidencia en `:StudyLink`). El grafo elige las cinco concesiones con más posibles venteos y sus 72 estudios desde 2022; el resumen guardado cita cada estudio (`layer/energia/textos/venteos.json`).
- **«Explicame la consulta»**: en la vista técnica, un botón explica la consulta y el SQL en palabras de negocio. Las preguntas de ejemplo traen su explicación guardada (la app no tiene un LLM configurado); las propias se explican en vivo si hay uno.
- **Logo** (`app/logo.svg`): un rastro de puntos unidos, que también es un pequeño grafo. En la app y en las portadas de los tres mazos.
- **Favicons junto a las empresas**: `app/sitios.yaml` (lo arma `layer/sitios.py`: Wikidata para los grupos de proveedores y una lista revisada por IA para el resto). La app pide cada ícono una vez al servicio de favicons de Google, en el servidor, porque la tabla no dibuja imágenes de otro sitio; sin internet, la columna queda vacía.

## 2026-10-19 — Petróleo y gas: una sola propiedad para «en la concesión»

El diccionario tenía `:concession` (la producción) e `:inConcession` (participaciones, venteos, enlaces y estudios). En la evaluación, Rastro falló la participación de YPF (e01) en las 4 formas: el LLM unió la participación con la concesión por `:concession` y dio 0.

- **Arreglo:** queda solo `:inConcession`, con un comentario que dice que es la única propiedad que une algo con su concesión, y una línea igual en `layer/energia/sparql-notes.md`. Cambiaron el mapeo, `cq1.rq` y la referencia de e01; todas las consultas del dominio y las de evidencia de la app dan lo mismo que antes, y la referencia de e01 sigue en 12.581.213 m³.
- **Es un arreglo hecho después de medir.** Se volvieron a medir solo las 4 respuestas de Rastro de e01, con subagentes nuevos que solo vieron el prompt; las viejas se descartaron. Las 4 dieron 12.581.213.
- **Antes y después (Rastro):** correctas 6 de 7 → 7 de 7; misma respuesta en 4 formas, 5 de 5 (antes las 4 daban 0, igual de mal) → 5 de 5; correctas en la prueba de consistencia, 16 de 20 → 20 de 20. Sin Rastro y SQL + enlaces no se tocaron (5 de 7 y 7 de 7).
- **Cómo leerlo:** el 7 de 7 es después de corregir el diccionario con la pregunta a la vista; las otras seis no se volvieron a medir. Lo que muestra es que un error del diccionario se arregla en un lugar y vale para todas las formas de preguntar, no que Rastro acierte todo a la primera.

## 2026-10-19 — Consola SPARQL y petróleo y gas como dominio de inicio

- **Consola SPARQL** en la vista técnica de los tres dominios: un editor que arranca desde cualquier consulta de ejemplo, ejecuta sobre el Ontop del dominio y muestra el resultado y el SQL que generó Ontop. Dice también la dirección del endpoint (`http://localhost:8080`, `8081`, `8082`/sparql) para usarlo desde otras herramientas.
- **La app abre en petróleo y gas** (el primero de `app/dominios.yaml`).

## 2026-10-19 — «Así se ve un dato del grafo»

Para que se entienda qué es una instancia: en la vista técnica (pestaña «Consola SPARQL») se elige una entidad real de ejemplo (una concesión, una empresa, una participación con su evidencia, la operadora de un pozo, un venteo y dónde cae; un grupo, un proveedor y su enlace; un fármaco, un ensayo y su enlace) y se ven todas sus propiedades, cada una con su nombre en el diccionario de negocio, y la misma entidad en Turtle. Cada mazo suma una diapositiva de anexo con un enlace real y su evidencia, generada desde los datos.

## 2026-10-19 — Petróleo y gas: mapa y «concesión para revisar»

- **Geometrías en el grafo, con el estándar de OGC (GeoSPARQL, `geo:asWKT`):** los contornos de las concesiones, los puntos de venteo y el trazado de los gasoductos de ENARGAS (`:Pipeline`). La app dibuja el mapa leyendo solo de Rastro (pydeck), y cualquier herramienta de mapas puede leer lo mismo.
- **«Concesión para revisar» (`:ConcessionToReview`)**, una clase sin mapeo que Ontop deduce de dos reglas escritas una vez (`linking/energia/links.sql`, `energia.concesion_revisar`): posibles venteos desde 2024 y el gasoducto más cercano a 10 km o más (33), o 20 o más posibles venteos y ninguna planilla de venteo presentada desde 2022 (21). 45 concesiones, 9 con las dos. Pregunta nueva (e08), en el mapa en rojo y en una diapositiva. Es un indicio, no una conclusión; el umbral de 20 es una decisión de negocio.
- **Duplicados de venteos:** los venteos se unían con la tabla del mapa, que tiene siete concesiones con dos polígonos; quedaban 131 filas repetidas (7.959 en lugar de 7.828). Ahora se unen con `energia.concesion`, una fila por concesión. Las respuestas medidas contaban puntos distintos y no cambian.

## 2026-10-19 — Un prefijo con nombre por dominio

Cada dominio ya tenía su propio espacio de nombres, pero las consultas lo usaban con el prefijo vacío (`:Supplier`, `:Trial`), y en la demo no se veía de qué dominio era cada término.

- **Ahora se escribe `proveedores:Supplier`, `oncologia:Trial` y `energia:Well`**, en ontologías, mapeos, consultas, notas para el LLM, la app y las diapositivas. Petróleo y gas pasó en un segundo paso, después del trabajo sobre la historia de operadoras.
- **Oncología cambia de espacio de nombres:** `https://w3id.org/rastro/ontology#` pasa a `https://w3id.org/rastro/oncologia#`, igual que los otros dos (`proveedores#`, `energia#`). Los IRI de las instancias (`drug/…`, `trial/…`) no cambian.
- **Las respuestas guardadas de la evaluación se tradujeron con un script** (solo el prefijo y el espacio de nombres; nada más de la consulta). Se volvieron a ejecutar: las 62 consultas de Rastro guardadas corren, y los puntajes no cambian (oncología: Rastro 20 de 20; proveedores y petróleo y gas, igual que antes: en petróleo y gas, Rastro 7 de 7).

## 2026-10-19 — Petróleo y gas: quién operó cada concesión, de 2023 a 2025

Para mostrar los cambios de operadora (por ejemplo, las áreas maduras que YPF vendió).

- **Datos:** las declaraciones juradas de 2023 y 2024, los archivos completos del Capítulo IV (no los «DDJJ abiertas y cerradas»): 57 y 59 operadoras, 37,4 y 41,2 M m³ de petróleo, años completos como 2025 (69 y 46,6 M m³). Van a su propia tabla (`capitulo4.produccion_historica`) para que `capitulo4.produccion` siga siendo solo 2025 y no cambie ninguna respuesta medida. Los dos recursos de 2024 del catálogo son el mismo archivo.
- **Regla:** cada mes, la operadora de una concesión es la empresa que declara la mayor parte de su producción (petróleo en m³ más gas en miles de m³, que en energía equivalen más o menos; `energia.operador_area_mes`). Hay cambio cuando otra empresa la declara al menos 3 meses seguidos: un mes suelto no cuenta (`energia.cambio_operadora`, `:OperatorChange`, con evidencia). Antes y después: lo que producía la concesión por mes, en promedio, con cada operadora.
- **Resultado:** 55 cambios; 25 son áreas que dejó YPF (Pecom, Petróleos Sudamericanos, Bentia, Quintana, Venoil, PCR). Pregunta nueva, e09. Cinco áreas no están en el mapa de concesiones: la consulta muestra su código y la evidencia, el nombre del Capítulo IV.
- **Sin cambios en lo medido:** los nombres de empresa de 2023 y 2024 se suman a `energia.empresa_nombre`; la evaluación (`layer/energia/resultados.json`) da lo mismo, y las consultas guardadas, vueltas a ejecutar, dan las mismas respuestas.


## 2026-10-19 — Pendientes al día

- **Guion de oncología** (`docs/demo-guion-oncologia.md`), con la misma forma que los otros dos. Oncología no tiene «Demo en 3 pasos»: el guion usa la pregunta de ejemplo de HER2 y la pregunta sobre textos.
- **Verificación humana de los tres dominios** (`docs/verificacion-humana.md`, partes 5 y 6): las empresas de Leidos, Austal, los socios de cuatro concesiones, los grupos, los venteos en áreas protegidas, tres LEI, tres cambios de operadora y los resúmenes de textos, con enlaces para comprobar.
- **Un número viejo:** la diapositiva de fuentes de petróleo y gas, el guion y las preguntas de competencia decían 29 concesiones sin gasoducto cerca; desde el arreglo de distancias son 33.
- README y `CLAUDE.md` describen los tres dominios, un mapeo por dominio y un prefijo por dominio.

## 2026-10-19 — Petróleo y gas: el petróleo y el gas se leen de la tabla original, como en oncología

En la prueba de cambio, Rastro seguía en 7 de 7 aunque la fuente renombrara una columna: los mapeos leían la producción ya sumada en una tabla de enlaces (`energia.produccion_pozo`), que no se entera del cambio hasta que se vuelve a armar. No se veía el impacto ni dónde se arregla.

- **Ahora el mapeo lee el petróleo y el gas de `capitulo4.produccion`** (`<#WellProductionAmounts>` en `mappings/energia.r2rml.ttl`), como oncología lee el estado de AACT. Los enlaces siguen haciendo lo difícil: quién declara (el nombre de la empresa unido entre fuentes), el pozo y la concesión. Las respuestas no cambian (Rastro 7 de 7; las consultas guardadas dan lo mismo).
- **La prueba de cambio, medida de nuevo** (`layer/energia/cambio/resultado.json`): con la columna renombrada, sin Rastro se rompen 2 consultas y con Rastro 3; una línea del mapeo deja a Rastro en 7 de 7, y sin Rastro hay que reescribir cada consulta. Con el petróleo en barriles, las dos formas dan 79 millones de m³ en lugar de 12,6, pero Rastro avisa; una línea del mapeo lo arregla.
- **SQL + enlaces** sigue leyendo la tabla de enlaces con la producción sumada, como en la evaluación; la prueba de cambio compara sin Rastro y con Rastro.
- **«Por qué confiar», en la vista técnica:** las tres pruebas (correctas, consistencia y cambios) quedaron en tres pestañas, en los tres dominios. Antes estaban una debajo de la otra, y elegir una pregunta de la evaluación parecía cambiar los escenarios de cambio, que son siempre de todas las preguntas. Los escenarios suman una tabla pregunta por pregunta.

## 2026-10-19 — Cada respuesta nombra las fuentes de las que salen los enlaces

En la demo de petróleo y gas, el paso de integración decía «Fuentes: Capítulo IV, enlaces de Rastro», aunque los socios salen del mapa de concesiones: el enlace tapaba su fuente.

- **`link_sources` en `layer/dominios.yaml`:** para cada término de un enlace de Rastro, las fuentes de las que sale (por ejemplo, la participación sale del mapa; el cambio de operadora, del Capítulo IV; la distancia al gasoducto, de ENARGAS). Cada respuesta nombra esas fuentes y, además, los enlaces de Rastro. Vale para los tres dominios.
- **Nombres de fuente que dicen qué traen:** «Capítulo IV: producción y padrón de pozos» y «Mapas de la Secretaría de Energía: concesiones, socios y venteos por satélite». El paso 2 cruza la producción declarada con el padrón y el paso 3, el contorno de las concesiones con la capa satelital: son dos conjuntos de datos de la misma fuente, y ahora se ve.
- **Seis fuentes, no cinco:** la FAQ, la descripción del dominio, la diapositiva del dominio y el guion no contaban los estudios ambientales. Las notas para el LLM quedan como se midieron.

## 2026-10-19 — Logo de huella, logos de empresas, la misma pregunta en las dos vistas y la instancia como grafo

- **Logo nuevo** (`app/logo_build.py` dibuja `app/logo.svg` y `app/logo-horizontal.svg`): una huella digital hecha de datos, con el centro naranja y las crestas de afuera punteadas, en azul. Rastro es el rastro de cada dato. En la app y en las portadas de los tres mazos.
- **Más logos de empresas:** una filial toma el sitio de su grupo cuando su nombre empieza con el del grupo («BAE SYSTEMS LAND AND ARMAMENTS» → BAE Systems), y se sumaron sitios revisados por IA (a confirmar por una persona) de patrocinadores, proveedores y operadoras conocidos. Si Google no tiene el ícono, se prueba DuckDuckGo. Con logo, en las respuestas: oncología de 18 a 56 de 91 nombres; proveedores, de 98 a 206 de 299; petróleo y gas, de 16 a 24 de 44 (las que faltan son empresas chicas sin sitio confirmado). La búsqueda por nombre en Wikidata quedó afuera: Wikidata limitó las consultas.
- **La misma pregunta con y sin «Ver detalles técnicos»:** el selector mostraba otra redacción en la vista técnica («anomalías térmicas» en lugar de «posibles venteos»), y parecían preguntas distintas. Ahora muestra siempre la pregunta simple; la vista técnica suma debajo su formulación precisa.
- **«Así se ve un dato del grafo», dibujado como grafo** (app y diapositivas): burbujas para las entidades, burbujas naranjas para las clases, rectángulos para los datos simples y flechas con el nombre de negocio. En la app se puede seguir un enlace a otra entidad, sin salir de la app (las IRI se recorren adentro); la tabla y el Turtle quedan debajo. Las diapositivas se dibujan con `docs/slides/grafo_instancia.py`.

## 2026-10-19 — «Diccionario, enlaces y mapeos» en la vista técnica, y nueve preguntas con siete medidas

- **Una pestaña técnica nueva, en los tres dominios:** el diccionario como documentación (clases, relaciones y atributos, con su etiqueta, su descripción y entre qué clases van, leídos del archivo de la ontología, al estilo de WIDOCO, más el dibujo del diccionario); registros reales de las tablas de entity linking que usa la demo en 3 pasos; y los mapeos R2RML de esos pasos, tal como están en el archivo. No se sumó WIDOCO: es una herramienta Java aparte, y la misma lectura se hace con lo que la app ya usa.
- **Nueve preguntas, siete medidas:** petróleo y gas tiene nueve preguntas de ejemplo, pero la evaluación midió las siete primeras; las concesiones para revisar (e08) y los cambios de operadora (e09) se sumaron después. La diapositiva de preguntas lista las nueve y lo aclara, y las tarjetas de «Por qué confiar» dicen «las preguntas medidas».

## 2026-10-19 — Preguntas frecuentes: primero las de todos los casos

Las preguntas generales (qué es Rastro, por qué confiar, qué pasa si una base cambia, qué es cada pieza en términos de SQL, GraphRAG…) estaban solo en oncología, escritas con sus ejemplos y sus números. Ahora están en `app/faq-general.yaml`, con respuestas que valen para los tres casos, y la app las muestra primero en todos los dominios; después vienen las propias de cada caso («De este caso: …»), en la vista simple y en la técnica. Las de oncología con números propios quedaron como preguntas de oncología («En oncología, ¿qué dio la comparación con SQL?»).

## 2026-10-19 — Petróleo y gas: las nueve preguntas medidas, y un arreglo en los cambios de operadora

La app y el mazo mostraban nueve preguntas pero la evaluación medía siete. Se midieron las dos que faltaban, con el mismo protocolo.

- **Preguntas:** e08 (concesiones para revisar: posibles venteos y, además, gasoducto a 10 km o más, o 20+ venteos sin planillas de venteo desde 2022) y e09 (cambios de operadora de 2023 a 2025). Cada una dice su definición, como las otras siete; e09 nombra las tres empresas que cuentan como una sola (Pluspetrol, CGC, GeoPark), como e04.
- **Antes de medir:** cada forma tenía que poder ver los datos. Sin Rastro suma permiso y notas para los estudios ambientales (`ambiental.estudio`) y una línea sobre las declaraciones de 2023 y 2024; SQL + enlaces suma las tablas `energia.estudio`, `concesion_revisar`, `operador_area_mes` y `cambio_operadora`; las notas de SPARQL, una línea sobre `energia:OperatorChange`. Las siete preguntas ya medidas no se volvieron a pedir.
- **Arreglo después de medir:** en e09 el SQL sin Rastro dio 64 y Rastro 55. Se revisó con los datos: los 9 de más son reales, en áreas donde cada mes declara una sola empresa aunque declare cero (YPF → Bentia en Don Ruiz, YPF → PCR en Llancanelo R, ExxonMobil → Pluspetrol en Los Toldos II Oeste). La regla de Rastro descartaba los meses sin producción. Ahora un mes sin producción cuenta si lo declara una sola empresa (no hay ninguno con dos). Se rehicieron las dos tablas, se volvieron a ejecutar las consultas guardadas sin pedir respuestas nuevas, y Rastro y SQL + enlaces dan 64. Con la referencia corregida y sin el arreglo, Rastro habría quedado 8 de 9.
- **Resultado:** Rastro 9 de 9, SQL + enlaces 9 de 9, sin Rastro 6 de 9 (e08 sin respuesta: se le acabó el tiempo calculando distancias, como en e05). Cambios de operadora: 64; 27 son áreas que dejó YPF. Cinco cambios ajustan su producción promedio de antes y después porque ahora cuentan los meses en cero, y Vega Grande cambia un mes antes (09/2024).
- **Dónde se ve:** `layer/energia/resultados.md` y `adjudicacion.md`; las tarjetas de «Por qué confiar» leen los números de `resultados.json`; la diapositiva de pruebas dice 9 de 9 y cuenta el arreglo.

## 2026-10-19 — Petróleo y gas se une con Wikidata por el LEI

Oncología ya unía Rastro con Wikidata en vivo (`layer/externo/`); petróleo y gas no se conectaba a ningún grafo de afuera.

- **Una consulta en GraphDB** (`layer/energia/externo/wikidata.rq`), sin cargar nada: de Rastro, las empresas con LEI y el petróleo que declararon en 2025; de Wikidata, por el mismo LEI (P1278), la sede, la bolsa en la que cotizan, el dueño o la matriz y el sitio web. Resultado guardado en `resultado-2026-10-19.csv`.
- **Solo 3 de las 12 empresas con LEI están en Wikidata con ese LEI:** YPF, Pan American Energy y Pampa Energía. Lo nuevo: YPF y Pampa cotizan en la Bolsa de Nueva York, un dato que no está en ninguna de las seis fuentes. Ninguna tiene dueño o matriz cargados, lo que confirma que los grupos siguen siendo correcciones revisadas.
- **Sin cruce por nombre:** por nombre exacto aparecen Pluspetrol, Tecpetrol, Compañía General de Combustibles y Vista, pero son el grupo y no la sociedad argentina, y Vista tiene dos entradas. Usarlos pediría una revisión; el LEI, no.
- **No es una pregunta de ejemplo:** las preguntas de la app corren en Ontop, que no consulta grafos de afuera. Queda como pregunta frecuente en `app/dominios/energia.yaml` y como diapositiva del anexo (`e-externo`).

## 2026-10-20 — Íconos «?» con ayuda rápida

La app tiene muchos detalles. Cada parte importante suma un ícono «?» que, al pasar el mouse, explica en una o dos oraciones qué se está viendo: el dominio, el tipo de pregunta, cada paso de la demo, «Sin Rastro» y «Con Rastro», las fuentes de una respuesta, cada tarjeta de «Por qué confiar», los escenarios de cambio, el mapa, la consola SPARQL, la instancia, la ontología, el entity linking y los mapeos. Los textos están todos en `app/ayuda.yaml`, para corregirlos en un solo lugar.

## 2026-10-20 — Petróleo y gas: «Datos de afuera (Wikidata)» en la app

La consulta federada con Wikidata (`layer/energia/externo/wikidata.rq`) estaba solo en el repo, una pregunta frecuente y una diapositiva. Ahora es un modo de «Preguntar», visible sin «Ver detalles técnicos»: un dibujo de cómo se unen los dos grafos por el LEI, un botón que la corre en vivo en GraphDB (unos 15 segundos) y, si Wikidata no responde, el resultado guardado el 19 de octubre, con la fecha a la vista. La configuración está en `externo:` de `app/dominios/energia.yaml`, así que otro dominio puede sumarla igual.

## 2026-10-20 — El grafo de cada instancia, dibujado por Rastro

El dibujo automático (graphviz en el navegador) quedaba ilegible: burbujas sin relleno con texto oscuro sobre el tema oscuro, flechas larguísimas y la IRI en el centro. Ahora la app y las diapositivas usan el mismo dibujo, `app/grafo.py`: la entidad al centro con su nombre, cada propiedad alrededor con su nombre de negocio (también las de PROV-O: «se derivó de», «lo generó»), sobre un fondo claro propio que se lee con cualquier tema, y más alto cuando hay muchas propiedades.

## 2026-10-20 — Tablas con texto largo: elegir una fila para leerla completa

Las tablas de la app cortan el texto largo y la celda no tiene scroll. Todas las tablas pasan por `dominio.tabla`: si alguna celda tiene más de 60 caracteres, la tabla deja elegir una fila y muestra, debajo, la fila completa con cada campo en su propia línea; si no, es una tabla común.

## 2026-10-20 — En los textos, Rastro y no Ontop

Ontop es la herramienta de mapeos; quien responde es Rastro. En la app, los mazos y los guiones se dice «Rastro deduce», «Rastro traduce» y «el SQL que generó Rastro», no «Ontop deduce» ni «Rastro (Ontop)». Las herramientas se nombran donde se explican: los diagramas de arquitectura, «Sé SQL. ¿Qué es cada pieza?» y «¿Dónde está cada pieza?».

## 2026-10-20 — Wikidata en petróleo y gas: la parte según socios, no lo declarado

La consulta con Wikidata mostraba el petróleo que cada empresa declara como operadora (YPF: 21,4 millones de m³), justo después de que el paso 1 de la demo dijera que su parte es 12,6. Los dos números son correctos, pero miden cosas distintas. Ahora la consulta trae primero la parte según la participación en cada concesión (el número del paso 1) y, en otra columna con su nombre, lo que declara como operadora. Resultado guardado de nuevo el 20 de octubre; la diapositiva usa la parte.

## 2026-10-20 — «Una pregunta sobre textos», paso a paso

Para que se entienda la idea de GraphRAG anclado en el grafo, la pregunta sobre textos se muestra en pasos numerados, en los tres dominios: 1, la pregunta; 2, el grafo elige con una consulta exacta (cuántos registros, y la consulta en la vista técnica); 3, la IA lee solo esos textos (que se pueden abrir); 4, el resumen, con las citas de cada tema; 5, comprobar. En oncología, un paso 6: el motivo pasa a ser un dato del grafo, contado sin IA.

De paso: los escenarios de «Por qué confiar» dividían por las 9 preguntas medidas, pero la prueba de cambio de petróleo y gas usó 7; ahora cada escenario divide por las preguntas que tiene.

## 2026-10-20 — Petróleo y gas: la prueba de cambio con las nueve preguntas

La prueba de cambio se había grabado cuando había siete preguntas medidas, y la app seguía mostrando «de 7». Se volvió a correr (`layer/energia/cambio/cambio.sh registrar`) con las nueve: con la columna del petróleo renombrada, sin Rastro se rompen 3 consultas (antes 2: se suma la de cambios de operadora) y Rastro falla en 3 hasta que se arregla una línea del mapeo, después 9 de 9. Con el petróleo en barriles, las dos formas dan otro número; Rastro avisa y, con una línea, vuelve a 9 de 9.

## 2026-10-20 — La demo en 3 pasos explica por qué esos pasos

Cada paso de la demo dice qué es (integración, trazabilidad, cruce con mapas o análisis de textos) y qué muestra, y arriba hay un «¿Por qué estos 3 pasos?»: uno por cada cosa que hace Rastro y que una consulta hecha a mano no hace sola. Los textos están en `demo_porque` y en cada paso de `demo` (`que_es`, `muestra`) de `app/dominios/*.yaml`.

## 2026-10-20 — Cobertura de la evidencia, medida

«Cada respuesta se puede auditar» decía «Sí». Ahora es un número, de `layer/evidencia.py`: qué porcentaje de los enlaces entre fuentes guarda su fuente, su regla y su texto (PROV-O), y cuántas columnas de las respuestas a las preguntas de competencia dicen de qué fuente salen. Petróleo y gas: 107.795 de 107.795 enlaces, 34 de 34 columnas. Proveedores: 9.108 de 9.108, 41 de 41. Oncología: 112.461 de 112.461 enlaces ensayo → fármaco, 28 de 28 columnas (una consulta no se pudo analizar y queda afuera). Los motivos de detención «Otro motivo» (2.447) no tienen texto que coincidió, porque ninguna regla coincidió: es el resultado, no un hueco.

**Un error encontrado al medir:** los 303 tramos de gasoducto de ENARGAS salían también como «enlaces» (`energia:PipelineLink`), porque `energia:pipelineOperator` tenía ese dominio y el gasoducto lo usa. Se le quitó el dominio; ahora hay 293 enlaces, todos con evidencia, y las consultas dan lo mismo.

**Una prueba que no se hizo:** comparar con cambios reales entre los archivos de 2023, 2024 y 2025 del Capítulo IV. No hay cambios para medir: el esquema es el mismo (2024 suma una columna `id`) y solo 3 nombres de empresa de 2023–2024 no están en 2025, ninguno de una empresa que siga activa.

## 2026-10-20 — «¿Por qué este número?» y lo que cuesta no integrar

- **«¿Por qué este número?»**: debajo de una respuesta se elige una fila y se ve la evidencia que hay detrás, dibujada como grafo (la fila al centro, cada enlace alrededor) y en una tabla con la fuente y la regla. Configurado en las preguntas de la demo: la parte de cada empresa, concesión por concesión, con el texto de socios del mapa (e01); los posibles venteos de una concesión, con dónde cae cada punto (e03); y las empresas de un grupo, con la regla y la evidencia de cada una (p01). Se suma a otra pregunta con `porque:` en `app/dominios/*.yaml`.
- **Lo que cuesta no integrar**, en el paso 1 de petróleo y gas: sin integrar, a YPF se le asignan 8,8 millones de m³ de más (55 millones de barriles), unos US$ 3.600 millones con un precio supuesto de US$ 65 por barril. El precio es un supuesto y se dice; la diferencia en m³ no.

## 2026-10-20 — Menos pestañas, y el protocolo de las preguntas a ciegas

- **Pestañas:** «Demo en 3 pasos» (cuando el dominio la tiene), «Preguntar», «Por qué confiar» y «Preguntas frecuentes»; en la vista técnica, una sola más, «Bajo el capó», con la consola SPARQL, una instancia del grafo, el diccionario, los enlaces y los mapeos. Antes la demo era un modo de «Preguntar» y la vista técnica sumaba dos pestañas.
- **Preguntas a ciegas** (`docs/preguntas-a-ciegas.md`): el protocolo para que alguien del sector, sin ver Rastro, escriba de 5 a 10 preguntas; se miden con el mismo protocolo y no se arregla el diccionario antes de publicar. Corta la circularidad de que las preguntas y las referencias las armemos nosotros. Falta la persona.

## 2026-10-20 — «¿Por qué este número?» en todas las preguntas que lo admiten

Además de e01, e03 y p01: en petróleo y gas, los pozos de YPF por regla con lo que dice cada fuente (e02), el no convencional por formación (e04), el gasoducto más cercano (e05), el entorno de cada posible venteo (e06), el LEI (e07), los motivos para revisar con su evidencia (e08) y el cambio de operadora (e09); en proveedores, las empresas del grupo (p02, p03), los enlaces de un proveedor con su grupo y su LEI (p04, p08), la coincidencia con una lista de control (p05), de dónde sale que un grupo cotiza en bolsa (p07) y los proveedores para revisar de un organismo (p09); en oncología, cómo se reconoció el fármaco de una fila en los ensayos, en toda respuesta con fármacos. Queda afuera p06, que es un solo número sin filas.

## 2026-10-20 — Petróleo y gas: dos participaciones corregidas por la verificación humana

La verificación humana (parte 6a) encontró 2 de 4 participaciones del mapa desactualizadas:

- **La Amarga Chica:** el mapa la reparte entre YPF y Petronas E&P Argentina (50 % cada una), y es correcto: Petronas E&P Argentina sigue siendo la titular. Pero Vista compró el 100 % de esa empresa en abril de 2025. Se agregó como corrección de grupo (Petronas E&P Argentina → Vista) en `linking/energia/correcciones.csv`, con la fuente de la compra. Para 2025 completo se cuenta en Vista, aunque los primeros meses y medio eran de Petronas; se dice.
- **Aguada Pichana Este:** el mapa la reparte en partes iguales (27,27 % para Total, Wintershall e YPF; 18,18 % para Pan American). El Acuerdo Marco de la Legislatura de Neuquén (8 de septiembre de 2026, Anexo IV, páginas 28 y 29) dice Total 55 %, Wintershall 22,5 %, YPF 16,9 % y Pan American 5,6 %. Se agregó `linking/energia/participaciones-revisadas.csv`: si una concesión tiene participaciones revisadas, reemplazan a las del mapa, con el documento como evidencia y la regla «corrección revisada con documento».

**El efecto:** la parte de YPF pasa de 12.581.213 a 12.570.093 m³ (Aguada Pichana Este es de gas y produce poco petróleo) y Vista sube a 7,0 millones con la mitad de La Amarga Chica. Se volvieron a ejecutar las consultas guardadas: la referencia de e01 cambia y las tres formas siguen dentro de la tolerancia, así que los puntajes no cambian. Sin Rastro, el SQL sigue leyendo el mapa: no puede saber de estas correcciones, que viven en un solo lugar en Rastro.

## 2026-10-20 — Petróleo y gas: el gas, a la vista

Rastro tenía el gas de cada pozo, pero la app casi solo mostraba petróleo (el gas aparecía en los cambios de operadora y en una instancia). En Vaca Muerta el gas pesa tanto como el petróleo, y varias concesiones son de gas (Aguada Pichana Este, Fortín de Piedra).

- **Participación con petróleo y gas:** la pregunta de participación muestra las dos partes (YPF: 12,6 millones de m³ de petróleo y 12.300 millones de m³ de gas), y «¿Por qué este número?» las muestra por concesión.
- **Una pregunta de gas (e10):** quiénes declaran más gas de shale en 2025. Se midió con el mismo protocolo (subagentes que solo ven el prompt): sin Rastro, SQL con enlaces y con Rastro aciertan las tres; es una pregunta sin cruces difíciles. La evaluación pasa a 10 preguntas: sin Rastro 7 de 10, SQL con enlaces 10 de 10, con Rastro 10 de 10.
- **El tipo de pozo** (`energia:wellType`): Petrolífero, Gasífero, de inyección…, tal como lo declara la empresa en su última declaración de 2025. El cargador ahora guarda la columna `tipopozo` del Capítulo IV, que antes descartaba. 43.231 pozos petrolíferos y 6.606 gasíferos.

## 2026-10-20 — Petróleo y gas: la producción, fila por fila y rápida

Desde que el mapeo lee el petróleo de la tabla original (para que la prueba de cambio muestre el impacto), cada consulta sumaba el millón de filas de 2025 y calculaba una clave al vuelo: la participación tardaba 18 segundos y, al sumar el gas, su «¿Por qué este número?» no terminaba en 5 minutos (la app quedaba cargando).

- **Cada fila de la declaración jurada es una producción** (pozo, mes, concesión y empresa), leída tal cual de `capitulo4.produccion`, sin sumar antes. La tabla tiene esa clave única; con ella, Rastro une el petróleo, el gas y la concesión de cada fila sin cruzar la tabla consigo misma.
- **Las tablas de enlaces tienen su clave** (participación, empresa, nombres de empresa, concesión): Rastro ya no quita repetidos en cada consulta.
- **Resultado:** la participación, de 18 a 8 segundos (4 sin la columna de lo que declara como operadora); su «¿Por qué este número?», de más de 5 minutos a 1 segundo; el gas de shale y el no convencional, 1 segundo. Las respuestas no cambian (se volvieron a ejecutar todas las consultas guardadas).
- **La prueba de cambio sigue igual de visible:** la línea que lee el petróleo (`prod_pet AS petroleo_m3`) es la que se rompe al renombrar la columna y la que se arregla.

## 2026-10-20 — Petróleo y gas: los pozos de YPF por tipo, y la app sin espera al abrir

- **Trazabilidad por tipo de pozo:** el paso 2 decía «15.809 pozos» sin aclarar que son de todo tipo, y parecía que eran solo de petróleo. Ahora la pregunta 2 los separa por tipo (5.391 petrolíferos, 1.394 gasíferos, 1.318 de inyección, 7.579 de otro tipo) y aclara que 5.689 produjeron petróleo o gas en 2025. «¿Por qué este número?» muestra los pozos de cada tipo.
- **La app abre sin esperar:** las respuestas se guardan en disco y valen mientras no cambien los datos (cargas registradas, tablas de enlaces) ni el mapeo o la ontología; al abrir, la app prepara en segundo plano las preguntas de los dominios y los íconos de las fuentes. Tras reiniciar, la primera carga pasó de más de 20 segundos a menos de 4.

## 2026-10-20 — Rastro Lab en petróleo y gas: explicar el gas de Vaca Muerta

Estudio sin modelo (`docs/lab-gas-vaca-muerta.md`, consulta en `lab/gas/pozos-nuevos.sql`). El centro de Rastro Lab es la **explicabilidad**; lo segundo, la robustez ante cambios de la fuente; la precisión solo muestra que no se pierde nada.

- **Qué aporta Rastro y qué no:** el peso de cada variable lo calcula una técnica estándar (SHAP), igual con o sin Rastro. Rastro aporta que cada variable sea un concepto del diccionario con fuente, regla y evidencia, que se agrupe por concepto, el «¿qué pasaría si…?» en términos de negocio y la marca de datos dudosos. No vuelve transparente al modelo.
- **Tres pasos:** explicaciones sin fractura, lado a lado «Sin Rastro / Con Rastro»; la fractura como fuente nueva (credibilidad y robustez con dos versiones); la precisión en una línea. Guardar las explicaciones en el grafo queda para después.
- **Medida:** prueba a ciegas con un consultor (20 explicaciones mezcladas), trazabilidad por variable y predicciones con datos dudosos (hoy 96 de 245 pozos de gas nuevos).
- **Datos:** 245 pozos de gas nuevos de 2023 a 2025 (223 con 6 meses); objetivo, el gas de los meses 2 a 7. La fractura es pública, diaria y se une por pozo (237 de 245).
- **Cambio previo a la capa:** la operadora y el tipo de pozo de Rastro son los de diciembre de 2025; para un modelo eso es usar el futuro. Hacen falta los del mes de inicio.

## 2026-10-20 — Rastro Lab, paso 1: el inicio de cada pozo y el mismo modelo dos veces

- **El inicio de un pozo** (`energia:WellStart`, tabla `energia.inicio_pozo`): primer mes con producción, quién lo declaró ese mes y con qué nombre, tipo de pozo, formación y concesión. Para predecir un pozo nuevo, la operadora de hoy sería usar el futuro. Se descartan los pozos que ya estaban en enero de 2023. 2.263 pozos nuevos, 244 de shale gas de Vaca Muerta. `energia:aboutWell` pierde su dominio, porque ahora la usan dos clases.
- **El modelo es una regresión lineal**, no un modelo de árboles con SHAP: con pocos pozos predice igual de bien y el aporte de cada variable sale exacto, en millones de m³. La operadora y la concesión entran como categorías. La historia de cada operadora calculada pozo por pozo (sin usar el futuro) se probó y predecía peor que la mediana: en 2023 casi ningún pozo tiene anteriores con 7 meses.
- **Resultado:** A y B, error medio 16,7 millones de m³ y R² 0,44 en 49 pozos de 2025 (la mediana de la operadora, 17,7). Como validación, sin citarla en Lab: una tesis con las mismas fuentes y datos de fractura reporta R² 0,47 para la mediana por área y 0,75 para su mejor modelo, así que 0,44 sin fractura es razonable.
- **La distancia al gasoducto queda afuera** del paso 1: repite la concesión y salía al revés.
- **Trabajos relacionados en la app,** no en Lab: en las preguntas frecuentes generales (grafos de conocimiento virtuales; grafos de conocimiento para explicar aprendizaje automático) y en las de petróleo y gas (la tesis).
- **En la app, una pestaña «Rastro Lab»** en petróleo y gas (`app/lab.py`): el mismo modelo con y sin Rastro y la explicación de un pozo lado a lado, con «¿Por qué?» en cada variable. El modelo vive en `lab/gas/modelo.py` y la app lo lee montado en `/lab`. La regresión está escrita con numpy (la misma fórmula de ridge) para no sumar una dependencia a la app. Los datos y los dos modelos se guardan en disco como las respuestas, y se preparan al abrir la app.

## 2026-10-21 — Rastro Lab: explicaciones respaldadas por Rastro

- **El gas que se predice está en Rastro** (`energia:gasMonths2to7`, `energia:gasFirst12Months` del inicio de cada pozo, sumando sus formaciones). B lo lee de Rastro y A lo calcula con SQL; coinciden en todos los pozos.
- **Un solo factor en la explicación:** con estos datos, operadora y socios son fijos dentro de cada concesión, así que el modelo aprende un efecto por concesión y repartirlo en tres variables era arbitrario (la concesión llegó a «restar» con pozos por encima del promedio). La explicación con Rastro dice ese factor, por qué suma o resta (sus pozos de entrenamiento y su mediana) y los hechos de Rastro que lo respaldan (operadora, socios, cambios de operadora), cada uno con «¿De dónde sale?». La de A sigue mostrando las tres columnas, que es lo que da una herramienta estándar sobre las tablas crudas.
- **«Qué aprendió el modelo»:** una tabla por concesión con su operadora y socios de Rastro, sus pozos, su mediana y su efecto.
- **El R² de 0,44 es el mejor caso:** según el corte va de 0,06 a 0,44, y con 12 meses no valida. Lo dice la app y el estudio; el paso 2 suma años y fractura.

## 2026-10-21 — Rastro Lab, paso 2: más años del Capítulo IV y datos de fractura

- **Un cargador aparte** (`data/lab-gas/`, `lab-gas-loader`): el Capítulo IV de 2018 a 2022 en su propio esquema (`capitulo4_anterior`) y los datos de fractura como fuente nueva (`fractura`). Así no cambia nada de Rastro Layer: se volvieron a ejecutar las consultas de la evaluación de petróleo y gas y dan lo mismo. El enlazador crea esas tablas vacías si no se cargaron.
- **`energia:Fracturing`:** la fractura de cada pozo, sumando las fracturas informadas hasta el mes en que arrancó (las de después no se sabían). La empresa que informa se une a las demás por su nombre, como en las otras fuentes. `energia:declaredName` pierde su dominio porque la usan el inicio del pozo y su fractura.
- **El inicio de cada pozo va desde 2018** cuando están los años anteriores. Los pozos sin fractura usan el promedio de entrenamiento: no suman ni restan.
- **Resultado:** R² 0,45 hacia el futuro (antes 0,44). La fractura agrega poco al predecir pozos nuevos.
- **Validación con el diseño de otro trabajo con las mismas fuentes:** la línea de base coincide (0,45 contra 0,47). Su R² de 0,75 sale de separar la prueba tomando uno de cada cinco pozos en orden cronológico y de más variables; hacia el futuro, ese trabajo informa 0,25 y nosotros 0,30 con un modelo de árboles. No se suma un modelo de árboles a la app: el objetivo de Rastro Lab es la explicación, y la lineal se explica sola.
- **Las consultas del modelo filtran primero los pozos de shale gas de Vaca Muerta:** con 2018 a 2022, la de las tablas crudas pasó de más de un minuto a 9 segundos.

## 2026-10-21 — Rastro Lab: cuándo llega cada dato, y lo que entra al modelo

- **La prueba de cambio en Lab es la fractura que llega tarde,** no dos días de la fuente (la del 21 de octubre era igual a la del 20). Medido: en 36 de 43 pozos de 2025, la fractura se cargó después de que el pozo arrancó; cuando llega, la predicción cambia 4,8 millones de m³ en promedio. Rastro guarda cuándo se cargó cada fractura (`energia:loadedOn`, de `fecha_data` de la fuente) y la explicación lo marca. Se descartó simular un cambio de unidad: agrega piezas y la fractura tardía es un caso real.
- **«Lo que entra al modelo»:** la tabla de entrada de los dos modelos, como la respuesta en Rastro Layer. Con Rastro, cada columna dice de qué concepto y de qué fuente sale.

## 2026-10-21 — La demo en cuatro momentos, solo petróleo y gas, y una corrección que llega a todo

- **La app abre solo en petróleo y gas.** Proveedores y oncología se ven con «Ver detalles técnicos», como prueba de que el mismo Rastro sirve para otros datos. No se borró nada.
- **La demo pasa de tres pasos a cuatro momentos, una frase cada uno:** preguntar (participación, con evidencia), la base cambia (una columna renombrada: sin Rastro 3 consultas rotas que hay que encontrar; con Rastro, una línea), predecir (Rastro Lab) y una corrección. Trazabilidad y venteos quedan en «Preguntar» y en el anexo del mazo. El mazo de petróleo y gas tiene 7 diapositivas para la historia y el resto en el anexo; el guion dura 3 minutos.
- **Una corrección, todos los resultados** (`layer/energia/cambio/correccion.sh`): se saca la participación corregida de Aguada Pichana Este, se rearma Rastro, se mide y se vuelve a poner. Cambian solas la respuesta de participación de YPF (12,58 → 12,57 millones de m³, con Rastro y con SQL sobre Rastro), lo que entra al modelo (27,27 % → 55 %) y su explicación (aparece la marca). Sin Rastro no cambia nada: el dato se lee del mapa en 5 lugares. La predicción casi no se mueve (54,32 → 54,29), porque la participación es fija dentro de cada concesión; la diapositiva no dice que cambie.
- **Revisión de las explicaciones de Lab, antes de la prueba a ciegas:** la evidencia del inicio del pozo mostraba el gas que se predice (se sacó); cuando la operadora no figura entre los socios del mapa (por ejemplo Aguada Villanueva Norte: el mapa dice YPF 100 %, las declaraciones juradas, Pluspetrol) ahora se marca en lugar de decir «nan»; y la fractura ya no dice «más rama, más gas» en general: muestra el aporte real de cada variable y que la rama y las etapas se reparten un mismo efecto (en el modelo lineal, la rama sola puede restar).
- **Prueba a ciegas de las explicaciones lista para mandar** (`docs/lab-explicaciones-a-ciegas.md`, clave en `lab/gas/a-ciegas-clave.json`, se arma con `lab/gas/a_ciegas.py`): 20 explicaciones de 10 pozos de 2025, mezcladas, con tres preguntas de 1 a 5.

## 2026-10-21 — Orden y consistencia del proyecto

Una revisión del código y de la documentación (dos auditorías, una de cada uno) antes de seguir.

- **Reglas a la vista:** `CLAUDE.md` describe el proyecto como es hoy (petróleo y gas como demo, Rastro Lab de gas) y junta las reglas que estaban repartidas en estas decisiones: medir con tres caminos, adjudicar, no usar el futuro en Lab, no cambiar Layer con lo que carga Lab, números leídos de sus JSON, registro de negocio.
- **Skills para que se pueda repetir:** se actualizaron `verificar` (los tres dominios, con petróleo y gas primero), `agregar-pregunta`, `agregar-fuente` y `cerrar-fase`, y se sumaron `evaluar`, `rastro-lab`, `pruebas-de-cambio` y `mazos`.
- **Errores corregidos:** la app esperaba al Ontop de oncología y no al de petróleo y gas; rearmar los enlaces borraba los permisos de los usuarios de la evaluación (el enlazador los vuelve a dar); una oración de oncología cambiaba sus comas por puntos; la tabla de resultados de oncología tenía columnas de menos; la pregunta elegida en «Correctas» se compartía entre dominios; una variable tapaba una función en Lab.
- **Menos código repetido:** los cargadores de datos.gob.ar comparten `data/comun.py`; los scripts de Lab, la prueba de la corrección y la prueba a ciegas usan las mismas funciones de `lab/gas/modelo.py` para leer Postgres y Rastro; el puerto de Ontop sale de `ONTOP_ENERGIA_PORT`. Se sacó código que no se usaba.
- **Calidad:** `ruff` (líneas de hasta 140 caracteres) y 17 pruebas con `pytest` que corren sin Docker: que los aportes del modelo sumen la predicción, que los términos de los mapeos y consultas de petróleo y gas estén en la ontología, que la configuración de la app nombre archivos que existen. Corren en GitHub en cada push (`.github/workflows/calidad.yml`). Versiones fijas en `requirements-dev.txt` y `anthropic` fijado en la imagen.
- **Deuda conocida, que no se tocó porque es código que funciona y es difícil de verificar sin riesgo:** la pantalla de oncología sigue en `app/app.py` en lugar de un YAML como los otros dominios; hay tres `cambio.sh` y tres `probar.py` casi iguales (uno por dominio) y varios scripts de evaluación de oncología con su propio puntaje; textos de un dominio dentro de `app/dominio.py` («Leidos», «APE»); los 15 cargadores repiten su bloque en `infra/docker-compose.yml`. Falta elegir una licencia para el repo (decisión del dueño).
- **Otra mirada (una conversación con otro asistente de IA sobre el mismo caso):** coincide en separar «de dónde sale cada valor» de «cuánto pesa en la predicción», que es lo que hace Lab. Se tomó una idea enseguida: la app aclara que la explicación dice cómo llegó el modelo a su número, no la causa física. Quedan como pasos siguientes: guardar cada predicción con su explicación, la versión del modelo y los registros de origen exactos como datos enlazados en el grafo (para poder consultarlas), y versionar los datos de entrenamiento.

## 2026-10-21 — Rastro Lab: las predicciones y sus explicaciones, en Rastro

- **Cada corrida del modelo se publica en Rastro** (`python3 lab/gas/modelo.py --publicar`), en su propio esquema (`lab_gas`, que el enlazador no borra): `energia:ModelRun` (una `prov:Activity` con la versión, que es una huella del código, la fecha, el corte, el error y si es la vigente), `energia:Prediction` (valor, rango, `prov:wasGeneratedBy` y `prov:used` a las identidades de Rastro que ya existían: el inicio del pozo, su fractura y la participación) y `energia:Contribution` (el aporte de cada factor). Responde a la falta que señaló otra mirada: la explicación vivía solo en la app.
- **Dos preguntas nuevas** (11 y 12). La 11 cuenta 24 predicciones de 2025 con un dato corregido, lo mismo que el modelo por su lado. Se consultan con SPARQL, en la app (Rastro Lab → «Las predicciones, en Rastro») y con el asistente de IA, que conoce los términos nuevos por `layer/dominios.yaml` y las notas de SPARQL.
- **Rango de cada predicción:** de los errores del año anterior a la prueba (entrenando con los pozos anteriores a 2024 y midiendo en 2024), sin mirar la prueba. Cubre 71 de cada 100 pozos de 2025; se dice así, aunque se buscaba 80.
- **La app nota una corrida nueva:** la versión de los datos que usa el caché mira también la última corrida publicada.

## 2026-10-21 — Rastro Lab: los registros de origen, uno por uno, y la versión de cada corrida

- **Cada registro de origen tiene su identidad en Rastro:** cada fractura informada (`energia:FractureReport`, con su identificador del Adjunto IV, fecha, etapas y fecha de carga) y cada mes de gas de un pozo nuevo (`energia:MonthlyGas`, de las declaraciones juradas). La fractura de un pozo y su inicio dicen de qué registros salen (`prov:wasDerivedFrom`), así que la cadena completa se consulta: predicción → datos que usó → registros de origen (pregunta 13, en 2 segundos). Comprobado contra la fuente: el pozo 166133 usa la fractura n.º 4703 (18 etapas, cargada el 14/01/2025) y seis meses de gas que suman sus 30,2 millones de m³.
- **En la app:** el gas real dice de qué meses de las declaraciones juradas sale, y el «¿De dónde sale?» de la fractura lista las fracturas informadas con su número y su fecha de carga, leídos de Rastro.
- **Versión:** cada corrida ya guarda la huella del código, la fecha, el corte y el error, y las anteriores quedan (solo deja de ser la vigente). Con los registros de origen, una predicción se puede rehacer y comprobar.

## 2026-10-21 — Rastro Lab: la entrada de cada corrida y la huella de cada archivo

- **No se versiona cada fuente completa** (el Capítulo IV son cerca de un millón de filas por año): sería una pieza de más para el MVP. Se guardan dos cosas chicas que alcanzan para rehacer y comparar.
- **La entrada de cada corrida** (`lab_gas.entrada`): lo que vio el modelo, pozo por pozo, junto a sus predicciones. Con el mismo código y los mismos datos, dos corridas dan exactamente lo mismo; `python3 lab/gas/modelo.py --comparar` dice qué pozos cambiaron, en qué variable y cuánto se movió la predicción (probado con una copia temporal: detectó las etapas cambiadas de un pozo y su predicción, de 22,7 a 28,8).
- **La huella de cada archivo descargado** en `rastro_meta.load_run` (nombre, SHA-256 y día de descarga), que registra `copiar()` de `data/comun.py`. Si la fuente publica otra versión, la huella cambia. Las columnas se agregan solas la primera vez; los archivos de petróleo y gas la tendrán la próxima vez que corra su cargador.

## 2026-10-21 — Rastro Lab: qué cambia cuando cambia un dato, una fuente nueva y el asistente sobre las predicciones

Tres pruebas que siguieron a otra mirada sobre el caso (que propuso medir el impacto de un cambio como lo más fuerte) y a las sugerencias propias.

- **Impacto de un cambio en la fuente** (`layer/energia/cambio/impacto.sh`, pregunta 14). Rastro dice de antemano qué predicciones dependen de una fractura informada, recorriendo el linaje al revés; si el registro es de un pozo de entrenamiento, dice que hay que reentrenar. Se probó con la fractura n.º 4703 (pozo 166133, de 2025): se corrigieron sus etapas (18 → 30), se rearmó Rastro y se publicó una corrida. Rastro había dicho una predicción y cambió exactamente esa (de 22,7 a 30,2 millones de m³), ninguna otra; al restaurar, todo volvió a dar igual. Sin Rastro, para saberlo hay que rehacer todas y comparar.
- **Una fuente nueva: las trayectorias de pozo** (profundidad vertical y rama, datos.energia.gob.ar, CC-BY 4.0), con la regla «una por pozo: la de rama más larga entre las perforadas antes de que arrancara». Esfuerzo, contado en líneas: sin Rastro, unas 7 en la consulta del modelo; con Rastro, unas 15 en el enlace, 11 en el mapeo y 6 en el diccionario, y 3 en la consulta del modelo. Con Rastro cuesta más la primera vez, y a cambio la regla queda escrita una vez y la usan las preguntas, el asistente, la explicación (con su evidencia) y el linaje (`prov:used`). La precisión casi no cambia (R² de 0,45 a 0,46; la profundidad pesa 1,0 contra 8,6 de la concesión): el valor del paso es la integración, no la precisión.
- **El asistente de IA sobre las predicciones** (`layer/energia_lab/`, 5 preguntas, mismo protocolo que Layer: subagentes que solo ven el prompt). Sin Rastro (SQL sobre las fuentes y las tablas que deja el modelo) 4 de 5; SQL con los enlaces de Rastro 5 de 5; con Rastro 4 de 5. Cuando el modelo guarda sus resultados en tablas, el SQL responde qué pozos, qué fracturas y qué fechas de carga; falla la pregunta que necesita las reglas de Rastro (cuántas predicciones se apoyan en un dato corregido: 0). Con Rastro falla esa misma (22 en lugar de 24): llegó a la operadora por la participación y no por el inicio del pozo, una falta de las notas del diccionario que se anota y no se arregló antes de publicar el número. Otra vez, la ventaja viene de la integración hecha una vez, la consulte quien la consulte.
- **La prueba a ciegas de las explicaciones, como formulario:** una página que muestra las 20 explicaciones con tres escalas de 1 a 5 y arma un resumen para copiar y enviar. No guarda las respuestas en el servidor a propósito: una página que guarda datos solo la abre gente de la organización, y la prueba es para alguien de afuera.

## 2026-10-21 — Un mazo más profesional

- **Un estilo parejo, aplicado por un script** (`docs/slides/estilo.py`) en lugar de a mano: IBM Plex Sans para el texto y Source Serif 4 para los títulos (antes, Times New Roman en todo); una escala de seis tamaños (24, 28, 32, 40, 56 y 72 px; antes había 19 tamaños distintos); tarjetas con un borde fino y el mismo radio; el mismo pie en cada diapositiva de contenido, con el nombre del mazo y su número; los dibujos con la tipografía del mazo y una altura que entra. Se puede correr siempre: da lo mismo.
- **Las diapositivas compartidas con los otros mazos** (Qué es Rastro, Beneficios) tienen una copia propia del mazo de petróleo y gas, para que su pie y su número sean de este mazo. Los otros mazos no cambiaron.
- **Nada pasa del pie:** se midió en el navegador que el contenido de las 24 diapositivas termine antes de los 920 px. Cinco pasaban: dos por exceso de texto (se acortó: «¿Cuánto petróleo…?» decía dos veces los dólares) y tres dibujos a todo el ancho (se les fijó la altura).
- **Contenido al día:** «Predecir» con el error de hoy (16,7 con y sin Rastro), una diapositiva nueva en el anexo, «Cada predicción, hasta su origen» (el impacto de un cambio, las trayectorias y el asistente sobre las predicciones), y el anexo sin la numeración vieja de los pasos.

## 2026-10-21 — Enriquecer con datos de afuera: en vivo y guardado

- **El concepto, con su nombre:** lo de Wikidata es **enriquecer** los datos: sumar lo que sabe una fuente de afuera, por una clave compartida (el LEI), sin perder de dónde vino. Se eligió «enriquecer» y no «aumentar», que en aprendizaje automático quiere decir generar ejemplos sintéticos. Está en las preguntas frecuentes, la app («Enriquecer con datos de afuera»), el mazo, el guion y `CLAUDE.md`.
- **Dos formas, las dos en Rastro:** en vivo, una consulta federada une Rastro y Wikidata al momento (siempre al día, sin copiar nada; necesita internet). Guardado, `wikidata-energia-loader` baja la respuesta del día con su huella, el enlazador la une por el LEI (`energia.enriquecimiento`, regla «mismo LEI en Wikidata y en GLEIF») y Rastro la publica como `energia:Enrichment`, con el día de la consulta. Así no depende de internet y se puede repetir. Hoy lo usa la pregunta 15 y lo puede usar el asistente; no entra al modelo de Rastro Lab ni a las preguntas que se puntúan.
- **Lo que suma hoy es poco:** Wikidata tiene el LEI de 3 de las 12 empresas (YPF, Pampa Energía y Pan American Energy), y la bolsa de 2. El valor está en mostrar el patrón con su procedencia.

## 2026-10-21 — Lo que faltaba en el diccionario para la pregunta l01 de Rastro Lab

- **La falta:** las notas del diccionario de petróleo y gas no describían `energia:CompanyName` (cada nombre de empresa como lo escribe una fuente, con su regla). Por eso, en l01, Rastro llegó a la operadora por la participación y no por el nombre declarado al arrancar el pozo, y respondió 22 en lugar de 24. Se había anotado y no se arregló antes de publicar.
- **El arreglo:** una línea en `layer/energia/sparql-notes.md`, al mismo nivel que lo que ya decían las notas de SQL con enlaces (`empresa_nombre`). No dice cómo responder la pregunta.
- **Se volvió a medir solo l01, con Rastro**, con un subagente nuevo que solo vio el prompt: 24, correcto. El resultado pasa de 4, 5 y 4 de 5 a **4, 5 y 5 de 5** (sin Rastro, SQL con enlaces, con Rastro). Las demás respuestas guardadas no cambian. El empate con SQL más enlaces se mantiene: la ventaja es la integración hecha una vez.
- **Las notas son las mismas que usa la evaluación de Layer** de petróleo y gas. Sus respuestas guardadas no cambian; la línea nueva solo cuenta para las mediciones que vengan.
- **De paso:** `ontology-check` revisaba solo oncología si no se le pasaba un dominio; ahora revisa los tres (oncología, petróleo y gas, proveedores). Todo OK, y las 15 preguntas de petróleo y gas responden en Rastro. Y se corrigió lo que se había escrito del enriquecimiento guardado: hoy lo usa la pregunta 15, no el modelo de Rastro Lab.

## 2026-10-21 — El mazo abre con «la respuesta conocida»

- **La idea:** un asistente de IA que responde de memoria da la respuesta más repetida, no la comprobada, y no puede mostrar de dónde sale; una respuesta segura y equivocada se ve igual que una correcta. El mazo de petróleo y gas abre con eso (diapositiva 2), antes de «Qué es Rastro».
- **La pregunta:** ¿quién produjo más gas en Argentina en 2025? Tres respuestas, medidas el 21/10/2026:
  - un asistente de IA solo (un subagente sin herramientas ni datos): YPF 13–14, Tecpetrol 7–8, Pan American 6–7 miles de millones de m³. Acierta los dos primeros; el tercero no es, los números están entre un 10 y un 20 % arriba y dice que su confianza es media o baja;
  - SQL sobre la declaración jurada (`capitulo4.produccion`, por quien declara): Total Austral 12,3, YPF 11,7, Tecpetrol 6,9. Exacto, pero cada operadora declara todo el gas de la concesión, también el de sus socios;
  - con Rastro (la pregunta 1, ordenada por gas: la parte de cada empresa según su participación): YPF 12,3, Tecpetrol 6,4, Total Austral 5,2. El 99,4 % del gas de 2025 tiene sus participaciones.
- **Honesto:** la respuesta conocida acierta el primer puesto. El mensaje no es «la IA se equivoca», sino que una respuesta conocida no es una respuesta comprobada: Rastro la confirma donde acierta y muestra dónde no.
- **De dónde sale la idea:** artículos de divulgación sobre grafos de conocimiento y razonamiento con reglas («el problema de la respuesta conocida»). Lo demás que proponen (sin esquema fijo, reemplazar SQL) no se toma: el público sabe SQL, y nuestro mensaje es que SQL con los enlaces de Rastro acierta igual.
- **El mazo publicado:** las últimas publicaciones habían quedado fuera de `project/`, donde el mazo no las lee; se volvieron a publicar todas las diapositivas en su lugar y se borraron las copias sueltas. La skill `mazos` lo aclara.

## 2026-10-21 — Reglas de calidad en SHACL

- **Qué:** cinco reglas sobre los datos integrados de petróleo y gas, en SHACL (`ontology/energia/calidad/reglas.ttl`), con las palabras del diccionario: cada enlace con su fuente y su evidencia; cada participación entre 0 y 100 %, de una empresa en una concesión; las participaciones de una concesión suman 100 % o menos (medio punto de tolerancia por el redondeo del mapa); cada predicción sale de un inicio de pozo y cae dentro de su rango; cada empresa tiene a lo sumo un LEI, con su formato.
- **Cómo, simple:** `docker compose run --rm calidad` trae de Rastro con CONSTRUCT solo lo que miran las reglas (unos 440 mil triples), valida con pySHACL y escribe `layer/energia/calidad.json`, que lee la app. Unos 3 minutos. Ningún servicio nuevo; una dependencia (pySHACL). Una prueba por regla en `tests/test_calidad.py`: deja pasar un dato bueno y marca uno malo.
- **Lo que encontraron:** 5 trayectorias de pozo sin evidencia, las que no tienen rama horizontal informada: en SQL, concatenar un valor vacío borra todo el texto. Se arregló en `linking/energia/links.sql` y ahora las cinco se cumplen.
- **Las predicciones sin fractura o sin participación** (17 y 14 de 559 en la corrida vigente) no son una falla: el modelo usa el promedio y la explicación lo dice. Por eso la regla exige solo el inicio del pozo.
- **Dónde se ven:** en «Por qué confiar», en palabras de negocio; con «Ver detalles técnicos», en «Bajo el capó → Reglas de calidad (SHACL)», cada regla en Turtle con lo que no cumple. Y una diapositiva en el anexo del mazo.
- **De paso:** algunas siglas de pozo de las trayectorias llegan con la codificación rota («BAÃ±» en lugar de «Bañ»). No cambia ningún número; queda anotado para el cargador.

## 2026-10-21 — El mazo vuelve a Times New Roman

- Al darle al mazo un estilo más profesional se cambió la tipografía a IBM Plex Sans y Source Serif 4 sin consultarlo. Al usuario no le gustó: el mazo vuelve a Times New Roman, en todo el mazo. Es del sistema, así que el mazo no descarga ninguna tipografía. El resto del estilo (escala de tamaños, tarjetas, pie con número) se mantiene. `docs/slides/estilo.py` lo aplica.

## 2026-10-21 — La apertura del mazo: una pregunta, dos significados

- **Por qué cambió:** el usuario hizo la misma pregunta a un asistente de IA con búsqueda en internet. Respondió con el ranking publicado (datos de la cámara de empresas del sector): Total Austral 33,8, YPF 32,2 y Tecpetrol 18,9 millones de m³ por día. Por 365 son 12,3, 11,8 y 6,9 miles de millones de m³: lo mismo que el SQL sobre la declaración jurada. La columna «un asistente de IA solo», que respondía de memoria y sin herramientas, era un rival débil.
- **El mensaje nuevo:** la pregunta tiene dos respuestas correctas. Lo que opera cada empresa (rankings publicados, SQL, IA con búsqueda): Total Austral, YPF, Tecpetrol. Lo que le corresponde por su participación (Rastro): YPF 12,3, Tecpetrol 6,4, Total Austral 5,2. Nadie dice qué midió; Rastro escribe la definición una vez, muestra las dos y la evidencia de cada número.
- **De paso, una validación:** lo operado que sale de nuestros datos coincide con los rankings publicados.

## 2026-10-21 — Cuando no tiene el dato, y comprobar una afirmación

- **La idea:** un asistente de IA solo puede inventar con seguridad; con los datos, responde desde ellos, y lo que los datos no tienen tiene que decirlo. Viene de un artículo de divulgación sobre IA con y sin datos («dos verdades y una mentira»).
- **La regla, igual para todos los caminos:** si los datos no alcanzan, el asistente devuelve «SIN DATOS:» y qué falta, en lugar de una consulta (`NO_DATA_RULE` en `layer/answer.py`). Cambia el prompt de la evaluación y de las preguntas libres, en los tres dominios: las respuestas guardadas no cambian; vale para las mediciones que vengan.
- **La medición** (`layer/fuera.py`, `layer/energia/fuera/`): 5 preguntas del sector que los datos no responden (precio del gas, reservas de YPF, inversión de Tecpetrol, gas de 2026, empleados de Pluspetrol) y una de control que sí (el gas que declaró Tecpetrol en 2025). Un subagente por camino, que solo ve su prompt. Resultado: los cuatro caminos dijeron qué faltaba en las 5; en la de control, los tres con datos respondieron 6.910 millones de m³ (correcto) y la IA sola dijo que no lo sabía. LLM solo 5 de 6; SQL, SQL con enlaces y Rastro 6 de 6.
- **Honesto:** con la regla de decir qué falta, la IA sola tampoco inventó; el artículo dice lo contrario, pero no lo mide. Lo que muestra la prueba no es que Rastro evite mentiras que el SQL dice: es que, con los datos, lo que está se responde con su fuente y lo que no está se dice. En la evaluación de antes, la IA sola tenía la consigna de estimar, y ahí sí da números.
- **Comprobar una afirmación** (Preguntar): tres ejemplos con su veredicto calculado en vivo sobre Rastro: se sostiene, no se sostiene (con el valor correcto) o Rastro no tiene el dato. Una frase con dos lecturas muestra las dos («Total Austral fue la mayor productora de gas»: sí por lo que opera, no por lo que le corresponde). Son ejemplos fijos porque la app no tiene un LLM configurado; con uno, se podría comprobar cualquier frase.
- **SHACL con RDF en «Bajo el capó»:** cada regla de calidad muestra, además de su SHACL, un dato real de Rastro en RDF que la cumple y un dato roto de ejemplo con lo que dice SHACL. Los ejemplos están en `ontology/energia/calidad/ejemplos.yaml` y los usan también las pruebas.

## 2026-10-21 — Lo que suma la tesis de referencia: reglas para lo que se decide en silencio, y la línea de base de la concesión

Se leyó entera la tesis que sirve de validación (solo para validar, sin citarla en Rastro Lab). Su mejor modelo no se puede rastrear hasta los registros: varias decisiones sobre los datos quedan en el código, sin regla ni evidencia. Se tomó lo que refuerza el mensaje de Rastro:

- **Valores imposibles, como reglas de calidad** (SHACL, `calidad:TrayectoriaPosible` y `calidad:FracturaPosible`): profundidad vertical entre 1.000 y 6.000 m, rama hasta 6.000 m, presión máxima hasta 20.000 psi, agua hasta 200.000 m³ por pozo (lo común: 11.000 psi y 28.000 m³). Marcan 2 trayectorias (una a 276.939 m; la rama de 9.965 m de WIN.Nq.AF-4(h), la misma que encontró la tesis) y 17 fracturas. **Cada falla lista las predicciones de la corrida vigente que usan ese dato** (prov:used): 4 (tres pozos con 537.184 m³ de agua cada uno y uno con 111.515 psi). No se cambia el dato: se marca para revisar. Que el modelo los excluya sería otra decisión, que habría que volver a medir.
- **Un error del diccionario que destaparon las reglas:** `energia:fracStages` y `energia:fracDate` tenían `rdfs:domain energia:Fracturing`, pero también los usa cada registro de fractura (`energia:FractureReport`), así que Rastro deducía que cada registro también era una fractura: 9.732 en lugar de 4.733. Rompía la regla del repo («una propiedad que usan dos clases va sin dominio»). Se sacó el dominio. El modelo no cambia (su consulta pide datos que los registros no tienen): error 16,7 y R² 0,46, y una corrida nueva publicada con 0 predicciones distintas. Las consultas guardadas de las dos evaluaciones dan lo mismo (4, 5, 5 y 7, 10, 10).
- **La línea de base de la concesión, a la vista:** sin modelo, la mediana de cada concesión (de los pozos de entrenamiento) da R² 0,42; el modelo, 0,46. Casi todo lo que sabe el modelo es dónde está el pozo; la fractura y la profundidad agregan poco. Rastro Lab lo dice en la app. La tesis muestra lo mismo con otros números: sus modelos de árboles suman +0,28 de R² sobre la mediana del área en una partición mezclada, pero en pozos de años futuros caen a 0,254.
- **La historia de las operadoras:** las dos razones sociales de Pan American Energy ya se unen por la regla del nombre; Apache no aparece desde 2018; Petrobras Argentina declara en 2018 como empresa propia y arranca un solo pozo, que no entra al modelo. No se agregó una corrección sin documento que no cambia nada.
- **Lo que no se tomó:** modelos de árboles (ganan precisión y pierden la explicación simple), geología interpolada (no hay datos públicos por pozo) y pozos de un mismo pad (la tesis no encontró casos concluyentes). Quedan para después: ubicación (longitud y latitud), intensidad por metro y año de inicio como variables, intervalos por bootstrap con 49 pozos de prueba, y el error por tamaño de pozo.

## 2026-10-22 — Control: la regla «SIN DATOS» no cambia las respuestas correctas

- **Por qué:** la regla «si los datos no alcanzan, decí qué falta» se agregó al prompt después de medir. Podía hacer que el asistente se negara en preguntas que sí tienen datos.
- **Control** (`layer/energia/remedicion-sin-datos/`): las 10 preguntas con el prompt nuevo, un subagente nuevo por camino que solo vio el prompt. Correctas 7, 10 y 10 de 10, igual que lo publicado; ningún camino dijo «SIN DATOS» en una pregunta con datos.
- **El límite, dicho:** para ahorrar tiempo, cada subagente recibió todas las preguntas juntas, también las cuatro formas de cada una, y repitió la misma consulta en las cuatro. Por eso la consistencia de este control (sin Rastro 4 de 5) no se compara con la publicada (3 de 5) y no se usa. Lo publicado sigue siendo la medición con el protocolo estricto (un subagente por prompt).
- **La invitación para la prueba a ciegas** quedó en `docs/invitacion-prueba-a-ciegas.md`: las dos partes (preguntas propias y explicaciones de Rastro Lab), lista para mandar a una o dos personas del sector que no hayan visto Rastro.

## 2026-10-22 — El método antes que los agentes

- **Pregunta:** ¿se generaliza Rastro como una orquestación de agentes, cada uno experto en algo (limpieza, mapeos, etc.)?
- **Decisión:** no, todavía. Primero el método, escrito (`docs/metodo.md`): ocho pasos, cada uno con su skill, un control que decide si pasa y una persona que aprueba solo lo que es de negocio. Un agente con skills; agentes separados solo donde importa la independencia (evaluar, preguntas a ciegas); más agentes solo si una medición lo pide.
- **Por qué:** en Rastro la experiencia estuvo en las skills, los errores los atraparon los controles (SHACL, evaluación, pruebas de cambio) y las decisiones difíciles fueron de negocio (operada o por participación). La literatura dice lo mismo: los modelos de lenguaje ayudan a proponer mapeos, pero inventan términos y escriben mapeos inválidos; la corrección la dan pruebas que se ejecutan.
- **Lo que falta para venderlo:** un experimento en dos dominios nuevos que mida horas, intervenciones humanas y errores atrapados. Nada implementado todavía.

## 2026-10-22 — Technical work in English; skills per method step

- **Language:** from now on, code, comments, technical docs, skills and commits are in English, so the method and its skills can be reused and sold beyond Argentina. What users see stays in Spanish: the app, the decks, the demo scripts and the ontology labels (`@es`). Existing Spanish comments and docs are translated when they are touched; this log keeps its history as written.
- **Skills, renamed to English and translated:** `add-source`, `add-question`, `verify`, `evaluate`, `rastro-lab`, `change-tests`, `decks`, `close-phase`. `docs/metodo.md` is now `docs/method.md`; `CLAUDE.md` and the README are in English.
- **Three new skills, one per method step that had none:** `map-source` (dictionary and mapping together, steps 2 and 3), `link-entities` (step 4) and `quality-rules` (step 5). Each has a contract, the steps "narrow down, decide, test", the check that decides, what a person approves, its grounding in the literature and what went wrong in Rastro.
- **Two lessons written into the rules:** one prompt per evaluator (`evaluate`, `CLAUDE.md`), and stage only the files you changed when committing (`close-phase`, `CLAUDE.md`).
- **Still in Spanish, for a second pass:** comments and docstrings in the code, and the other technical docs.

## 2026-10-22 — Executable contracts for method skills

Keep the existing skill structure and add a shared contract (`docs/method-contracts.md`) plus `start-domain`.
Questions progress from proposed requirements to approved, implemented and validated states. New-domain experiments
must record measured time, interventions, caught errors and method changes; closure checks their evidence without
inventing history for existing domains.

`layer/method.py` validates registry targets and fingerprinted query assertions, and gates new accuracy claims on
independently reviewed references for every question, matching the reference actually scored. Missing evidence
remains pending; existing published numbers were not re-adjudicated. Correct the Lab question-set target, declare
legacy/current evaluation harnesses and remove registry paths that do not exist. Quality defects have explicit
reviewed dispositions, distinct from failed runners.

Energy change tests now preserve actual starting files and affected tables through `layer/change_guard.py`, including
local edits, untracked answers and original model runs. Restoration uses saved values and transactional equality
checks instead of inverse arithmetic or Git checkout. Recovery data survives failed cleanup; concurrent writers
must be stopped. Database helpers explicitly select the same database as the snapshots. Full energy scenarios
still require loaded sources; isolated Postgres recovery tests exercise the rollback without those sources.

## 2026-10-22 — Generic domain infrastructure and enforced lifecycle

Add executable lifecycle transitions in `layer/lifecycle.py`. Real human approval artifacts bind exact proposals;
query validation executes HTTP assertions and ontology checks. Changes to definitions, approval records, source
manifests, mappings, queries or expectations invalidate dependent receipts. Adopted domains expose only current
validated questions in the app; accuracy cards and guided demos remain hidden while independent review is pending.
Existing domains retain explicit legacy status rather than invented historical approvals.

Move quality CONSTRUCT queries and prediction-lineage queries into domain files. The shared SHACL runner and tests
read every configured domain's namespace, paths and endpoint. Zero-target checks remain pending, and good/bad
examples cannot pass vacuously. Move app instance lists, mapping/link panels and map queries/settings into domain
YAML; console and ontology paths come from the registry. App cache invalidation no longer requires Lab tables.
Pin PyArrow 19.0.1 because the previously resolved release rejected the development NumPy 1.26.4 at render time.

The new shared-property checker found three energy domains to remove: `date` wrongly typed environmental studies as
venting, `aboutVenting` wrongly typed surroundings links as location links, and `reviewReason` redundantly implied a
superclass already supplied by the mapped subclass hierarchy. Keep the existing definitions, ranges and hierarchy;
remove the shared-property domains as required by the method. Inference regression tests cover the unwanted types
and the preserved superclass. The full energy evaluation must be rerun with loaded source data before new claims.

`layer/experiment.py` preserves each technical check's exit status, output, duration and method-file fingerprints.
A legacy rerun no longer generates missing LLM answers when a provider is configured. `app/check_domain.py` checks
live examples and both app views; it requires the real services. The synthetic tests use an unfamiliar library
vocabulary, with no claims of real business approval. Validation here: 56 tests passed, including five isolated
Postgres checks, HTTP lifecycle validation and both template views; registry, ontology, lint and dependency checks
passed. These software tests are distinct from the proposed public-data experiment.

Profile public country/currency-code datasets over verified HTTPS and retain exact file hashes in
`docs/experiments/countrycodes/source-profile.json`; source snapshots remain outside version control. The concrete
proposal is unapproved, and no independent answer review, model comparison or two-domain generalization result is
claimed. The next empirical step is approval of scope/questions, then the documented experiment with independent
B/D/C evaluators and live time/intervention logging, repeated on a second unfamiliar domain.

## 2026-10-22 — Read-only source inspection before domain initialization

Add the generic `inspect-sources` skill and route to it from the method, `start-domain` and `add-source` when source
feasibility is uncertain. It preserves inspected versions, actual coverage, grain, keys, reuse terms, source
dependencies, candidate joins and measured time before proposing implementation. This avoids registering a domain
just to discover whether its sources are suitable. Inspection returns a recommendation, not business approval.

The electricity inspection motivated the skill but was performed before it existed. Keep that distinction in its
evidence; this is a method change before any electricity implementation, not proof of unchanged-skill transfer.

## 2026-10-22 — Oil and gas re-checked after the method changes

The method commits asked for the full energy evaluation to be rerun with loaded data before new claims. Done after
pulling them: Ontop restarted with the new ontology, the 15 competency queries return the same row counts, the saved
evaluation queries give 7, 10 and 10 correct (consistency 3, 5 and 5), the Lab question set 4, 5 and 5, and the
quality rules the same results (17 impossible fracturing records, 2 trajectories, 4 affected predictions).
`app/check_domain.py` passes both views. Only dates and the quality file's layout changed, so nothing was
republished. Oil and gas has no `lifecycle`, so its accuracy cards and guided demo stay visible.

## 2026-10-22 — Transfer experiment: state of the discussion

The discussion with the other assistant is kept in `docs/experiments/countrycodes/discussion.md`. Agreed so far:
countrycodes stays a reserve technical control; accuracy ties are valid; an energy extension is not evidence of
transfer; non-accuracy checks and a stop budget are fixed before execution. The user approved a read-only
electricity source inspection (3 hours, GPT inspects, Claude reviews). The inspection
(`docs/experiments/electricity/inspection.md`) reproduces, but its recommended case depends on CAMMESA data whose
terms prohibit reproduction without express authorization; the review (`review.md` in the same folder) recommends
not accepting it as the first transfer case. Nothing is approved or implemented.

## 2026-10-22 — Source-inspection skill explicitly approved

The user confirmed approval of `inspect-sources` and asked that it be recorded. The skill and its method/documentation
integration in `002a39d` were separately requested after the read-only electricity inspection and authorized for
publication. This corrects the authorization context missing from the electricity review: the method change was
authorized separately, not part of the original inspection scope. The inspection itself predates the skill.
See the approval entry in `docs/experiments/countrycodes/discussion.md`. No domain, new inspection budget, business
question or experiment implementation is approved by this skill decision.

## 2026-10-22 — Record the semantic-layer proposal after source inspection

At the user's request, retain the research-affiliations conceptual schema and its worked example in the experiment
folder. Extend `inspect-sources` to propose a minimal question/source-grounded semantic layer after inspection when
evidence permits; `map-source` reuses it before proposing executable terms and mappings. Missing evidence remains
pending. This adds a reviewable handoff rather than a new approval gate, and does not retroactively change what the
earlier inspection did. Record the skill change against the actual frozen method version if implementation has
already begun; it is not evidence of unchanged-skill transfer.

## 2026-10-22 — Research affiliations: a new domain for the transfer experiment

- **What:** the domain `afiliaciones` identifies Argentine research organizations (ROR v2.15) in the affiliations of a
  bounded set of 100 Crossref works from 2025, drawn with seed 20261022. Scope, questions and the reference plan were
  approved by the user; the discussion is in `docs/experiments/countrycodes/discussion.md` and the log in
  `docs/experiments/afiliaciones.yaml` (method frozen at `05428c5`).
- **Load:** one loader, two schemas (`crossref`, `ror`). It loads the approved snapshots and checks their
  fingerprints instead of downloading, because Crossref is a live API. 100 works and 1,456 affiliations (962 distinct
  strings, 2 with a publisher-supplied ROR identifier); ROR complete: 146,716 organizations, 538 in Argentina.
- **Not yet:** mapping, links, quality rules, evaluation and app. The named reference reviewer is pending.
- **Process notes** for improving the skills are kept as the experiment runs, in
  `docs/experiments/research-affiliations/process-notes.md`.

## 2026-10-22 — The quality runner keeps each finding's severity

- **What:** `ontology/calidad.py` saves the SHACL severity of each finding, counts per rule and in total
  (`por_severidad`), and a new status `review_findings` when there are warnings or informational findings but no
  violation. `defects_detected` now means at least one violation. `fallas` stays the total, so the app reads it as
  before.
- **Why:** in research affiliations, a withdrawn ROR record (warning) and 91 AI decisions awaiting a person (info) were
  saved as «fallas» with `defects_detected`, the same as an impossible value. GPT's review caught it. Approved by the
  user as a recorded method change in the frozen experiment (`docs/experiments/afiliaciones.yaml`).
- **Numbers:** oil and gas unchanged: 19 violations (2 trajectories, 17 fracturing jobs), no warnings. Research
  affiliations: 0 violations, 1 warning, 91 informational, status `review_findings`.

## 2026-10-23 — The change-test guard reads each domain's lists from the registry

- **What:** `layer/change_guard.py` takes the files and tables each change test may change from the domain's
  `method.change_guard` entry, and the linker, Ontop service and script folder from its method block. Oil and gas
  keeps its exact lists, moved to the registry. Usage: `run <test> [domain]`, defaulting to energia.
- **Why:** research affiliations needed the same guarded snapshot and restore for its alias correction test. Approved
  by the user as a recorded method change in that experiment.
- **Numbers (research affiliations):**
  - alias correction: with Rastro and SQL with links, 11 of 11 saved runs behaved as declared (two changed, the rest
    stayed the same), with no query edited; without Rastro, no answer changed, which does not measure B's edits;
  - traceability on 30 cells drawn from Rastro's identifications: 30, 30 and 0, for the evidence each approach
    keeps in this setup;
  - the restore matched the starting fingerprints exactly.

## 2026-10-23 — Saved answers are kept until the domain's own tables change

- **What:** the app's cache key (`data_version` in `app/dominio.py`) uses only the tables the domain's mapping reads:
  each table's id and its row-change counters. Rastro Lab adds the raw tables its SQL reads. Before, the key was the
  database's WAL position, so any write in any domain discarded every domain's saved answers.
- **Why:** the app felt slow. Oil and gas, the domain the app opens with, recomputed everything, including retraining
  the two Lab models, after any linker or load in another domain.
- **Numbers (browser, real app):**
  - first load after the change: about 26 s, since every answer gets a new key once;
  - warm reload: 1.7 s;
  - reload after an afiliaciones linker run and the 60-second key refresh: 1.7 s (before: about 25–40 s).

## 2026-10-23 — Keep the JDBC directory traversable in clean container builds

- **Problem:** building Ontop from scratch with remote `ADD --chmod=644` created its JDBC parent directory with
  mode 0644. The non-root `ontop` user could not traverse it, and both deployed endpoints exited with
  `Cannot load the driver: org.postgresql.Driver`.
- **Change:** name the downloaded JAR explicitly, restore mode 0755 on its directory as root, and return to the
  original `ontop` runtime user. The JAR stays readable with mode 0644. No mappings or source rules change.
- **Validation:** rebuilt images; checked directory traversal and JAR readability as the runtime user; both oil/gas
  and affiliations endpoints became healthy. Both domains' live app checks passed in business and technical views.
  Deployment scope and restart commands are in `docs/local-deployment.md`.

## 2026-10-23 — «Paso a paso» walkthroughs use real data, and become a method skill

- **What:** the oil and gas walkthroughs follow real records, read live. The integration walkthrough follows well
  164166 and the two names of the Compañía General de Combustibles; the Lab walkthrough shows the model's real
  calculation for its example well. Each walkthrough says what it is for (`para_que`) and which part of Rastro each
  step shows (`parte`). The new `walkthrough` skill (step 7b, after `show-in-app`) makes this the method for any
  domain. The renderer runs each step's queries: raw SQL as the «without Rastro» reader, SPARQL over Rastro.
- **Why:** the first version, written by GPT at the user's request, used invented wells and a maintenance source
  Rastro does not load. Next to real data that was hard to tell apart and sold a missing feature. The user asked for
  each walkthrough's purpose to be explicit.
- **Numbers (23/10/2026):**
  - «CGC ENERGIA SAU» had 78,621 declarations and «COMPAÑÍA GENERAL DE COMBUSTIBLES S.A.» 8,684; Rastro counts
    87,305 for one company;
  - Lab well 165404: 51.64 − 3.57 + 6.80 − 0.72 = 54.15 million m³.

## 2026-10-23 — The walkthrough opens the technical part of the deck, with a bridge on AI

- **What:** in the oil and gas deck, the three «Paso a paso» slides open the technical appendix (10–12), before
  the results. A new slide 13, «Lo mismo le pasa a un asistente de IA», shows the measured scores: without Rastro 7 of
  10, SQL with Rastro's links 10 of 10, with Rastro 10 of 10. The Lab walkthrough follows the Rastro Lab slide
  (18–20). Footers and the demo script's slide references were renumbered. The `walkthrough` skill now says where its
  slides go.
- **Why:** the user saw the walkthrough as the motivation for semantic technologies and for using LLMs with knowledge
  graphs. The bridge slide states the measured reason: the gain comes from integrating once, with evidence (SQL with
  the same links scores the same); the graph is where that integration is defined, documented and audited, and gives
  the AI concepts and evidence to cite.

## 2026-10-23 — The Lab walkthrough explains the formula's origin and shows the real trail

- **What:**
  - Step 3 says where the formula comes from: a linear regression whose coefficients are learned on the wells
    before 2025, with ridge so that none takes off.
  - It then shows the example well's calculation variable by variable (value, training average, coefficient,
    contribution), followed by the grouped explanation.
  - Step 4 queries that well's published prediction live: its value and range, the factors stored with it, and the
    four records it used (`prov:used`), each with its rule, evidence and source.
  - `lab/gas/modelo.py` gains `ajustar()`, the fit shared by `entrenar()` and the new `detalle()`. Predictions are
    identical to before (maximum difference 0) and the model's tests pass.
- **Why:** the user found the formula unexplained and the traceability step to be text without a concrete example.
- **Numbers (well 165404, 23/10/2026):**
  - stages (53 − 38.8) × 0.651 = +9.28;
  - lateral length (3,186 − 2,278 m) × −0.0050 = −4.53;
  - the grouped explanation sums to 54.15, and the published prediction is 54.148.
  - The fracturing was reported on 04/10/2024, before the well started in 02/2025, and loaded on 24/04/2025, after it.

## 2026-10-23 — The oil and gas deck opens with five measured facts

- **What:** the cover keeps the logo and «Los datos cambian. Las preguntas, no.», and adds five measured facts, each
  with its «without Rastro» value:
  - 10 of 10 correct answers (without Rastro, 7);
  - 5 of 5 consistent answers (without Rastro, 3);
  - 1 line to absorb a source change;
  - 1 place to correct a value (without Rastro, 5);
  - 100 % of the 107,841 links with source, rule and evidence.

  A line says how and with which limits they were measured, in the appendix.
- **Why:** the user asked for a high-impact first slide with the strongest facts, explained later. All five come from
  the measurement files (`resultados.json`, the change and correction tests, `evidencia.json`). The slide's notes keep
  the caveat that SQL with Rastro's links also scores 10 of 10 (slide 13).

## 2026-10-23 — The cover stays; slide 2 says why a semantic layer, in words

- **What:** replaces the previous entry. The cover is back as it was. A new slide 2, «Por qué una capa semántica»,
  gives six reasons without figures:
  - meaning is defined once;
  - sources are joined once, with evidence;
  - questions do not depend on how the data is stored;
  - every answer can be audited;
  - AI asks about concepts instead of guessing tables;
  - open standards, not a black box.

  Each reason is shown later with real data. Footers and every slide reference in the demo script moved by one.
- **Why:** the user wanted the original cover, and the conceptual case for a semantic layer before any number.

## 2026-10-24 — One selected well connects Lab inputs, calculation and evidence

- **Approval:** the user asked to implement the proposed walkthrough improvements.
- **Behavior:** one Lab selector drives its input/mapping table, numerical contribution explorer, raw source rows,
  semantic provenance and prediction comparison. Original missing values remain visible beside imputed values;
  late arrivals and pending human confirmations remain explicit. The split is chronological, but the example is
  retrospective and does not claim historical availability of every input.
- **Run identity:** compare the complete saved input table and code version, plus the selected well's prediction,
  contributions and source IDs, respecting saved precision. Audit queries use the exact captured run ID. Current
  evidence is distinguished from the historical run's saved numeric inputs and outputs.
- **Deployment:** reuse the existing Lab read-only role and initialize it through the energy linker on new installs.
  Layer's baseline role is unchanged. No model algorithm, source rule or measured evaluation result changes.
- **Deck:** four slides follow 165404 from report 4799 through 53 stages and its 54.14767395030741 M m³ prediction;
  slide footers and script references were updated. Details and validation: `docs/walkthrough-improvements.md`.


## 2026-10-24 · Connect the regression formula to the Lab example

The user approved a short explanation in Lab step 3 and one appendix slide before the numeric example. Show the generic linear prediction and its equivalent training-mean form, define the symbols, and explain that fracture groups five terms. Keep the selected well calculation live; the model and data are unchanged.


## 2026-10-24 · Evaluate trees before adding them to Lab

The user approved a controlled experiment and a visual tree. Compare the unchanged ridge with a fixed forest and a depth-2 tree, on both raw and semantic paths, for 2023/2024/2025 and a late-fracture sensitivity. In 2025 retrospective path B, MAE is 16.67 for ridge, 16.92–16.98 for three forest seeds and 21.17 for the small tree (million m³). Improvements are not consistent across years or availability conditions; retain ridge in the app. The small tree is an experimental diagram, not a forest explanation. Evidence and limitations: `docs/experiments/gas-trees/README.md` and `results.json`. No model run was published.


## 2026-10-24 · Attempt a thesis-style Q12 tree replication

The user requested a tree-based reproduction before considering app integration. The original PDF/code could not be retrieved because UTDT redirects to maintenance; requested a local/alternate copy. The existing Q12 check was rerun, followed by a fixed-seed Random Forest comparison on 501 local wells. Existing features give interleaved R² 0.496–0.500; a separately labeled extension with loaded registry coordinates, depth, start year and fracture intensities gives 0.671–0.675, and 0.355–0.361 on starts from 2023. The thesis values (0.75, 642 wells) remain prior-note references pending primary-source verification. Keep the result experimental: cohort, preprocessing, feature and ensemble differences prevent claiming reproduction or replacing the current Lab model. Evidence: `docs/experiments/gas-thesis/`.

## 2026-10-24 · Verify the supplied thesis and replay its tree pipeline

The user provided `MiM_Fernandez Gazzaniga_2026.pdf`, SHA-256 `2e1e9cd9e1375c4ca763acba96493440c460fea1e46dff6d6fa24affd8de336b`. Reviewed its methodology and verified Table 4 directly. Downloaded the public nonconventional-production history into an isolated ignored folder and filtered observations through March 2026. Implemented the reported RF/XGB/LGBM hyperparameters, log target, KNN, target encoding, derived features and training-only temporal neighbors. Strict coverage gives 609 wells, versus 642 in the thesis, and ensemble R² about 0.69 versus its 0.7539. A separate cutoff-only completeness sensitivity gives 616 wells and similar interleaved results. Record the missing fluid-window coefficients, source-version differences, preprocessing ambiguities, unit labels and retrospective limitations; no exact-reproduction or independent-validation claim. Preserve the earlier simplified experiments. No database or published model changes. Evidence: `docs/experiments/gas-thesis/pdf-replay/`.

## 2026-10-24 · Add a thesis-algorithm alternative and real tree visualization

The user clarified that exact thesis reproduction is not the goal: compare its algorithms and add a useful alternative to the app. Compared fixed RF/XGB/LGBM configurations with direct and log targets on the existing months-2–7 variables. Select using mean annual MAE in 2023–2024; show 2025 separately. Direct Random Forest was selected (validation MAE 15.802 million m³); 2025 MAE is 16.274 versus ridge 16.672, with lower R² (0.430 versus 0.457). Treat the small improvement as exploratory. Keep ridge as default and all candidate results visible.

Added the alternative selector, shared-well comparison, source explorer, a real first-tree path with its estimate distinguished from the complete forest average, and SVG download. Added plain Spanish FAQ descriptions of ridge, RF, XGBoost, LightGBM, selection and the visualization. Saved outputs are fingerprinted and disabled when inputs/code differ; no production ML dependencies, mapping edits or replacement of the published RDF run. Evidence and generation instructions: `docs/experiments/gas-alternative/`. The independent-reference publication gate remains pending, so the UI explicitly labels this evaluation experimental.

The user also approved highlighting the selection and comparing each well against regression. Mark Random Forest as selected on 2023–2024 and direct XGBoost as the lowest-MAE tree configuration in 2025; these are different distinctions. Compare each selected well's absolute prediction errors against observed gas, showing better, worse or equal accuracy. The example well favors regression despite the forest's lower overall MAE. Verification: 89 tests passed, 5 skipped; both app views and desktop/mobile browser checks passed, including wells where the forest performs better and worse.

## 2026-10-25 · Show Layer's answer, connections and original evidence

The user approved a simple Layer screen sketch and matching slides: answer first, then an optional calculation, connected sources and original records. Reuse the existing ownership-share question, with Chevron and Loma Campana as the initial explanation. Business results show company and attributable oil; the technical view retains all columns and identifiers. Company/concession selection drives the calculation, original stake text, labeled production sample and name-link evidence. Preserve pending human confirmation of grouping corrections. Distinguish operated production from ownership share and acknowledge that SQL over the same links can obtain the result. No ontology, mapping, source, evaluation reference or Lab model changes.

The three slides use a captured query bundle whose unrounded concession products reconcile with the main answer; the app reads live data. Evidence and generation: `docs/experiments/layer-answer/`, `docs/slides/layer_story.py`; brief script: `docs/demo-layer.md`. Existing slides retain their layout and their numbered footers shift to match the inserted slides. Verification: 94 tests passed, 5 skipped; lint passed; all ten app questions and both views passed, including the open explanation for Chevron and YPF; desktop/mobile interaction and three slide layouts passed.

The user additionally requested missing company logos. Verified eight more official websites, retained 19 official icons/logos with source URLs and fingerprints, and prefer local assets before the existing remote fallback. Of 43 company names in visible Layer answers, 18 have retained assets, 13 have configured sites with remote fallback, and 12 remain unverified/text-only. Excluded a recruiting-business homonym and white-only images that were invisible on tables. This changes display metadata only; it does not establish entity identity or corporate ownership. Sources, limitations and unresolved names: `docs/company-icons.md`.

## 2026-10-26 · Preserve Layer's earlier comparison and result detail

The user approved three compatibility adjustments after comparing the new journey with the previous app. Restore attributable gas in the business answer table; provide the complete concession breakdown in an optional panel; and show a live optional comparison of operated oil versus ownership share for the selected company. Use the existing answer and explanation queries, retain their units, label the two measures explicitly, and avoid restoring static company-specific figures as if they applied to every selection. The compact answer-first journey remains. Verification: 94 tests passed, 5 skipped; lint and whitespace checks passed; live checks confirmed gas, the complete breakdown and comparison in both app views; desktop/mobile interaction and company switching passed.

## 2026-10-26 — Fixes after reviewing the Lab and Layer walkthrough commits

- **Lab, pending marker:** only an AI-reviewed company-name correction (rule «corrección revisada», from
  `linking/energia/correcciones.csv`) is shown as waiting for a person. A stake corrected with a document («… con
  documento», verified by a person) is no longer marked pending, and the fracturing values are not marked by the
  rule of the reporting company's name. The test now checks both cases.
- **Layer, Chevron's pending link:** most of Chevron's Loma Campana share rests on «COMPAÑIA DE HIDROCARBURO NO
  CONVENCIONAL S.R.L.» counting as Chevron, an AI-reviewed link still waiting for a person. The app warns about it
  next to the calculation, and the three slides say it in visible text. In both cases the status is read from the
  link's evidence, not typed.
- **Lab step 3:** restored why a single coefficient can look odd (correlated fracturing variables) and how the
  coefficients are learned.
- **Model selector:** the experimental tree alternatives are shown only with «Ver detalles técnicos»; the business
  view keeps the regression.
- **Slide notes:** the three Layer slides' notes are in Spanish, and percentages use the Spanish format.
- **Not decided here:**
  - which walkthrough belongs in the timed demo;
  - restoring the without/with Rastro contrast of the first moment;
  - the framing of the tree results;
  - the company logos.

## 2026-10-26 — Python comments and docstrings in English

- **What:** the Spanish comments and docstrings of 46 Python files are now in English (about 400), following the
  project's language rule. Identifiers, queries, prompts given to the AI evaluator, stored rule and evidence texts,
  and every text a user sees stay as they were.
- **Checked:** each file's syntax tree, with docstrings blanked, is identical to the previous commit, so no code
  changed. Tests, lint and both app views pass.
- **Left for later:** `lab/gas/modelo.py`, `alternative.py`, `thesis_pipeline.py`, `compare_trees.py` and
  `reproduce_thesis.py`. Their source is fingerprinted: the model's version and the alternative's and the thesis
  experiment's receipts would change. They will be translated together with a new published run.

## 2026-10-26 — The app can be shown in English, with Spanish as the default

- **What:** a switch in the sidebar («Idioma»), also `?lang=en` in the address.
  - Code texts moved to `app/textos/*.yaml`, with Spanish and English per key. That is about 300, from
    `app/dominio.py`, `app/lab.py` and the app's frame.
  - The oil and gas configuration, the help texts and the general FAQ have English overlays (`*.en.yaml`) that
    hold only the texts. They are laid over the Spanish file, and anything untranslated falls back to Spanish.
  - Numbers follow the language. The AI writes its query explanations, and what it says when it lacks the data,
    in the chosen language. The evaluation's Spanish prompts are unchanged.
- **Checked:**
  - Every text the oil and gas screens show in Spanish is identical to before, in both views
    (`app/text_snapshot.py`).
  - `tests/test_idioma.py` checks that overlays only fill existing keys and keep their placeholders.
- **Still Spanish in English:**
  - data from the sources: names, rules, evidence;
  - the per-well explanation generated by `lab/gas/modelo.py`, which waits for the step with a new run;
  - glossary term names, which are dictionary keys;
  - the technical view's extra texts, and the other domains and oncology (phase 2).

## 2026-10-26 — English interface, phase 2: technical view, other domains and oncology

- **What:**
  - The remaining code texts (technical view, the experimental tree screen, the oncology screen in `app/app.py`)
    moved to `app/textos/*.yaml`.
  - The suppliers, research-affiliations and oncology configurations, the oncology FAQ and its simple-words list
    got English overlays.
  - Internal names stay fixed where code compares them (tabs, radio choices, table titles); only labels change.
- **Checked:**
  - In all four domains and in both views, every Spanish text is identical to before, and neither language raises
    an error (`app/text_snapshot.py`, now also able to drive the oncology screen).
  - 105 tests pass, among them `tests/test_idioma.py`.
- **Still Spanish in English:**
  - data from the sources and measurement files: names, licences, rules, evidence, quality-rule names, evaluation
    questions;
  - query titles read from the ontology folders;
  - dictionary keys an overlay cannot rename: glossary term names and example-instance labels;
  - the per-well explanation from `lab/gas/modelo.py`, which waits for the step with a new run.

## 2026-10-26 — The first demo moment goes back to YPF; Chevron to the appendix; trees as an experiment; no logos

- **First moment:**
  - One slide again, «Sin Rastro YPF: 21,4 M m³ / Con Rastro: 12,6». Today's data gives 21,39 and 12,57.
  - In the app, «¿Por qué este número?» opens on YPF and Loma Campana: 50 % of 5,146,799 m³. YPF's names are joined
    by the same name, so nothing in it waits for a person.
  - The contrast card and the slide say that Vista's and Chevron's shares rest on AI-reviewed corrections awaiting
    a person.
  - The three Chevron slides move to the appendix (15–17) as «Del número a la evidencia».
- **Tree models:** shown only in the technical view, with neutral wording: no star, trophy or «más preciso que la
  regresión»; a single well is not enough to prefer a model. Rastro keeps the regression. They are out of the demo
  script.
- **Company logos removed:** the icon module, the website list, the 19 stored official icons and the calls to icon
  services. Tables show company names only: no trademark question in a commercial demo, and the app works offline.
- **Why:** the user approved the four recommendations made after reviewing the Lab and Layer walkthrough commits.

## 2026-10-26 — Clarity: what Rastro is, one link status, live contrast numbers

- **First screen:** under the slogan, one sentence on what Rastro is and how to read each screen (question → answer →
  «¿Por qué este número?»), with the three link marks.
- **One status mark for every link** (`app/enlaces.py`), read from the link's rule and evidence: 🔹 Regla automática,
  🟠 Revisada por IA, falta una persona, ✅ Confirmada por una persona (a correction with its document). It is the
  «Estado» column of every link table (the «¿Por qué?» tables and the technical link tables), the pending note of the
  Layer story and the Lab's marks and input statuses. Before, the same status was said in five different ways.
- **The demo's contrast cards read their numbers live:** each oil and gas card (questions 1–3) has its queries, SQL
  over the sources as they come for «Sin Rastro» and SPARQL for «Con Rastro», and its texts name the values in braces.
  Under the card, the date of each source's latest load. A test fails if a card with queries types a number. Today
  the values equal the ones that were typed: 21,4 / 12,6 M m³ (8,8 too many, 55 million barrels, US$ 3.600 million at
  an assumed US$ 65), 12.006 or 15.809 wells (3.796 disagree), Neuquén 6.256 / La Calera 482 of 6.636.
- **Why:** the user approved improvements 1, 2 and 5 of the clarity review. The slides still carry their own typed
  copy of these numbers.

## 2026-10-26 — Four tabs in the business view, one volume unit, slides with the app's numbers

- **Tabs:** the business view has Demo, Preguntar, Por qué confiar and Rastro Lab. «Paso a paso» opens inside «Por
  qué confiar»; the frequent questions open from a button in the sidebar. The technical view keeps both as tabs. In
  «Preguntar», «Comprobar una afirmación» and «Enriquecer con datos de afuera» appear only with «Ver detalles
  técnicos». Before: six tabs and five question modes.
- **Units:** every computed volume in the business view is in millions of m³ (answer tables, «¿Por qué este
  número?», the calculation trail and the appendix slides): `formatos` says whether a column is in m³ (`m3`) or in
  thousands of m³ (`miles_m3`, gas as declared). The technical view keeps the exact figure; the original records
  stay in their source's unit, labeled. Before, oil came in m³ and gas in thousands of m³, next to cards in M m³.
- **Slides read the app's numbers:** `app/contraste.py` computes each contrast card's numbers for the app and, from
  the command line, writes them to `docs/slides/numeros/energia.json`; `build.py` fills tokens such as
  `{{energia.e01.ypf_sin}}` and fails if one is missing. The three contrast slides (integration, traceability,
  maps) use them, notes included. Rebuilt today, the deck shows the same numbers as before.
- **Why:** the user approved improvements 3 and 4 of the clarity review and slides that read the app's numbers.

## 2026-10-26 — Oil and gas query gate, trust cards that state their status, plain messages when a service is down

- **Query gate** (`layer/energia/query-checks.yaml`): one entry per competency query (15), with its fingerprint and
  columns. The expectations come from SQL over the raw tables, never from Rastro's output: cq2 (YPF's wells by type
  and how many the registry assigns to another company), cq13 (the fracture report and gas months of well 166133)
  and cq15 (2 companies listed on an exchange in the saved Wikidata answer) are full checks; the rest are row bounds
  with their basis (LIMIT 10 with more candidates in the raw tables, or a ceiling such as the 300 concessions of the
  map). `python layer/method.py verify energia --expectations layer/energia/query-checks.yaml`: 15 of 15 passed.
- **«Por qué confiar»:** under each card, one line on how its number was measured. The evaluation cards say their
  date and, while the publication gate is pending, «🟠 referencias revisadas por IA, falta que una persona las
  confirme»; the change card, that the database was really changed and left as it was; the audit card, that it
  covers every link, not a sample.
- **A service down:** if Ontop or Postgres does not answer, each tab says so in plain words where the answer would be,
  with the command for whoever runs the demo, and the rest of the screen keeps working (answers already saved on
  disk still show). Checked by stopping the oil and gas Ontop.
- **Why:** the user approved these three items after the clarity review.

## 2026-10-26 — Aligned volume columns, Lab prepared first and drawn last, trust slide and English glossary

- **Volumes:** a column of millions of m³ uses the decimals of its largest value (15,9 · 4,0 instead of 15,9 · 3,99).
- **Rastro Lab's first load:** the warm-up trains the model in its own thread as soon as the app starts, the waiting
  message says what happens and how long it takes, and the Lab tab is drawn last, so «Preguntar» and «Por qué
  confiar» no longer wait for the model after a data change.
- **The «Por qué confiar» slide reads the app's numbers:** `contraste.trust_numbers` computes them for the app and
  for `numeros/energia.json` (`{{energia.confiar.*}}`). «79 en lugar de 12,6» became «un número equivocado»: no
  file holds that figure directly. Other slides still type figures (the gas answer, the Lab error, quality counts,
  the Wikidata table); they are the next candidates.
- **English glossary:** an overlay entry may be `{term, text}`, so «Participación» reads «Share» in English; all 28
  terms of the three domains. The shale-gas term now says the sources declare thousands of m³ and Rastro shows
  millions.
- **Why:** the user asked to continue with the pending clarity improvements.

## 2026-10-26 — Method: a log written by commands, two levels of validation, rules tested per constraint

Priorities 1 to 3 of the affiliations experiment's conclusions, approved by the user as planned. Recorded in that
experiment's log as method changes made after it; they do not change its measured result.

- **Experiment log by command** (`layer/experiment_log.py`, `method.py experiment --start/--stop/--append/--lint`):
  hours come from the sessions; the lint refuses duplicate keys, overlaps, an end before its start, open sessions and
  hours that differ from the intervals. `close-phase` lints before committing. The affiliations log was rewritten once
  by the command; its parsed content is identical apart from the three new entries.
- **Two levels of validation:** each `query-checks.yaml` entry declares `evidence: invariant | independent`; the
  lifecycle binds a question to its own entry and records the level, and the technical view shows it. New
  assertions: `keys` (affiliations' cq1 now proves it covers exactly the 1,456 source mentions) and `bounds` (cq2: each
  organization in 1 to 100 publications). Oil and gas: cq2 and cq13 are `independent`, the other 13 `invariant`.
  The three affiliations questions were revalidated (technical). The publication gate refuses a reference reviewer who
  approved the requirements; the contracts name both roles.
- **Rules tested per constraint:** quality examples now break every `sh:property` or `sh:sparql` block of each rule
  and assert the reported severity. Oil and gas got 7 more broken cases, affiliations 6 and two declared severities
  (Warning, Info); no rule of either domain turned out wrong. The oil and gas correction got a checker with exact
  expectations (`correccion.py verificar`, run by `correccion.sh`) and a broken-fixture test; the recorded run passes.

## 2026-10-26 — Affiliations: the five linking defects fixed, e3 and e5 re-measured

- **Blind score first** (GPT's source-blind reference, AI-reviewed, pending a person): with Rastro 4/5, SQL with
  Rastro's links 4/5, without Rastro 3/5. All three missed e5; 30 of 1,456 mentions differed.
- **Fixed in one place** (`linking/afiliaciones/link.py`): a glued footnote letter, matching across segments, a short
  name inside a longer one, and the generic acronym «CCT» (it names a centre only with that centre's own ROR acronym
  in the same segment). The six «CIC» acceptances became rejections under the approved definition (a shared acronym
  does not name); 13 new candidates were rejected; all pending a person.
- **Re-measured, re-running the same saved queries:** C and D 5/5 (e3 70, e5 37 for a reference of 38), B 3/5.
  Disagreement with the reference 30 → 5 mentions (the debatable «Hospital Italiano»). The re-measured score is
  optimistic: the fixes were guided by the same reference. The blind number is the first one.
- **Why:** the user asked to fix the defects and re-measure e3 and e5, saying so.

## 2026-10-26 — Rastro Lab in English, with a new published run

- **The explanation leaves the code:** the sentences `lab/gas/modelo.py` writes for each prediction (summary,
  factors, facts and their marks) are in `app/textos/modelo.yaml`, in Spanish and English; `explicacion_a`,
  `explicacion_b`, `num`, `signo`, `marca` and `socios_texto` take a language, Spanish by default. Facts carry an
  `id` so the app does not compare a visible name. Data from the sources (names, link rules, evidence, raw columns)
  stays as it comes. The Spanish explanations of all 559 wells are byte-identical before and after, so the blind test
  of the explanations (`a_ciegas.py`) is unaffected.
- **The technical view's tables** (what goes in, what the model learned, the weight of each concept) get English
  headers in the app, laid over `modelo`'s Spanish ones by position; a test checks the Spanish lists still match
  `modelo`. «Pesa dos cosas» listed three factors since depth was added; it now names no count.
- **New run** `20261026-212547-1b8209a1`: the run version is the fingerprint of `modelo.py`, so the old run showed
  "differs in code version". `--comparar` against `20261021-140450-6e4f1278`: 0 wells with another input or
  prediction. Re-run because they name the run: quality (same failures; the «Prediccion» rule checks the predictions
  of every published run, 5,590 → 6,149), the predictions evaluation (`energia_lab`: same answers and scores), the
  query gate (15/15) and the slide numbers (only `Prediccion_revisados` changed).
- **Why:** the user asked for Rastro Lab in English with a new published run.

## 2026-10-26 — The predictions rule checks the current run; the change check in English

- **Quality:** the «Prediccion» rule read the predictions of every published run (11 runs, 6,149 checked), so its
  count grew with each publish and the slide said «· 6.149» for 559 predictions. Its data query
  (`ontology/energia/calidad/datos.yaml`) now takes only the current run's: 559 checked, none fail; the other rules
  and their failures are unchanged. Re-run: quality and the slide numbers (only `Prediccion_revisados`).
- **The change test's warning** («Rastro avisa: …») is recorded in Spanish by each domain's `probar.py`. In English
  the app writes the three known checks (units, scope, vocabulary) again with the numbers it reads from the recorded
  text; any other check is shown as recorded. The recorded results are not touched, so nothing is re-measured.
- **Why:** the user approved both after the Lab in English.

## 2026-10-27 — Affiliations: the linking fixes tested on unseen affiliations

- **What:** 100 more works from the same approved capture (seed 20261027, none of the original 100; 886 mentions,
  556 strings), linked with the rules before and after the five fixes, in a temporary table, against a blind
  annotation by three fresh Claude reviewers who saw only the strings and the ROR list.
- **Result:** mentions that agree 854 → 866 of 886; precision 0.961 → 0.985; recall 0.979 → 0.977. The fixes
  generalize; the earlier 5/5 re-measurement remains optimistic because it scores questions on the tuned sample.
- **Found:** a footnote digit glued to a name (6 strings) and a short name inside a longer one not followed by
  «de/del/of» (2). Not fixed, so the holdout stays a fair measurement; three reviewer calls were wrong.
- **Why:** it was the pending fair test; the user asked to complete the pending work. A person still has to confirm
  both references.

## 2026-10-27 — Easier to debug: the screen code split by part, and how to trace a number

- **What:** `app/dominio.py` (1,598 lines) is now the package `app/dominio/`: `common.py` (258 lines), `answers.py`
  (540), `hood.py` (351), `trust_view.py` (265), `faq.py` (69) and `screen.py` (174). The split was done by a script:
  every function is identical to the original once `module.name` is read as `name` (71 of 71, checked on the syntax
  tree). Modules call each other as `common.run(...)`, so a call says where the function lives and a test patches it
  there; `dominio.<name>` keeps working for the rest of the app. A new test fails if a variable takes a module's name
  (a tab called `trust_tab` hid the module of that name; the app check found it, the unit tests did not).
- **Guide:** ONBOARDING.md traces one demo number (YPF's share in Loma Campana) from the raw tables, through the linker,
  the mapping and the SQL Rastro generates, to the screen, with commands that were run.
- **CI** already ran ruff and pytest on every push (`.github/workflows/calidad.yml`); nothing to add.
- **Checked:** 139 tests, ruff, `check_domain.py` for oil and gas, suppliers and affiliations (both views, every
  example query) and oncology's screen in the browser. No number changes, so nothing is re-measured.
- **Why:** the user asked that the code be easy for developers to review and debug.

## 2026-10-27 — Skills checked against the code, generic, without typed numbers

- **What:** all 15 skills were reviewed against the repository (26 files changed). A mechanical check confirmed
  every path, compose service and `method.py` command they name; three reviewers then read five skills each.
- **Fixed:** steps that no longer matched the code (the link classes live in the registry, the independent reference
  is `eval/referencias.json`, `layer/experiment.py` runs the gates, footers are written by `estilo.py`, a model edit
  needs `--publicar`); repeated steps became one-line handoffs; the slide procedure lives only in `decks`; measured
  numbers are read through placeholders, never typed; every app text is edited in Spanish and English; the
  research-affiliations domain is in the examples.
- **Generic:** method skills name no domain or data source outside their `examples.md`. Only `rastro-lab` and `decks`,
  the demo's own skills, stay specific.
- **Left for a decision:** commands to fill the experiment log's header fields (until then the skill says to fill
  them by hand and run `--lint`), and a guard for the suppliers change test (until then the skill says not to run it).
  The slide `e-ejemplo-ia` still types three measured numbers.
- **Why:** the user asked to review all skills, and that they stay generic for any domain and source.

## 2026-10-27 — Documentation for developers, and the repository is public

- **What:** `ONBOARDING.md` (start, stop, restart, check, reset, and how to trace a number), `docs/code-structure.md`
  (how a value flows, what each main file does, where to change what, what the Spanish file names mean), and a link
  to the GitHub repository in the app's sidebar, in Spanish and English.
- **The repository is public;** the plan's open question about keeping it private is closed by that.
- **Why:** the user wants developers to be able to run, review and debug Rastro on their own.

## 2026-10-28 — Decoupling, step 1: Rastro Lab is the oil and gas extension

- **What:** the shared screen (`app/dominio/`) no longer imports Rastro Lab. A domain names its own code in its YAML
  (`extension: gas_lab.GasLab`); `app/dominio/extension.py` defines the interface (`Extension`: a tab, a walkthrough's
  example record and published run, its step flags, a demo moment, the warm-up, its slide numbers), every method
  empty by default. The Lab tab's three modules moved unchanged to `app/extensions/gas_lab/`. The walkthrough
  placeholder `{pozo_ejemplo}` is now `{registro_ejemplo}`.
- **Same screen:** every visible text of the four domains, in Spanish and English, is identical before and after
  (`app/text_snapshot.py`, 16 views); the slide numbers JSON is identical; `check_domain.py` passes for oil and gas,
  suppliers and affiliations; the Lab demo moment and the four walkthrough steps checked in the browser. The
  model's code (`lab/gas/modelo.py`) is not touched, so its published run stays valid. Nothing re-measured.
- **Inside the extension,** `lab.py` still names `energia`: that is its domain, so it is not coupling.
- **Why:** the user asked that the main app stay independent of the domains (plan in `docs/plan-decoupling.md`).

## 2026-10-28 — Decoupling, step 2: units, warnings and slide numbers are configuration; no default domain

- **Units:** a domain declares the units its screen scales (`unidades: {m3: {escala: 1000000}, …}`);
  `idioma.millions(value, "m3")` became `idioma.scaled(value, scale)`. The answer table, «¿Por qué este número?» and
  the outside-data view read the domain's YAML (`formatos`, `numeros`, `externo.numericas` and `tecnicas`).
- **Change warnings:** the three Spanish regexes in shared code (oil and gas units, suppliers' scope, oncology's
  vocabulary) are now each domain's `avisos_cambio` (pattern, and the English text in its `.en.yaml`); numbers keep
  the decimals they were recorded with. The saved change results are not touched.
- **Slide numbers:** the oil and gas queries of `contraste.story_numbers` are `numeros_demo` in `energia.yaml`
  (one-row queries plus arithmetic, like a contrast card; `{fallas}` is the failing data a prediction used).
- **Oil and gas code moved into its extension** (`app/extensions/energia/`, the class renamed `OilAndGas`): the
  «Paso a paso» of the first answer (`story.py`, was `app/layer_story.py`) and the correction view (`correction.py`,
  with its texts in `app/textos/energia.yaml`). Demo moments of a type the shared screen does not know go to the
  extension.
- **No default domain:** `layer/answer.py` (12 functions) and `ontology/calidad.py` require it; oncology's legacy
  scripts pass `"oncologia"`; the `calidad` service names `energia` in compose.
- **Same screen:** see the snapshot comparison in the commit; nothing re-measured.

## 2026-10-28 — Decoupling, step 3: oncology's screen leaves app.py; the frame knows no domain

- **What:** `app/app.py` went from 913 lines to 45: logo, language, view switch, domain selector and
  `dominio.render`. Oncology's screen moved as it is to its extension (`app/extensions/oncologia/screen.py`, class
  `Oncology`), which tells the template it draws its own screen (`has_own_screen`). Its FAQ, plain-words questions and
  diagram moved next to it; its 228 texts moved from `app/textos/app.yaml` to `app/textos/oncologia.yaml` (keys
  `app.*` → `oncologia.*`). Every domain now has a `config:` in `app/dominios.yaml`.
- **Not rebuilt on the template:** the user chose to keep oncology's screen as it is (rebuilding it would change its
  look and its demo script); it is now one more extension, so the decision can be revisited without touching the frame.
- **Same screen:** see the snapshot comparison in the commit; nothing re-measured.
- **Why:** the user asked that the main app stay independent of the domains.

## 2026-10-28 — Decoupling, step 4: a test keeps the shared code generic

- **What:** `tests/test_generic_code.py` reads the frame and the shared template (`app/app.py`, `app/dominio/`,
  `idioma`, `contraste`, `enlaces`, `grafo`, `check_domain`, `layer/answer.py`) and fails if a name or a string of
  their code (not a comment or docstring) names a domain, a source the registry knows or a business word that slipped
  in before (pozo, well, concesión, m³, YPF), or if they import an extension. The words come from
  `layer/dominios.yaml`, so a new domain is covered without editing the test.
- **What it found and moved:** the outside-data diagram's labels and saved columns (now `externo.grafo` and
  `columnas_guardado` in `energia.yaml`), MeSH as the source of `rdfs:label` (now `label_source` in the registry) and
  the model tab's internal name (`lab` → `model`; the label is still «Rastro Lab»). `app/text_snapshot.py` lost its
  oncology branch: oncology renders through the template like the others.
- **Why:** so the frame stays independent of the domains after this change, not only today.

## 2026-10-28 — The shared oil and gas deck in sync; slides with inline styles only

- **What:** the shared deck had 27 of the repo's 40 slides and old numbers (the quality slide said 5.590 predictions
  checked, now 559; its page numbers and one sentence of «1 · Preguntar» were behind). It now has the 40 slides, the
  repo's order and sections, and every number from `docs/slides/numeros/energia.json`. It had no content of its own
  beyond the repo's; the layout the page editor had saved for `e-integracion` was replaced by the repo's slide.
- **Slides fixed for the deck's format:** 17 slides (12 of the oil and gas appendix, 5 of the other decks) used a
  `<style>` block, classes or margins, which the shared deck drops. They now use inline styles only, measured in the
  browser at the same positions (only `preguntas-*` lists are tighter without their item margins). The generator of
  the three «Del número a la evidencia» slides (`docs/slides/layer_story.py`) writes inline styles too, and one of its
  sentences is shorter so the slide ends above the footer (927 → under 900 px).
- **No typed numbers:** `e-ejemplo-ia` reads B, D and C from the evaluation through `{{energia.confiar.*}}`.
- **Guard:** `tests/test_slides_format.py` fails if a slide in a deck has `<style>`, a class or a margin, or a
  placeholder without its number.

## 2026-10-28 — «Bajo el capó»: a SPARQL editor that checks the query, and an R2RML mapping editor

- **What:** the SPARQL console is now a code editor (Ace, through `streamlit-ace`, the one new dependency) with line
  numbers and colors. Before a query runs, Rastro checks its syntax (an error is marked on its line and column) and
  warns about terms the dictionary does not declare; «Ejecutar» stays off while it has an error. A new part,
  «Editor de mapeos (R2RML)», loads the domain's mapping or an uploaded `.ttl`, checks it (Turtle syntax with its
  line; every triples map with a table and a subject; every predicate-object map with a property and a value; every
  class and property in the dictionary; `ontology/check.py`'s shared-property rule), shows what changes and saves it
  to the real file only if it passes. The file it replaces goes to `mappings/.backup/` (not versioned), with one-click
  undo. Ontop's development mode restarts on the change in about two seconds (seen in its log); the app waits and
  says whether Rastro answers with the new mapping.
- **Why:** the user asked for a real editor with a syntax check, and to load and edit mappings from the app. The
  user chose the dependency and saving to the real file with checks over a download-only draft.
- **Limits:** the checks do not know the database: a table or column that does not exist only shows when Ontop
  refuses the mapping, and then the app says so and offers the undo. The app's `mappings/` mount is now writable.

## 2026-10-28 — Slide 3: a conceptual schema of a semantic layer

- **What:** a new slide after «Por qué una capa semántica» (`e-esquema-capa`): the sources as they come on the left,
  the semantic layer in the middle (the business dictionary drawn as Empresa, Concesión and Pozo with their relations,
  and its translations, joins with evidence and quality rules), and who uses it on the right (business questions, AI
  assistants, models, other tools). Business words only, as in the rest of the story; the technical pieces stay in
  the appendix («Cómo está armado»). Every later footer moved one place (by the footer alone: the styling script's
  other changes to slides it had not touched were discarded), and the demo script's slide numbers too.
- **Why:** the user asked for a slide 3 with the conceptual schema, so the audience sees the whole before the cases.

## 2026-10-28 — The demo opens with the problem; the six reasons become the summary

- **What:** the story is now 9 slides: cover; the problem («¿quién produjo más gas?», operated vs. share); the
  schema of a semantic layer; the four moments; «Por qué una capa semántica» as the summary; «Consideraciones».
  «Qué es Rastro» left the oil and gas deck: the schema says the same with more, and it showed the suppliers'
  dictionary words (now oil and gas words in the repo copy). The demo script follows the new order, and its audience
  line now says consultants and data teams who know SQL, as agreed. The app's Demo tab already had the same four
  moments in the same order; it is unchanged.
- **Why:** five slides before the first live moment were too many for three minutes, two of them said the same, and
  the strongest hook (the two rankings) came fourth. The user approved the change.

## 2026-10-28 — A Colab notebook that shows how Rastro explains an ML prediction

- **What:** `lab/notebooks/rastro-lab.ipynb` (with an «Open in Colab» link) trains the same ridge model with the
  raw-table features (A) and with Rastro's (B), using `lab/gas/modelo.py` itself, and centers on the explanation:
  well 165404 explained as columns (A) and as concepts with their facts, rule, evidence, source and what to look at
  twice (B); the 2025 predictions to review (24 of 49 rest on a link or a value that does not come as is from the
  source; 36 of 49 had their fracturing loaded after the well started); what the Aguada Pichana Este correction
  changes (37 of 49 predictions); other algorithms (forests 16.92–16.98 against ridge 16.67); and a last cell that
  fails unless its 559 predictions are the published run's (they are, within 0.0005 million m³).
- **Data:** a snapshot of the model's five inputs and the published predictions, `lab/notebooks/datos/` (about
  670 KB, the B file compressed), saved by `lab/gas/snapshot.py` with a manifest of fingerprints. It is the one
  exception to «data outside the repo» (CLAUDE.md says so), because Colab cannot reach Postgres or Ontop.
  `tests/test_notebook_snapshot.py` fails when `modelo.py` changes until the snapshot is saved again.
- **Why:** the user asked for an advanced companion for technical audiences that shows Rastro's explanation
  capability for ML; accuracy is the same with and without Rastro, so the notebook says so first.

## 2026-10-28 — The notebook shows the algorithm and runs every algorithm tried

- **The algorithm:** a new section shows the ridge regression's formula and its code (read from `modelo.py`
  with `inspect`), checks that scikit-learn's `Ridge(alpha=1)` gives the same predictions (difference 9·10⁻¹³) and
  that a well's prediction is exactly the average well plus its contributions.
- **The experiments:** the last section runs, with settings the reader can change (features A or B, cutoff date,
  fracturing as it was when the well started, ridge's alpha), the concession median, ridge, the small tree and the
  forest of `compare_trees.py`, and Random Forest, XGBoost and LightGBM with the thesis settings on log gas and on
  gas (`alternative.py`). The thesis pipeline is left out: it needs its own downloads.
- **What it shows, with the published settings:** XGBoost and Random Forest on gas directly have a slightly lower
  mean error than ridge (B: 16.12 and 16.27 against 16.67) and a lower R² (0.40 and 0.43 against 0.46); on log gas
  they do worse. The notebook says so, and that ridge is published because it splits exactly into contributions
  Rastro can back with evidence, not because it is the most accurate on every cut. With 49 test wells these
  differences move with the seed and the cutoff year.
- **Why:** the user asked to see the linear regression and to run every algorithm from the notebook.

## 2026-10-28 — The notebook shows what Rastro adds to a tree model

- **What:** a section 7 with XGBoost on gas: TreeSHAP contributions (XGBoost's own `pred_contribs`, no new package)
  grouped into the same three business factors as ridge, with Rastro's facts and flags next to each; the XGBoost
  predictions to review with their reason (47 of 49 for 2025, counting late fracturing); XGBoost trained with the
  fracturing as it was when each well started (error 16.12 → 16.29: part of today's accuracy rests on data that
  arrived later); and the Aguada Pichana Este correction reaching XGBoost (49 of 49 predictions change).
- **The message:** Rastro does not make trees more accurate; it works on the inputs, so provenance, the list to
  review, data without the future and a correction made once apply to any model. What an ensemble loses is ridge's
  exact account: TreeSHAP splits the prediction, and Rastro puts the evidence next to each contribution.
- **Why:** the user asked what Rastro adds to trees, with examples in the notebook.

## 2026-10-28 — The notebook, clearer; the Lab tab links to it

- **Clearer:** section 2 is a two-line answer and its baselines moved to section 6 (which gains the median of all
  wells); section 7 breaks the 47 wells to review into section 4's reasons plus late fracturing; a paragraph says why
  ridge and XGBoost split a prediction differently (even with opposite signs) while Rastro's facts stay the same;
  tables have no row numbers and wrap long text («Real» is now «Gas real»); two waterfall charts show well 165404 from
  the average well to its prediction, with ridge and with XGBoost side by side.
- **In the app:** the Rastro Lab tab ends with «Para correrlo uno mismo: abrir el cuaderno en Colab · verlo en
  GitHub» (`lab.show_lab.notebook`, Spanish and English).
- **Why:** the user asked for a clearer notebook and a link to it from the app.

## 2026-10-28 — A pilot offer and a 6-slide executive deck

- **Pilot offer:** `docs/piloto.md`, one page in Spanish for a prospect: the problem, what Rastro does, what the demo
  already measured (with its source), a 6-week pilot week by week, success criteria measured with the demo's own
  tests on the client's data, what the client provides (read-only access, about 2 hours a week of a business
  person), what stays with the client (open standards) and the honest limits. The price, the contact and one
  client-specific criterion are placeholders for the owner.
- **Executive deck:** `docs/slides/mazos/ejecutivo.json`, six slides reused from the main deck plus one new one:
  the cover, the two rankings, the schema, the US$ 3.600 millones answer, «Por qué confiar» and the pilot
  (`e-piloto`). `docs/slides/build.py` now numbers each deck's footers by its own order, so a shared slide shows
  the right page in every deck. Published as its own shared deck.
- **Why:** the user asked for what it takes to sell; a concrete pilot and a short deck for decision makers came first.

## 2026-10-28 — Rastro is under the Business Source License 1.1

- **What:** `LICENSE` is the official BSL 1.1 text (checked word for word against the SPDX list) with its
  parameters: licensor German Braun; Additional Use Grant: production use for research and teaching, and a 90-day
  evaluation for any organization; Change Date 2030-10-28; Change License Apache 2.0. `NOTICE` credits each public
  data source with the license recorded in `rastro_meta.source`. The README says what is free and what needs a
  license.
- **Why:** to sell it, commercial production use has to be licensed, while the repository and the Colab notebook stay
  public for evaluation and trust, and each version opens up after four years (an answer to lock-in). Alternatives
  set aside: PolyForm Noncommercial (never opens up), open core (more work to split), a private repository (the public
  notebook link would break).
- **Pending, for the owner:** a lawyer's review before the first contract, and the intellectual-property clause of
  any employment contract.

## 2026-10-28 — The one-pagers tell the oil and gas case

- **What:** `docs/one-pager.md` and `docs/one-pager-tecnico.md` now describe the demo case (YPF's oil, the same
  question four ways, a renamed column, a corrected stake, Rastro Lab) instead of oncology, and point to the pilot
  offer. Every number is the one in `layer/energia/resultados.json`, `layer/energia/cambio/correccion.json` and
  `docs/slides/numeros/energia.json`; oncology's numbers stay in `docs/results.md`.
- **Why:** the old pages described a case the demo no longer shows.

## 2026-10-28 — The experiment log's header and human hours are set by command

- **What:** `python layer/method.py experiment <domain> --set KEY=VALUE` sets `sources` (one per call),
  `question_author`, `started_on`, `ended_on` or `result`; `--human-hours STEP=HOURS` records the person's time on a
  step. Dates must parse; human hours only go to a step that exists; agent hours stay derived from the sessions.
  `tests/test_experiment_log.py` covers it.
- **Why:** the last fields filled by hand; a log written only by commands cannot carry a typo past the lint.

## 2026-10-28 — The suppliers change test runs under the guard

- **What:** the registry's `change_guard` gains `renamed: {table, column, to}`, the column a `cambio` test renames,
  so `layer/change_guard.py` no longer names oil and gas tables in code. Suppliers has its entry (mapping, saved
  answers, `usaspending.contract`, `awarding_agency`), and its `deshacer` restores from the snapshot instead of
  multiplying the amounts back by 1000.
- **Numbers:** the guarded run on the live database gives the same verdicts as before in every act (with Rastro 9 of
  9 break on the rename and 9 of 9 are fixed in one line; without Rastro 6 of 9 stay right and 3 break). After it,
  `usaspending.contract` has the same 36.145 rows, sum and minimum, the mapping is byte for byte the same, and no
  snapshot schema is left. The amounts quoted in `resultado.json` are today's answers, which moved since the last
  run because the data did.

## 2026-10-28 — Affiliations: the glued footnote number is fixed; the longer-name rule is not

- **What:** `linking/afiliaciones/link.py` removes a footnote number glued to a name («11Hospital…», «3CEMIC»), as it
  already did for a letter. A second rule (an institute's name followed by a word of its own is the start of a
  longer name) was written too, and dropped.
- **How it was tested:** both fixes were written first; then a second holdout (`docs/experiments/research-affiliations/holdout-2/`,
  seed 20261028 fixed before drawing, 100 works, 993 mentions, 583 strings, none of the earlier samples' works) was
  annotated blind by three fresh Claude reviewers.
- **Numbers:** before, 955 of 993 mentions agree (precision 1.000, recall 0.909). With both fixes, 942 (recall
  0.886): the longer-name rule fixed nothing new and broke 11 strings («Instituto Nacional de Tecnología
  Agropecuaria» followed by a local town). With only the footnote number, 955 again, and on the first holdout, where
  it was found, 866 → 872 of 886. Rastro's own sample does not change (529 links, 104 candidates) and the saved
  queries were re-run with no change.
- **Why:** a fix tuned on a holdout is only known to generalize on a set it never saw; this one showed that one of
  the two did not. The second holdout is consumed for the longer-name rule. Its reference was reviewed by AI only.

## 2026-10-28 — The executive deck: a sharper «why trust it», «why now», a sales talk track and an English version

- **Slide 5** (`x-pruebas`, only in the executive deck): four big numbers instead of four paragraphs, and the fourth
  test is now Rastro Lab (24 of 49 predictions say which value to check, same error as without Rastro) instead of
  link coverage, which the main deck keeps. All numbers are placeholders.
- **«Por qué ahora»** (`x-por-que-ahora`): three changes (AI assistants already query the data, sources change often,
  models have to explain themselves), with no market figures: none were measured.
- **Speaker notes for sales:** a deck can give a shared slide its own notes (`notes` in `mazos/*.json`), so the
  executive deck carries a «qué decir» talk track per slide (about 5 minutes) without touching the main deck's notes.
- **English version:** `mazos/ejecutivo-en.json` with `en-*` slides, generated from the Spanish ones and kept as
  files; `"lang": "en"` swaps the number separators (US$ 3,600 million). An exception to «decks in Spanish only»,
  for international prospects; the decks skill says a change to an executive slide goes to its `en-` twin.
- **Export:** `build.py --export <deck> <folder>` writes the shared deck's slide files with numbers, page numbers and
  notes filled in. Both shared decks are updated; PowerPoint and PDF come from the deck's own Export menu.
- **Not done:** a price slide, since a «[US$ __]» placeholder must not reach a prospect; the price stays in
  `docs/piloto.md`. A draft email to a prospect is in `docs/email-prospecto.md`.
- **Why:** the user asked for all the improvements offered on the executive deck.
