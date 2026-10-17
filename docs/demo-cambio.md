# Demo de cambio: cuando la fuente cambia

Muestra el costo de mantener: qué pasa con las 20 queries guardadas cuando AACT publica una versión nueva, y dónde se arregla. Todo con `layer/cambio/cambio.sh`, desde la carpeta del repo.

## Comandos

| Comando | Qué hace |
|---|---|
| `cambio.sh probar` | Vuelve a ejecutar las 20 queries del SQL directo y de Rastro, las compara con las respuestas guardadas y corre el control de vocabulario |
| `cambio.sh renombrar` | Acto 1: `aact.studies.overall_status` pasa a llamarse `status` |
| `cambio.sh valores` | Acto 2: `TERMINATED` pasa a escribirse `Terminated` (todos los estados) |
| `cambio.sh arreglar renombrar` / `arreglar valores` | Cambia **una línea** del mapeo (`mappings/rastro.r2rml.ttl`) y reinicia Ontop |
| `cambio.sh deshacer` | Deja la base y el mapeo como estaban. **Correrlo siempre al terminar.** |

`probar` tarda medio minuto. Reiniciar Ontop, otro medio minuto.

## Lo que pasa (ensayado el 16 oct 2026)

| | SQL directo | Rastro |
|---|---|---|
| Antes del cambio | 20 de 20 iguales | 20 de 20 iguales |
| **Acto 1**, columna renombrada | 5 queries con error | 14 con error: falla todo junto |
| … después de arreglar | sigue con 5 errores: hay que reescribir 5 queries | **20 de 20**, con 1 línea del mapeo |
| **Acto 2**, valores en otro formato | 5 respuestas pasan a 0, **sin error** | igual, pero el **control de vocabulario avisa** |
| … después de arreglar | sigue dando 0 hasta que alguien lo note | **20 de 20**, con 1 línea del mapeo |

Las preguntas afectadas son las que filtran por estado: q03, q08, q09, q14 y q17. Por ejemplo, «ensayos detenidos en cáncer de páncreas» pasa de 569 a 0.

## Cómo contarlo con honestidad

- **En el acto 1 Rastro falla más que el SQL directo**, porque la primera consulta que falla deja la conexión de Ontop en un estado de error y arrastra a las demás. Decirlo así: «Rastro falla todo junto y en voz alta; se arregla en un lugar».
- **En el acto 2 Rastro también da 0** hasta que se arregla. La diferencia es que la capa es el lugar natural para controlar el vocabulario: el control compara los estados con los que documenta la ontología y avisa.
- **Unas vistas SQL también absorberían el cambio de nombre.** Es cierto, y conviene decirlo: cualquier capa ayuda, vistas incluidas. Por qué esta capa y no vistas está en la diapositiva 8.

## Cuántas queries tocaría cada cambio

Cuenta de las 20 queries del SQL directo que usan cada columna, contra los lugares que hay que cambiar en Rastro:

| Si cambia… | Queries del SQL directo | En Rastro |
|---|---|---|
| `browse_conditions` (enfermedad de cada ensayo) | 11 | 1 (`linking/conditions.sql`) |
| `interventions` / `intervention_other_names` | 10 | 1 (`linking/drugs.sql`) |
| `gene_symbol` (targets de ChEMBL) | 8 | 1 mapeo |
| `overall_status` (estado) | 5 | 1 línea del mapeo |
| `phase` | 5 | 1 línea del mapeo |
