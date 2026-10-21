---
name: cerrar-fase
description: Cerrar un paso o una fase del plan de Rastro (verificar, marcar el plan, documentar decisiones y commitear). Usalo cuando termina un checkpoint o un bloque de trabajo.
---

# Cerrar una fase

1. **Verificá** con la skill `verificar`. No cierres una fase con su checkpoint fallando.
2. **Revisá que los números coincidan** en todos lados: lo que cambió en la app (que los lee de sus JSON) tiene que decir lo mismo en `docs/decisions.md`, el guion de la demo, el estudio de Lab y las diapositivas (skill `mazos`).
3. **Marcá el plan** en `docs/plan.md`: los pasos hechos con `[x]`. Mantené el plan corto: un resumen de lo logrado, no la historia.
4. **Decisiones:** una entrada en `docs/decisions.md` por cada decisión nueva, con fecha, qué se decidió, por qué y los números que la respaldan. Si una decisión es una regla que hay que seguir siempre, va también a `CLAUDE.md` o a una skill.
5. **README y `CLAUDE.md`:** si cambió cómo se levanta, se carga o se mide algo.
6. **Antes de commitear, revisá secretos y nombres:**
   ```bash
   grep -E '^[A-Z_]*(KEY|TOKEN|PASSWORD|USER)=.+' .env.example   # solo valores de desarrollo local (rastro), nunca claves
   git status --short                                            # nada de .env ni data/raw
   python3 -m ruff check .                                       # sin errores
   python3 -m pytest -q                                          # las pruebas pasan
   ```
   Y que no haya nombres de productos ni empresas comerciales de grafos de conocimiento (ver `CLAUDE.md`).
7. **Commit en español**: un título que diga qué se ve distinto («Rastro Lab: …», «Petróleo y gas: …») y un párrafo corto con los números. Termina con la línea `Co-Authored-By` que corresponda.
8. **Push solo si el usuario lo pide.**
