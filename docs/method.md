# El método de Rastro

Cómo se arma y se mantiene una capa semántica en la que se pueda confiar, en cualquier dominio. Es lo que ya se hizo en
petróleo y gas, proveedores y oncología, escrito como método. Todavía no está automatizado: este documento es el boceto.

## La idea

**Un agente arma y mantiene la capa semántica; cada decisión queda con su evidencia; una persona aprueba lo que es de
negocio.** El agente hace el trabajo; los controles deciden si está bien; la persona decide qué significa.

Tres principios:

1. **Primero las preguntas.** Lo que hay que mapear y cómo se mide si funciona sale de las preguntas de negocio.
2. **La corrección la deciden pruebas que se ejecutan**, no la opinión de un modelo: que cargue, que responda, que cumpla
   las reglas de calidad, que acierte las preguntas con referencias independientes.
3. **Lo que significa un dato lo decide una persona.** Si una empresa «opera», «es dueña», «tiene una participación» o
   «declara la producción» no es intercambiable. El agente propone, con evidencia y alternativas; no decide en silencio.

## Los pasos

Cada paso tiene una skill que lo hace, un control que decide si pasa, una aprobación humana solo donde hay una decisión de
negocio, y la evidencia que queda.

| # | Paso | Lo hace (skill) | Control que decide | Aprueba una persona | Queda como evidencia |
|---|---|---|---|---|---|
| 0 | **Preguntas de negocio** | `agregar-pregunta`: cada pregunta con sus definiciones y el tipo de respuesta | Cada pregunta tiene definición, respuesta esperada y su consulta | El cliente: qué preguntas importan y qué quiere decir cada palabra | `ontology/<dominio>/competency-questions.md` |
| 1 | **Conectar las fuentes** | `agregar-fuente`: descargar, cargar, registrar la carga | Conteo por fuente, huella de cada archivo, carga repetible | El recorte: qué entra y qué no | `rastro_meta.load_run` |
| 2 | **Diccionario mínimo** | Proponer solo los conceptos que piden las preguntas | `ontology-check`: cada término existe; una propiedad que usan dos clases va sin dominio | Las definiciones (por ejemplo, operada o por participación) | La ontología, con comentarios |
| 3 | **Mapeos** | Escribir cómo se traduce cada fuente al diccionario | Rastro arranca y cada pregunta de competencia responde | — | El mapeo R2RML |
| 4 | **Enlaces con evidencia** | Unir empresas, pozos y concesiones entre fuentes, con su regla y su texto | Regla de calidad: cada enlace tiene fuente y evidencia | Las correcciones dudosas («revisado por IA, a confirmar») | `prov:wasDerivedFrom`, regla y evidencia en cada enlace; CSV revisados |
| 5 | **Reglas de calidad** | Proponer reglas y valores posibles | `calidad` (SHACL) después de cada carga, con las predicciones que usan lo que falla | Los umbrales y si se corrige la fuente | `layer/<dominio>/calidad.json` |
| 6 | **Medir** | `evaluar`: tres caminos (sin Rastro, SQL con enlaces, con Rastro); qué hace cuando no tiene el dato; prueba de cambio | Evaluadores independientes que solo ven el prompt; referencias que no salen solo de Rastro | La adjudicación donde los caminos difieren; las pruebas a ciegas | `layer/<dominio>/resultados.json`, `adjudicacion.md` |
| 7 | **Mantener** | `pruebas-de-cambio`: ante un cambio en una fuente, el arreglo más chico | Volver a ejecutar las consultas guardadas; las predicciones afectadas, por `prov:used` | El arreglo | `layer/<dominio>/cambio/*.json` |

Rastro Lab agrega un paso aparte (`rastro-lab`): el mismo modelo con variables crudas y de Rastro, sin usar el futuro, y
cada predicción guardada con los datos que usó.

## Cómo se proponen los mapeos y los enlaces

**Acotar, decidir, probar.** Primero, métodos deterministas acotan las opciones: etiquetas, definiciones, tipos de dato,
valores de ejemplo y los mapeos que ya existen. Después, el modelo de lenguaje elige entre esas pocas opciones y explica por
qué, solo donde hay ambigüedad. Al final, la prueba que se ejecuta decide. Es más confiable y escala mejor que pedirle al
modelo el mapeo entero de una vez.

## Agentes: uno, con skills

- **La experiencia está en las skills**, no en agentes distintos: cada una con su contrato (qué recibe, qué devuelve),
  ejemplos y pruebas. El mismo agente carga la que hace falta.
- **Agentes separados solo donde importa la independencia:** el que evalúa no ve cómo se armó la respuesta, y el que
  escribe las preguntas a ciegas no ve Rastro. Un evaluador que ve las cuatro formas de una pregunta juntas ya no mide la
  consistencia: pasó, y esa medición se descartó.
- **Más agentes, solo si una medición lo pide:** muchas fuentes a la vez, o un diccionario que no entra en un contexto.

## Cuando algo falla: de qué tipo es

Cada falla de la medición se clasifica, para saber qué paso reforzar:

| Tipo | Ejemplo en Rastro | Paso que se refuerza |
|---|---|---|
| Falta el dato | Precios, reservas, 2026 | 1 (otra fuente) o decirlo |
| Enlace equivocado | Un nombre de empresa unido a otro grupo | 4 |
| Mapeo equivocado | Un dominio en el diccionario que convertía cada registro de fractura en una fractura | 2 o 3 |
| Consulta equivocada | Rastro llegó a la operadora por la participación y no por el nombre declarado | 2 (las notas del diccionario) |
| Definición ambigua | Producir: lo que opera cada empresa o lo que le corresponde | 0 |
| Dato imposible de la fuente | 111.515 psi de presión | 5 |

## Qué ya está probado y qué no

**Probado en un dominio, con números:** correctas 10 de 10 con Rastro y 7 de 10 sin Rastro; una corrección en 1 lugar
en vez de 5; las reglas de calidad encontraron errores reales; nadie inventó cuando faltaba el dato; las predicciones se
explican con sus registros. El mismo Rastro sirve en otros dos dominios.

**No probado:** que el método generalice sin rehacerlo. Eso se mide con el experimento de abajo.

## El experimento que falta

1. Elegir una fuente pública que Rastro nunca vio, de otro dominio.
2. Escribir antes sus preguntas de negocio, con alguien del dominio.
3. Armar la capa solo con las skills y los controles de este método.
4. Medir: horas, cuántas veces intervino una persona y por qué, cuántos errores atraparon los controles, y las preguntas
   correctas con los tres caminos.
5. Repetir en un segundo dominio sin reescribir las skills.

Si el segundo dominio pide solo sus definiciones y algunas reglas nuevas, el método generaliza. Si pide cambiar el
proceso, queda a la vista qué no es general todavía. Se publica lo que dé.

## Cómo se contaría

«Un agente experto en capas semánticas, para equipos de consultoría: arma y mantiene la capa con la evidencia de cada
decisión, y una persona aprueba lo que es de negocio.» Primero como herramienta de consultoras, para entregar proyectos de
integración más rápido y con trazabilidad; cada proyecto suma un dominio al método. El número que lo sostiene es el del
experimento: horas, intervenciones y errores atrapados.
