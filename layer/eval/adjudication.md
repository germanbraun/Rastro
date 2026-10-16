# Adjudicación: ¿quién tiene razón cuando B y C no coinciden?

Las respuestas de referencia salen de Rastro. Por eso, cuando el SQL directo (B) y Rastro (C) dan resultados distintos, B podría tener razón y Rastro estar equivocado. Esto revisa, con ensayos reales, cada pregunta donde la diferencia cambia el puntaje.

## Lo que la evaluación encontró en Rastro (y ya está corregido)

La primera corrida le daba a Rastro 19 de 20, pero la adjudicación mostró que **B encontraba ensayos que Rastro perdía**. Se corrigieron los enlaces de fármacos (`linking/`) y se volvieron a ejecutar las mismas queries:

- **Nombres con dosis, separadores o texto libre** ("Pembrolizumab 200 mg", "lenvatinib pembrolizumab", "Nivolumab or Pembrolizumab", "Coformulated vibostolimab/pembrolizumab"). Se agregó la regla "nombre como palabra entera": 94 % de precisión en dos revisiones de 50 enlaces.
- **Un error de ChEMBL**: lista "bicalutamide" entre los sinónimos de talazoparib, y Rastro descartaba el nombre por ambiguo. Ningún ensayo con bicalutamida quedaba enlazado. Ahora el nombre preferido de un fármaco gana sobre los sinónimos de otros.

- **Prodrogas**: una prodroga ahora actúa sobre los targets de su molécula activa, con el dato de ChEMBL (`active_chembl_id`). El acetato de abiraterona hereda el receptor de andrógenos de la abiraterona.
- **Una pregunta ambigua** (q08) no decía si "fase 2" incluía las fases 1/2 y 2/3. Se reescribió y sus tres respuestas se generaron de nuevo.

Salvo q08, las queries que escribió el LLM no cambiaron: solo los datos sobre los que corren.

## Resultado final

| | Correctas |
|---|---|
| LLM solo | 5 de 20 |
| LLM + SQL crudo | 18 de 20 |
| LLM + Rastro | 20 de 20 |

## Las dos que falla el SQL directo

| # | SQL directo | Rastro | Quién tiene razón |
|---|---|---|---|
| q02 · ensayos de fase 3 con fármacos anti-EGFR | 488 | 438 | **Rastro.** 40 de los 50 ensayos extra del SQL directo salen de "humab", un fragmento que encuentra dentro de "rhuMAb HER2" (trastuzumab, que es anti-HER2). Rastro pierde unos 10 ensayos reales en los que el fármaco solo aparece en los alias de AACT: queda a menos del 5 % y el SQL a un 9 %. |
| q16 · fármacos distintos en mieloma múltiple | 545 | 604 | **Rastro.** El SQL compara el nombre completo de la intervención y pierde fármacos escritos con dosis, en combinación o con código (PTK787 = vatalanib, Zevalin). En una muestra de 10 fármacos que solo encuentra Rastro, 8 son reales y 2 son ruido ("cytosine", y levofloxacino por ofloxacino). Aun descontando ese ruido, Rastro queda más cerca. |

## Cómo cambió el puntaje con la adjudicación

| | Primera corrida | Final |
|---|---|---|
| LLM solo | 5 | 5 |
| LLM + SQL crudo | 14 | 18 |
| LLM + Rastro | 19 | 20 |

El SQL directo subió porque las referencias mejoraron: varias "fallas" eran, en realidad, ensayos que Rastro no enlazaba. Rastro subió porque se corrigieron esos enlaces y la pregunta ambigua.

## Lo que el número no dice

Con un LLM fuerte, el SQL directo acierta casi tanto como Rastro (18 contra 20). **La ventaja de Rastro no está en cuántas acierta, sino en cuánto se puede confiar en cada respuesta.** Medido sobre las 20 respuestas guardadas:

| | SQL directo | Rastro |
|---|---|---|
| Correctas | 18 de 20 | 20 de 20 |
| Preguntas en las que tuvo que inventar cómo reconocer un fármaco en el texto | 16 de 20 | 0 (usa el enlace revisado) |
| Formas distintas de reconocer un fármaco | 4 (nombre exacto, ILIKE, pedazos del nombre, expresiones regulares) | 1 |
| Queries que necesitaron un segundo intento | 3 (por tiempo límite) | 0 |
| Tiempo de ejecución de las 20 queries | 20 s (una tarda 7 s) | 2 s |
| Procedencia de cada dato | enterrada en la query | una fuente por columna |

Lo que eso significa:

1. **Cada respuesta del SQL directo define las cosas a su manera.** "Ensayos que prueban el fármaco X" se calcula de cuatro formas distintas según la pregunta, así que dos respuestas del mismo sistema no son comparables. Rastro lo define una vez, lo revisa a mano y lo reusa.
2. **Sus errores no avisan.** 488 ensayos en vez de 438 parece razonable. Solo se descubre revisando ensayo por ensayo, como en esta adjudicación.
3. **El costo de integrar se paga en cada pregunta.** Con SQL directo, el LLM rehace la integración en cada query: más tiempo, más tokens y más lugar para errores. Con Rastro se hace una vez, y Rastro Lab la reusa.
4. **El LLM solo acertó 5 de 20**: listas de fármacos conocidos, pero ningún conteo.

**Cautela honesta:** el 18 de 20 del SQL directo es con el modelo más capaz y con notas del esquema. Con un modelo más barato, o con preguntas fuera de estas 20, la diferencia probablemente crezca, pero no está medido.
