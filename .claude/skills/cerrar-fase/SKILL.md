---
name: cerrar-fase
description: Cerrar un paso o una fase del plan de Rastro (marcar el plan, documentar decisiones y commitear). Usalo cuando termina un checkpoint o un bloque de trabajo.
---

# Cerrar una fase

1. **Verificá** con la skill `verificar`. No cierres una fase con su checkpoint fallando.
2. **Marcá el plan** en `docs/plan.md`: los pasos hechos con `[x]`, y la fase con ✅ si su checkpoint pasó. Mantené el plan corto: un resumen de lo logrado, no la historia.
3. **Decisiones:** una entrada en `docs/decisions.md` por cada decisión nueva, con fecha, qué se decidió, por qué y los números que la respaldan.
4. **README:** si cambió cómo se levanta o se carga algo.
5. **Antes de commitear, revisá secretos:**
   ```bash
   grep -E '^(AACT_USER|AACT_PASSWORD|OPENFDA_API_KEY)=.+' .env.example   # no debe imprimir nada
   git status --short                                                    # nada de .env ni data/raw
   ```
6. **Commit en español**, con el formato `Fase N: <qué cambió>` y viñetas cortas en el cuerpo.
7. **Push solo si el usuario lo pide.**
