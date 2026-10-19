# Adjudicación: petróleo y gas en Argentina

Las referencias salen de Rastro, así que donde las respuestas difieren se revisó con los datos antes de publicar un número. Revisión hecha por un asistente de IA (Claude Code), a confirmar por una persona.

| Pregunta | Diferencia | Qué se encontró | Resultado |
|---|---|---|---|
| e05 (gasoductos) | SQL + enlaces dio 33 en una forma; la referencia daba 29 | Rastro no tenía distancia para las concesiones sin ningún gasoducto a menos de ~100 km, y la pregunta las incluye. **Error de Rastro**: se corrigió `linking/energia/link.py` (si no hay gasoducto cerca, se mide contra todos) y se volvieron a ejecutar todas las consultas guardadas. | Referencia: 33 |
| e06 (áreas protegidas) | SQL sin Rastro dio 41–43; Rastro, 60 | Se volvió a contar con los contornos originales del IGN, huecos incluidos: 60. El SQL trata las partes de un área protegida con varios polígonos como un solo contorno y el test de paridad se invierte. | Referencia: 60 |
| e02, forma 2 | SQL sin Rastro dio 6.263 | Leyó «pozos con producción» como «con producción mayor que cero». La pregunta dice «con producción declarada»: es una lectura distinta, no un error de datos. | Cuenta como respuesta distinta |
| e01 (Rastro) | Rastro dio 0 en las 4 formas | El LLM unió la participación con la concesión por `:concession` en lugar de `:inConcession`. Las dos propiedades se parecen y la ontología no dice cuál va con cada clase. **Debilidad del diccionario**, no de los datos. Se dejó una sola propiedad (`:inConcession`) y se volvió a medir: 4 de 4 correctas. | Medido de nuevo: correcta |

Además, las primeras siete respuestas con Rastro se descartaron y se repitieron: las notas de SPARQL no decían cómo están escritos los nombres de empresa (las de proveedores sí). Se agregó la misma frase general («como en cada fuente, casi siempre en mayúsculas y con su forma societaria»), sin nombrar ninguna empresa.
