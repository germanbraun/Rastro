# Preguntas a ciegas: una evaluación que no armamos nosotros

Hoy las preguntas de la evaluación, sus referencias y la revisión las armó el mismo equipo (con un asistente de IA) que construyó Rastro. Por eso la ventaja de Rastro puede ser circular: las preguntas se escribieron sabiendo qué tiene el diccionario. Esta prueba lo corta: las preguntas las escribe alguien de afuera, sin ver Rastro.

## Quién

Una persona del sector del dominio (por ejemplo, un consultor de petróleo y gas o de compras públicas) que no haya visto la app, el diccionario ni las preguntas de ejemplo. Basta con una persona; mejor dos.

## Qué se le pide

Entre 5 y 10 preguntas que le harían a estos datos en su trabajo, con estas reglas:

1. **En palabras de negocio**, como se las preguntaría a un colega. Sin nombres de tablas ni de columnas.
2. **Con una respuesta exacta:** un número o una lista corta. «¿Cuánto…?», «¿Cuáles son las 5…?», «¿Cuántas… que…?».
3. **Con las definiciones a la vista:** si la pregunta depende de una definición («operadora», «no convencional», «cerca de»), escribir cuál usa.
4. **Sobre lo que hay:** las fuentes del dominio, tal como se describen en «¿De dónde salen los datos?» de la app (sin mostrarle nada más).
5. **Sin mirar Rastro** antes de mandarlas.

Se le da solo la lista de fuentes y, como ejemplo de formato, una pregunta inventada de otro dominio.

## Qué hacemos con ellas

1. **No se cambian.** Si una pregunta no se puede responder con las fuentes, se anota como «fuera de alcance» y cuenta en el resultado; no se reescribe.
2. **La referencia la escriben dos caminos por separado:** una consulta SQL sobre las fuentes tal como vienen, escrita a mano por alguien que no mira Rastro, y la consulta sobre Rastro. Si coinciden, esa es la referencia; si no, se adjudica con los datos de cada fuente (como en `layer/*/adjudicacion.md`) y se anota quién tenía razón.
3. **Se mide con el mismo protocolo** que el resto de la evaluación (`layer/evaluar.py <dominio> prompt|try|rerun|puntaje`): el mismo asistente de IA, sin ver la respuesta, sin Rastro (SQL), SQL con los enlaces de Rastro y con Rastro, hasta 3 intentos.
4. **Si Rastro falla por algo del diccionario** (falta un concepto o una definición), se anota y **no** se arregla antes de publicar el número. Se puede arreglar después, como una medición aparte, diciéndolo.

## Qué se publica

| | Sin Rastro (SQL) | SQL + enlaces | Con Rastro |
|---|---|---|---|
| Correctas, de N preguntas a ciegas | | | |
| Fuera de alcance (las fuentes no alcanzan) | | | |
| Fallas del diccionario de Rastro | | | |

Con una frase: quién escribió las preguntas (su rol, no su nombre), cuándo, y que no vio Rastro antes.

## Formato para mandar las preguntas

| # | Pregunta | Definiciones que usa | Respuesta esperada (número o lista) |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
