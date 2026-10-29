# Diapositivas

Un mazo por caso de uso, con la misma estructura: qué es Rastro, el dominio y su problema, las preguntas, la demo en tres momentos (sin Rastro y con Rastro), por qué confiar, consideraciones y un anexo técnico (arquitectura, diccionario de negocio y por qué funciona).

El mazo de petróleo y gas, el de la demo, es más corto: la historia va en las diapositivas 1 a 9 (el problema, el esquema de una capa semántica, la demo, por qué una capa semántica como resumen y las consideraciones), con la demo en dos actos: Rastro Layer (preguntar, la base cambia, una corrección) y Rastro Lab (predecir, donde la misma corrección ya llegó al modelo), y todo lo demás (pruebas, otras preguntas, mapas, textos y el detalle técnico) queda en el anexo.

| Mazo | Archivo | Guion |
|---|---|---|
| Proveedores del Estado de EE. UU. | `proveedores.html` | [demo-guion.md](../demo-guion.md) |
| Petróleo y gas en Argentina | `energia.html` | [demo-guion-energia.md](../demo-guion-energia.md) |
| Ensayos clínicos de oncología | `oncologia.html` | [demo-guion-oncologia.md](../demo-guion-oncologia.md) |

- **Ver:** abrir el `.html` del mazo en el navegador.
- **Editar:** cada diapositiva está en `slides/`; el orden de cada mazo, en `mazos/<nombre>.json`. Las diapositivas genéricas (qué es Rastro, beneficios, arquitectura, anexo) se comparten. Las notas del orador están en el `<aside>` de cada una. Después de editar, correr `python3 docs/slides/build.py`.
- **Números de la demo:** no se escriben a mano. Una diapositiva escribe `{{energia.e01.ypf_sin}}` (contraste), `{{energia.confiar.c_correct}}` («Por qué confiar») o `{{energia.demo.error_b}}` (las demás: afirmaciones, calidad, sin dato, Wikidata y Rastro Lab) y `build.py` lo completa con `numeros/energia.json`, los mismos números que muestra la app (`app/contraste.py`). Antes de construir, actualizarlos con `docker compose exec -T app python /app/contraste.py energia > docs/slides/numeros/energia.json`; si falta un número, `build.py` falla.

El mazo de petróleo y gas tiene un estilo parejo que aplica `estilo.py` (tipografías, escala de tamaños, tarjetas, pie con el número de diapositiva); después de cambiar una diapositiva, corré `python3 estilo.py` y `python3 build.py`.
