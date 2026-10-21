Además, las tablas que arma Rastro (esquema `energia`), con regla y evidencia:

- `inicio_pozo`: cómo arrancó cada pozo nuevo (`mes`, `empresa_id`, `nombre_declarado`, `id_concesion`, `gas_2_7`).
- `empresa_nombre` (`fuente`, `nombre`, `empresa_id`, `regla`): cada nombre de empresa en cada fuente y por qué es esa empresa; `regla` «corrección revisada» si se unió a un grupo a mano.
- `participacion` (`id_concesion`, `empresa_id`, `porcentaje`, `regla`): los socios de cada concesión; `regla` «corrección revisada con documento» si se corrigió.
- `fractura_pozo` (`idpozo`, `cargada`, …): la fractura de cada pozo, sumando las fracturas informadas hasta el mes en que arrancó; `fractura_registro` (`id`, `idpozo`, `usada`): cada fractura informada y si entra en la del pozo.
- `trayectoria_pozo`: la trayectoria de cada pozo, una por pozo.
