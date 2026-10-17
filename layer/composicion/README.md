# Prueba de composición

Cinco preguntas que cruzan 3 o 4 conceptos que ninguna pregunta anterior combinaba (`preguntas.yaml`): sponsors de ensayos con fármacos anti-BRAF, genes de los fármacos de ensayos detenidos de páncreas, reportes serios de los anti-EGFR en ensayos activos de pulmón, fármacos aprobados en ensayos de fase 3 de mama y de pulmón, y el sponsor con más ensayos detenidos de la familia ERBB.

La idea era ver si, en preguntas más complejas, el SQL sobre las tablas de enlaces se equivoca más que SPARQL.

## Resultado (17 oct 2026)

| | SQL + enlaces | Rastro |
|---|---|---|
| Correctas | **5 de 5** | **5 de 5** |
| Al primer intento | 5 | 4 (una consulta tardó más de 120 s en Ontop y se reescribió) |

**No hubo diferencia.** Con las tablas de enlaces documentadas, un LLM fuerte escribe joins de 6 u 8 tablas sin errores. La ventaja de la capa semántica no está en la dificultad de la consulta.

Mismo método que la evaluación: subagentes de Claude Code (Claude Opus 5.5), el mismo prompt, hasta 3 intentos, y el mismo puntaje. Las referencias las escribió un asistente de IA.

```bash
docker compose run --rm -T layer-eval python /layer/composicion/manual.py puntaje
```
