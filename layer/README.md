# Rastro Layer

Preguntas en lenguaje natural sobre las fuentes integradas. `answer.py` tiene tres formas de responder (A: el LLM solo, B: SQL sobre las tablas crudas, C: SPARQL sobre Rastro) y `eval/` las compara con 20 preguntas.

Esto es oncología. Petróleo y gas y proveedores se evalúan con `evaluar.py` (ver su docstring), con tres formas: B, sin Rastro (SQL sobre las tablas crudas); D, SQL con las tablas de enlaces de Rastro; y C, con Rastro (SPARQL). Los resultados quedan en `layer/<dominio>/resultados.md`.

```bash
docker compose run --rm -T layer-eval python /layer/evaluar.py energia puntaje
```

## Qué LLM usar

Se elige en `.env` con `RASTRO_PROVIDER`:

| Opción | Qué hace falta | Costo |
|---|---|---|
| `anthropic` (por defecto) | `ANTHROPIC_API_KEY` de la Claude API | De pago por uso: unos pocos dólares por una corrida completa con Claude Opus 5.5 |
| `ollama` | Ollama instalado y corriendo en la Mac | Gratis, sin internet; más débil para escribir queries |
| Ninguna | Nada | `eval/manual.py` imprime cada prompt para responderlo a mano (por ejemplo, en claude.ai) |

Las respuestas de la evaluación ya están guardadas en `eval/results.json`: para verlas y puntuarlas no hace falta ningún LLM.

```bash
docker compose run --rm layer-eval
```

## Usar Ollama en la Mac

Ollama corre en la Mac, fuera de Docker, para aprovechar la GPU de Apple.

1. Instalar Ollama desde https://ollama.com y abrirlo.
2. Bajar un modelo bueno para código (unos 5 GB):
   ```bash
   ollama pull qwen2.5-coder:7b
   ```
3. En `.env`:
   ```
   RASTRO_PROVIDER=ollama
   ```
   Opcional: `RASTRO_MODEL` para otro modelo (por ejemplo `qwen2.5-coder:14b`, mejor y más lento) y `OLLAMA_URL` si Ollama no está en el puerto por defecto.
4. Regenerar las respuestas con ese modelo, sin pisar las guardadas de Claude: copiar antes `eval/results.json`, y correr
   ```bash
   docker compose run --rm layer-eval python /layer/eval/run.py --fresh A B C
   ```

El contenedor llega a Ollama por `host.docker.internal:11434`.
