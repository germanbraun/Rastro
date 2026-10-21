Base PostgreSQL con las fuentes públicas tal como se cargaron y las tablas que deja el modelo de gas:

- `capitulo4.produccion` (2025), `capitulo4.produccion_historica` (2023 y 2024) y `capitulo4_anterior.produccion` (2018 a 2022): las declaraciones juradas mensuales del Capítulo IV, una fila por pozo, mes y formación. `prod_gas` es gas en miles de m³; `empresa`, la empresa que declara; `idareapermisoconcesion`, el código de la concesión.
- `sig_energia.concesion`: las concesiones del mapa, con los socios en un texto (`participacion`, con el formato «<br> EMPRESA: 50 %<br> OTRA: 50 %»).
- `fractura.fractura`: los datos de fractura (Adjunto IV), una fila por fractura informada: `id_base_fractura_adjiv` (su identificador), `idpozo`, `cantidad_fracturas` (etapas), `fecha_inicio_fractura`, `fecha_data` (cuándo se cargó en el portal), `empresa_informante`.
- `trayectoria.trayectoria`: las trayectorias de pozo (`idpo` es el identificador del pozo), con profundidad vertical y largo de la rama.
- `lab_gas.*`: lo que deja el modelo de gas en cada corrida.
  - `corrida`: `id`, `version`, `fecha`, `vigente` (la corrida vigente).
  - `prediccion`: `corrida`, `idpozo`, `gas` (gas esperado de los meses 2 a 7, millones de m³), `minimo`, `maximo`, `de_prueba` (pozos que empezaron en 2025).
  - `entrada`: lo que vio el modelo por pozo: `inicio` (primer mes con producción), `operadora`, `concesion`, `participacion` (el porcentaje de la operadora que usó), `rama`, `etapas`, `arena`, `agua`, `presion`, `profundidad`, `gas`.
  - `aporte`: el aporte de cada factor a cada predicción.

Los nombres de empresa pueden variar entre fuentes (con o sin «S.A.», acentos, mayúsculas).
