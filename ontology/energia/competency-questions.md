# Preguntas de competencia: petróleo y gas en Argentina

Las preguntas que Rastro tiene que poder responder en el tercer dominio, pensado para operadoras y consultoras del sector. El diccionario de negocio ([`energia.ttl`](energia.ttl)) tiene solo lo necesario para estas diez, y cada una tiene su SPARQL en [`queries/`](queries/). Todas corren contra el tercer Ontop (http://localhost:8082/sparql). Los números «sin Rastro» salen de [`layer/energia/sin-rastro.sql`](../../layer/energia/sin-rastro.sql).

| # | Pregunta | Fuentes | Qué muestra | Sin Rastro → con Rastro |
|---|---|---|---|---|
| 1 | ¿Cuánto petróleo y cuánto gas de 2025 le corresponde a cada empresa, según su participación? | Capítulo IV, mapas | Los socios están en un texto del mapa: se separan una vez, con su porcentaje, y los nombres se unen entre fuentes. | YPF: 21,4 M m³ (todo lo que opera) → 12,6 M m³ (su parte); Petronas: no aparece → 2,1 M m³ |
| 2 | ¿Cuántos pozos opera hoy YPF? | Capítulo IV | El padrón y las declaraciones no coinciden: una regla escrita una vez decide, y la otra versión queda a la vista. | 12.006 o 15.809 → 15.809, con 3.796 pozos en desacuerdo explicados |
| 3 | ¿En qué concesiones vio el satélite más posibles venteos desde 2024, y quién las opera? | Mapas | Cada punto se ubica en el contorno de su concesión una vez, y así llega a la operadora. | Solo por provincia → por concesión y operadora (La Calera, Pluspetrol: 482, sin puntos declarados) |
| 4 | ¿Quiénes producen más petróleo no convencional? | Capítulo IV | «No convencional» (shale o tight) es una clase deducida: ningún mapeo la asigna. | — |
| 5 | ¿Qué concesiones con posibles venteos no tienen un gasoducto de transporte cerca? | Mapas, ENARGAS | Une dos organismos: la distancia de cada concesión al gasoducto más cercano se calcula una vez. | 33 concesiones con posibles venteos a 10 km o más; Chihuido de la Sierra Negra (YPF): 334, a 32,5 km |
| 6 | ¿Qué posibles venteos están dentro de un área protegida o cerca de una localidad? | Mapas, IGN | Cada punto se ubica respecto de localidades y áreas protegidas del IGN, con su evidencia. | 60 dentro de áreas protegidas (Auca Mahuida, Meseta Espinosa); 61 a menos de 3 km de una localidad |
| 7 | ¿Qué empresas tienen identificador global (LEI)? | Capítulo IV, GLEIF | El LEI se acepta solo si coincide el nombre legal, y lo descartado queda a la vista. | 12 empresas, entre ellas YPF, Pan American, Vista y Pluspetrol |
| 8 | ¿Qué concesiones hay que revisar por venteos, y por qué? | Mapas, ENARGAS, estudios ambientales | «Concesión para revisar» es una clase deducida de dos reglas escritas una vez: venteos sin gasoducto cerca, o sin planillas de venteo. | 45 concesiones: 33 sin gasoducto cerca, 21 sin planillas, 9 con las dos |
| 9 | ¿Qué áreas cambiaron de operadora entre 2023 y 2025, y cuánto producían antes y después? | Capítulo IV (2023 a 2025), mapas | Tres años de declaraciones juradas, unidos: mes a mes, quién declara la mayor parte de cada concesión, y cada cambio (`energia:OperatorChange`) con su evidencia. | 64 cambios; 27 son áreas que dejó YPF (Bentia, Petróleos Sudamericanos, Quintana, Pecom, PCR, Venoil) |
| 10 | ¿Quiénes declaran más gas de shale en 2025? | Capítulo IV | La misma clase deducida que el no convencional (shale), mirada por el gas: el gas y el petróleo salen de las mismas declaraciones juradas. | Medida: las tres formas (sin Rastro, SQL con enlaces y con Rastro) aciertan: YPF, Tecpetrol, Pluspetrol y 2 más |

## Conceptos de Rastro Lab

Rastro Lab responde otra pregunta: **¿Cuánto gas va a dar un pozo nuevo y por qué?** Para eso el diccionario suma cuatro conceptos, que usa el modelo de gas de Vaca Muerta (`lab/gas/`, detalle en [docs/lab-gas-vaca-muerta.md](../../docs/lab-gas-vaca-muerta.md)):

- `energia:WellStart`: cómo arrancó cada pozo (primer mes con producción, quién lo declaró, con qué nombre y qué tipo de pozo).
- `energia:Fracturing`: cómo se fracturó el pozo (rama horizontal, etapas, arena, agua y presión).
- `energia:gasMonths2to7`: el gas de los meses 2 a 7, lo que se predice.
- `energia:loadedOn`: cuándo se cargó el dato de fractura, para marcar el que llegó después de que el pozo arrancó.
- `energia:Prediction`, `energia:Contribution` y `energia:ModelRun`: cada predicción de una corrida del modelo, con su rango, el aporte de cada factor y los datos de Rastro que usó (`prov:used`). Las publica `python3 lab/gas/modelo.py --publicar`.

Preguntas sobre las predicciones (necesitan una corrida publicada):

| # | Pregunta | Para |
|---|---|---|
| 11 | ¿Qué predicciones de pozos de 2025 se apoyan en un dato corregido, y en cuál? | Lab |
| 12 | ¿Qué pozos de 2025 se esperan con más gas, en qué rango, y cuánto aporta cada factor? | Lab |
