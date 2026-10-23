# Evaluation runs: research affiliations

Collected on 2026-10-23 (UTC 03:46), following the approved plan (`evaluation-proposal.md`). **Not scored:**
the reference is the blind reviewer's annotation, deferred to the end. Saved answers are in
`layer/afiliaciones/respuestas/`; nothing in them was edited by hand.

- **Model:** fresh Claude Code subagents (general-purpose), Claude Opus 5.5 (`claude-opus-5-5`), one per prompt.
- **What each saw:** an instruction to read one prompt file (generated with `evaluar.py afiliaciones prompt`) and
  reply with its JSON, using no other tool. Retries went back to the same subagent with the harness's error message.
- **Sources:** sample SHA-256 `707ec8cc…`, ROR v2.15 MD5 `55229906…` (`layer/afiliaciones/sources.yaml`).
- **Orchestrator error:** the first attempt of `e1-0-B` was Claude's transcription of the subagent's JSON with its
  backslash escaping left in (a broken regular expression), not the subagent's query. From then on, replies were
  decoded with a script. That attempt stays in the file; the subagent had two real attempts left and used both.

| Run | Prompt SHA-256 (first 16) | Attempts saved | Evaluator's failed attempts | Orchestrator attempts |
|---|---|---|---|---|
| e1-0-B | `9ba17ccb7c3aab88` | 3 | 1 | 1 |
| e1-0-C | `87065656522b2319` | 1 | 0 | 0 |
| e1-0-D | `04ea7b845962591a` | 1 | 0 | 0 |
| e1-1-B | `d04f8460f91df343` | 1 | 0 | 0 |
| e1-1-C | `e9314da5afa355b0` | 1 | 0 | 0 |
| e1-1-D | `585ac601cad2e032` | 1 | 0 | 0 |
| e1-2-B | `641edf829f3b3437` | 1 | 0 | 0 |
| e1-2-C | `ac8526f3ca1f6b43` | 1 | 0 | 0 |
| e1-2-D | `a20d6cbf4edf109e` | 1 | 0 | 0 |
| e1-3-B | `63125947d06e04ff` | 2 | 1 | 0 |
| e1-3-C | `64a7b11afd0dac90` | 1 | 0 | 0 |
| e1-3-D | `0db8e0e2b6e8aabb` | 1 | 0 | 0 |
| e2-0-B | `60d3218790a3c9c0` | 1 | 0 | 0 |
| e2-0-C | `6b790171aba877d2` | 1 | 0 | 0 |
| e2-0-D | `7003f5de32ca3e07` | 1 | 0 | 0 |
| e3-0-B | `f6c0cecbe3716266` | 1 | 0 | 0 |
| e3-0-C | `0fd81195599211e9` | 1 | 0 | 0 |
| e3-0-D | `2a03b4ddb270a4dd` | 1 | 0 | 0 |
| e4-0-B | `0ab2a862fd278f86` | 2 | 1 | 0 |
| e4-0-C | `475b7e6c25ea4db2` | 1 | 0 | 0 |
| e4-0-D | `03da92e2396fb531` | 1 | 0 | 0 |
| e4-1-B | `2136cfaf8fc9c6fe` | 2 | 1 | 0 |
| e4-1-C | `58f737d9428523ee` | 1 | 0 | 0 |
| e4-1-D | `648496ea37fb8447` | 1 | 0 | 0 |
| e4-2-B | `5e7e46e5a0ba4cf9` | 1 | 0 | 0 |
| e4-2-C | `4907fb4516ae1ebe` | 1 | 0 | 0 |
| e4-2-D | `455b78366a39b28e` | 1 | 0 | 0 |
| e4-3-B | `7c0b4fe0707a76d9` | 1 | 0 | 0 |
| e4-3-C | `85b0ea4cc474bfce` | 1 | 0 | 0 |
| e4-3-D | `a302329d45080dfe` | 1 | 0 | 0 |
| e5-0-B | `389f6daf04463b93` | 1 | 0 | 0 |
| e5-0-C | `e02844f5a06b303d` | 1 | 0 | 0 |
| e5-0-D | `44e564a0a992b500` | 1 | 0 | 0 |

All 33 runs have an answer. 38 attempts are saved; 5 of them failed. 4 were the evaluator's own
queries hitting the 60-second statement timeout, and 1 was the orchestrator error above.

**How the incident is counted (decided before scoring):** the orchestrator attempt stays in the saved file as part
of the audit trail, but it is not an evaluator failure. It is excluded from every failure or retry count. `e1-0-B`
therefore had an effective budget of 2 attempts instead of 3; it answered on the second. No remedial run is made,
because the run answered within its effective budget. A clean retry and failure-rate comparison across approaches
reports this run with its reduced budget.
