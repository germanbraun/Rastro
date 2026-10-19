# Preguntas de competencia: petróleo y gas en Argentina

Las preguntas que Rastro tiene que poder responder en el tercer dominio, pensado para operadoras y consultoras del sector. El diccionario de negocio ([`energia.ttl`](energia.ttl)) tiene solo lo necesario para estas ocho, y cada una tiene su SPARQL en [`queries/`](queries/). Todas corren contra el tercer Ontop (http://localhost:8082/sparql). Los números «sin Rastro» salen de [`layer/energia/sin-rastro.sql`](../../layer/energia/sin-rastro.sql).

| # | Pregunta | Fuentes | Qué muestra | Sin Rastro → con Rastro |
|---|---|---|---|---|
| 1 | ¿Cuánto petróleo de 2025 le corresponde a cada empresa, según su participación? | Capítulo IV, mapas | Los socios están en un texto del mapa: se separan una vez, con su porcentaje, y los nombres se unen entre fuentes. | YPF: 21,4 M m³ (todo lo que opera) → 12,6 M m³ (su parte); Petronas: no aparece → 2,1 M m³ |
| 2 | ¿Cuántos pozos opera hoy YPF? | Capítulo IV | El padrón y las declaraciones no coinciden: una regla escrita una vez decide, y la otra versión queda a la vista. | 12.006 o 15.809 → 15.809, con 3.796 pozos en desacuerdo explicados |
| 3 | ¿En qué concesiones vio el satélite más posibles venteos desde 2024, y quién las opera? | Mapas | Cada punto se ubica en el contorno de su concesión una vez, y así llega a la operadora. | Solo por provincia → por concesión y operadora (La Calera, Pluspetrol: 482, sin puntos declarados) |
| 4 | ¿Quiénes producen más petróleo no convencional? | Capítulo IV | «No convencional» (shale o tight) es una clase deducida: ningún mapeo la asigna. | — |
| 5 | ¿Qué concesiones con posibles venteos no tienen un gasoducto de transporte cerca? | Mapas, ENARGAS | Une dos organismos: la distancia de cada concesión al gasoducto más cercano se calcula una vez. | 29 concesiones con posibles venteos a 10 km o más; Chihuido de la Sierra Negra (YPF): 334, a 32,5 km |
| 6 | ¿Qué posibles venteos están dentro de un área protegida o cerca de una localidad? | Mapas, IGN | Cada punto se ubica respecto de localidades y áreas protegidas del IGN, con su evidencia. | 60 dentro de áreas protegidas (Auca Mahuida, Meseta Espinosa); 61 a menos de 3 km de una localidad |
| 7 | ¿Qué empresas tienen identificador global (LEI)? | Capítulo IV, GLEIF | El LEI se acepta solo si coincide el nombre legal, y lo descartado queda a la vista. | 12 empresas, entre ellas YPF, Pan American, Vista y Pluspetrol |
| 8 | ¿Qué concesiones hay que revisar por venteos, y por qué? | Mapas, ENARGAS, estudios ambientales | «Concesión para revisar» es una clase deducida de dos reglas escritas una vez: venteos sin gasoducto cerca, o sin planillas de venteo. | 45 concesiones: 33 sin gasoducto cerca, 21 sin planillas, 9 con las dos |
