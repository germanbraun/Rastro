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

Resultado: 74,4 % de las intervenciones enlazadas y 99 de 100 correctas en la revisión a mano. El plan preveía un LLM para los casos ambiguos, pero con este nivel no hace falta para el MVP. Lo que no enlaza es sobre todo lo que no es un fármaco ("placebo", "chemotherapy").

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

- **Regla "nombre como palabra entera"** para dosis, separadores y texto libre ("Pembrolizumab 200 mg", "Nivolumab or Pembrolizumab"): 94 % de precisión revisada a mano, cobertura de 74 % a 81 % de las intervenciones.
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

"¿Cómo lo supe?" muestra la consulta del LLM, el SQL que Ontop genera y ejecuta (`/ontop/reformulate`, disponible en modo desarrollo) y las fuentes. Hace visible que Rastro no copia datos: traduce la pregunta a SQL sobre las tablas originales y los enlaces, con uniones simples. En la comparación, ese SQL queda al lado del que el LLM escribió a mano.

Cada fuente lleva un ícono según dónde vive: 🐘 Postgres (AACT, ChEMBL, openFDA, enlaces de Rastro) y 🕸️ GraphDB (MeSH completo, con su jerarquía copiada en Postgres).


## 2026-10-16 — Posicionamiento: el valor es la integración revisada

Rastro acierta porque la parte difícil (qué ensayo prueba qué fármaco) se resolvió una vez, con reglas explícitas, y se revisó a mano. Si al SQL directo le diéramos las mismas tablas de enlaces, probablemente acertaría casi todas. El mensaje honesto es: **el valor de Rastro es la integración revisada, expuesta como un vocabulario de negocio**. La capa semántica la hace estable ante cambios de tablas, autodocumentada, estándar y con procedencia por dato. La demo lo explica así en "Por qué Rastro acierta".

Pendiente, si se quiere medir: un cuarto enfoque, "LLM + SQL sobre las tablas de Rastro", para separar cuánto aporta la integración y cuánto la capa semántica.

## 2026-10-16 — Las explicaciones van en Preguntas frecuentes

La demo se mantiene corta: cada pestaña muestra lo esencial y una línea que manda a "Preguntas frecuentes". Las explicaciones viven en `app/faq.yaml`, una pregunta y una respuesta corta por entrada, editable sin tocar código. Los números de las respuestas (reintentos, tiempos, formas de reconocer un fármaco) los completa la app desde la evaluación guardada, así que no quedan desactualizados.
