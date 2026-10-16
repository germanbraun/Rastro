# Rastro Layer · en una página

**Preguntas de negocio sobre ensayos de oncología, con la respuesta y de dónde viene cada dato.**

## El problema

Cuatro fuentes públicas que no se hablan: ensayos (AACT), fármacos (ChEMBL), eventos adversos (openFDA) y enfermedades (MeSH). El mismo fármaco aparece como «Pembrolizumab 200 mg», CHEMBL3137343 y «KEYTRUDA».

## Qué hace Rastro

1. **Enlaza** una vez: reconoce qué fármaco nombra cada ensayo, revisado a mano.
2. **Nombra** con un vocabulario de negocio: ensayo, fármaco, target, sponsor, evento adverso.
3. **Responde**: un LLM pregunta en esos conceptos y cada dato dice de qué fuente sale.

Tecnología abierta y estándar: OWL, R2RML y SPARQL, con Ontop, Postgres y GraphDB.

## Los números

| | LLM solo | LLM + SQL directo | LLM + Rastro |
|---|---|---|---|
| Preguntas correctas (de 20) | 5 | 18 | **20** |
| Formas de reconocer un fármaco | — | 4 distintas | **1, revisada** |
| Tiempo total de las queries | — | 20 s | **2 s** |
| Queries que necesitaron reintento | — | 3 | **0** |
| Dice de dónde sale cada dato | No | No | **Sí** |

Mismo LLM (Claude Opus 5.5) en las tres formas. Cada diferencia se revisó contra ensayos reales.

**Lo que integramos:** 106.483 ensayos de oncología · 3.739 fármacos · 774 de 778 fármacos aprobados con sus eventos adversos · MeSH completo · 81 % de las intervenciones de tipo fármaco enlazadas, con 98-99 % de precisión.

## La ventaja real

No es cuántas acierta, sino cuánto se puede confiar. Los errores del SQL directo no avisan: 488 ensayos en lugar de 438 parece razonable. Rastro usa siempre la misma definición y muestra la fuente de cada columna.

## Límites, dichos de entrada

- Con las mismas tablas de enlaces, el SQL directo probablemente acertaría igual: el valor está en la integración revisada, expuesta como vocabulario estándar.
- Es una foto fija de octubre de 2026, no datos en vivo.
- La evaluación son 20 preguntas propias.

## Próximo paso

Un piloto con datos del cliente sumados a las fuentes públicas.

---

Detalle de cada número y cómo se midió: [results.md](results.md).
