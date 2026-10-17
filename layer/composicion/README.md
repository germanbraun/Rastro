# Prueba de composición

Cinco preguntas que cruzan 3 o 4 conceptos que ninguna pregunta anterior combinaba (`preguntas.yaml`): sponsors de ensayos con fármacos anti-BRAF, genes de los fármacos de ensayos detenidos de páncreas, reportes serios de los anti-EGFR en ensayos activos de pulmón, fármacos aprobados en ensayos de fase 3 de mama y de pulmón, y el sponsor con más ensayos detenidos de la familia ERBB.

La idea era ver si, en preguntas más complejas, el SQL sobre las tablas de enlaces se equivoca más que SPARQL.

## Resultado (17 oct 2026)

| | SQL + enlaces | Rastro |
|---|---|---|
| Correctas, 5 preguntas de 3 o 4 cruces | **5 de 5** | **5 de 5** |
| Correctas, 3 preguntas con clases de fármaco | **3 de 3** | **3 de 3** |
| Al primer intento | 8 | 7 (una consulta tardó más de 120 s en Ontop y se reescribió) |

Después se sumaron 3 preguntas con clases de fármaco (m6 a m8): terapia dirigida, anticuerpos monoclonales y quimioterapia, según la clasificación ATC. En Rastro, «terapia dirigida» no tiene mapeo: Ontop la deduce de la ontología. El SQL con enlaces tiene la misma tabla (`linking.drug_class`) y la misma definición en su documentación. **Los dos acertaron 3 de 3 al primer intento.**

**No hubo diferencia.** Con las tablas de enlaces documentadas, un LLM fuerte escribe joins de 6 u 8 tablas sin errores. La ventaja de la capa semántica no está en la dificultad de la consulta.

Mismo método que la evaluación: subagentes de Claude Code (Claude Opus 5.5), el mismo prompt, hasta 3 intentos, y el mismo puntaje. Las referencias las escribió un asistente de IA.

```bash
docker compose run --rm -T layer-eval python /layer/composicion/manual.py puntaje
```
