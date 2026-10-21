---
name: pruebas-de-cambio
description: Correr y registrar las pruebas que muestran qué pasa cuando una base cambia (una columna o una unidad) y cuando se corrige un dato una vez (la corrección llega a todos los resultados). Usalo al tocar layer/*/cambio/, los mapeos que esas pruebas cambian o las correcciones revisadas.
---

# Pruebas de cambio

Son el argumento central de la demo: con Rastro, lo difícil se arregla o se corrige en un lugar.

## La base cambia (`layer/<dominio>/cambio/cambio.sh`)

Simula una versión nueva de la fuente y vuelve a ejecutar las consultas guardadas de la evaluación, sin Rastro y con Rastro.

```bash
layer/energia/cambio/cambio.sh registrar    # los dos actos (columna renombrada, petróleo en barriles), con y sin arreglo
```

- Cada acto cambia la base, reinicia Ontop, mide, arregla **una línea** del mapeo y vuelve a medir. Siempre termina en `deshacer`; si se corta a la mitad, corré `cambio.sh deshacer`.
- El resultado queda en `cambio/resultado.json`, que leen «Por qué confiar» y el momento 2 de la demo.
- Si cambiás la línea del mapeo que lee el petróleo (`prod_pet AS petroleo_m3`), actualizá el patrón en `cambio.sh` y los `arreglo` de `app/dominios/energia.yaml`.

## Una corrección, todos los resultados (`layer/energia/cambio/correccion.sh`)

Saca la participación corregida de Aguada Pichana Este (`linking/energia/participaciones-revisadas.csv`), rearma Rastro, mide y la vuelve a poner. Tarda unos 15 minutos.

```bash
layer/energia/cambio/correccion.sh registrar
git status --short    # al terminar, el CSV y las respuestas guardadas tienen que estar como antes
```

- Mide la respuesta de participación (con Rastro, SQL con enlaces y sin Rastro), lo que entra al modelo de Lab y su explicación.
- El resultado queda en `cambio/correccion.json`, que lee el momento 4 de la demo.
- Lo que se afirma tiene que coincidir con lo medido: la predicción casi no se mueve (la participación es fija dentro de la concesión), así que no se dice que cambie.

## Después

Si cambió un número, actualizalo en el guion y en las diapositivas «La base cambia» y «Una corrección» (skill `mazos`), y en `docs/decisions.md`.
