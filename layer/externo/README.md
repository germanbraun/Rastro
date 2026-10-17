# Enlazar con datos de afuera: Wikidata

Una sola consulta SPARQL, ejecutada en GraphDB, que combina tres grafos:

- **Rastro**, a través de Ontop: fármacos anti-HER2 aprobados y cuántos ensayos de cáncer de mama tienen.
- **MeSH**, en el propio GraphDB: el descriptor de cáncer de mama.
- **Wikidata**, en internet: qué enfermedades trata cada fármaco, en español.

El cruce es el **ChEMBL ID**: Rastro y Wikidata usan el mismo identificador, así que no hace falta cargar nada ni escribir un enlace nuevo. Es lo que una base SQL no hace en una sola consulta: unir datos de otra organización, en vivo, por un identificador compartido.

```bash
curl -s -H 'Accept: text/csv' --data-urlencode query@layer/externo/wikidata.rq http://localhost:7210/repositories/rastro
```

Tarda unos 10 segundos y necesita internet. Para la demo en vivo, el resultado del 17 oct 2026 está en `resultado-2026-10-17.csv`:

| Fármaco | Ensayos de cáncer de mama | Trata, según Wikidata |
|---|---|---|
| Trastuzumab | 670 | carcinoma ductal infiltrante, neoplasia secundaria, cáncer de mama |
| Neratinib | 40 | cáncer de mama |
| Tucatinib | 35 | cáncer de mama |
| Afatinib | 16 | carcinoma pulmonar no microcítico |
| Vandetanib | 8 | cáncer tiroideo, cáncer medular tiroideo |

Afatinib y vandetanib están aprobados para otros cánceres y se prueban en mama: un dato que ninguna de las cuatro fuentes de Rastro tiene así. Wikidata no siempre está completo (pertuzumab y lapatinib no tienen la enfermedad cargada).

Los ensayos cuentan cualquier fase, a diferencia de la pregunta de la demo (solo fase 3).

**Requisito:** Wikidata pide que quien consulta se identifique. GraphDB lo hace con `-Dhttp.agent` en `infra/docker-compose.yml`.
