---
name: mazos
description: Mantener la historia de la demo coherente en la app, el guion y los mazos de diapositivas, armar los mazos HTML y publicarlos. Usalo al cambiar un número o un mensaje de la demo, una diapositiva o el guion.
---

# La demo, el guion y los mazos

La historia de petróleo y gas son **cuatro momentos, una frase cada uno**, y se cuenta en tres minutos:

1. **Preguntar:** Rastro responde con evidencia (participación de YPF: 21,4 por quien declara contra 12,6 repartida entre los socios).
2. **La base cambia:** sin Rastro, consultas rotas que hay que encontrar; con Rastro, una línea.
3. **Predecir:** el mismo modelo con y sin Rastro predice igual; con Rastro la predicción se explica y marca los datos dudosos.
4. **Una corrección:** se corrige una vez y cambian solos la respuesta, lo que entra al modelo y su explicación.

Lo mismo en tres lugares, que tienen que decir lo mismo:

| Dónde | Archivo |
|---|---|
| App, pestaña Demo | `demo` y `demo_porque` en `app/dominios/energia.yaml` (los números salen de los JSON medidos) |
| Guion | `docs/demo-guion-energia.md` |
| Mazo | `docs/slides/mazos/energia.json` (orden) y `docs/slides/slides/*.html` (una diapositiva por archivo) |

## Pasos

1. **Cambiá el texto en los tres lugares a la vez.** Cada número de una diapositiva o del guion tiene que estar medido (en `layer/**/resultados.json`, `layer/energia/cambio/*.json` o lo que imprime `lab/gas/modelo.py`).
2. **Una diapositiva** es un `<section>` de 1920×1080 en `docs/slides/slides/<nombre>.html`, con el estilo de las demás (fondo `#F7F6F2`, títulos en `#14213D`, «Sin Rastro» y «Con Rastro» en dos tarjetas) y las notas del orador en `<aside>`. Las primeras siete son la historia; el resto va después de `anexo`.
3. **Estilo y HTML:** `python3 docs/slides/estilo.py` le da al mazo de petróleo y gas el estilo parejo (IBM Plex Sans y Source Serif 4, una escala de seis tamaños, tarjetas con borde fino, el pie con el número de cada diapositiva, los dibujos a una altura que entra); se puede correr siempre, da lo mismo. Después `python3 docs/slides/build.py` (genera `docs/slides/<mazo>.html` con sus tipografías; no se editan a mano).
4. **Revisalo en el navegador:** abrí `docs/slides/energia.html` y mirá las diapositivas que cambiaste. Medí que nada pase del pie: el contenido de cada diapositiva termina antes de los 920 px de alto (la medición con el navegador está en `docs/decisions.md`, 21 de octubre). Si algo pasa, se acorta el texto: nada se achica.
5. **Publicá en el mazo compartido** (si el usuario lo usa): copiá `order`, `sections` y `faces` de `docs/slides/mazos/energia.json` al `project/deck.json` del mazo y las diapositivas a `project/slides/`, y publicalo en el mismo artifact (leelo antes si cambió desde la última vez). `root` es la carpeta que **contiene** `project/`, y las rutas van con `project/` adelante: con `root` en `project/` los archivos quedan un nivel arriba y el mazo no los ve. Una diapositiva que salió del orden se borra al publicar (`null` en `files`): si no, aparece al final.
6. **Recorré la pestaña Demo** de la app y el guion de punta a punta, en voz alta: si no entra en tres minutos, hay que sacar algo.

## Reglas

- Solo petróleo y gas en la historia; proveedores y oncología son prueba de que generaliza (vista técnica, anexo).
- Sin nombres de herramientas en la vista de negocio («Rastro deduce», no el nombre del motor) ni de productos comerciales de grafos de conocimiento.
- Nada que el número medido no respalde: si un dato casi no se mueve, no se dice que cambia.
