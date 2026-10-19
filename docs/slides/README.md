# Diapositivas

Un mazo por caso de uso, con la misma estructura: qué es Rastro, el dominio y su problema, las preguntas, la demo en tres momentos (sin Rastro y con Rastro), por qué confiar, consideraciones y un anexo técnico (arquitectura, diccionario de negocio y por qué funciona).

| Mazo | Archivo | Guion |
|---|---|---|
| Proveedores del Estado de EE. UU. | `proveedores.html` | [demo-guion.md](../demo-guion.md) |
| Petróleo y gas en Argentina | `energia.html` | [demo-guion-energia.md](../demo-guion-energia.md) |
| Ensayos clínicos de oncología | `oncologia.html` | — |

- **Ver:** abrir el `.html` del mazo en el navegador.
- **Editar:** cada diapositiva está en `slides/`; el orden de cada mazo, en `mazos/<nombre>.json`. Las diapositivas genéricas (qué es Rastro, beneficios, arquitectura, anexo) se comparten. Las notas del orador están en el `<aside>` de cada una. Después de editar, correr `python3 docs/slides/build.py`.
