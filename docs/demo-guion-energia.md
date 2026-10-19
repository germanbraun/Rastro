# Guion de la demo de Rastro: petróleo y gas en Argentina (5 minutos)

> **Los datos cambian. Las preguntas, no.**

Para operadoras y consultoras del sector, sin conocimientos técnicos. Tres momentos: **integración, trazabilidad y cruce con mapas**, y un cierre con las fuentes que se suman. Cada momento termina en un número: sin Rastro y con Rastro. El mazo de petróleo y gas (`docs/slides/energia.html`) y la app en el dominio **Petróleo y gas en Argentina**, modo **Demo en 3 pasos**, con «Ver detalles técnicos» apagado.

## Antes de empezar

1. Levantar todo: `cd infra && docker compose up -d` (lo hace alguien técnico, una vez).
2. Abrir http://localhost:8501. Dominio: **Petróleo y gas en Argentina**; arriba, **Demo en 3 pasos**. Recorrer los tres pasos una vez: cada uno corre en vivo.

## 0:00 – 1:00 · Qué es Rastro y el problema (diapositivas 1 a 4)

> «Las bases de datos del sector no están conectadas entre sí. Rastro incorpora un diccionario de negocio: pozo, concesión, empresa, participación. Cada fuente se traduce a esos términos una sola vez.»
>
> «La demo usa cinco fuentes públicas de cuatro organismos: la producción declarada pozo por pozo y los mapas de la Secretaría de Energía, los gasoductos de ENARGAS, el Instituto Geográfico Nacional y el registro global de empresas.»

## 1:00 – 2:00 · 1 · Integración (app, paso 1; diapositiva 5)

> «¿Cuánto petróleo de 2025 le corresponde a cada empresa? Sumando por quien declara la producción, a YPF se le asignan 21,4 millones de metros cúbicos. Pero el petróleo se reparte entre los socios: su parte es 12,6. Petronas, que no opera ningún pozo, tiene 2,1. Los socios estaban en un texto del mapa; Rastro los separa una vez.»

## 2:00 – 3:00 · 2 · Trazabilidad (app, paso 2; diapositiva 6)

> «¿Cuántos pozos opera YPF? El padrón dice 12.006; las declaraciones juradas, 15.809. Rastro aplica una regla escrita, rige quien declara el último mes, y en cada pozo muestra lo que dice el padrón.»

Abrir **¿De dónde sale la respuesta?** para mostrar un pozo en desacuerdo.

## 3:00 – 4:00 · 3 · Cruce con mapas (app, paso 3; diapositiva 7)

> «La capa satelital marca posibles venteos de gas, pero solo dice la provincia. Rastro ubica cada punto en su concesión y llega a la operadora: La Calera, de Pluspetrol, tiene 482 y ningún punto de venteo declarado. Es un indicio para revisar, no una acusación.»

## 4:00 – 5:00 · Más fuentes y cierre (diapositivas 8 y 9)

> «Sumar fuentes no rehace nada: con ENARGAS, 38 concesiones con posibles venteos tienen el gasoducto de transporte más cercano a 10 km o más; con el IGN, 60 caen en áreas protegidas; con GLEIF, 12 empresas tienen identificador global.»
>
> «En síntesis: el valor está en integrar los datos una sola vez y mantenerlos en un único lugar. El siguiente paso es un piloto con datos propios.»

## Si preguntan

- **«¿Cómo saben que es correcto?»** Los números «sin Rastro» salen de SQL directo y legible (`layer/energia/sin-rastro.sql`). Todavía no hay una evaluación medida como en los otros dominios, y las correcciones de nombres (Chevron, Pluspetrol, CGC) las revisó un asistente de IA: falta que una persona las confirme.
- **«¿Por qué rige la declaración jurada?»** Es una decisión de negocio, escrita una vez y a la vista. Si se prefiere otra, se cambia en un solo lugar y vale para todas las preguntas.
- **«¿Los grupos salen de un registro?»** No: GLEIF no registra la matriz de estas empresas argentinas y Wikidata tampoco. Son correcciones revisadas, con su motivo.
- **«¿Y GraphRAG?»** En este dominio no hay todavía una fuente de textos. La misma idea que en proveedores y oncología (el grafo elige qué leer, la IA resume y cita) se aplicaría, por ejemplo, a resoluciones o informes de cada concesión.
